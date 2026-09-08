"""Provider routing for deterministic mock and explicitly selected clients.

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

OpenRouter is also explicitly selected and is restricted to non-research
product lanes. Its own free-model/fallback policy is handled by the isolated
client; it never falls back into Groq, Ollama, or DeepSeek.
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
from rag.generation.openrouter_client import (
    OpenRouterAuthError,
    OpenRouterClient,
    OpenRouterConfigError,
    OpenRouterNetworkError,
    OpenRouterProviderError,
    OpenRouterRateLimitError,
    OpenRouterRequestError,
    OpenRouterTimeoutError,
)

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
    requested_model: str | None = None
    served_provider: str | None = None


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


def _classify_openrouter_exception(exc: Exception) -> str:
    if isinstance(exc, OpenRouterConfigError):
        return "config_error"
    if isinstance(exc, OpenRouterRateLimitError):
        return "rate_limited"
    if isinstance(exc, OpenRouterAuthError):
        return "auth_failure"
    if isinstance(exc, OpenRouterTimeoutError):
        return "timeout"
    if isinstance(exc, OpenRouterNetworkError):
        return "network_failure"
    if isinstance(exc, OpenRouterProviderError):
        return "provider_error"
    if isinstance(exc, OpenRouterRequestError):
        return exc.failure_kind
    return "provider_error"


class ProviderRouter:
    def __init__(
        self,
        provider: str = "mock",
        mode: str = "development",
        groq_client: GroqClient | None = None,
        ollama_client: OllamaClient | None = None,
        deepseek_client: DeepSeekClient | None = None,
        openrouter_client: OpenRouterClient | None = None,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:3b",
        ollama_num_ctx: int = 8192,
        openrouter_model: str | None = None,
        openrouter_fallback_model: str | None = None,
        openrouter_base_url: str | None = None,
        openrouter_request_timeout_seconds: float | None = None,
        openrouter_max_requests_per_day: int | None = None,
        openrouter_allow_paid_models: bool | None = None,
        openrouter_http_referer: str | None = None,
        openrouter_x_title: str | None = None,
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
        self.openrouter_client = openrouter_client or OpenRouterClient(
            model=openrouter_model,
            fallback_model=openrouter_fallback_model,
            base_url=openrouter_base_url,
            timeout=openrouter_request_timeout_seconds,
            max_requests_per_day=openrouter_max_requests_per_day,
            allow_paid_models=openrouter_allow_paid_models,
            http_referer=openrouter_http_referer,
            x_title=openrouter_x_title,
        )

    def current_provider(self) -> str:
        if self.provider in {"mock", "groq", "ollama", "deepseek", "openrouter"}:
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
        if provider == "openrouter":
            return getattr(self.openrouter_client, "effective_model", self.openrouter_client.model)
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
        if provider == "openrouter":
            openrouter_payload = self.openrouter_client.status()
        else:
            openrouter_payload = {
                "provider": "openrouter",
                "model": self.openrouter_client.model,
                "fallback_model": self.openrouter_client.fallback_model,
                "available": False,
                "daily_requests_remaining": self.openrouter_client.status()["daily_requests_remaining"],
                "error": "Skipped because active provider is not openrouter.",
            }
        return {
            "provider": provider,
            "mode": self.mode,
            "model": self.current_model(),
            "groq_available": self.groq_client.available(),
            "deepseek_available": self.deepseek_client.available(),
            "openrouter_available": self.openrouter_client.available(),
            "openrouter": openrouter_payload,
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
        if self.mode == "research" and provider == "openrouter":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="OpenRouter is disabled in research mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
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
        if provider == "openrouter":
            return self._generate_json_openrouter(prompt, model=model, temperature=temperature, max_tokens=max_tokens)
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

    def _generate_json_openrouter(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderInvocation:
        requested_model = model or getattr(self.openrouter_client, "effective_model", self.openrouter_client.model)
        if not self.openrouter_client.available():
            return ProviderInvocation(
                provider="openrouter",
                model=requested_model,
                requested_model=requested_model,
                fallback_used=False,
                error="OpenRouter is not configured.",
                failure_kind="config_error",
                mode=self.mode,
            )
        try:
            request_kwargs: dict[str, Any] = {"model": requested_model}
            if temperature is not None:
                request_kwargs["temperature"] = temperature
            if max_tokens is not None:
                request_kwargs["max_tokens"] = max_tokens
            payload = self.openrouter_client.generate_json(prompt, **request_kwargs)
            served_model = self.openrouter_client.last_served_model or requested_model
            return ProviderInvocation(
                provider="openrouter",
                model=served_model,
                requested_model=requested_model,
                served_provider=self.openrouter_client.last_served_provider,
                payload=payload,
                fallback_used=served_model != requested_model,
                mode=self.mode,
                usage=self.openrouter_client.last_usage,
            )
        except OpenRouterRequestError as exc:
            return ProviderInvocation(
                provider="openrouter",
                model=exc.served_model or requested_model,
                requested_model=requested_model,
                served_provider=exc.served_provider,
                fallback_used=False,
                error=str(exc),
                failure_kind=_classify_openrouter_exception(exc),
                mode=self.mode,
                usage=exc.usage,
                provider_error_body=exc.provider_error_body,
            )
        except Exception as exc:
            return ProviderInvocation(
                provider="openrouter",
                model=requested_model,
                requested_model=requested_model,
                fallback_used=False,
                error=str(exc),
                failure_kind="provider_error",
                mode=self.mode,
            )
    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ProviderInvocation:
        if self.mode == "research" and self.current_provider() == "openrouter":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="OpenRouter tool calling is disabled in research mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
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
        if self.mode == "research" and self.current_provider() == "openrouter":
            return ProviderInvocation(
                provider="mock",
                model="deterministic-mock",
                fallback_used=True,
                error="OpenRouter chat is disabled in research mode.",
                failure_kind="policy_denied",
                mode=self.mode,
            )
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
