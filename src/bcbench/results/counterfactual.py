from bcbench.results.base import BaseEvaluationResult


class CounterfactualResult(BaseEvaluationResult):
    """Result class for counterfactual evaluation category.

    Inherits all shared metrics from BaseEvaluationResult.
    Tracks the base instance and variant description for comparative analysis.
    """

    base_instance_id: str = ""
    variant_description: str = ""
