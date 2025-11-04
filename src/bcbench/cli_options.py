"""Reusable CLI option definitions for typer commands."""

from pathlib import Path
from typing import Annotated

import typer

# Type aliases for cleaner command signatures
# Note: Defaults are provided in function signatures, not here
DatasetPath = Annotated[
    Path,
    typer.Option(help="Path to dataset file"),
]

RepoPath = Annotated[
    Path,
    typer.Option(help="Path to repository"),
]

SchemaPath = Annotated[
    Path,
    typer.Option(help="Path to schema file"),
]

OutputDir = Annotated[
    Path,
    typer.Option(help="Directory to save evaluation results"),
]

OptionalOutputDir = Annotated[
    Path | None,
    typer.Option(help="Directory to save output result"),
]

ContainerName = Annotated[
    str,
    typer.Option(help="BC container name"),
]

OptionalContainerName = Annotated[
    str | None,
    typer.Option(help="BC container name (required if --use-container)"),
]

ContainerUsername = Annotated[
    str,
    typer.Option(help="Username for BC container"),
]

ContainerPassword = Annotated[
    str | None,
    typer.Option(help="Password for BC container (or set BC_CONTAINER_PASSWORD env var)"),
]
