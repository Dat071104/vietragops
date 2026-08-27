from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_answer_generator, get_mcp_server, get_provider_router


router = APIRouter()


@router.get("/health")
def health() -> dict:
    generator = get_answer_generator()
    provider_router = get_provider_router()
    status = provider_router.status()
    return {
        "status": "ok",
        "groq_enabled": generator.groq_client.available(),
        "deepseek_enabled": status["deepseek_available"],
        "llm_provider": provider_router.current_provider(),
        "llm_model": provider_router.current_model(),
        "provider_mode": status["mode"],
        "ollama": status["ollama"],
        "mcp_configured": get_mcp_server().token_verifier.configured(),
    }
