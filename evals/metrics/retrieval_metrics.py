"""Retrieval metric helpers."""

from __future__ import annotations

from statistics import mean
from typing import Any


def recall_at_k(relevant_chunk_ids: list[str], predicted_chunk_ids: list[str], k: int) -> float:
    if not relevant_chunk_ids:
        return 0.0
    relevant = set(relevant_chunk_ids)
    hits = len(relevant.intersection(predicted_chunk_ids[:k]))
    return hits / len(relevant)


def precision_at_k(relevant_chunk_ids: list[str], predicted_chunk_ids: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_predictions = predicted_chunk_ids[:k]
    if not top_predictions:
        return 0.0
    relevant = set(relevant_chunk_ids)
    hits = len(relevant.intersection(top_predictions))
    return hits / k


def reciprocal_rank(relevant_chunk_ids: list[str], predicted_chunk_ids: list[str]) -> float:
    relevant = set(relevant_chunk_ids)
    for index, chunk_id in enumerate(predicted_chunk_ids, start=1):
        if chunk_id in relevant:
            return 1.0 / index
    return 0.0


def aggregate_retrieval_metrics(
    qa_items: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    ks: tuple[int, ...] = (3, 5, 10),
) -> dict[str, Any]:
    prediction_by_id = {item["question_id"]: item for item in predictions}
    answerable = [item for item in qa_items if item.get("is_answerable", True)]
    per_query: list[dict[str, Any]] = []

    recall_values = {k: [] for k in ks}
    precision_values = {k: [] for k in ks}
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []

    for qa_item in qa_items:
        prediction = prediction_by_id[qa_item["question_id"]]
        predicted_chunk_ids = prediction["predicted_chunk_ids"]
        latency = float(prediction["latency_ms"])
        latencies.append(latency)

        if qa_item.get("is_answerable", True):
            rr = reciprocal_rank(qa_item["relevant_chunk_ids"], predicted_chunk_ids)
            reciprocal_ranks.append(rr)
            for k in ks:
                recall_values[k].append(recall_at_k(qa_item["relevant_chunk_ids"], predicted_chunk_ids, k))
                precision_values[k].append(precision_at_k(qa_item["relevant_chunk_ids"], predicted_chunk_ids, k))
            miss_reason = None if rr > 0 else "retrieval_miss"
        else:
            rr = 0.0
            miss_reason = None

        per_query.append(
            {
                "question_id": qa_item["question_id"],
                "is_answerable": qa_item.get("is_answerable", True),
                "reciprocal_rank": rr,
                "latency_ms": latency,
                "predicted_chunk_ids": predicted_chunk_ids,
                "relevant_chunk_ids": qa_item["relevant_chunk_ids"],
                "miss_reason": miss_reason,
            }
        )

    metrics: dict[str, Any] = {
        f"recall_at_{k}": round(mean(recall_values[k]) if recall_values[k] else 0.0, 4)
        for k in ks
    }
    metrics.update(
        {
            "mrr": round(mean(reciprocal_ranks) if reciprocal_ranks else 0.0, 4),
            "precision_at_5": round(mean(precision_values.get(5, []) or [0.0]), 4),
            "latency_ms": round(mean(latencies) if latencies else 0.0, 2),
            "answerable_query_count": len(answerable),
            "total_query_count": len(qa_items),
        }
    )
    return {"metrics": metrics, "per_query": per_query}
