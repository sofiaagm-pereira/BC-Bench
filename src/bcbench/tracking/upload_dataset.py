"""Upload BC-Bench dataset to Braintrust for versioned experiment tracking.

Usage:
    BRAINTRUST_API_KEY=<key> uv run python -m bcbench.tracking.upload_dataset
    BRAINTRUST_API_KEY=<key> uv run python -m bcbench.tracking.upload_dataset --project MyProject
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import braintrust

from bcbench.config import get_config

DEFAULT_PROJECT = "BC-Bench-Thesis"


def upload_dataset(
    project: str = DEFAULT_PROJECT,
    api_key: str | None = None,
) -> None:
    config = get_config()
    base_path = config.paths.dataset_path
    cf_path = config.paths.counterfactual_dataset_path

    dataset = braintrust.init_dataset(
        project=project,
        name="bcbench-al",
        api_key=api_key,
    )

    _upload_file(dataset, base_path, source="base")
    _upload_file(dataset, cf_path, source="counterfactual")

    dataset.flush()
    print(f"Uploaded to project '{project}', dataset 'bcbench-al'")


def _upload_file(dataset: braintrust.Dataset, path: Path, source: str) -> None:
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            instance_id = entry["instance_id"]

            dataset.insert(
                id=instance_id,
                input={"instance_id": instance_id},
                expected=entry.get("patch", ""),
                metadata={
                    "source": source,
                    "base_instance_id": entry.get("base_instance_id"),
                    "failure_layer": entry.get("failure_layer"),
                    "variant_description": entry.get("variant_description"),
                },
                tags=[source],
            )
            count += 1

    print(f"  Inserted {count} entries from {path.name} ({source})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload BC-Bench dataset to Braintrust")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="Braintrust project name")
    parser.add_argument("--api-key", default=None, help="Braintrust API key (or set BRAINTRUST_API_KEY)")
    args = parser.parse_args()

    upload_dataset(project=args.project, api_key=args.api_key)
