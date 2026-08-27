"""Exact set-based Gate 07 metrics with deterministic bootstrap intervals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random
from typing import Any, Iterable

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.oracle.ground_truth import Gate07GroundTruth, get_ground_truth


@dataclass(frozen=True)
class CaseMetric:
    case_id: str
    family: str
    tool_alignment_at_1: float
    tool_alignment_at_3: float
    tool_alignment_at_5: float
    argument_precision: float
    argument_recall: float
    argument_f1: float
    false_alignment_rate: float
    no_equivalent_accuracy: float | None


def _tool_pairs(names: Iterable[str], old_names: Iterable[str]) -> frozenset[tuple[str, str]]:
    return frozenset((old_name, new_name) for old_name in old_names for new_name in names)


def _argument_pairs(values: Iterable[Iterable[str]]) -> frozenset[tuple[str, str, str, str]]:
    return frozenset(tuple(value) for value in values if len(tuple(value)) == 4)  # type: ignore[arg-type]


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def score_prediction(prediction: dict[str, Any], ground_truth: Gate07GroundTruth, *, k: int = 5) -> CaseMetric:
    expected_tools = frozenset(ground_truth.correct_new_tool_names)
    predicted_tools = frozenset(prediction.get("selected_tool_names", [])) if not prediction.get("abstain", False) else frozenset()
    ranked = tuple(prediction.get("ranked_tool_names", prediction.get("selected_tool_names", [])))
    at1 = float(predicted_tools == expected_tools)
    at3 = float(expected_tools <= set(ranked[:3]))
    at5 = float(expected_tools <= set(ranked[:k]))
    expected_args = frozenset(ground_truth.argument_pairs)
    predicted_args = _argument_pairs(prediction.get("argument_pairs", []))
    correct_args = expected_args & predicted_args
    precision = len(correct_args) / len(predicted_args) if predicted_args else (1.0 if not expected_args else 0.0)
    recall = len(correct_args) / len(expected_args) if expected_args else 1.0
    expected_tool_pairs = _tool_pairs(expected_tools, ground_truth.old_tool_names)
    predicted_tool_pairs = _tool_pairs(predicted_tools, ground_truth.old_tool_names)
    false_rate = len(predicted_tool_pairs - expected_tool_pairs) / len(predicted_tool_pairs) if predicted_tool_pairs else 0.0
    no_eq = None
    if not expected_tools:
        no_eq = float(bool(prediction.get("abstain", False)))
    return CaseMetric(ground_truth.case_id, ground_truth.family, at1, at3, at5, precision, recall, _f1(precision, recall), false_rate, no_eq)


def _summary(values: list[float], *, seed: int, bootstrap_samples: int) -> dict[str, Any]:
    if not values:
        return {"mean": None, "ci95": None, "n": 0}
    rng = random.Random(seed)
    samples = [sum(rng.choice(values) for _ in values) / len(values) for _ in range(bootstrap_samples)]
    samples.sort()
    lower = samples[int(0.025 * (len(samples) - 1))]
    upper = samples[int(0.975 * (len(samples) - 1))]
    return {"mean": sum(values) / len(values), "ci95": [lower, upper], "n": len(values)}


def _metric_values(rows: list[CaseMetric], field: str) -> list[float]:
    return [value for value in (getattr(row, field) for row in rows) if value is not None]


def aggregate_predictions(predictions: Iterable[dict[str, Any]], capability: EvaluatorCapability, *, bootstrap_samples: int = 2000) -> dict[str, Any]:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("aggregate_predictions requires a real EvaluatorCapability instance.")
    rows = [score_prediction(prediction, get_ground_truth(prediction["case_id"], capability)) for prediction in predictions]
    fields = ("tool_alignment_at_1", "tool_alignment_at_3", "tool_alignment_at_5", "argument_precision", "argument_recall", "argument_f1", "false_alignment_rate", "no_equivalent_accuracy")
    by_family: dict[str, list[CaseMetric]] = {}
    for row in rows:
        by_family.setdefault(row.family, []).append(row)
    result: dict[str, Any] = {"case_count": len(rows), "families": {}}
    for family, family_rows in sorted(by_family.items()):
        result["families"][family] = {field: _summary(_metric_values(family_rows, field), seed=20260827 + index, bootstrap_samples=bootstrap_samples) for index, field in enumerate(fields)}
    result["overall"] = {field: _summary(_metric_values(rows, field), seed=20260999 + index, bootstrap_samples=bootstrap_samples) for index, field in enumerate(fields)}
    result["case_metrics"] = [asdict(row) for row in rows]
    return result
