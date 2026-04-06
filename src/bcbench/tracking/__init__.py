"""Braintrust experiment tracking for BC-Bench thesis evaluation."""

from __future__ import annotations

from typing import Any

import braintrust

from bcbench.logger import get_logger
from bcbench.results.base import BaseEvaluationResult
from bcbench.results.counterfactual import CounterfactualResult
from bcbench.results.testgeneration import TestGenerationResult

logger = get_logger(__name__)

DEFAULT_PROJECT = "BC-Bench-Thesis"


def log_results(
    results: list[BaseEvaluationResult],
    experiment_name: str,
    project: str = DEFAULT_PROJECT,
    tags: list[str] | None = None,
    api_key: str | None = None,
) -> None:
    """Log evaluation results to a Braintrust experiment.

    Each result becomes one logged event with input (problem statement placeholder),
    output (generated patch), expected (gold patch from dataset), scores, and metadata.
    """
    experiment = braintrust.init(
        project=project,
        experiment=experiment_name,
        api_key=api_key,
    )

    for result in results:
        scores = _build_scores(result)
        metadata = _build_metadata(result)
        event_tags = list(tags or [])
        event_tags.append(result.category.value)

        experiment.log(
            input={"instance_id": result.instance_id},
            output=result.generated_patch,
            expected="",
            scores=scores,
            metadata=metadata,
            tags=event_tags,
        )

    experiment.flush()
    logger.info(f"Logged {len(results)} results to Braintrust experiment '{experiment_name}' in project '{project}'")


def _build_scores(result: BaseEvaluationResult) -> dict[str, int]:
    scores: dict[str, int] = {
        "resolved": int(result.resolved),
        "build": int(result.build),
    }

    if isinstance(result, TestGenerationResult):
        scores["pre_patch_failed"] = int(result.pre_patch_failed)
        scores["post_patch_passed"] = int(result.post_patch_passed)

    return scores


def _build_metadata(result: BaseEvaluationResult) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "model": result.model,
        "agent_name": result.agent_name,
        "project": result.project,
        "category": result.category.value,
        "timeout": result.timeout,
    }

    if result.error_message:
        metadata["error_message"] = result.error_message

    if result.metrics:
        metadata["prompt_tokens"] = result.metrics.prompt_tokens or 0
        metadata["completion_tokens"] = result.metrics.completion_tokens or 0
        metadata["llm_duration"] = result.metrics.llm_duration or 0
        metadata["execution_time"] = result.metrics.execution_time or 0
        metadata["turn_count"] = result.metrics.turn_count or 0
        metadata["tool_usage"] = result.metrics.tool_usage or {}

    if result.experiment:
        metadata["mcp_servers"] = result.experiment.mcp_servers
        metadata["custom_instructions"] = result.experiment.custom_instructions
        metadata["skills_enabled"] = result.experiment.skills_enabled
        metadata["custom_agent"] = result.experiment.custom_agent

    if isinstance(result, CounterfactualResult):
        metadata["base_instance_id"] = result.base_instance_id
        metadata["variant_description"] = result.variant_description

    return metadata
