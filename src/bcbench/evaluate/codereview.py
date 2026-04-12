import json
from collections.abc import Callable
from pathlib import Path

from bcbench.dataset.codereview import CodeReviewEntry, ReviewComment
from bcbench.evaluate.base import EvaluationPipeline
from bcbench.logger import get_logger, github_log_group
from bcbench.operations import apply_patch, setup_repo_prebuild
from bcbench.results.codereview import CodeReviewResult
from bcbench.types import EvaluationContext

logger = get_logger(__name__)

REVIEW_OUTPUT_FILE = "review.json"

__all__ = ["CodeReviewPipeline"]


def _parse_review_json(repo_path: Path) -> list[ReviewComment]:
    """Parse review.json produced by the agent into ReviewComment objects.

    NOTE: This is a minimal parser for the POC. The owning team should make this more robust.
    """
    review_path = repo_path / REVIEW_OUTPUT_FILE
    if not review_path.exists():
        logger.warning(f"No {REVIEW_OUTPUT_FILE} found at {review_path}")
        return []

    try:
        raw = json.loads(review_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse {review_path} as JSON")
        return []

    if not isinstance(raw, list):
        logger.warning(f"Expected JSON array in {review_path}, got {type(raw).__name__}")
        return []

    comments: list[ReviewComment] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            comments.append(ReviewComment.model_validate(item))
        except Exception:
            logger.debug(f"Skipping malformed comment: {item}")
    return comments


class CodeReviewPipeline(EvaluationPipeline[CodeReviewEntry]):
    """Pipeline for code-review evaluation category.

    Code review does not require a BC container — the agent reviews a patch
    and produces review comments without building or running tests.
    """

    def setup_workspace(self, entry: CodeReviewEntry, repo_path: Path) -> None:
        setup_repo_prebuild(entry, repo_path)
        apply_patch(repo_path, entry.patch, f"{entry.instance_id} code-review patch")

    def setup(self, context: EvaluationContext[CodeReviewEntry]) -> None:
        self.setup_workspace(context.entry, context.repo_path)

    def run_agent(self, context: EvaluationContext[CodeReviewEntry], agent_runner: Callable) -> None:
        with github_log_group(f"{context.agent_name} -- Entry: {context.entry.instance_id}"):
            context.metrics, context.experiment = agent_runner(context)

    def evaluate(self, context: EvaluationContext[CodeReviewEntry]) -> None:
        generated_comments: list[ReviewComment] = _parse_review_json(context.repo_path)
        logger.info(f"Parsed {len(generated_comments)} comments from {REVIEW_OUTPUT_FILE}")
        result = CodeReviewResult.create_success(context, generated_comments=generated_comments)
        # TODO: Code Review team should implement the real evaluation logic and populate metrics in the result
        for comment in generated_comments:
            logger.debug(f"  {comment}")
        self.save_result(context, result)
