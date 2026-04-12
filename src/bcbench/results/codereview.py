from typing import Any, Self

from pydantic import Field

from bcbench.dataset.codereview import ReviewComment
from bcbench.results.base import BaseEvaluationResult
from bcbench.types import EvaluationContext

__all__ = ["CodeReviewResult"]


class CodeReviewResult(BaseEvaluationResult):
    """Result for the code-review category."""

    generated_comments: list[ReviewComment] = Field(default_factory=list)

    @classmethod
    def create_success(
        cls,
        context: "EvaluationContext",
        generated_comments: list[ReviewComment],
        **kwargs: Any,
    ) -> Self:
        return cls._create_from_context(
            context,
            output="",
            generated_comments=generated_comments,
            **kwargs,
        )

    @property
    def category_metrics(self) -> dict[str, int | float | bool]:
        return {
            "generated_comment_count": len(self.generated_comments),
        }

    @property
    def display_row(self) -> dict[str, str]:
        return {
            "Comments": str(len(self.generated_comments)),
        }
