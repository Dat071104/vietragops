from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path

from rag.generation import AnswerGenerator, ContextBuilder, ProviderRouter
from rag.ingestion.firecrawl import FirecrawlAdapter
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.lifecycle.web_import import WebImportService
from rag.retrieval import ChunkIndexStore


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
    ollama_base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip())
    ollama_model: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "qwen2.5:3b").strip())
    ollama_num_ctx: int = field(default_factory=lambda: int(os.environ.get("OLLAMA_NUM_CTX", "8192")))


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_store() -> ChunkIndexStore:
    return ChunkIndexStore.from_jsonl(get_settings().chunks_path)


def refresh_live_caches() -> None:
    """Drop cached readers of the live manifest/chunks after a publish/retire/rollback.

    The next call to any of these rebuilds itself from whatever is on disk, so
    a request in flight during the swap either finishes against the old
    in-memory store or the caller re-fetches a fresh one -- never a mix.
    """
    get_store.cache_clear()
    get_context_builder.cache_clear()
    get_answer_generator.cache_clear()
    get_agent_answer_generator.cache_clear()


@lru_cache
def get_lifecycle_service() -> LifecycleService:
    settings = get_settings()
    registry = LifecycleRegistry(settings.lifecycle_root / "registry.db")
    return LifecycleService(
        registry=registry,
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
    registry = LifecycleRegistry(settings.lifecycle_root / "registry.db")
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
    return ContextBuilder(get_store())


@lru_cache
def get_provider_router() -> ProviderRouter:
    settings = get_settings()
    return ProviderRouter(
        provider=settings.llm_provider,
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
