"""Reciprocal rank fusion helpers."""

from __future__ import annotations

from typing import Iterable

from rag.retrieval.base import RetrievalResult


def reciprocal_rank_fusion(
    ranked_lists: Iterable[tuple[str, list[RetrievalResult]]],
    *,
    rrf_k: int = 60,
) -> dict[str, dict]:
    fused: dict[str, dict] = {}
    for label, results in ranked_lists:
        for result in results:
            item = fused.setdefault(
                result.chunk_id,
                {
                    "result": result,
                    "rrf_score": 0.0,
                    "component_scores": {},
                },
            )
            item["rrf_score"] += 1.0 / (rrf_k + result.rank)
            item["component_scores"][label] = result.score
    return fused
