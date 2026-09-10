from __future__ import annotations

from rag.generation.openrouter_client import OpenRouterRateLimitError
from rag.generation.groq_client import GroqRateLimitError
from rag.generation.answer_generator import AnswerGenerator
from rag.generation.provider_router import ProviderInvocation, ProviderRouter

PRIMARY = "nvidia/nemotron-3-super-120b-a12b:free"


class StubOpenRouter:
    model = "nvidia/nemotron-3-super-120b-a12b:free"
    fallback_model = "google/gemma-4-31b-it:free"

    def __init__(self, *, result=None, error=None):
        self.result = result or {"answer": "openrouter", "citations": [], "confidence": 0.8, "refusal": False}
        self.error = error
        self.calls = []
        self.last_usage = {"input_tokens_actual": 2, "output_tokens_actual": 3, "total_tokens_actual": 5}
        self.last_served_model = self.model
        self.last_served_provider = "StubUpstream"

    def available(self):
        return True

    def generate_json(self, prompt: str, **kwargs):
        self.calls.append((prompt, kwargs))
        if self.error is not None:
            raise self.error
        return self.result

    def status(self):
        return {
            "provider": "openrouter",
            "model": self.model,
            "fallback_model": self.fallback_model,
            "available": True,
            "daily_requests_remaining": 999,
        }


class UntouchableOpenRouter(StubOpenRouter):
    def generate_json(self, prompt: str, **kwargs):
        raise AssertionError("research mode must not call OpenRouter")


class FailingGroq:
    model = "groq-test"

    def available(self):
        return True

    def generate_json(self, prompt: str):
        raise GroqRateLimitError("synthetic groq limit")


class StubOllama:
    model = "qwen3:8b"
    base_url = "http://localhost:11434"

    def status(self):
        return type("Status", (), {"available": True, "model_available": True, "error": None})()

    def generate_json(self, prompt: str):
        return {"answer": "ollama", "citations": [], "confidence": 0.7, "refusal": False}


def test_explicit_openrouter_selection_has_no_groq_or_ollama_fallback():
    client = StubOpenRouter(error=OpenRouterRateLimitError("synthetic rate limit"))
    router = ProviderRouter(provider="openrouter", mode="development", openrouter_client=client)

    invocation = router.generate_json("synthetic prompt")

    assert invocation.provider == "openrouter"
    assert invocation.failure_kind == "rate_limited"
    assert invocation.fallback_used is False
    assert len(client.calls) == 1


def test_explicit_openrouter_success_exposes_serving_metadata():
    client = StubOpenRouter()
    router = ProviderRouter(provider="openrouter", mode="demo", openrouter_client=client)

    invocation = router.generate_json("synthetic prompt", temperature=0.0, max_tokens=32)

    assert invocation.provider == "openrouter"
    assert invocation.payload["answer"] == "openrouter"
    assert invocation.failure_kind is None
    assert invocation.served_provider == "StubUpstream"
    assert invocation.requested_model == client.model
    assert client.calls[0][1] == {"model": client.model, "temperature": 0.0, "max_tokens": 32}


def test_groq_failure_does_not_implicitly_fallback_into_openrouter():
    client = StubOpenRouter()
    router = ProviderRouter(
        provider="groq",
        mode="development",
        groq_client=FailingGroq(),
        ollama_client=StubOllama(),
        openrouter_client=client,
    )

    invocation = router.generate_json("synthetic prompt")

    assert invocation.provider == "ollama"
    assert client.calls == []


def test_research_openrouter_is_policy_denied_without_http_attempt():
    client = UntouchableOpenRouter()
    router = ProviderRouter(provider="openrouter", mode="research", openrouter_client=client)

    invocation = router.generate_json("synthetic prompt")

    assert invocation.provider == "mock"
    assert invocation.model == "deterministic-mock"
    assert invocation.failure_kind == "policy_denied"
    assert invocation.fallback_used is True
    assert client.calls == []


def test_openrouter_status_shape_is_non_secret():
    client = StubOpenRouter()
    router = ProviderRouter(provider="openrouter", mode="development", openrouter_client=client)

    status = router.status()

    assert status["provider"] == "openrouter"
    assert status["openrouter_available"] is True
    assert status["openrouter"]["daily_requests_remaining"] == 999
    assert "api_key" not in repr(status).casefold()


def test_answer_generator_default_path_uses_configured_router(monkeypatch):
    class ConfiguredRouter:
        def generate_json(self, prompt, **kwargs):
            assert kwargs["max_tokens"] == generator.config.max_output_tokens
            return ProviderInvocation(
                provider="openrouter",
                model=PRIMARY,
                payload={"answer": "configured", "citations": [], "confidence": 0.8, "refusal": False},
                mode="development",
            )

    configured = ConfiguredRouter()
    monkeypatch.setattr(
        "rag.generation.answer_generator.ProviderRouter",
        lambda **kwargs: configured,
    )
    generator = AnswerGenerator(context_builder=object())

    response, metadata = generator._generate_response("question", "synthetic prompt", object())

    assert generator.provider_router is configured
    assert response["answer"] == "configured"
    assert metadata["provider"] == "openrouter"
