"""Gate 07 V4 scoring and uncertainty summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Any, Iterable

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.oracle.ground_truth import Gate07GroundTruth, get_ground_truth


@dataclass(frozen=True)
class CaseMetric:
    case_id: str
    family: str
    tool_alignment_at_1: float
    argument_precision: float
    argument_recall: float
    argument_f1: float
    false_alignment_rate: float
    no_equivalent_accuracy: float | None
    abstention_rate: float


def _prediction_tools(prediction: dict[str, Any]) -> frozenset[str]:
    if "best_candidate_tool_names" in prediction:
        return frozenset(prediction.get("best_candidate_tool_names", []))
    if prediction.get("abstain", False):
        return frozenset()
    return frozenset(prediction.get("selected_tool_names", []))


def _argument_pairs(values: Iterable[Any]) -> frozenset[tuple[str, str, str, str]]:
    pairs: set[tuple[str, str, str, str]] = set()
    for value in values:
        if isinstance(value, dict):
            fields = tuple(value.get(key) for key in ("old_tool", "old_arg", "new_tool", "new_arg"))
        else:
            fields = tuple(value) if isinstance(value, (list, tuple)) else ()
        if len(fields) == 4 and all(isinstance(field, str) for field in fields):
            pairs.add(fields)  # type: ignore[arg-type]
    return frozenset(pairs)


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def score_prediction(prediction: dict[str, Any], ground_truth: Gate07GroundTruth) -> CaseMetric:
    expected_tools = frozenset(ground_truth.correct_new_tool_names)
    predicted_tools = _prediction_tools(prediction)
    at1 = float(predicted_tools == expected_tools)
    expected_args = frozenset(ground_truth.argument_pairs)
    predicted_args = _argument_pairs(prediction.get("argument_mapping", prediction.get("argument_pairs", [])))
    correct_args = expected_args & predicted_args
    precision = len(correct_args) / len(predicted_args) if predicted_args else (1.0 if not expected_args else 0.0)
    recall = len(correct_args) / len(expected_args) if expected_args else 1.0
    expected_tool_pairs = frozenset((old_name, new_name) for old_name in ground_truth.old_tool_names for new_name in expected_tools)
    predicted_tool_pairs = frozenset((old_name, new_name) for old_name in ground_truth.old_tool_names for new_name in predicted_tools)
    false_rate = len(predicted_tool_pairs - expected_tool_pairs) / len(predicted_tool_pairs) if predicted_tool_pairs else 0.0
    no_eq = None
    if not expected_tools:
        verdict = prediction.get("equivalence_verdict")
        no_eq = float(verdict == "not_equivalent") if verdict is not None else float(bool(prediction.get("abstain", False)))
    return CaseMetric(
        ground_truth.case_id,
        ground_truth.family,
        at1,
        precision,
        recall,
        _f1(precision, recall),
        false_rate,
        no_eq,
        float(bool(prediction.get("abstain", False))),
    )


def _summary(values: list[float], *, seed: int, bootstrap_samples: int) -> dict[str, Any]:
    """Bootstrap a continuous score, explicitly marking degenerate vectors."""
    if not values:
        return {"mean": None, "ci95": None, "n": 0, "interval_method": "bootstrap", "degenerate": False}
    mean = sum(values) / len(values)
    degenerate = all(value == values[0] for value in values)
    if degenerate:
        return {
            "mean": mean,
            "ci95": [values[0], values[0]],
            "n": len(values),
            "interval_method": "bootstrap",
            "degenerate": True,
        }
    rng = random.Random(seed)
    samples = [sum(rng.choice(values) for _ in values) / len(values) for _ in range(bootstrap_samples)]
    samples.sort()
    lower = samples[int(0.025 * (len(samples) - 1))]
    upper = samples[int(0.975 * (len(samples) - 1))]
    if lower == upper:
        raise ValueError("non-degenerate bootstrap produced a zero-width interval")
    return {
        "mean": mean,
        "ci95": [lower, upper],
        "n": len(values),
        "interval_method": "bootstrap",
        "degenerate": False,
    }


def _proportion_summary(values: list[float]) -> dict[str, Any]:
    """Return a Wilson 95% interval for a binary/proportion-valued metric."""
    if not values:
        return {"mean": None, "ci95": None, "n": 0, "interval_method": "wilson", "degenerate": False}
    if any(value not in {0.0, 1.0} for value in values):
        raise ValueError("Wilson interval requires binary values")
    n = len(values)
    successes = sum(values)
    p = successes / n
    z = 1.959963984540054
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    half_width = z * math.sqrt((p * (1.0 - p) / n) + (z2 / (4.0 * n * n))) / denominator
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    return {
        "mean": p,
        "ci95": [lower, upper],
        "n": n,
        "interval_method": "wilson",
        "degenerate": False,
    }


def _metric_values(rows: list[CaseMetric], field: str) -> list[float]:
    return [value for value in (getattr(row, field) for row in rows) if value is not None]


def aggregate_predictions(
    predictions: Iterable[dict[str, Any]],
    capability: EvaluatorCapability,
    *,
    bootstrap_samples: int = 2000,
) -> dict[str, Any]:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("aggregate_predictions requires a real EvaluatorCapability instance.")
    rows = [score_prediction(prediction, get_ground_truth(prediction["case_id"], capability)) for prediction in predictions]
    proportion_fields = {"tool_alignment_at_1", "no_equivalent_accuracy", "abstention_rate"}
    continuous_fields = {"argument_precision", "argument_recall", "argument_f1", "false_alignment_rate"}
    fields = tuple(proportion_fields | continuous_fields)

    def summary(field_rows: list[CaseMetric], field: str, seed: int) -> dict[str, Any]:
        values = _metric_values(field_rows, field)
        return _proportion_summary(values) if field in proportion_fields else _summary(values, seed=seed, bootstrap_samples=bootstrap_samples)

    by_family: dict[str, list[CaseMetric]] = {}
    for row in rows:
        by_family.setdefault(row.family, []).append(row)
    result: dict[str, Any] = {"case_count": len(rows), "families": {}}
    for family, family_rows in sorted(by_family.items()):
        result["families"][family] = {field: summary(family_rows, field, 20260827 + index) for index, field in enumerate(sorted(fields))}
    result["overall"] = {field: summary(rows, field, 20260999 + index) for index, field in enumerate(sorted(fields))}
    result["case_metrics"] = [asdict(row) for row in rows]
    return result


__all__ = ["CaseMetric", "_proportion_summary", "_summary", "aggregate_predictions", "score_prediction"]
