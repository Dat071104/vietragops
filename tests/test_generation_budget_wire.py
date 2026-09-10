from __future__ import annotations

import json

from rag.generation.deepseek_client import DeepSeekClient
from rag.generation.groq_client import GroqClient
from rag.generation.ollama_client import OllamaClient


class _UrlResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {"content": '{"ok": true}'},
                        "finish_reason": "stop",
                    }
                ]
            }
        ).encode("utf-8")


def test_groq_output_budget_reaches_wire(monkeypatch):
    captured = []

    def fake_urlopen(raw_request, timeout):
        captured.append(json.loads(raw_request.data.decode("utf-8")))
        return _UrlResponse()

    monkeypatch.setattr("rag.generation.groq_client.request.urlopen", fake_urlopen)
    client = GroqClient(api_key="test-key", max_retries=0)

    assert client.generate_json("hello", max_tokens=2048) == {"ok": True}
    assert captured[0]["max_tokens"] == 2048


def test_deepseek_output_budget_reaches_wire(monkeypatch):
    captured = []

    def fake_urlopen(raw_request, timeout):
        captured.append(json.loads(raw_request.data.decode("utf-8")))
        return _UrlResponse()

    monkeypatch.setattr("rag.generation.deepseek_client.request.urlopen", fake_urlopen)
    client = DeepSeekClient(api_key="test-key")

    assert client.generate_json("hello", max_tokens=2048) == {"ok": True}
    assert captured[0]["max_tokens"] == 2048


def test_ollama_output_budget_reaches_wire(monkeypatch):
    captured = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": '{"ok": true}'}}

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json):
            captured.append(json)
            return FakeResponse()

    monkeypatch.setattr("rag.generation.ollama_client.httpx.Client", lambda **kwargs: FakeClient())
    client = OllamaClient()

    assert client.generate_json("hello", max_tokens=2048) == {"ok": True}
    assert captured[0]["options"]["num_predict"] == 2048
