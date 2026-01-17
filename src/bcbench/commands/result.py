import json
import re
from pathlib import Path

import typer
from typing_extensions import Annotated

from bcbench.cli_options import DatasetPath, OutputDir, RunId
from bcbench.config import get_config
from bcbench.logger import get_logger
from bcbench.results import BaseEvaluationResult, EvaluationResultSummary, create_console_summary, create_github_job_summary, create_result_from_json, write_bceval_results

logger = get_logger(__name__)


_config = get_config()

result_app = typer.Typer(help="Process and display evaluation results")


@result_app.command("summarize")
def result_summarize(
    run_id: RunId,
    result_dir: OutputDir = _config.paths.evaluation_results_path,
    result_pattern: Annotated[str, typer.Option(help="Pattern for the per instances result files")] = f"*{_config.file_patterns.result_pattern}",
    dataset_path: DatasetPath = _config.paths.dataset_path,
    summary_output: Annotated[str, typer.Option(help="Output filename for summary JSON")] = "evaluation_summary.json",
    bceval_output: Annotated[str, typer.Option(help="Output filename for bceval results")] = "bceval_results.jsonl",
):
    """
    Summarize evaluation results from a completed run.

    Aggregates individual instance results, displays job summaries and generates bceval output format.
    """
    run_dir: Path = result_dir / run_id

    if not run_dir.exists():
        logger.error(f"Results directory not found: {run_dir}")
        raise typer.Exit(code=1)

    result_files = list(run_dir.rglob(result_pattern))
    if not result_files:
        logger.error(f"No result files matching '{result_pattern}' found in {run_dir}")
        raise typer.Exit(code=1)

    # Filter to only instance-specific result files (exclude combined results and summaries)
    instance_pattern_regex = re.compile(_config.file_patterns.instance_pattern)
    result_files = [f for f in result_files if instance_pattern_regex.match(f.stem)]

    if not result_files:
        logger.error(f"No instance-specific result files found in {run_dir}")
        raise typer.Exit(code=1)

    results: list[BaseEvaluationResult] = []
    for results_path in result_files:
        logger.info(f"Reading results from: {results_path}")
        with open(results_path) as f:
            results.extend(create_result_from_json(json.loads(line)) for line in f if line.strip())

    if not results:
        logger.error("No results found in the result files")
        raise typer.Exit(code=1)

    write_bceval_results(results, run_dir, run_id, dataset_path, bceval_output)

    if _config.env.github_actions:
        create_github_job_summary(results)
    else:
        create_console_summary(results)

    # Save summary JSON
    summary = EvaluationResultSummary.from_results(results, run_id=run_id)
    summary.save(run_dir, summary_output)


def _get_combination_key(result: EvaluationResultSummary) -> tuple[str, str, str | None]:
    """Get a unique key for agent+model+experiment combination."""
    exp_key = None
    if result.experiment and not result.experiment.is_empty():
        exp_key = json.dumps(result.experiment.model_dump(mode="json"), sort_keys=True)
    return (result.agent_name, result.model, exp_key)


@result_app.command("update")
def result_update(
    evaluation_summary: Annotated[Path, typer.Argument(help="Path to a single evaluation run's summary JSON", exists=True, file_okay=True, dir_okay=False)],
    leaderboard_dir: Annotated[Path, typer.Option(help="Path to the directory containing category-specific leaderboard files")] = _config.paths.leaderboard_dir,
    n: Annotated[int, typer.Option(help="Max number of results to store per agent+model+experiment combination (for pass@k)")] = 5,
):
    """
    Update the public leaderboard with a new evaluation summary.

    Takes a single evaluation run's summary and updates the appropriate category-specific leaderboard file (e.g. bug-fix.json).
    Supports storing multiple results per agent-model-experiment combination for multi-run metrics.

    Stores up to n results per combination, removing the oldest when exceeding n.
    """
    logger.info(f"Loading evaluation summary from: {evaluation_summary}")
    with open(evaluation_summary, encoding="utf-8") as f:
        new_result = EvaluationResultSummary.model_validate_json(f.read())

    logger.info(f"Processing result for agent '{new_result.agent_name}' with model '{new_result.model}' in category '{new_result.category.value}'")

    # Determine the appropriate leaderboard file based on category
    leaderboard_path = leaderboard_dir / f"{new_result.category.value}.json"

    logger.info(f"Using leaderboard file: {leaderboard_path}")

    # Load or create leaderboard file
    if leaderboard_path.exists():
        logger.info(f"Loading existing leaderboard from: {leaderboard_path}")
        with open(leaderboard_path, encoding="utf-8") as f:
            existing_results: list[EvaluationResultSummary] = [EvaluationResultSummary.model_validate(entry) for entry in json.load(f)]
    else:
        logger.info(f"Creating new leaderboard file: {leaderboard_path}")
        existing_results = []

    # Group results by combination key
    new_result_key: tuple[str, str, str | None] = _get_combination_key(new_result)

    # Find all results matching this combination
    matching_indices: list[int] = [i for i, r in enumerate(existing_results) if _get_combination_key(r) == new_result_key]

    if n == 1:
        # Legacy behavior: replace existing result
        if matching_indices:
            logger.info(f"Found existing result for '{new_result.agent_name}' + '{new_result.model}', replacing...")
            existing_results[matching_indices[0]] = new_result
        else:
            logger.info(f"No existing result found for '{new_result.agent_name}' + '{new_result.model}', adding new entry")
            existing_results.append(new_result)
    else:
        # Multi-result mode for pass@k
        matching_results: list[EvaluationResultSummary] = [existing_results[i] for i in matching_indices]

        if len(matching_results) < n:
            # Room for more results, just append
            logger.info(f"Adding result ({len(matching_results) + 1}/{n}) for '{new_result.agent_name}' + '{new_result.model}'")
            existing_results.append(new_result)
        else:
            # Need to remove oldest and add new
            # Sort matching results by date to find oldest
            matching_with_indices: list[tuple[int, EvaluationResultSummary]] = [(i, existing_results[i]) for i in matching_indices]
            matching_with_indices.sort(key=lambda x: x[1].date)
            oldest_index = matching_with_indices[0][0]

            logger.info(f"Replacing oldest result (date: {existing_results[oldest_index].date}) for '{new_result.agent_name}' + '{new_result.model}'")
            existing_results[oldest_index] = new_result

    # Write back as list of dicts
    with open(leaderboard_path, "w", encoding="utf-8") as f:
        json.dump([result.to_dict() for result in existing_results], f, indent=2)
        f.write("\n")

    logger.info(f"Successfully updated leaderboard at: {leaderboard_path}")
