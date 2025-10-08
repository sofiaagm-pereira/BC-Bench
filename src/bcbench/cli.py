"""CLI entry point for bcbench using typer."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from bcbench.core.logger import setup_logger
from bcbench.core.utils import DATASET_PATH, NAV_REPO_PATH
from bcbench.dataset import dataset_app

app = typer.Typer(
    name="bcbench",
    help="BC-Bench: Benchmarking tool for Business Central (AL) ecosystem",
    no_args_is_help=True,
    add_completion=False,
)

collect_app = typer.Typer(help="Collect dataset entries from various sources")
run_app = typer.Typer(help="Run benchmarks with various agents")

app.add_typer(collect_app, name="collect")
app.add_typer(run_app, name="run")
app.add_typer(dataset_app, name="dataset")


@app.callback()
def logging_callback(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable debug logging")] = False,
):
    """Setup logging for all commands."""
    setup_logger(verbose)


@app.command("version")
def show_version():
    """Show bcbench version."""
    from importlib.metadata import version

    print(f"bcbench version {version('bcbench')}")


@collect_app.command("nav")
def collect_nav(
    pr_number: Annotated[int, typer.Argument(help="Pull request number to collect")],
    output: Annotated[Path, typer.Option(help="Output file path")] = DATASET_PATH,
    overwrite: Annotated[bool, typer.Option(help="Overwrite output file instead of appending")] = False,
):
    """
    Collect dataset entry from Azure DevOps NAV pull request.

    Try it out with: bcbench collect nav 210528 --output dataset/bcbench_nav.jsonl --overwrite
    """
    from bcbench.collection.collect_nav import collect_nav_entry

    collect_nav_entry(
        pr_number=pr_number,
        output=output,
        overwrite=overwrite,
    )


@run_app.command("mini")
def run_mini(
    dataset_path: Annotated[Path, typer.Option(help="Path to dataset file")] = DATASET_PATH,
    entry_id: Annotated[Optional[str], typer.Option(help="Single entry ID to run")] = None,
    version: Annotated[Optional[str], typer.Option(help="Run all entries for this version")] = None,
    repo_path: Annotated[Path, typer.Option(help="Path to NAV repository")] = NAV_REPO_PATH,
    use_container: Annotated[bool, typer.Option(help="Allow Agent to use BC container")] = False,
    container_name: Annotated[Optional[str], typer.Option(help="BC container name (required if --use_container)")] = None,
    username: Annotated[str, typer.Option(help="Username for BC container")] = "admin",
    password: Annotated[Optional[str], typer.Option(help="Password for BC container (or set BC_CONTAINER_PASSWORD env var)")] = None,
    step_limit: Annotated[int, typer.Option(help="Maximum number of agent steps")] = 20,
    cost_limit: Annotated[float, typer.Option(help="Maximum cost limit for agent")] = 1.0,
):
    """
    Run mini-bc-agent on dataset entries.

    Specify either --entry-id for a single entry or --version for all entries of that version.

    Examples:
        bcbench run mini --entry-id "microsoftInternal__NAV-210528" --step-limit 5
    """
    from bcbench.agent.mini import run_mini_agent

    run_mini_agent(
        dataset_path=dataset_path,
        entry_id=entry_id,
        version=version,
        repo_path=repo_path,
        use_container=use_container,
        container_name=container_name,
        username=username,
        password=password,
        step_limit=step_limit,
        cost_limit=cost_limit,
    )


if __name__ == "__main__":
    app()
