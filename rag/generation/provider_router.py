"""Provider routing for deterministic mock, Groq, and optional local Ollama."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.generation.groq_client import GroqClient
from rag.generation.ollama_client import OllamaClient


@dataclass(frozen=True)
class ProviderInvocation:
    provider: str
    model: str
    payload: dict[str, Any] | None = None
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None


class ProviderRouter:
    def __init__(
        self,
        provider: str = "mock",
        groq_client: GroqClient | None = None,
        ollama_client: OllamaClient | None = None,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:3b",
        ollama_num_ctx: int = 8192,
    ) -> None:
        self.provider = provider.strip().casefold() or "mock"
        self.groq_client = groq_client or GroqClient()
        self.ollama_client = ollama_client or OllamaClient(
            base_url=ollama_base_url,
            model=ollama_model,
            num_ctx=ollama_num_ctx,
        )

    def current_provider(self) -> str:
        if self.provider in {"mock", "groq", "ollama"}:
            return self.provider
        return "mock"

    def current_model(self) -> str:
        provider = self.current_provider()
        if provider == "groq":
            return self.groq_client.model
        if provider == "ollama":
            return self.ollama_client.model
        return "deterministic-mock"

    def status(self) -> dict[str, Any]:
        ollama_status = self.ollama_client.status()
        return {
            "provider": self.current_provider(),
            "model": self.current_model(),
            "groq_available": self.groq_client.available(),
            "ollama": {
                "available": ollama_status.available,
                "model_available": ollama_status.model_available,
                "base_url": ollama_status.base_url,
                "model": ollama_status.model,
                "models": ollama_status.models,
                "error": ollama_status.error,
            },
        }

    def generate_json(self, prompt: str) -> ProviderInvocation:
        provider = self.current_provider()
        if provider == "groq":
            if not self.groq_client.available():
                return ProviderInvocation(provider=provider, model=self.current_model(), fallback_used=True, error="Groq is not configured.")
            try:
                return ProviderInvocation(
                    provider=provider,
                    model=self.current_model(),
                    payload=self.groq_client.generate_json(prompt),
                )
            except Exception as exc:
                return ProviderInvocation(provider=provider, model=self.current_model(), fallback_used=True, error=str(exc))
        if provider == "ollama":
            ollama_status = self.ollama_client.status()
            if not ollama_status.available:
                return ProviderInvocation(
                    provider=provider,
                    model=self.current_model(),
                    fallback_used=True,
                    error=ollama_status.error or "Ollama is unavailable.",
                )
            if not ollama_status.model_available:
                return ProviderInvocation(
                    provider=provider,
                    model=self.current_model(),
                    fallback_used=True,
                    error=f"Model '{self.current_model()}' is not installed in Ollama.",
                )
            try:
                return ProviderInvocation(
                    provider=provider,
                    model=self.current_model(),
                    payload=self.ollama_client.generate_json(prompt),
                )
            except Exception as exc:
                return ProviderInvocation(provider=provider, model=self.current_model(), fallback_used=True, error=str(exc))
        return ProviderInvocation(provider="mock", model=self.current_model(), fallback_used=True)

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ProviderInvocation:
        if self.current_provider() != "ollama":
            return ProviderInvocation(
                provider=self.current_provider(),
                model=self.current_model(),
                fallback_used=True,
                error="Tool calling demo is only enabled for Ollama in this build.",
            )
        ollama_status = self.ollama_client.status()
        if not ollama_status.available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=ollama_status.error or "Ollama is unavailable.",
            )
        if not ollama_status.model_available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=f"Model '{self.current_model()}' is not installed in Ollama.",
            )
        try:
            payload = self.ollama_client.chat(messages=messages, tools=tools)
        except Exception as exc:
            return ProviderInvocation(provider="ollama", model=self.current_model(), fallback_used=True, error=str(exc))
        message = payload.get("message") or {}
        return ProviderInvocation(
            provider="ollama",
            model=self.current_model(),
            content=message.get("content", ""),
            tool_calls=message.get("tool_calls") or [],
        )

    def chat(self, messages: list[dict[str, Any]]) -> ProviderInvocation:
        if self.current_provider() != "ollama":
            return ProviderInvocation(provider=self.current_provider(), model=self.current_model(), fallback_used=True)
        ollama_status = self.ollama_client.status()
        if not ollama_status.available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=ollama_status.error or "Ollama is unavailable.",
            )
        if not ollama_status.model_available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=f"Model '{self.current_model()}' is not installed in Ollama.",
            )
        try:
            payload = self.ollama_client.chat(messages=messages)
        except Exception as exc:
            return ProviderInvocation(provider="ollama", model=self.current_model(), fallback_used=True, error=str(exc))
        message = payload.get("message") or {}
        return ProviderInvocation(
            provider="ollama",
            model=self.current_model(),
            content=message.get("content", ""),
        )
