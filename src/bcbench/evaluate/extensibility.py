import json
from collections.abc import Callable

from bcbench.config import get_config
from bcbench.dataset import ExtensibilityDatasetEntry
from bcbench.evaluate.base import EvaluationPipeline
from bcbench.logger import get_logger, github_log_group
from bcbench.operations.setup_operations import setup_repo_prebuild
from bcbench.results.extensibility import ExtensibilityResult
from bcbench.types import EvaluationContext, ExtAgentMetrics

logger = get_logger(__name__)
_config = get_config()

__all__ = ["ExtensibilityPipeline"]


class ExtensibilityPipeline(EvaluationPipeline):
    def setup(self, context: EvaluationContext) -> None:
        setup_repo_prebuild(context.entry, context.repo_path)

    def run_agent(self, context: EvaluationContext, agent_runner: Callable) -> None:
        with github_log_group(f"{context.agent_name} -- Entry: {context.entry.instance_id}"):
            context.metrics, context.experiment = agent_runner(context)

    def evaluate(self, context: EvaluationContext) -> None:
        """Evaluate agent output by comparing with expected results."""
        # Validate agent produced JSON output and compare with expected
        resolved = False
        error_message = None

        if isinstance(context.entry, ExtensibilityDatasetEntry):
            # Extract expected labels from dataset
            expected_labels_str = context.entry.expected.get("labels", "")
            expected_labels = {label.strip() for label in expected_labels_str.split(",") if label.strip()}

            # Check if agent produced JSON output
            if context.metrics and isinstance(context.metrics, ExtAgentMetrics) and context.metrics.json_output:
                try:
                    # Parse agent's JSON output
                    agent_output = context.metrics.json_output
                    if isinstance(agent_output, str):
                        agent_output = json.loads(agent_output)

                    # Extract outcome and labels
                    final_determination = agent_output.get("final_determination", {})
                    outcome = final_determination.get("outcome", "")
                    agent_labels = final_determination.get("labels_to_apply", [])
                    agent_labels_set = set(agent_labels) if isinstance(agent_labels, list) else set()

                    logger.info(f"Agent outcome: {outcome}, labels: {agent_labels}")
                    logger.info(f"Expected labels: {expected_labels}")

                    # Check if outcome is FEASIBLE and labels match
                    if outcome == "FEASIBLE" and agent_labels_set == expected_labels:
                        resolved = True
                    else:
                        error_message = f"Agent outcome '{outcome}' (expected 'FEASIBLE')" if outcome != "FEASIBLE" else f"Labels mismatch: expected {expected_labels}, got {agent_labels_set}"

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    error_message = f"Failed to parse/validate JSON output: {e}"
                    logger.error(error_message)
            else:
                error_message = "Agent did not produce JSON output"
                logger.warning(error_message)

        # Create result based on validation
        if resolved:
            result = ExtensibilityResult.create_success(context, "")
            logger.info(f"✓ Successfully validated {context.entry.instance_id}")
        else:
            result = ExtensibilityResult.create_test_failure(context, "", error_msg=error_message or "Validation failed")
            logger.warning(f"✗ Validation failed for {context.entry.instance_id}: {error_message}")

        if result is not None:
            result.save(context.result_dir, f"{context.entry.instance_id}{_config.file_patterns.result_pattern}")
        else:
            logger.error(f"No result generated for {context.entry.instance_id}")
            raise RuntimeError(f"No result generated for {context.entry.instance_id}")
