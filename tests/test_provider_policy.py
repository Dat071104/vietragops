"""Gate 05 Phase 5.1/5.2: typed provider outcomes and mode-aware fallback.

Covers: distinct 429/timeout/network/auth/config outcomes for Groq (never
collapsed into a generic error); Groq-primary -> Ollama-fallback in
development/demo on any typed failure; research mode's hard refusal of
fallback (proven with a spy that fails the test if Ollama is ever touched);
the isolated DeepSeek provider never triggering or being triggered by any
other provider's fallback.
"""

from __future__ import annotations

import pytest

from rag.generation.groq_client import (
    GroqAuthError,
    GroqNetworkError,
    GroqProviderError,
    GroqRateLimitError,
    GroqTimeoutError,
)
from rag.generation.provider_router import ProviderRouter


class StubOllamaStatus:
    def __init__(self, available=True, model_available=True, error=None):
        self.available = available
        self.model_available = model_available
        self.base_url = "http://localhost:11434"
        self.model = "qwen3:8b"
        self.models = ["qwen3:8b"] if model_available else []
        self.error = error


class StubOllamaClient:
    model = "qwen3:8b"
    base_url = "http://localhost:11434"

    def __init__(self, status=None, generate_result=None, generate_error=None):
        self._status = status or StubOllamaStatus()
        self._generate_result = generate_result or {"answer": "ok", "citations": [], "confidence": 0.8, "refusal": False}
        self._generate_error = generate_error

    def status(self):
        return self._status

    def generate_json(self, prompt: str):
        if self._generate_error is not None:
            raise self._generate_error
        return self._generate_result


class UntouchableOllamaClient:
    """Fails the test the instant anything on it is accessed -- proves the
    local provider was never invoked (research-mode no-fallback guarantee)."""

    model = "qwen3:8b"
    base_url = "http://localhost:11434"

    def status(self):
        raise AssertionError("Ollama must not be probed in research mode after a Groq failure")

    def generate_json(self, prompt: str):
        raise AssertionError("Ollama must not be called in research mode after a Groq failure")


class FailingGroqClient:
    model = "qwen/qwen3.6-27b"

    def __init__(self, exc: Exception | None = None, configured: bool = True):
        self._exc = exc
        self._configured = configured

    def available(self) -> bool:
        return self._configured

    def generate_json(self, prompt: str):
        if self._exc is not None:
            raise self._exc
        raise AssertionError("generate_json should not be called when Groq is not configured")


class SucceedingGroqClient:
    model = "qwen/qwen3.6-27b"

    def available(self) -> bool:
        return True

    def generate_json(self, prompt: str):
        return {"answer": "groq answer", "citations": [], "confidence": 0.9, "refusal": False}


class StubDeepSeekClient:
    model = "deepseek-chat"

    def __init__(self, configured=True, result=None, error=None):
        self._configured = configured
        self._result = result or {"answer": "deepseek answer", "citations": [], "confidence": 0.7, "refusal": False}
        self._error = error

    def available(self):
        return self._configured

    def generate_json(self, prompt: str):
        if self._error is not None:
            raise self._error
        return self._result


GROQ_TYPED_FAILURES = [
    (GroqRateLimitError("rate limited"), "rate_limited"),
    (GroqTimeoutError("timed out"), "timeout"),
    (GroqNetworkError("network down"), "network_failure"),
    (GroqAuthError("bad key"), "auth_failure"),
    (GroqProviderError("server error"), "provider_error"),
]


