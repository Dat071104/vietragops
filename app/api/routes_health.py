from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_answer_generator, get_provider_router


router = APIRouter()


@router.get("/health")
def health() -> dict:
    generator = get_answer_generator()
    provider_router = get_provider_router()
    return {
        "status": "ok",
        "groq_enabled": generator.groq_client.available(),
        "llm_provider": provider_router.current_provider(),
        "llm_model": provider_router.current_model(),
        "ollama": provider_router.status()["ollama"],
    }
