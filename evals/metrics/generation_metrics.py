"""Generation metric helpers for deterministic evaluation."""

from __future__ import annotations

from statistics import mean
from typing import Any

from rag.retrieval.base import tokenize


def normalized_exact_match(expected: str, actual: str) -> float:
    return 1.0 if " ".join(tokenize(expected)) == " ".join(tokenize(actual)) else 0.0


def token_f1(expected: str, actual: str) -> float:
    expected_tokens = tokenize(expected)
    actual_tokens = tokenize(actual)
    if not expected_tokens or not actual_tokens:
        return 0.0
    expected_counts = {}
    for token in expected_tokens:
        expected_counts[token] = expected_counts.get(token, 0) + 1
    actual_counts = {}
    for token in actual_tokens:
        actual_counts[token] = actual_counts.get(token, 0) + 1
    overlap = 0
    for token, count in expected_counts.items():
        overlap += min(count, actual_counts.get(token, 0))
    if overlap == 0:
        return 0.0
    precision = overlap / len(actual_tokens)
    recall = overlap / len(expected_tokens)
    return 2 * precision * recall / (precision + recall)


def aggregate_generation_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    exact = [normalized_exact_match(row["expected_answer"], row["answer"]) for row in records if row["is_answerable"]]
    f1_scores = [token_f1(row["expected_answer"], row["answer"]) for row in records if row["is_answerable"]]
    citation_support = [1.0 if row["citations_valid"] else 0.0 for row in records if row["is_answerable"]]
    answer_correct = [1.0 if token_f1(row["expected_answer"], row["answer"]) >= 0.45 else 0.0 for row in records if row["is_answerable"]]
    return {
        "exact_match": round(mean(exact) if exact else 0.0, 4),
        "token_f1": round(mean(f1_scores) if f1_scores else 0.0, 4),
        "citation_support_rate": round(mean(citation_support) if citation_support else 0.0, 4),
        "answer_correctness_rate": round(mean(answer_correct) if answer_correct else 0.0, 4),
    }
