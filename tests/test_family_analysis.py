"""Tests for family-level evaluation models, aggregation, and metrics."""

import pytest

from bcbench.analysis.family import FamilyOutcome, FamilyType, InstanceResult
from bcbench.analysis.family_aggregator import build_families
from bcbench.results.base import BaseEvaluationResult
from bcbench.results.counterfactual import CounterfactualResult
from bcbench.types import EvaluationCategory, FailureLayer
from evaluator.thesis_metrics import (
    cf_exposed_failure_count,
    failure_layer_distribution,
    family_type_distribution,
    fragility_rate,
    layer_conditioned_fragility,
    mean_severity,
)


def _inst(instance_id: str, *, is_base: bool, compiled: bool, passed: bool) -> InstanceResult:
    return InstanceResult(instance_id=instance_id, is_base=is_base, compiled=compiled, passed=passed)


def _family(
    family_id: str,
    base_passed: bool,
    cf_passed: list[bool],
    layer: FailureLayer | None = None,
) -> FamilyOutcome:
    base = _inst(family_id, is_base=True, compiled=True, passed=base_passed)
    cfs = tuple(_inst(f"{family_id}__cf-{i + 1}", is_base=False, compiled=True, passed=p) for i, p in enumerate(cf_passed))
    return FamilyOutcome(family_id=family_id, failure_layer=layer, base=base, cfs=cfs)


class TestFamilyOutcome:
    def test_stable_correct_pattern(self):
        f = _family("F1", True, [True, True])
        assert f.pattern == (1, 1, 1)
        assert f.family_type == FamilyType.STABLE_CORRECT
        assert not f.is_fragile
        assert f.severity == 0.0

    def test_fragile_all_cf_fail(self):
        f = _family("F2", True, [False, False])
        assert f.pattern == (1, 0, 0)
        assert f.family_type == FamilyType.FRAGILE
        assert f.is_fragile
        assert f.severity == 1.0

    def test_fragile_partial_cf_fail(self):
        f = _family("F3", True, [True, False])
        assert f.pattern == (1, 1, 0)
        assert f.family_type == FamilyType.FRAGILE
        assert f.is_fragile
        assert f.severity == 0.5

    def test_unsolved(self):
        f = _family("F4", False, [False, False])
        assert f.pattern == (0, 0, 0)
        assert f.family_type == FamilyType.UNSOLVED
        assert not f.is_fragile
        assert f.severity is None

    def test_inconsistent(self):
        f = _family("F5", False, [True, False])
        assert f.pattern == (0, 1, 0)
        assert f.family_type == FamilyType.INCONSISTENT
        assert not f.is_fragile
        assert f.severity is None

    def test_cf_fail_count(self):
        f = _family("F6", True, [True, False, False])
        assert f.cf_fail_count == 2
        assert f.cf_total == 3

    def test_single_cf_stable(self):
        f = _family("F7", True, [True])
        assert f.pattern == (1, 1)
        assert f.family_type == FamilyType.STABLE_CORRECT
        assert f.severity == 0.0


class TestBuildFamilies:
    def _base_result(self, instance_id: str, resolved: bool) -> BaseEvaluationResult:
        return BaseEvaluationResult(
            instance_id=instance_id,
            project="Test",
            model="test-model",
            agent_name="test",
            category=EvaluationCategory.BUG_FIX,
            resolved=resolved,
            build=True,
        )

    def _cf_result(self, instance_id: str, base_id: str, resolved: bool) -> CounterfactualResult:
        return CounterfactualResult(
            instance_id=instance_id,
            project="Test",
            model="test-model",
            agent_name="test",
            category=EvaluationCategory.COUNTERFACTUAL_EVALUATION,
            resolved=resolved,
            build=True,
            base_instance_id=base_id,
        )

    def test_builds_single_family(self):
        results = [
            self._base_result("NAV-100", True),
            self._cf_result("NAV-100__cf-1", "NAV-100", False),
            self._cf_result("NAV-100__cf-2", "NAV-100", True),
        ]
        families = build_families(results)
        assert len(families) == 1
        f = families[0]
        assert f.family_id == "NAV-100"
        assert f.pattern == (1, 0, 1)
        assert f.family_type == FamilyType.FRAGILE

    def test_skips_base_without_cfs(self):
        results = [self._base_result("NAV-200", True)]
        families = build_families(results)
        assert len(families) == 0

    def test_multiple_families(self):
        results = [
            self._base_result("NAV-100", True),
            self._cf_result("NAV-100__cf-1", "NAV-100", True),
            self._base_result("NAV-200", False),
            self._cf_result("NAV-200__cf-1", "NAV-200", False),
        ]
        families = build_families(results)
        assert len(families) == 2
        assert families[0].family_type == FamilyType.STABLE_CORRECT
        assert families[1].family_type == FamilyType.UNSOLVED

    def test_failure_layers_applied(self):
        results = [
            self._base_result("NAV-100", True),
            self._cf_result("NAV-100__cf-1", "NAV-100", False),
        ]
        layers = {"NAV-100": FailureLayer.L3_EVENT}
        families = build_families(results, failure_layers=layers)
        assert families[0].failure_layer == FailureLayer.L3_EVENT


