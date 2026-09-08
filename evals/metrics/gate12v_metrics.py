"""Metrics for the Gate 12-V product-lane validation.

The module is deliberately independent from the live runner.  It consumes
ignored run records after collection and returns numerator/denominator-backed
metrics so a rounded percentage is never the only evidence for a rate.
"""

from __future__ import annotations

from collections import Counter
import math
from statistics import mean
from typing import Any, Iterable

from evals.metrics.generation_metrics import token_f1


def wilson_interval(successes: int, total: int, z: float = 1.96) -> dict[str, float | int | None]:
    """Return a 95% Wilson interval with its raw count."""

    if total <= 0:
        return {
            "numerator": int(successes),
            "denominator": int(total),
            "value": None,
            "ci95_low": None,
            "ci95_high": None,
        }
    successes = max(0, min(int(successes), int(total)))
    p = successes / total
    denominator = 1.0 + (z * z / total)
    centre = (p + (z * z / (2.0 * total))) / denominator
    margin = (z / denominator) * math.sqrt((p * (1.0 - p) / total) + (z * z / (4.0 * total * total)))
    return {
        "numerator": successes,
        "denominator": int(total),
        "value": round(p, 6),
        "ci95_low": round(max(0.0, centre - margin), 6),
        "ci95_high": round(min(1.0, centre + margin), 6),
    }


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(math.floor((len(ordered) - 1) * fraction))
    return round(ordered[index], 3)


def distribution(values: Iterable[int | float | None], *, unit: str = "count") -> dict[str, Any]:
    observed = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    payload: dict[str, Any] = {
        "unit": unit,
        "n_observed": len(observed),
        "n_missing": 0,
        "min": None,
        "p50": None,
        "p95": None,
        "max": None,
        "mean": None,
    }
    if observed:
        payload.update(
            {
                "min": round(min(observed), 3),
                "p50": _percentile(observed, 0.50),
                "p95": _percentile(observed, 0.95),
                "max": round(max(observed), 3),
                "mean": round(mean(observed), 3),
            }
        )
    return payload


def _final_response(row: dict[str, Any]) -> dict[str, Any]:
    response = row.get("final_response")
    return response if isinstance(response, dict) else {}


def _citations(row: dict[str, Any]) -> list[dict[str, Any]]:
    citations = _final_response(row).get("citations") or []
    return [citation for citation in citations if isinstance(citation, dict)]


def _answerable_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in records if bool(row.get("is_answerable"))]


