"""Core utilities and shared components for bcbench."""

from bcbench.core.dataset_entry import DatasetEntry, TestEntry
from bcbench.core.utils import (
    extract_patches,
    strip_html,
    normalize_repo_subpath,
    find_project_paths_from_patch,
    colored,
    CYAN,
    GREEN,
    YELLOW,
    BLUE,
    MAGENTA,
    RED,
    GREY,
    BC_BENCH_ROOT,
    DATASET_PATH,
    DATASET_SCHEMA_PATH,
    NAV_REPO_PATH,
)

# Don't import BCEnvironment here to avoid mini-swe-agent imports
# Import it directly when needed: from bcbench.agent.bc_environment import BCEnvironment

__all__ = [
    "DatasetEntry",
    "TestEntry",
    "extract_patches",
    "strip_html",
    "normalize_repo_subpath",
    "find_project_paths_from_patch",
    "colored",
    "CYAN",
    "GREEN",
    "YELLOW",
    "BLUE",
    "MAGENTA",
    "RED",
    "GREY",
    "BC_BENCH_ROOT",
    "DATASET_PATH",
    "DATASET_SCHEMA_PATH",
    "NAV_REPO_PATH",
]
