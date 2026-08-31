from __future__ import annotations

from rag.generation.groq_client import GroqClient, GroqRateLimitError
from rag.generation.provider_router import ProviderRouter


class FailingGroq:
    model = "test-groq-model"

    def available(self) -> bool:
        return True

    def generate_json(self, prompt: str):
        raise GroqRateLimitError("rate limited")


class UntouchableOllama:
    model = "qwen3:8b"
    base_url = "http://127.0.0.1:11434"

    def status(self):
        raise AssertionError("cloud mode must not probe localhost Ollama")

    def generate_json(self, prompt: str):
        raise AssertionError("cloud mode must not call localhost Ollama")


def test_cloud_groq_failure_is_typed_and_uses_deterministic_fallback():
    router = ProviderRouter(
        provider="groq",
        mode="cloud",
        groq_client=FailingGroq(),
        ollama_client=UntouchableOllama(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "mock"
    assert invocation.model == "deterministic-mock"
    assert invocation.fallback_used is True
    assert invocation.failure_kind == "rate_limited"
    assert invocation.primary_attempt["provider"] == "groq"


def test_cloud_ollama_selection_is_policy_denied_without_network_probe():
    router = ProviderRouter(
        provider="ollama",
        mode="cloud",
        ollama_client=UntouchableOllama(),
    )

    invocation = router.generate_json("hello")

    assert invocation.provider == "mock"
    assert invocation.fallback_used is True
    assert invocation.failure_kind == "policy_denied"


def test_cloud_groq_client_ignores_indexed_key_rotation_variables(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "cloud")
    monkeypatch.setenv("GROQ_API_KEY", "single-test-key")
    monkeypatch.setenv("GROQ_API_KEY_1", "indexed-test-key")
    monkeypatch.setenv("GROQ_API_KEY_2", "indexed-test-key-2")

    client = GroqClient()

    assert client.key_count == 1
    assert client._keys == ["single-test-key"]
