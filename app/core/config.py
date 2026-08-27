from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path

from app.mcp.server import BuiltMcpServer, build_mcp_server
from rag.generation import AnswerGenerator, ContextBuilder, ProviderRouter
from rag.ingestion.firecrawl import FirecrawlAdapter
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.lifecycle.web_import import WebImportService
from rag.retrieval import ChunkIndexStore, VersionResolver
from rag.retrieval.source_priority import load_manifest_rows


ROOT = Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    override = os.environ.get(name, "").strip()
    return Path(override) if override else default


@dataclass(frozen=True)
class Settings:
    chunks_path: Path = field(
        default_factory=lambda: _env_path("VIETRAGOPS_CHUNKS_PATH", ROOT / "data" / "chunks" / "chunks_500.jsonl")
    )
    manifest_path: Path = field(
        default_factory=lambda: _env_path(
            "VIETRAGOPS_MANIFEST_PATH", ROOT / "data" / "manifests" / "documents_manifest.csv"
        )
    )
    dev_qa_path: Path = ROOT / "evals" / "datasets" / "dev_qa.jsonl"
    validation_qa_path: Path = ROOT / "evals" / "datasets" / "validation_qa.jsonl"
    raw_upload_dir: Path = ROOT / "data" / "raw" / "uploads"
    experiment_dir: Path = ROOT / "dist" / "experiments"
    lifecycle_root: Path = field(
        default_factory=lambda: _env_path("VIETRAGOPS_LIFECYCLE_ROOT", ROOT / "data" / "lifecycle")
    )
    lifecycle_max_upload_bytes: int = field(
        default_factory=lambda: int(os.environ.get("VIETRAGOPS_LIFECYCLE_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    )
    candidate_pdf_parser: str = field(
        default_factory=lambda: os.environ.get("VIETRAGOPS_CANDIDATE_PDF_PARSER", "markitdown").strip().casefold()
    )
    firecrawl_allowed_domains: str = field(
        default_factory=lambda: os.environ.get("FIRECRAWL_ALLOWED_DOMAINS", "").strip()
    )
    firecrawl_denied_domains: str = field(
        default_factory=lambda: os.environ.get("FIRECRAWL_DENIED_DOMAINS", "").strip()
    )
    firecrawl_timeout_seconds: float = field(
        default_factory=lambda: float(os.environ.get("FIRECRAWL_TIMEOUT_SECONDS", "20"))
    )
    firecrawl_max_response_bytes: int = field(
        default_factory=lambda: int(os.environ.get("FIRECRAWL_MAX_RESPONSE_BYTES", str(2 * 1024 * 1024)))
    )
    firecrawl_max_search_results: int = field(
        default_factory=lambda: int(os.environ.get("FIRECRAWL_MAX_SEARCH_RESULTS", "5"))
    )
    firecrawl_max_retries: int = field(
        default_factory=lambda: int(os.environ.get("FIRECRAWL_MAX_RETRIES", "2"))
    )
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "mock").strip().casefold())
    provider_mode: str = field(default_factory=lambda: os.environ.get("PROVIDER_MODE", "development").strip().casefold())
    ollama_base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip())
    ollama_model: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "qwen2.5:3b").strip())
    ollama_num_ctx: int = field(default_factory=lambda: int(os.environ.get("OLLAMA_NUM_CTX", "8192")))
    mcp_bearer_token: str = field(default_factory=lambda: os.environ.get("MCP_BEARER_TOKEN", "").strip())
    mcp_host: str = field(default_factory=lambda: os.environ.get("MCP_HOST", "127.0.0.1").strip())
    mcp_enable_protected_probe_tool: bool = field(
        default_factory=lambda: os.environ.get("MCP_ENABLE_PROTECTED_PROBE_TOOL", "").strip().casefold()
        in {"1", "true", "yes", "on"}
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_store() -> ChunkIndexStore:
    return ChunkIndexStore.from_jsonl(get_settings().chunks_path)


@lru_cache
def get_lifecycle_registry() -> LifecycleRegistry:
    return LifecycleRegistry(get_settings().lifecycle_root / "registry.db")


@lru_cache
def get_version_resolver() -> VersionResolver:
    """Version-aware resolution for retrieved chunks (Gate 04).

    Reuses the existing manifest loader (`load_manifest_rows`, already used
    by `AdvancedHybridRetriever` for authority/recency scoring) and the
    existing lifecycle registry -- no new source of truth. Cache-cleared by
    `refresh_live_caches` alongside the store it describes so a
    publish/retire/rollback is reflected on the next call.
    """
    settings = get_settings()
    manifest_rows = load_manifest_rows(settings.manifest_path) if settings.manifest_path.exists() else {}
    return VersionResolver(
        manifest_rows,
        get_store().index_version,
        registry=get_lifecycle_registry(),
    )


def refresh_live_caches() -> None:
    """Drop cached readers of the live manifest/chunks after a publish/retire/rollback.

    The next call to any of these rebuilds itself from whatever is on disk, so
    a request in flight during the swap either finishes against the old
    in-memory store or the caller re-fetches a fresh one -- never a mix.
    """
    get_store.cache_clear()
    get_version_resolver.cache_clear()
    get_context_builder.cache_clear()
    get_answer_generator.cache_clear()
    get_agent_answer_generator.cache_clear()
    get_mcp_server.cache_clear()


@lru_cache
def get_lifecycle_service() -> LifecycleService:
    settings = get_settings()
    return LifecycleService(
        registry=get_lifecycle_registry(),
        originals_dir=settings.lifecycle_root / "originals",
        candidates_dir=settings.lifecycle_root / "candidates",
        live_manifest_path=settings.manifest_path,
        live_chunks_path=settings.chunks_path,
        max_upload_bytes=settings.lifecycle_max_upload_bytes,
        refresh_live_caches=refresh_live_caches,
        pdf_parser_policy=settings.candidate_pdf_parser,
    )


@lru_cache
def get_web_import_service() -> WebImportService:
    """Local-only wiring for the Gate-03 Firecrawl adapter. There is no
    FastAPI route for this: the application has no admin authorization to
    gate a public HTTP endpoint, so `scripts/web_import.py` is the only
    caller, run directly by an operator on this machine."""

    settings = get_settings()
    registry = get_lifecycle_registry()
    adapter = FirecrawlAdapter(
        timeout_seconds=settings.firecrawl_timeout_seconds,
        max_response_bytes=settings.firecrawl_max_response_bytes,
        max_search_results=settings.firecrawl_max_search_results,
        max_retries=settings.firecrawl_max_retries,
    )
    return WebImportService(
        registry=registry,
        adapter=adapter,
        originals_dir=settings.lifecycle_root / "originals",
        candidates_dir=settings.lifecycle_root / "candidates",
        allowed_domains_csv=settings.firecrawl_allowed_domains,
        denied_domains_csv=settings.firecrawl_denied_domains,
        max_search_results=settings.firecrawl_max_search_results,
    )


@lru_cache
def get_context_builder() -> ContextBuilder:
    return ContextBuilder(get_store(), version_resolver=get_version_resolver())


@lru_cache
def get_provider_router() -> ProviderRouter:
    settings = get_settings()
    return ProviderRouter(
        provider=settings.llm_provider,
        mode=settings.provider_mode,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_num_ctx=settings.ollama_num_ctx,
    )


@lru_cache
def get_answer_generator() -> AnswerGenerator:
    return AnswerGenerator(
        context_builder=get_context_builder(),
        provider_router=get_provider_router(),
    )


@lru_cache
def get_agent_provider_router() -> ProviderRouter:
    settings = get_settings()
    return ProviderRouter(
        provider=settings.llm_provider,
        mode=settings.provider_mode,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_num_ctx=settings.ollama_num_ctx,
    )


@lru_cache
def get_agent_answer_generator() -> AnswerGenerator:
    return AnswerGenerator(
        context_builder=get_context_builder(),
        provider_router=get_agent_provider_router(),
    )


@lru_cache
def get_mcp_server() -> BuiltMcpServer:
    settings = get_settings()
    return build_mcp_server(
        context_builder=get_context_builder(),
        lifecycle_service=get_lifecycle_service(),
        store=get_store(),
        bearer_token=settings.mcp_bearer_token or None,
        host=settings.mcp_host,
        enable_protected_probe_tool=settings.mcp_enable_protected_probe_tool,
    )
