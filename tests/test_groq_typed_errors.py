"""The real `GroqClient` raises typed exceptions after single-key retries.

Rotation/cooldown behavior was retired by Gate 11-OR-I; this file preserves
the typed error contract and single-key retry checks.
"""

from __future__ import annotations

from urllib import error

import pytest

from rag.generation.groq_client import (
    GroqAuthError,
    GroqClient,
    GroqNetworkError,
    GroqProviderError,
    GroqRateLimitError,
    GroqRequestError,
    GroqTimeoutError,
)


def _raise_http_error(code: str, reason: str):
    def _urlopen(raw_req, timeout):
        raise error.HTTPError(raw_req.full_url, code, reason, {}, None)

    return _urlopen


def test_exhausted_429_raises_rate_limit_error(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(429, "Too Many Requests"))

    with pytest.raises(GroqRateLimitError) as exc_info:
        client.generate_json("hello")
    assert isinstance(exc_info.value, GroqRequestError)
    assert exc_info.value.__cause__ is not None


def test_exhausted_401_raises_auth_error(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(401, "Unauthorized"))

    with pytest.raises(GroqAuthError):
        client.generate_json("hello")


def test_exhausted_503_raises_provider_error(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(503, "Service Unavailable"))

    with pytest.raises(GroqProviderError):
        client.generate_json("hello")


def test_exhausted_timeout_raises_timeout_error(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)

    def _urlopen(raw_req, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    with pytest.raises(GroqTimeoutError):
        client.generate_json("hello")


def test_exhausted_connection_refused_raises_network_error(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)

    def _urlopen(raw_req, timeout):
        raise error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    with pytest.raises(GroqNetworkError):
        client.generate_json("hello")


def test_typed_error_preserves_original_message_text(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(429, "Too Many Requests"))

    with pytest.raises(GroqRateLimitError) as exc_info:
        client.generate_json("hello")
    assert "Groq request failed after" in str(exc_info.value)
    assert "429" in str(exc_info.value)


def test_single_key_does_not_rotate_after_rate_limit(monkeypatch):
    client = GroqClient(api_key="only_key", max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(429, "Rate Limit"))

    with pytest.raises(GroqRateLimitError):
        client.generate_json("hello")
    assert client.key_count == 1
    assert client._keys == ["only_key"]


def test_single_key_honors_retry_after_before_retrying(monkeypatch):
    sleeps = []
    calls = []
    client = GroqClient(api_key="only_key", max_retries=1, sleep_fn=sleeps.append)
    client.jitter_seconds = 0.0

    def _urlopen(raw_req, timeout):
        calls.append(raw_req.headers.get("Authorization"))
        raise error.HTTPError(raw_req.full_url, 429, "Rate Limit", {"Retry-After": "2"}, None)

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    with pytest.raises(GroqRateLimitError):
        client.generate_json("hello")

    assert calls == ["Bearer only_key", "Bearer only_key"]
    assert sleeps == [2.0]
