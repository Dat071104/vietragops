from __future__ import annotations

from fastapi import APIRouter

from fastapi.responses import JSONResponse

from app.core.config import get_answer_generator, get_live_manifest_rows, get_mcp_server, get_provider_router, get_settings, get_store


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
        "mcp_configured": get_settings().mcp_cloud_iam or get_mcp_server().token_verifier.configured(),
        "storage_backend": get_settings().storage_backend,
    }


@router.get("/health/live")
def liveness() -> dict:
    """Process liveness without touching providers or durable storage."""

    return {"status": "ok"}


@router.get("/health/ready", response_model=None)
def readiness() -> dict:
    """Readiness requires the configured index and live manifest to load."""

    try:
        store = get_store()
        manifest_rows = get_live_manifest_rows()
    except Exception as exc:  # noqa: BLE001 - readiness must return a stable typed response
        code = getattr(exc, "code", "readiness_check_failed")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason_code": code},
        )
    return {
        "status": "ready",
        "index_version": store.index_version,
        "chunk_count": len(store),
        "document_count": len({row.get("doc_id") for row in manifest_rows if row.get("doc_id")}),
        "storage_backend": get_settings().storage_backend,
    }
