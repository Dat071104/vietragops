from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path

from rag.generation import AnswerGenerator, ContextBuilder, ProviderRouter
from rag.retrieval import ChunkIndexStore


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    chunks_path: Path = ROOT / "data" / "chunks" / "chunks_500.jsonl"
    manifest_path: Path = ROOT / "data" / "manifests" / "documents_manifest.csv"
    dev_qa_path: Path = ROOT / "evals" / "datasets" / "dev_qa.jsonl"
    validation_qa_path: Path = ROOT / "evals" / "datasets" / "validation_qa.jsonl"
    raw_upload_dir: Path = ROOT / "data" / "raw" / "uploads"
    experiment_dir: Path = ROOT / "dist" / "experiments"
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
        provider="ollama",
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
