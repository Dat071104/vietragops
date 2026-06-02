from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_answer_generator, get_store
from app.core.errors import AppError
from app.schemas.query import AskRequest, AskResponse
from rag.generation import AnswerGenerator, ContextBuilder, GuardrailEngine
from rag.retrieval import AdvancedHybridRetriever
from rag.retrieval.advanced_hybrid_retriever import AdvancedHybridConfig


router = APIRouter(tags=["query"])


def _build_answer_generator(use_reranker: bool) -> AnswerGenerator:
    if not use_reranker:
        return get_answer_generator()
    store = get_store()
    retriever = AdvancedHybridRetriever(
        store,
        config=AdvancedHybridConfig(enable_reranker=True, enable_source_priority=False, enable_recency=False),
    )
    return AnswerGenerator(
        context_builder=ContextBuilder(store, retriever=retriever),
        guardrails=GuardrailEngine(),
    )


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    if not payload.use_guardrail:
        raise AppError("API guardrails must remain enabled on /ask.", status_code=400)
    response = _build_answer_generator(payload.use_reranker).answer(
        payload.question,
        debug=payload.debug,
        top_k=payload.top_k,
    )
    return AskResponse(**response)