class TestThesisMetrics:
    @pytest.fixture
    def sample_families(self) -> list[FamilyOutcome]:
        return [
            _family("F1", True, [True, True], FailureLayer.L2_EXECUTION),
            _family("F2", True, [False, False], FailureLayer.L3_EVENT),
            _family("F3", True, [True, False], FailureLayer.L3_EVENT),
            _family("F4", False, [False, False], FailureLayer.L4_WORKFLOW),
            _family("F5", False, [True, False], FailureLayer.L5_TOOLCHAIN),
        ]

    def test_family_type_distribution(self, sample_families):
        dist = family_type_distribution(sample_families)
        assert dist["stable-correct"] == 1
        assert dist["fragile"] == 2
        assert dist["unsolved"] == 1
        assert dist["inconsistent"] == 1

    def test_fragility_rate(self, sample_families):
        # 3 families where base passed (F1, F2, F3), 2 are fragile (F2, F3)
        rate = fragility_rate(sample_families)
        assert rate == pytest.approx(2 / 3)

    def test_fragility_rate_no_eligible(self):
        families = [_family("F1", False, [False])]
        assert fragility_rate(families) == 0.0

    def test_mean_severity(self, sample_families):
        # F1: 0.0, F2: 1.0, F3: 0.5 → mean of stable+fragile severities = (0.0+1.0+0.5)/3
        sev = mean_severity(sample_families)
        assert sev == pytest.approx(0.5)

    def test_layer_conditioned_fragility(self, sample_families):
        lcf = layer_conditioned_fragility(sample_families)
        # L2: 1 family (F1, stable), fragility = 0/1 = 0
        assert lcf[FailureLayer.L2_EXECUTION.value] == 0.0
        # L3: 2 families (F2 fragile, F3 fragile), both base passed, fragility = 2/2 = 1.0
        assert lcf[FailureLayer.L3_EVENT.value] == 1.0

    def test_failure_layer_distribution(self, sample_families):
        dist = failure_layer_distribution(sample_families)
        assert dist[FailureLayer.L2_EXECUTION.value] == 1
        assert dist[FailureLayer.L3_EVENT.value] == 2

    def test_cf_exposed_failure_count(self, sample_families):
        # F2 is fragile with all CFs failing (cf_fail_count == cf_total)
        count = cf_exposed_failure_count(sample_families)
        assert count == 1  # Only F2 (F3 has 1 pass, 1 fail)


class TestSampleFailures:
    def test_samples_fragile_instances(self):
        from bcbench.analysis.sample_failures import sample_failures

        families = [
            _family("F1", True, [True, True]),  # stable — skipped
            _family("F2", True, [False, False], FailureLayer.L3_EVENT),  # fragile — 2 failed CFs
            _family("F3", False, [False], FailureLayer.L4_WORKFLOW),  # unsolved — 1 failed base + 1 failed CF
        ]
        rows = sample_failures(families)
        # F2: 2 failed CFs, F3: 1 failed base + 1 failed CF = 4 rows
        assert len(rows) == 4
        assert all(r["family_id"] in ("F2", "F3") for r in rows)
        # Fragile families come first
        assert rows[0]["family_type"] == "fragile"

    def test_max_samples_limit(self):
        from bcbench.analysis.sample_failures import sample_failures

        families = [_family("F1", True, [False, False, False])]
        rows = sample_failures(families, max_samples=2)
        assert len(rows) == 2

    def test_writes_csv(self, tmp_path):
        from bcbench.analysis.sample_failures import sample_failures, write_annotation_csv

        families = [_family("F1", True, [False], FailureLayer.L2_EXECUTION)]
        rows = sample_failures(families)
        csv_path = tmp_path / "annotations.csv"
        write_annotation_csv(rows, csv_path)
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "family_id" in content
        assert "primary_failure_layer" in content