def _metric_set(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    answerable = _answerable_rows(records)
    unanswerable = [row for row in records if not bool(row.get("is_answerable"))]
    attempted = [row for row in records if int(row.get("provider_request_count", 0) or 0) > 0]

    citation_valid = sum(
        1
        for row in records
        if bool((_final_response(row).get("citation_verification") or {}).get("is_valid"))
    )
    citation_valid_nonrefusal_rows = [row for row in records if not bool(_final_response(row).get("refusal"))]
    citation_valid_nonrefusal = sum(
        1
        for row in citation_valid_nonrefusal_rows
        if bool((_final_response(row).get("citation_verification") or {}).get("is_valid"))
    )

    grounding_precision_numerator = 0
    grounding_precision_denominator = 0
    grounding_recall_numerator = 0
    grounding_recall_denominator = 0
    for row in answerable:
        relevant = {str(value) for value in row.get("relevant_chunk_ids", [])}
        cited = {str(citation.get("chunk_id")) for citation in _citations(row) if citation.get("chunk_id")}
        grounding_precision_numerator += len(cited & relevant)
        grounding_precision_denominator += len(cited)
        grounding_recall_numerator += len(cited & relevant)
        grounding_recall_denominator += len(relevant)

    must_cite_rows = [row for row in records if bool(row.get("must_cite"))]
    must_cite_compliant = sum(
        1
        for row in must_cite_rows
        if bool(_final_response(row).get("refusal"))
        or (
            bool(_citations(row))
            and bool((_final_response(row).get("citation_verification") or {}).get("is_valid"))
        )
    )

    refusal_count = sum(1 for row in unanswerable if bool(_final_response(row).get("refusal")))
    false_answer_count = len(unanswerable) - refusal_count
    refusal_accuracy = sum(
        1
        for row in records
        if bool(_final_response(row).get("refusal")) == (not bool(row.get("is_answerable")))
    )

    answer_f1_values: list[float] = []
    answer_correct_count = 0
    for row in answerable:
        value = token_f1(str(row.get("expected_answer", "")), str(_final_response(row).get("answer", "")))
        answer_f1_values.append(value)
        if value >= 0.45:
            answer_correct_count += 1

    raw_calls = [call for row in records for call in (row.get("raw_calls") or []) if isinstance(call, dict)]
    finish_length_count = sum(1 for call in raw_calls if call.get("finish_reason") == "length")
    completion_values = [
        (call.get("usage") or {}).get("output_tokens_actual")
        for call in raw_calls
        if isinstance(call.get("usage"), dict)
    ]
    reasoning_values = [
        (call.get("usage") or {}).get("reasoning_tokens_actual")
        for call in raw_calls
        if isinstance(call.get("usage"), dict)
    ]
    completion_over_budget = sum(
        1 for value in completion_values if isinstance(value, (int, float)) and value > 1024
    )

    error_kinds = Counter()
    for row in records:
        kind = row.get("typed_error_kind")
        if kind:
            error_kinds[str(kind)] += 1
        for call in row.get("raw_calls") or []:
            call_kind = call.get("typed_error_kind")
            if call_kind:
                error_kinds[str(call_kind)] += 1

    model_counts = Counter(
        str(row.get("serving_model_class") or row.get("served_model") or "unserved")
        for row in records
        if int(row.get("provider_request_count", 0) or 0) > 0
    )
    fallback_served = sum(1 for row in records if row.get("serving_model_class") == "gemma")

    return {
        "question_count": total,
        "answerable_count": len(answerable),
        "unanswerable_count": len(unanswerable),
        "provider_attempted_question_count": len(attempted),
        "schema_validity_first_attempt": wilson_interval(
            sum(1 for row in attempted if row.get("first_attempt_schema_valid") is True),
            len(attempted),
        ),
        "schema_validity_not_attempted_count": total - len(attempted),
        "citation_validity": wilson_interval(citation_valid, total),
        "citation_validity_nonrefusal": wilson_interval(
            citation_valid_nonrefusal,
            len(citation_valid_nonrefusal_rows),
        ),
        "citation_grounding_precision": wilson_interval(
            grounding_precision_numerator,
            grounding_precision_denominator,
        ),
        "citation_grounding_recall": wilson_interval(
            grounding_recall_numerator,
            grounding_recall_denominator,
        ),
        "refusal_correctness": wilson_interval(refusal_accuracy, total),
        "false_answer_rate_unanswerable": wilson_interval(false_answer_count, len(unanswerable)),
        "must_cite_compliance": wilson_interval(must_cite_compliant, len(must_cite_rows)),
        "answer_token_f1": {
            "n": len(answer_f1_values),
            "mean": round(mean(answer_f1_values), 6) if answer_f1_values else None,
            "p50": _percentile(answer_f1_values, 0.50),
            "p95": _percentile(answer_f1_values, 0.95),
        },
        "answer_correctness_rate": wilson_interval(answer_correct_count, len(answerable)),
        "refusal_count": refusal_count,
        "false_answer_count": false_answer_count,
        "latency_ms": distribution((row.get("latency_ms") for row in records), unit="milliseconds"),
        "provider_request_latency_ms": distribution(
            (call.get("latency_ms") for call in raw_calls),
            unit="milliseconds",
        ),
        "reasoning_tokens": distribution(reasoning_values, unit="tokens"),
        "completion_tokens": distribution(completion_values, unit="tokens"),
        "completion_over_1024_count": completion_over_budget,
        "finish_reason_length_count": finish_length_count,
        "raw_generation_request_count": len(raw_calls),
        "error_taxonomy": dict(sorted(error_kinds.items())),
        "serving_model_question_counts": dict(sorted(model_counts.items())),
        "fallback_activation_rate": wilson_interval(fallback_served, len(attempted)),
        "fallback_served_question_count": fallback_served,
    }


def compute_gate12v_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute headline metrics and a serving-model breakdown."""

    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        model = str(row.get("serving_model_class") or row.get("served_model") or "unserved")
        by_model.setdefault(model, []).append(row)
    return {
        "overall": _metric_set(records),
        "by_serving_model": {
            model: _metric_set(rows) for model, rows in sorted(by_model.items())
        },
    }


def quality_gap(openrouter: dict[str, Any], groq: dict[str, Any]) -> dict[str, Any]:
    """Compare pre-registered quality rates against the Groq control."""

    rate_names = (
        "schema_validity_first_attempt",
        "citation_validity",
        "citation_grounding_precision",
        "citation_grounding_recall",
        "refusal_correctness",
        "must_cite_compliance",
        "answer_correctness_rate",
    )
    rows: dict[str, Any] = {}
    for name in rate_names:
        open_value = openrouter.get(name, {}).get("value")
        groq_value = groq.get(name, {}).get("value")
        rows[name] = {
            "openrouter": open_value,
            "groq": groq_value,
            "gap_openrouter_minus_groq": (
                round(open_value - groq_value, 6)
                if open_value is not None and groq_value is not None
                else None
            ),
        }
    open_f1 = openrouter.get("answer_token_f1", {}).get("mean")
    groq_f1 = groq.get("answer_token_f1", {}).get("mean")
    rows["answer_token_f1"] = {
        "openrouter": open_f1,
        "groq": groq_f1,
        "gap_openrouter_minus_groq": (
            round(open_f1 - groq_f1, 6) if open_f1 is not None and groq_f1 is not None else None
        ),
    }
    return rows


__all__ = ["compute_gate12v_metrics", "distribution", "quality_gap", "wilson_interval"]
