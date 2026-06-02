from __future__ import annotations

import httpx

from rag.generation.ollama_client import OllamaClient


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.request = httpx.Request("GET", "http://localhost")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=self.request, response=httpx.Response(self.status_code))

    def json(self) -> dict:
        return self._payload


class FakeHttpxClient:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str):
        return FakeResponse(self.responses[url])

    def post(self, url: str, json: dict):
        return FakeResponse(self.responses[url])


def test_ollama_client_status_reports_model_availability(monkeypatch):
    def fake_client(*args, **kwargs):
        return FakeHttpxClient(
            {"http://localhost:11434/api/tags": {"models": [{"name": "qwen2.5:3b"}, {"name": "phi3"}]}}
        )

    monkeypatch.setattr("rag.generation.ollama_client.httpx.Client", fake_client)
    client = OllamaClient()

    status = client.status()

    assert status.available is True
    assert status.model_available is True
    assert "qwen2.5:3b" in status.models


def test_ollama_client_generate_json_uses_chat_endpoint(monkeypatch):
    def fake_client(*args, **kwargs):
        return FakeHttpxClient(
            {
                "http://localhost:11434/api/chat": {
                    "message": {"content": '{"answer":"ok","citations":[],"confidence":0.5,"refusal":false}'}
                }
            }
        )

    monkeypatch.setattr("rag.generation.ollama_client.httpx.Client", fake_client)
    client = OllamaClient()

    payload = client.generate_json("hello")

    assert payload["answer"] == "ok"
    assert payload["refusal"] is False