@pytest.mark.parametrize("mode", ["development", "demo"])
def test_groq_success_has_no_failure_kind(mode):
    router = ProviderRouter(
        provider="groq",
        mode=mode,
        groq_client=SucceedingGroqClient(),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "groq"
    assert invocation.payload["answer"] == "groq answer"
    assert invocation.failure_kind is None
    assert invocation.fallback_used is False
    assert invocation.primary_attempt is None


@pytest.mark.parametrize("exc,expected_kind", GROQ_TYPED_FAILURES)
def test_groq_failure_kinds_are_typed_and_distinct(exc, expected_kind):
    router = ProviderRouter(
        provider="groq",
        mode="research",
        groq_client=FailingGroqClient(exc=exc),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "groq"
    assert invocation.failure_kind == expected_kind
    assert invocation.error is not None


def test_groq_not_configured_is_a_config_error_not_a_generic_failure():
    router = ProviderRouter(
        provider="groq",
        mode="research",
        groq_client=FailingGroqClient(configured=False),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.failure_kind == "config_error"


@pytest.mark.parametrize("exc,expected_kind", GROQ_TYPED_FAILURES)
def test_development_mode_falls_back_to_ollama_on_any_typed_groq_failure(exc, expected_kind):
    router = ProviderRouter(
        provider="groq",
        mode="development",
        groq_client=FailingGroqClient(exc=exc),
        ollama_client=StubOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "ollama"
    assert invocation.payload["answer"] == "ok"
    assert invocation.fallback_used is True
    assert invocation.primary_attempt is not None
    assert invocation.primary_attempt["provider"] == "groq"
    assert invocation.primary_attempt["failure_kind"] == expected_kind


def test_demo_mode_falls_back_to_ollama_and_discloses_actual_provider():
    router = ProviderRouter(
        provider="groq",
        mode="demo",
        groq_client=FailingGroqClient(exc=GroqRateLimitError("429")),
        ollama_client=StubOllamaClient(),
    )

    invocation = router.generate_json("hello")

    # Demo must never claim the fallback answer came from Groq.
    assert invocation.provider == "ollama"
    assert invocation.model == "qwen3:8b"
    assert invocation.fallback_used is True
    assert invocation.primary_attempt["provider"] == "groq"


def test_research_mode_never_falls_back_and_never_touches_ollama():
    router = ProviderRouter(
        provider="groq",
        mode="research",
        groq_client=FailingGroqClient(exc=GroqRateLimitError("429")),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "groq"
    assert invocation.payload is None
    assert invocation.fallback_used is False
    assert invocation.failure_kind == "rate_limited"
    assert invocation.primary_attempt is None


def test_research_mode_preserves_typed_outcome_for_every_failure_kind():
    for exc, expected_kind in GROQ_TYPED_FAILURES:
        router = ProviderRouter(
            provider="groq",
            mode="research",
            groq_client=FailingGroqClient(exc=exc),
            ollama_client=UntouchableOllamaClient(),
        )
        invocation = router.generate_json("hello")
        assert invocation.failure_kind == expected_kind
        assert invocation.fallback_used is False


def test_development_fallback_when_ollama_itself_is_unavailable_reports_ollama_network_failure():
    router = ProviderRouter(
        provider="groq",
        mode="development",
        groq_client=FailingGroqClient(exc=GroqNetworkError("down")),
        ollama_client=StubOllamaClient(status=StubOllamaStatus(available=False, error="connection refused")),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "ollama"
    assert invocation.payload is None
    assert invocation.fallback_used is True
    assert invocation.failure_kind == "network_failure"
    assert invocation.primary_attempt["provider"] == "groq"


def test_development_fallback_when_ollama_model_not_installed_reports_config_error():
    router = ProviderRouter(
        provider="groq",
        mode="development",
        groq_client=FailingGroqClient(exc=GroqTimeoutError("timeout")),
        ollama_client=StubOllamaClient(status=StubOllamaStatus(available=True, model_available=False)),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "ollama"
    assert invocation.failure_kind == "config_error"
    assert invocation.primary_attempt["failure_kind"] == "timeout"


def test_invalid_mode_normalizes_to_development():
    router = ProviderRouter(provider="groq", mode="not-a-real-mode", groq_client=SucceedingGroqClient())
    assert router.mode == "development"


def test_deepseek_is_isolated_and_never_calls_ollama():
    router = ProviderRouter(
        provider="deepseek",
        mode="research",
        deepseek_client=StubDeepSeekClient(),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "deepseek"
    assert invocation.payload["answer"] == "deepseek answer"
    assert invocation.failure_kind is None


def test_deepseek_not_configured_is_a_config_error_and_never_falls_back():
    router = ProviderRouter(
        provider="deepseek",
        mode="development",
        deepseek_client=StubDeepSeekClient(configured=False),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "deepseek"
    assert invocation.failure_kind == "config_error"
    assert invocation.fallback_used is True


def test_deepseek_failure_never_rescues_via_ollama_even_in_development():
    router = ProviderRouter(
        provider="deepseek",
        mode="development",
        deepseek_client=StubDeepSeekClient(error=RuntimeError("deepseek down")),
        ollama_client=UntouchableOllamaClient(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "deepseek"
    assert invocation.failure_kind == "provider_error"


def test_status_reports_mode_and_deepseek_availability():
    router = ProviderRouter(
        provider="groq",
        mode="demo",
        groq_client=SucceedingGroqClient(),
        deepseek_client=StubDeepSeekClient(configured=False),
    )

    status = router.status()

    assert status["mode"] == "demo"
    assert status["deepseek_available"] is False
    assert status["groq_available"] is True
