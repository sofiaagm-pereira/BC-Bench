"""Compute code complexity metrics for BC-Bench tasks using rust-code-analysis-cli.

For each task in the dataset, extracts the files touched by the gold patch,
retrieves them at the base_commit (before fix), and computes metrics using
rust-code-analysis-cli with AL language support.

Usage:
    uv run python scripts/compute_metrics.py
    uv run python scripts/compute_metrics.py --output metrics.jsonl
    uv run python scripts/compute_metrics.py --entry-id microsoftInternal__NAV-210528
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from bcbench.collection.patch_utils import extract_file_paths_from_patch
from bcbench.dataset.dataset_entry import DatasetEntry
from bcbench.dataset.dataset_loader import load_dataset_entries

REPO_PATH_MAP: dict[str, Path] = {
    "microsoftInternal/NAV": Path(r"C:\depot\NAV"),
    "microsoft/BCApps": Path(r"C:\depot\BCApps"),
}

DATASET_PATH = Path(__file__).resolve().parent.parent / "dataset" / "bcbench.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "dataset" / "bcbench_metrics.jsonl"


def get_file_at_commit(repo_path: Path, commit: str, file_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{file_path}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def compute_metrics_for_content(content: str) -> dict | None:
    with tempfile.NamedTemporaryFile(suffix=".al", mode="w", encoding="utf-8", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["rust-code-analysis-cli", "-m", "-p", temp_path, "-O", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        raw = json.loads(result.stdout)
        # Return top-level file metrics only (drop nested spaces for brevity)
        return raw.get("metrics")
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"  WARNING: metrics computation failed: {e}", file=sys.stderr)
        return None
    finally:
        Path(temp_path).unlink(missing_ok=True)


def process_entry(entry: DatasetEntry) -> dict:
    repo_path = REPO_PATH_MAP.get(entry.repo)
    if repo_path is None:
        print(f"  WARNING: unknown repo '{entry.repo}', skipping files", file=sys.stderr)
        return build_result(entry, [])

    fix_files = extract_file_paths_from_patch(entry.patch)

    file_results: list[dict] = []
    for file_path in fix_files:
        content = get_file_at_commit(repo_path, entry.base_commit, file_path)
        if content is None:
            print(f"  SKIP (new file): {file_path}", file=sys.stderr)
            file_results.append({"path": file_path, "is_new_file": True, "metrics": None})
            continue

        metrics = compute_metrics_for_content(content)
        file_results.append({"path": file_path, "is_new_file": False, "metrics": metrics})

    return build_result(entry, file_results)


def build_result(entry: DatasetEntry, file_results: list[dict]) -> dict:
    return {
        "instance_id": entry.instance_id,
        "repo": entry.repo,
        "base_commit": entry.base_commit,
        "area": entry.metadata.area,
        "project_name": entry.extract_project_name(),
        "num_fix_files": len(file_results),
        "num_files_with_metrics": sum(1 for f in file_results if f["metrics"] is not None),
        "files": file_results,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Compute code metrics for BC-Bench tasks")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL file path")
    parser.add_argument("--entry-id", type=str, default=None, help="Process a single entry by ID")
    args = parser.parse_args()

    entries = load_dataset_entries(DATASET_PATH, entry_id=args.entry_id)
    print(f"Processing {len(entries)} tasks...", file=sys.stderr)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out:
        for i, entry in enumerate(entries, 1):
            print(f"[{i}/{len(entries)}] {entry.instance_id} ({len(extract_file_paths_from_patch(entry.patch))} files)", file=sys.stderr)
            result = process_entry(entry)
            out.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Done. Output written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
