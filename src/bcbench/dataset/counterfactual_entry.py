"""Counterfactual dataset entry model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from bcbench.dataset.dataset_entry import TestEntry
from bcbench.types import FailureLayer

if TYPE_CHECKING:
    from bcbench.dataset.dataset_entry import DatasetEntry

__all__ = ["CounterfactualEntry"]


class CounterfactualEntry(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    instance_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+__[a-zA-Z0-9_-]+-[0-9]+__cf-[0-9]+$")
    base_instance_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+__[a-zA-Z0-9_-]+-[0-9]+$")

    variant_description: Annotated[str, Field(min_length=1)]
    failure_layer: FailureLayer | None = None

    test_patch: Annotated[str, Field(min_length=1)]
    patch: Annotated[str, Field(min_length=1)]
    fail_to_pass: Annotated[list[TestEntry], Field(alias="FAIL_TO_PASS", min_length=1)]
    pass_to_pass: Annotated[list[TestEntry], Field(alias="PASS_TO_PASS")] = []

    problem_statement_override: Annotated[str, Field(min_length=1)]

    def to_dataset_entry(self, base: DatasetEntry) -> DatasetEntry:
        """Merge this counterfactual entry with its base to produce a DatasetEntry.

        Repo-level fields (repo, base_commit, project_paths, environment_setup_version)
        come from the base entry. Specification fields (test_patch, patch, FAIL_TO_PASS,
        PASS_TO_PASS) come from this counterfactual entry.
        """
        from bcbench.dataset.dataset_entry import DatasetEntry

        return DatasetEntry(
            instance_id=self.instance_id,
            repo=base.repo,
            base_commit=base.base_commit,
            created_at=base.created_at,
            environment_setup_version=base.environment_setup_version,
            project_paths=base.project_paths,
            metadata=base.metadata,
            test_patch=self.test_patch,
            patch=self.patch,
            fail_to_pass=self.fail_to_pass,
            pass_to_pass=self.pass_to_pass,
        )
