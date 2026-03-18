"""Tests for counterfactual dataset entry, loader, and result."""

import json
from pathlib import Path

import pytest

from bcbench.dataset import CounterfactualEntry, DatasetEntry, load_counterfactual_entries
from bcbench.dataset.dataset_entry import TestEntry
from bcbench.exceptions import EntryNotFoundError
from bcbench.results.counterfactual import CounterfactualResult
from bcbench.types import EvaluationCategory
from tests.conftest import (
    VALID_BASE_COMMIT,
    VALID_CREATED_AT,
    VALID_ENVIRONMENT_VERSION,
    VALID_PATCH,
    VALID_PROJECT_PATHS,
    VALID_REPO,
    VALID_TEST_PATCH,
    create_dataset_entry,
    create_evaluation_context,
    create_test_entry,
)

VALID_CF_INSTANCE_ID = "microsoftInternal__NAV-123456__cf-1"
VALID_BASE_INSTANCE_ID = "microsoftInternal__NAV-123456"
VALID_CF_PATCH = "diff --git a/cf.al b/cf.al\n+counterfactual fix"
VALID_CF_TEST_PATCH = "diff --git a/cf_test.al b/cf_test.al\n+counterfactual test"


def create_counterfactual_entry(
    instance_id: str = VALID_CF_INSTANCE_ID,
    base_instance_id: str = VALID_BASE_INSTANCE_ID,
    variant_description: str = "Modified test expectation",
    test_patch: str = VALID_CF_TEST_PATCH,
    patch: str = VALID_CF_PATCH,
    fail_to_pass: list[TestEntry] | None = None,
    problem_statement_override: str = "dataset/problemstatement/microsoftInternal__NAV-123456__cf-1",
    intervention_type: str | None = None,
) -> CounterfactualEntry:
    if fail_to_pass is None:
        fail_to_pass = [create_test_entry()]

    return CounterfactualEntry(
        instance_id=instance_id,
        base_instance_id=base_instance_id,
        variant_description=variant_description,
        test_patch=test_patch,
        patch=patch,
        fail_to_pass=fail_to_pass,
        problem_statement_override=problem_statement_override,
        intervention_type=intervention_type,
    )


def create_counterfactual_file(tmp_path: Path, entries: list[CounterfactualEntry] | None = None) -> Path:
    if entries is None:
        entries = [create_counterfactual_entry()]

    cf_path = tmp_path / "counterfactual.jsonl"
    with open(cf_path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry.model_dump(by_alias=True, mode="json")) + "\n")
    return cf_path


def create_base_dataset_file(tmp_path: Path, entries: list[DatasetEntry] | None = None) -> Path:
    if entries is None:
        entries = [create_dataset_entry()]

    dataset_path = tmp_path / "bcbench.jsonl"
    with open(dataset_path, "w") as f:
        for entry in entries:
            entry_dict = {
                "instance_id": entry.instance_id,
                "repo": entry.repo,
                "base_commit": entry.base_commit,
                "environment_setup_version": entry.environment_setup_version,
                "FAIL_TO_PASS": [{"codeunitID": t.codeunitID, "functionName": list(t.functionName)} for t in entry.fail_to_pass],
                "PASS_TO_PASS": [{"codeunitID": t.codeunitID, "functionName": list(t.functionName)} for t in entry.pass_to_pass],
                "project_paths": entry.project_paths,
                "patch": entry.patch,
                "test_patch": entry.test_patch,
                "created_at": entry.created_at,
            }
            f.write(json.dumps(entry_dict) + "\n")
    return dataset_path


class TestCounterfactualEntryModel:
    def test_valid_entry_is_created(self):
        entry = create_counterfactual_entry()
        assert entry.instance_id == VALID_CF_INSTANCE_ID
        assert entry.base_instance_id == VALID_BASE_INSTANCE_ID

    def test_invalid_instance_id_pattern_raises(self):
        with pytest.raises(Exception):
            create_counterfactual_entry(instance_id="invalid-id")

    def test_invalid_base_instance_id_pattern_raises(self):
        with pytest.raises(Exception):
            create_counterfactual_entry(base_instance_id="invalid")

    def test_intervention_type_is_optional(self):
        entry = create_counterfactual_entry(intervention_type=None)
        assert entry.intervention_type is None

    def test_intervention_type_is_set(self):
        entry = create_counterfactual_entry(intervention_type="test-spec-change")
        assert entry.intervention_type == "test-spec-change"

    def test_model_is_frozen(self):
        entry = create_counterfactual_entry()
        with pytest.raises(Exception):
            entry.instance_id = "new_id"


