"""Metrics for refusal and abstention behavior."""

from __future__ import annotations

from statistics import mean
from typing import Any


def aggregate_abstention_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    expected_refusal = [1.0 if not row["is_answerable"] else 0.0 for row in records]
    actual_refusal = [1.0 if row["refusal"] else 0.0 for row in records]
    accuracy = [1.0 if exp == act else 0.0 for exp, act in zip(expected_refusal, actual_refusal, strict=False)]
    unsupported_answers = [
        1.0
        for row in records
        if (not row["is_answerable"]) and (not row["refusal"])
    ]
    return {
        "refusal_accuracy": round(mean(accuracy) if accuracy else 0.0, 4),
        "unsupported_answer_rate": round((sum(unsupported_answers) / len(records)) if records else 0.0, 4),
    }
