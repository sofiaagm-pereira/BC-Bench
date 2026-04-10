"""Utilities for loading counterfactual dataset entries from JSONL files."""

from pathlib import Path

from bcbench.dataset.counterfactual_entry import CounterfactualEntry
from bcbench.dataset.dataset_entry import BugFixEntry
from bcbench.exceptions import EntryNotFoundError

__all__ = ["load_counterfactual_entries"]


def _load_raw_counterfactual_entries(cf_path: Path, entry_id: str | None = None) -> list[CounterfactualEntry]:
    if not cf_path.exists():
        raise FileNotFoundError(f"Counterfactual dataset file not found: {cf_path}")

    entries: list[CounterfactualEntry] = []

    with open(cf_path, encoding="utf-8") as file:
        for line in file:
            stripped_line: str = line.strip()
            if not stripped_line:
                continue

            entry = CounterfactualEntry.model_validate_json(stripped_line)

            if entry_id:
                # Match by exact variant ID
                if entry.instance_id == entry_id:
                    return [entry]
                # Match by base instance ID — return all variants for that family
                if entry.base_instance_id == entry_id:
                    entries.append(entry)
                    continue
                continue

            entries.append(entry)

    if entry_id and not entries:
        raise EntryNotFoundError(entry_id)

    return entries


def _resolve_base_entry(base_instance_id: str, base_entries: list[BugFixEntry]) -> BugFixEntry:
    for entry in base_entries:
        if entry.instance_id == base_instance_id:
            return entry
    raise EntryNotFoundError(base_instance_id)


def load_counterfactual_entries(
    cf_path: Path,
    base_path: Path,
    entry_id: str | None = None,
) -> list[tuple[CounterfactualEntry, BugFixEntry]]:
    """Load counterfactual entries and resolve their base dataset entries.

    Args:
        cf_path: Path to counterfactual JSONL file
        base_path: Path to base dataset JSONL file (bcbench.jsonl)
        entry_id: Optional entry ID — can be a variant ID (exact match) or base instance ID (all variants)

    Returns:
        List of (CounterfactualEntry, BugFixEntry) tuples
    """
    cf_entries = _load_raw_counterfactual_entries(cf_path, entry_id)
    base_entries = BugFixEntry.load(base_path)

    return [(cf_entry, _resolve_base_entry(cf_entry.base_instance_id, base_entries)) for cf_entry in cf_entries]
