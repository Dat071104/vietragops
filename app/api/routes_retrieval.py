from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_store
from app.core.errors import AppError
from app.schemas.query import RetrieveRequest, RetrieveResponse, RetrieveResult
from rag.retrieval import AdvancedHybridRetriever, BM25Retriever, DenseRetriever, HybridRetriever
from rag.retrieval.advanced_hybrid_retriever import AdvancedHybridConfig


router = APIRouter(tags=["retrieval"])


def _build_retriever(name: str, use_reranker: bool = False):
    store = get_store()
    if name == "hybrid" and use_reranker:
        return AdvancedHybridRetriever(
            store,
            config=AdvancedHybridConfig(enable_reranker=True, enable_source_priority=False, enable_recency=False),
        )
    if name == "bm25":
        return BM25Retriever(store)
    if name == "dense":
        return DenseRetriever(store)
    if name == "hybrid":
        return HybridRetriever(store)
    if name == "advanced_hybrid":
        return AdvancedHybridRetriever(store, config=AdvancedHybridConfig(enable_reranker=True, enable_source_priority=True, enable_recency=True))
    raise AppError(f"Unsupported retriever '{name}'.", status_code=400)


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(payload: RetrieveRequest) -> RetrieveResponse:
    retriever = _build_retriever(payload.retriever, use_reranker=payload.use_reranker)
    results = retriever.retrieve(payload.question, top_k=payload.top_k)
    return RetrieveResponse(
        results=[
            RetrieveResult(
                chunk_id=result.chunk_id,
                doc_id=result.doc_id,
                score=result.score,
                rank=result.rank,
                text=result.text,
                source_url=result.source_url,
                heading_path=result.heading_path,
                authority_level=result.authority_level,
                domain=result.domain,
                component_scores=result.component_scores,
            )
            for result in results
        ],
        retriever=retriever.name,
        backend=getattr(retriever, "backend_name", "unknown"),
        debug=(
            {
                "top_k": payload.top_k,
                "use_reranker": payload.use_reranker,
                "result_count": len(results),
                "component_score_keys": sorted({key for result in results for key in result.component_scores}),
            }
            if payload.debug
            else None
        ),
    )
