"""Provider routing for deterministic mock, Groq, local Ollama fallback, and optional isolated DeepSeek.

Mode policy (Gate 05):
- `development`/`demo`: Groq primary; on any typed Groq failure, fall back to
  the local Ollama model for service continuity. Trace records the primary
  attempt, the actual final provider/model, fallback status, and the typed
  failure reason.
- `research`: no fallback, ever. A typed Groq failure is returned as a
  terminal outcome; Ollama is never invoked.

DeepSeek is a fully isolated, explicitly-selected provider (`provider=
"deepseek"`) -- it is never triggered by a Groq failure and never triggers
Ollama itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.generation.deepseek_client import DeepSeekClient
from rag.generation.groq_client import (
    GroqAuthError,
    GroqClient,
    GroqNetworkError,
    GroqProviderError,
    GroqRateLimitError,
    GroqRequestError,
    GroqTimeoutError,
)
from rag.generation.ollama_client import OllamaClient

PROVIDER_MODES = ("development", "demo", "research", "cloud")
FALLBACK_ELIGIBLE_MODES = ("development", "demo")


@dataclass(frozen=True)
class ProviderInvocation:
    provider: str
    model: str
    payload: dict[str, Any] | None = None
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None
    failure_kind: str | None = None
    mode: str | None = None
    primary_attempt: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    provider_error_body: str | None = None


def _classify_groq_exception(exc: Exception) -> str:
    if isinstance(exc, GroqRateLimitError):
        return "rate_limited"
    if isinstance(exc, GroqAuthError):
        return "auth_failure"
    if isinstance(exc, GroqTimeoutError):
        return "timeout"
    if isinstance(exc, GroqNetworkError):
        return "network_failure"
    return "provider_error"


class ProviderRouter:
    def __init__(
        self,
        provider: str = "mock",
        mode: str = "development",
        groq_client: GroqClient | None = None,
        ollama_client: OllamaClient | None = None,
        deepseek_client: DeepSeekClient | None = None,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:3b",
        ollama_num_ctx: int = 8192,
    ) -> None:
        self.provider = provider.strip().casefold() or "mock"
        normalized_mode = (mode or "development").strip().casefold()
        self.mode = normalized_mode if normalized_mode in PROVIDER_MODES else "development"
        self.groq_client = groq_client or GroqClient()
        self.ollama_client = ollama_client or OllamaClient(
            base_url=ollama_base_url,
            model=ollama_model,
            num_ctx=ollama_num_ctx,
        )
        self.deepseek_client = deepseek_client or DeepSeekClient()

    def current_provider(self) -> str:
        if self.provider in {"mock", "groq", "ollama", "deepseek"}:
            return self.provider
        return "mock"

    def current_model(self) -> str:
        provider = self.current_provider()
        if provider == "groq":
            return self.groq_client.model
        if provider == "ollama":
            return self.ollama_client.model
        if provider == "deepseek":
            return self.deepseek_client.model
        return "deterministic-mock"

    def status(self) -> dict[str, Any]:
        provider = self.current_provider()
        if provider == "ollama":
            ollama_status = self.ollama_client.status()
            ollama_payload = {
                "available": ollama_status.available,
                "model_available": ollama_status.model_available,
                "base_url": ollama_status.base_url,
                "model": ollama_status.model,
                "models": ollama_status.models,
                "error": ollama_status.error,
            }
        else:
            ollama_payload = {
                "available": False,
                "model_available": False,
                "base_url": self.ollama_client.base_url,
                "model": self.ollama_client.model,
                "models": [],
                "error": "Skipped because active provider is not ollama.",
            }
        return {
            "provider": provider,
            "mode": self.mode,
            "model": self.current_model(),
            "groq_available": self.groq_client.available(),
            "deepseek_available": self.deepseek_client.available(),
            "ollama": ollama_payload,
        }

    def generate_json(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderInvocation:
        provider = self.current_provider()
        if self.mode == "cloud" and provider == "ollama":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="Ollama is disabled in cloud mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
        if self.mode == "cloud" and provider == "deepseek":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="DeepSeek is disabled in cloud mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
        if provider == "groq":
            return self._generate_json_groq(prompt, model=model, temperature=temperature, max_tokens=max_tokens)
        if provider == "ollama":
            return self._generate_json_ollama(prompt, primary_attempt=None)
        if provider == "deepseek":
            return self._generate_json_deepseek(prompt)
        return ProviderInvocation(provider="mock", model=self.current_model(), fallback_used=True, mode=self.mode)

    def _generate_json_groq(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderInvocation:
        model = model or self.groq_client.model
        if not self.groq_client.available():
            primary = {"provider": "groq", "model": model, "error": "Groq is not configured.", "failure_kind": "config_error"}
            return self._resolve_groq_failure(prompt, primary)
        try:
            request_kwargs: dict[str, Any] = {}
            if model != self.groq_client.model:
                request_kwargs["model"] = model
            if temperature is not None:
                request_kwargs["temperature"] = temperature
            if max_tokens is not None:
                request_kwargs["max_tokens"] = max_tokens
            payload = self.groq_client.generate_json(prompt, **request_kwargs)
            return ProviderInvocation(
                provider="groq",
                model=model,
                payload=payload,
                mode=self.mode,
                usage=getattr(self.groq_client, "last_usage", None),
            )
        except GroqRequestError as exc:
            primary = {
                "provider": "groq",
                "model": model,
                "error": str(exc),
                "failure_kind": _classify_groq_exception(exc),
                "provider_error_body": getattr(exc, "provider_error_body", None),
                "usage": getattr(exc, "usage", None),
            }
            return self._resolve_groq_failure(prompt, primary)
        except Exception as exc:  # unexpected, non-typed failure -- still surfaced, never silently swallowed
            primary = {
                "provider": "groq",
                "model": model,
                "error": str(exc),
                "failure_kind": "provider_error",
                "provider_error_body": getattr(exc, "provider_error_body", None)
                or getattr(self.groq_client, "last_provider_error_body", None),
                "usage": getattr(self.groq_client, "last_usage", None),
            }
            return self._resolve_groq_failure(prompt, primary)

    def _resolve_groq_failure(self, prompt: str, primary: dict[str, Any]) -> ProviderInvocation:
        if self.mode not in FALLBACK_ELIGIBLE_MODES:
            if self.mode == "cloud":
                return ProviderInvocation(
                    provider="mock",
                    model="deterministic-mock",
                    fallback_used=True,
                    error=primary["error"],
                    failure_kind=primary["failure_kind"],
                    mode=self.mode,
                    primary_attempt=primary,
                    usage=primary.get("usage"),
                    provider_error_body=None,
                )
            # research mode: no fallback, no model substitution -- the typed
            # failure itself is the run outcome.
            return ProviderInvocation(
                provider="groq",
                model=primary["model"],
                fallback_used=False,
                error=primary["error"],
                failure_kind=primary["failure_kind"],
                mode=self.mode,
                usage=primary.get("usage"),
                provider_error_body=primary.get("provider_error_body"),
            )
        return self._generate_json_ollama(prompt, primary_attempt=primary)

    def _generate_json_ollama(self, prompt: str, primary_attempt: dict[str, Any] | None) -> ProviderInvocation:
        is_fallback = primary_attempt is not None
        ollama_status = self.ollama_client.status()
        if not ollama_status.available:
            return ProviderInvocation(
                provider="ollama",
                model=self.ollama_client.model,
                fallback_used=True,
                error=ollama_status.error or "Ollama is unavailable.",
                failure_kind="network_failure",
                mode=self.mode,
                primary_attempt=primary_attempt,
            )
        if not ollama_status.model_available:
            return ProviderInvocation(
                provider="ollama",
                model=self.ollama_client.model,
                fallback_used=True,
                error=f"Model '{self.ollama_client.model}' is not installed in Ollama.",
                failure_kind="config_error",
                mode=self.mode,
                primary_attempt=primary_attempt,
            )
        try:
            payload = self.ollama_client.generate_json(prompt)
            return ProviderInvocation(
                provider="ollama",
                model=self.ollama_client.model,
                payload=payload,
                fallback_used=is_fallback,
                mode=self.mode,
                primary_attempt=primary_attempt,
            )
        except Exception as exc:
            return ProviderInvocation(
                provider="ollama",
                model=self.ollama_client.model,
                fallback_used=True,
                error=str(exc),
                failure_kind="provider_error",
                mode=self.mode,
                primary_attempt=primary_attempt,
            )

    def _generate_json_deepseek(self, prompt: str) -> ProviderInvocation:
        model = self.deepseek_client.model
        if not self.deepseek_client.available():
            return ProviderInvocation(
                provider="deepseek",
                model=model,
                fallback_used=True,
                error="DeepSeek is not configured.",
                failure_kind="config_error",
                mode=self.mode,
            )
        try:
            payload = self.deepseek_client.generate_json(prompt)
            return ProviderInvocation(provider="deepseek", model=model, payload=payload, mode=self.mode)
        except Exception as exc:
            return ProviderInvocation(
                provider="deepseek",
                model=model,
                fallback_used=True,
                error=str(exc),
                failure_kind="provider_error",
                mode=self.mode,
            )

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ProviderInvocation:
        if self.mode == "cloud" and self.current_provider() == "ollama":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="Ollama is disabled in cloud mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
        if self.current_provider() != "ollama":
            return ProviderInvocation(
                provider=self.current_provider(),
                model=self.current_model(),
                fallback_used=True,
                error="Tool calling demo is only enabled for Ollama in this build.",
                mode=self.mode,
            )
        ollama_status = self.ollama_client.status()
        if not ollama_status.available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=ollama_status.error or "Ollama is unavailable.",
                mode=self.mode,
            )
        if not ollama_status.model_available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=f"Model '{self.current_model()}' is not installed in Ollama.",
                mode=self.mode,
            )
        try:
            payload = self.ollama_client.chat(messages=messages, tools=tools)
        except Exception as exc:
            return ProviderInvocation(provider="ollama", model=self.current_model(), fallback_used=True, error=str(exc), mode=self.mode)
        message = payload.get("message") or {}
        return ProviderInvocation(
            provider="ollama",
            model=self.current_model(),
            content=message.get("content", ""),
            tool_calls=message.get("tool_calls") or [],
            mode=self.mode,
        )

    def chat(self, messages: list[dict[str, Any]]) -> ProviderInvocation:
        if self.mode == "cloud" and self.current_provider() == "ollama":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="Ollama is disabled in cloud mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
        if self.current_provider() != "ollama":
            return ProviderInvocation(provider=self.current_provider(), model=self.current_model(), fallback_used=True, mode=self.mode)
        ollama_status = self.ollama_client.status()
        if not ollama_status.available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=ollama_status.error or "Ollama is unavailable.",
                mode=self.mode,
            )
        if not ollama_status.model_available:
            return ProviderInvocation(
                provider="ollama",
                model=self.current_model(),
                fallback_used=True,
                error=f"Model '{self.current_model()}' is not installed in Ollama.",
                mode=self.mode,
            )
        try:
            payload = self.ollama_client.chat(messages=messages)
        except Exception as exc:
            return ProviderInvocation(provider="ollama", model=self.current_model(), fallback_used=True, error=str(exc), mode=self.mode)
        message = payload.get("message") or {}
        return ProviderInvocation(
            provider="ollama",
            model=self.current_model(),
            content=message.get("content", ""),
            mode=self.mode,
        )
