from __future__ import annotations

from rag.generation.provider_router import ProviderRouter


class StubGroqClient:
    model = "llama-3.3-70b-versatile"

    def available(self) -> bool:
        return False

    def generate_json(self, prompt: str) -> dict:
        raise AssertionError("Should not be called when unavailable")


class StubOllamaClient:
    model = "qwen2.5:3b"

    def status(self):
        return type(
            "Status",
            (),
            {
                "available": True,
                "model_available": True,
                "models": ["qwen2.5:3b"],
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:3b",
                "error": None,
            },
        )()

    def generate_json(self, prompt: str) -> dict:
        return {"answer": "structured", "citations": [], "confidence": 0.7, "refusal": False}

    def chat(self, messages, tools=None):
        if tools:
            return {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {"name": "retrieve_policy_context", "arguments": {"question": "abc"}},
                        }
                    ],
                }
            }
        return {"message": {"content": "done"}}


def test_provider_router_mock_is_safe_and_deterministic():
    router = ProviderRouter(provider="mock", groq_client=StubGroqClient(), ollama_client=StubOllamaClient())

    invocation = router.generate_json("hello")

    assert invocation.provider == "mock"
    assert invocation.payload is None
    assert invocation.fallback_used is True


def test_provider_router_ollama_returns_structured_payload():
    router = ProviderRouter(provider="ollama", groq_client=StubGroqClient(), ollama_client=StubOllamaClient())

    invocation = router.generate_json("hello")

    assert invocation.provider == "ollama"
    assert invocation.payload["answer"] == "structured"
    assert invocation.fallback_used is False


def test_provider_router_ollama_tool_call_trace():
    router = ProviderRouter(provider="ollama", groq_client=StubGroqClient(), ollama_client=StubOllamaClient())

    invocation = router.chat_with_tools([{"role": "user", "content": "x"}], [{"type": "function"}])

    assert invocation.tool_calls
    assert invocation.tool_calls[0]["function"]["name"] == "retrieve_policy_context"
