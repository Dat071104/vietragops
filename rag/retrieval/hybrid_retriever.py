"""Hybrid retrieval using reciprocal rank fusion over BM25 and dense baselines."""

from __future__ import annotations

from dataclasses import dataclass

from rag.retrieval.base import BaseRetriever, RetrievalResult
from rag.retrieval.bm25_retriever import BM25Retriever
from rag.retrieval.dense_retriever import DenseRetriever
from rag.retrieval.index_store import ChunkIndexStore
from rag.retrieval.rrf import reciprocal_rank_fusion


@dataclass(frozen=True)
class HybridConfig:
    rrf_k: int = 60
    candidate_pool: int = 30


class HybridRetriever(BaseRetriever):
    name = "hybrid"

    def __init__(self, store: ChunkIndexStore, config: HybridConfig | None = None) -> None:
        super().__init__(store)
        self.config = config or HybridConfig()
        self.bm25 = BM25Retriever(store)
        self.dense = DenseRetriever(store)
        self.backend_name = f"rrf({self.bm25.backend_name}+{self.dense.backend_name})"

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        depth = max(top_k, self.config.candidate_pool)
        bm25_results = self.bm25.retrieve(query, top_k=depth)
        dense_results = self.dense.retrieve(query, top_k=depth)
        fused = reciprocal_rank_fusion(
            [
                ("bm25_score", bm25_results),
                ("dense_score", dense_results),
            ],
            rrf_k=self.config.rrf_k,
        )
        ranked = sorted(
            fused.values(),
            key=lambda item: (-item["rrf_score"], item["result"].chunk_id),
        )[:top_k]
        return [
            RetrievalResult(
                chunk_id=item["result"].chunk_id,
                doc_id=item["result"].doc_id,
                score=item["rrf_score"],
                rank=rank,
                text=item["result"].text,
                source_url=item["result"].source_url,
                heading_path=list(item["result"].heading_path),
                authority_level=item["result"].authority_level,
                domain=item["result"].domain,
                component_scores={
                    "hybrid_score": item["rrf_score"],
                    "bm25_score": item["component_scores"].get("bm25_score", 0.0),
                    "dense_score": item["component_scores"].get("dense_score", 0.0),
                },
                metadata=item["result"].metadata,
            )
            for rank, item in enumerate(ranked, start=1)
        ]
