"""Reranker abstractions with a deterministic offline fallback."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import importlib
import logging
from typing import Any, Iterable

from rag.retrieval.base import RetrievalResult, make_word_bigrams, normalize_text, tokenize

logger = logging.getLogger(__name__)


_RERANKER_BACKEND_FAILURES = (ImportError, OSError, RuntimeError, TypeError, ValueError)


@dataclass(frozen=True)
class RerankScore:
    result: RetrievalResult
    score: float


class BaseReranker(ABC):
    name = "base_reranker"

    @abstractmethod
    def rerank(self, query: str, candidates: Iterable[RetrievalResult]) -> list[RerankScore]:
        raise NotImplementedError

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": "active",
            "degraded": False,
            "degradation_reason": None,
        }


class LexicalReranker(BaseReranker):
    name = "lexical_fallback"

    def __init__(self, degradation_reason: str | None = None) -> None:
        self.degradation_reason = degradation_reason

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": "degraded" if self.degradation_reason else "active",
            "degraded": self.degradation_reason is not None,
            "degradation_reason": self.degradation_reason,
        }

    def rerank(self, query: str, candidates: Iterable[RetrievalResult]) -> list[RerankScore]:
        query_tokens = tokenize(query)
        query_token_set = set(query_tokens)
        query_bigrams = set(make_word_bigrams(query_tokens))
        normalized_query = normalize_text(query)

        scored: list[RerankScore] = []
        for candidate in candidates:
            text_tokens = tokenize(candidate.text)
            title_tokens = tokenize(str(candidate.metadata.get("title", "")))
            heading_tokens = tokenize(" ".join(candidate.heading_path))
            body_set = set(text_tokens)
            heading_set = set(title_tokens + heading_tokens)
            body_bigrams = set(make_word_bigrams(text_tokens))
            heading_bigrams = set(make_word_bigrams(title_tokens + heading_tokens))

            coverage = _ratio(query_token_set.intersection(body_set), query_token_set)
            heading_overlap = _ratio(query_token_set.intersection(heading_set), query_token_set)
            bigram_overlap = _ratio(
                query_bigrams.intersection(body_bigrams.union(heading_bigrams)),
                query_bigrams,
            )
            exact_bonus = 1.0 if normalized_query and normalized_query in normalize_text(candidate.text) else 0.0
            score = (0.55 * coverage) + (0.2 * heading_overlap) + (0.2 * bigram_overlap) + (0.05 * exact_bonus)
            scored.append(RerankScore(result=candidate, score=round(score, 6)))

        return sorted(scored, key=lambda item: (-item.score, item.result.chunk_id))


class BGEReranker(BaseReranker):
    name = "bge_reranker"

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", local_files_only: bool = True) -> None:
        self.model_name = model_name
        self.local_files_only = local_files_only
        self._model = self._load_model()

    def _load_model(self):
        flag_embedding = importlib.import_module("FlagEmbedding")
        reranker_cls = getattr(flag_embedding, "FlagReranker")
        return reranker_cls(self.model_name, use_fp16=False, local_files_only=self.local_files_only)

    def rerank(self, query: str, candidates: Iterable[RetrievalResult]) -> list[RerankScore]:
        pairs = [[query, candidate.text] for candidate in candidates]
        if not pairs:
            return []
        scores = self._model.compute_score(pairs)
        if not isinstance(scores, list):
            scores = list(scores)
        scored = [
            RerankScore(result=candidate, score=float(score))
            for candidate, score in zip(candidates, scores, strict=False)
        ]
        return sorted(scored, key=lambda item: (-item.score, item.result.chunk_id))


def build_reranker() -> BaseReranker:
    try:
        return BGEReranker()
    except _RERANKER_BACKEND_FAILURES as exc:
        reason = f"{type(exc).__name__}: {exc}"
        logger.warning("BGE reranker unavailable; active backend=%s; reason=%s", LexicalReranker.name, reason)
        return LexicalReranker(degradation_reason=reason)


def _ratio(numerator: set[str], denominator: set[str]) -> float:
    if not denominator:
        return 0.0
    return len(numerator) / len(denominator)