class TestCounterfactualToDatasetEntry:
    def test_merges_with_base_entry(self):
        cf_entry = create_counterfactual_entry()
        base_entry = create_dataset_entry()

        merged = cf_entry.to_dataset_entry(base_entry)

        assert merged.instance_id == cf_entry.instance_id
        assert merged.repo == base_entry.repo
        assert merged.base_commit == base_entry.base_commit
        assert merged.project_paths == base_entry.project_paths
        assert merged.environment_setup_version == base_entry.environment_setup_version
        assert merged.test_patch == cf_entry.test_patch
        assert merged.patch == cf_entry.patch
        assert merged.fail_to_pass == cf_entry.fail_to_pass

    def test_merged_entry_is_valid_dataset_entry(self):
        cf_entry = create_counterfactual_entry()
        base_entry = create_dataset_entry()

        merged = cf_entry.to_dataset_entry(base_entry)
        assert isinstance(merged, DatasetEntry)


class TestCounterfactualLoader:
    def test_loads_all_entries(self, tmp_path: Path):
        cf_entries = [
            create_counterfactual_entry(instance_id="microsoftInternal__NAV-123456__cf-1"),
            create_counterfactual_entry(instance_id="microsoftInternal__NAV-123456__cf-2"),
        ]
        cf_path = create_counterfactual_file(tmp_path, cf_entries)
        base_path = create_base_dataset_file(tmp_path)

        result = load_counterfactual_entries(cf_path, base_path)
        assert len(result) == 2

    def test_loads_by_variant_id(self, tmp_path: Path):
        cf_entries = [
            create_counterfactual_entry(instance_id="microsoftInternal__NAV-123456__cf-1"),
            create_counterfactual_entry(instance_id="microsoftInternal__NAV-123456__cf-2"),
        ]
        cf_path = create_counterfactual_file(tmp_path, cf_entries)
        base_path = create_base_dataset_file(tmp_path)

        result = load_counterfactual_entries(cf_path, base_path, entry_id="microsoftInternal__NAV-123456__cf-2")
        assert len(result) == 1
        assert result[0][0].instance_id == "microsoftInternal__NAV-123456__cf-2"

    def test_loads_by_base_instance_id(self, tmp_path: Path):
        cf_entries = [
            create_counterfactual_entry(instance_id="microsoftInternal__NAV-123456__cf-1"),
            create_counterfactual_entry(instance_id="microsoftInternal__NAV-123456__cf-2"),
        ]
        cf_path = create_counterfactual_file(tmp_path, cf_entries)
        base_path = create_base_dataset_file(tmp_path)

        result = load_counterfactual_entries(cf_path, base_path, entry_id="microsoftInternal__NAV-123456")
        assert len(result) == 2

    def test_resolves_base_entry(self, tmp_path: Path):
        cf_path = create_counterfactual_file(tmp_path)
        base_path = create_base_dataset_file(tmp_path)

        result = load_counterfactual_entries(cf_path, base_path)
        cf_entry, base_entry = result[0]
        assert base_entry.instance_id == VALID_BASE_INSTANCE_ID
        assert cf_entry.base_instance_id == base_entry.instance_id

    def test_missing_base_entry_raises(self, tmp_path: Path):
        cf_entry = create_counterfactual_entry(base_instance_id="microsoftInternal__NAV-999999")
        cf_path = create_counterfactual_file(tmp_path, [cf_entry])
        base_path = create_base_dataset_file(tmp_path)

        with pytest.raises(EntryNotFoundError):
            load_counterfactual_entries(cf_path, base_path)

    def test_missing_entry_id_raises(self, tmp_path: Path):
        cf_path = create_counterfactual_file(tmp_path)
        base_path = create_base_dataset_file(tmp_path)

        with pytest.raises(EntryNotFoundError):
            load_counterfactual_entries(cf_path, base_path, entry_id="nonexistent__NAV-999999")

    def test_missing_file_raises(self, tmp_path: Path):
        base_path = create_base_dataset_file(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_counterfactual_entries(tmp_path / "missing.jsonl", base_path)


class TestCounterfactualResult:
    def test_create_success(self, tmp_path: Path):
        context = create_evaluation_context(
            tmp_path,
            category=EvaluationCategory.COUNTERFACTUAL_EVALUATION,
        )
        result = CounterfactualResult.create_success(
            context,
            "generated patch",
            base_instance_id=VALID_BASE_INSTANCE_ID,
            variant_description="Modified test expectation",
        )

        assert result.resolved is True
        assert result.build is True
        assert result.base_instance_id == VALID_BASE_INSTANCE_ID
        assert result.variant_description == "Modified test expectation"
        assert result.category == EvaluationCategory.COUNTERFACTUAL_EVALUATION

    def test_create_build_failure(self, tmp_path: Path):
        context = create_evaluation_context(
            tmp_path,
            category=EvaluationCategory.COUNTERFACTUAL_EVALUATION,
        )
        result = CounterfactualResult.create_build_failure(
            context,
            "generated patch",
            "Build failed",
            base_instance_id=VALID_BASE_INSTANCE_ID,
            variant_description="Modified test",
        )

        assert result.resolved is False
        assert result.build is False

    def test_serialization_roundtrip(self, tmp_path: Path):
        context = create_evaluation_context(
            tmp_path,
            category=EvaluationCategory.COUNTERFACTUAL_EVALUATION,
        )
        result = CounterfactualResult.create_success(
            context,
            "generated patch",
            base_instance_id=VALID_BASE_INSTANCE_ID,
            variant_description="Modified test",
        )

        result_dict = result.model_dump(mode="json")
        restored = CounterfactualResult.model_validate(result_dict)

        assert restored.instance_id == result.instance_id
        assert restored.base_instance_id == result.base_instance_id
        assert restored.variant_description == result.variant_description


class TestCounterfactualDatasetIntegration:
    """Integration tests that load from the real dataset/counterfactual.jsonl file."""

    def test_load_real_counterfactual_dataset(self):
        from bcbench.config import get_config

        config = get_config()
        cf_path = config.paths.counterfactual_dataset_path
        base_path = config.paths.dataset_path

        pairs = load_counterfactual_entries(cf_path, base_path)
        assert len(pairs) >= 1

        cf_entry, base_entry = pairs[0]
        assert cf_entry.base_instance_id == base_entry.instance_id

    def test_load_real_entry_by_variant_id(self):
        from bcbench.config import get_config

        config = get_config()
        cf_path = config.paths.counterfactual_dataset_path
        base_path = config.paths.dataset_path

        pairs = load_counterfactual_entries(cf_path, base_path, entry_id="microsoftInternal__NAV-210528__cf-1")
        assert len(pairs) == 1

        cf_entry, base_entry = pairs[0]
        assert cf_entry.instance_id == "microsoftInternal__NAV-210528__cf-1"
        assert base_entry.instance_id == "microsoftInternal__NAV-210528"

    def test_load_real_entries_by_base_id(self):
        from bcbench.config import get_config

        config = get_config()
        cf_path = config.paths.counterfactual_dataset_path
        base_path = config.paths.dataset_path

        pairs = load_counterfactual_entries(cf_path, base_path, entry_id="microsoftInternal__NAV-210528")
        assert len(pairs) >= 1
        assert all(cf.base_instance_id == "microsoftInternal__NAV-210528" for cf, _ in pairs)

    def test_merged_entry_has_counterfactual_spec(self):
        from bcbench.config import get_config

        config = get_config()
        cf_path = config.paths.counterfactual_dataset_path
        base_path = config.paths.dataset_path

        pairs = load_counterfactual_entries(cf_path, base_path, entry_id="microsoftInternal__NAV-210528__cf-1")
        cf_entry, base_entry = pairs[0]

        merged = cf_entry.to_dataset_entry(base_entry)

        # Repo-level fields come from base
        assert merged.repo == base_entry.repo
        assert merged.base_commit == base_entry.base_commit
        assert merged.project_paths == base_entry.project_paths

        # Spec fields come from counterfactual
        assert merged.instance_id == cf_entry.instance_id
        assert merged.test_patch == cf_entry.test_patch
        assert merged.patch == cf_entry.patch
        assert merged.fail_to_pass == cf_entry.fail_to_pass

    def test_counterfactual_problem_statement_exists(self):
        from bcbench.config import get_config

        config = get_config()
        cf_path = config.paths.counterfactual_dataset_path
        base_path = config.paths.dataset_path

        pairs = load_counterfactual_entries(cf_path, base_path, entry_id="microsoftInternal__NAV-210528__cf-1")
        cf_entry, base_entry = pairs[0]

        merged = cf_entry.to_dataset_entry(base_entry)
        problem_dir = merged.problem_statement_dir
        readme = problem_dir / "README.md"
        assert readme.exists(), f"Problem statement README missing at {readme}"
        content = readme.read_text(encoding="utf-8")
        assert "Counterfactual" in content
