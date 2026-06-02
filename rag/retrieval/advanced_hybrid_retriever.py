"""Advanced hybrid retrieval with reranking, source authority, and recency scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag.retrieval.base import BaseRetriever, RetrievalResult
from rag.retrieval.hybrid_retriever import HybridRetriever
from rag.retrieval.index_store import ChunkIndexStore
from rag.retrieval.reranker import BaseReranker, LexicalReranker, build_reranker
from rag.retrieval.source_priority import load_manifest_rows, recency_score, source_authority_score


@dataclass(frozen=True)
class AdvancedHybridConfig:
    candidate_pool: int = 50
    enable_reranker: bool = True
    enable_source_priority: bool = True
    enable_recency: bool = True
    manifest_path: str = "data/manifests/documents_manifest.csv"


class AdvancedHybridRetriever(BaseRetriever):
    name = "advanced_hybrid"

    def __init__(
        self,
        store: ChunkIndexStore,
        config: AdvancedHybridConfig | None = None,
        reranker: BaseReranker | None = None,
    ) -> None:
        super().__init__(store)
        self.config = config or AdvancedHybridConfig()
        self.hybrid = HybridRetriever(store)
        self.reranker = reranker or (build_reranker() if self.config.enable_reranker else LexicalReranker())
        manifest_path = Path(self.config.manifest_path)
        self._manifest_rows = load_manifest_rows(manifest_path) if manifest_path.exists() else {}
        self.backend_name = (
            f"advanced({self.hybrid.backend_name}+{self.reranker.name}"
            f"+authority={self.config.enable_source_priority}"
            f"+recency={self.config.enable_recency})"
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        candidates = self.hybrid.retrieve(query, top_k=max(top_k, self.config.candidate_pool))
        if not candidates:
            return []

        hybrid_scores = {candidate.chunk_id: candidate.score for candidate in candidates}
        normalized_hybrid = _normalize_scores(hybrid_scores)

        rerank_scores = {candidate.chunk_id: 0.0 for candidate in candidates}
        if self.config.enable_reranker:
            reranked = self.reranker.rerank(query, candidates)
            rerank_scores = {item.result.chunk_id: item.score for item in reranked}
        normalized_rerank = _normalize_scores(rerank_scores)
        effective_rerank = {
            chunk_id: ((0.7 * normalized_rerank.get(chunk_id, 0.0)) + (0.3 * normalized_hybrid.get(chunk_id, 0.0)))
            if self.config.enable_reranker
            else normalized_hybrid.get(chunk_id, 0.0)
            for chunk_id in hybrid_scores
        }

        ranked_items = []
        for candidate in candidates:
            chunk = self.store.get(candidate.chunk_id)
            manifest_row = self._manifest_rows.get(chunk.doc_id)
            authority = source_authority_score(chunk) if self.config.enable_source_priority else 0.0
            recency = recency_score(chunk, manifest_row) if self.config.enable_recency else 0.0
            if self.config.enable_source_priority:
                final_score = (
                    0.65 * effective_rerank[candidate.chunk_id]
                    + 0.20 * normalized_hybrid[candidate.chunk_id]
                    + 0.10 * authority
                    + 0.05 * recency
                )
            else:
                final_score = (0.80 * effective_rerank[candidate.chunk_id]) + (0.20 * normalized_hybrid[candidate.chunk_id])
            ranked_items.append(
                (
                    final_score,
                    RetrievalResult(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        score=round(final_score, 6),
                        rank=0,
                        text=chunk.text,
                        source_url=chunk.source_url,
                        heading_path=list(chunk.heading_path),
                        authority_level=chunk.authority_level,
                        domain=chunk.domain,
                        component_scores={
                            "final_score": round(final_score, 6),
                            "rerank_score": round(effective_rerank[candidate.chunk_id], 6),
                            "hybrid_score": round(normalized_hybrid[candidate.chunk_id], 6),
                            "source_authority_score": round(authority, 6),
                            "recency_score": round(recency, 6),
                            "bm25_score": round(candidate.component_scores.get("bm25_score", 0.0), 6),
                            "dense_score": round(candidate.component_scores.get("dense_score", 0.0), 6),
                        },
                        metadata={"title": chunk.title},
                    ),
                )
            )

        ranked_items.sort(key=lambda item: (-item[0], item[1].chunk_id))
        output: list[RetrievalResult] = []
        for rank, (_, result) in enumerate(ranked_items[:top_k], start=1):
            output.append(
                RetrievalResult(
                    chunk_id=result.chunk_id,
                    doc_id=result.doc_id,
                    score=result.score,
                    rank=rank,
                    text=result.text,
                    source_url=result.source_url,
                    heading_path=result.heading_path,
                    authority_level=result.authority_level,
                    domain=result.domain,
                    component_scores=result.component_scores,
                    metadata=result.metadata,
                )
            )
        return output


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if high == low:
        baseline = 1.0 if high > 0 else 0.0
        return {key: baseline for key in scores}
    return {key: (value - low) / (high - low) for key, value in scores.items()}
