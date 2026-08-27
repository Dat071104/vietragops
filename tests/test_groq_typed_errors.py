"""Gate 05 Phase 5.1: the real `GroqClient` (not a stub) raises typed
exceptions once its multi-key rotation/retry is exhausted, instead of a
generic `RuntimeError`. Verifies the narrow, additive edit authorized in
DECISION_LOG.md DEC-0008 -- rotation/cooldown/retry behavior itself is
covered separately by the pre-existing `tests/test_groq_rotation.py` and is
untouched here.
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
    client = GroqClient(api_keys=["only_key"], max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(429, "Too Many Requests"))

    with pytest.raises(GroqRateLimitError) as exc_info:
        client.generate_json("hello")
    assert isinstance(exc_info.value, GroqRequestError)
    assert exc_info.value.__cause__ is not None


def test_exhausted_401_raises_auth_error(monkeypatch):
    client = GroqClient(api_keys=["only_key"], max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(401, "Unauthorized"))

    with pytest.raises(GroqAuthError):
        client.generate_json("hello")


def test_exhausted_503_raises_provider_error(monkeypatch):
    client = GroqClient(api_keys=["only_key"], max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(503, "Service Unavailable"))

    with pytest.raises(GroqProviderError):
        client.generate_json("hello")


def test_exhausted_timeout_raises_timeout_error(monkeypatch):
    client = GroqClient(api_keys=["only_key"], max_retries=0)

    def _urlopen(raw_req, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    with pytest.raises(GroqTimeoutError):
        client.generate_json("hello")


def test_exhausted_connection_refused_raises_network_error(monkeypatch):
    client = GroqClient(api_keys=["only_key"], max_retries=0)

    def _urlopen(raw_req, timeout):
        raise error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    with pytest.raises(GroqNetworkError):
        client.generate_json("hello")


def test_typed_error_preserves_original_message_text(monkeypatch):
    client = GroqClient(api_keys=["only_key"], max_retries=0)
    monkeypatch.setattr("urllib.request.urlopen", _raise_http_error(429, "Too Many Requests"))

    with pytest.raises(GroqRateLimitError) as exc_info:
        client.generate_json("hello")
    assert "Groq request failed after" in str(exc_info.value)
    assert "429" in str(exc_info.value)


def test_rotation_across_multiple_keys_still_works_before_exhaustion(monkeypatch):
    """Non-regression: the pre-existing rotation behavior (already covered by
    tests/test_groq_rotation.py) is unaffected by the typed-exception edit --
    a later key that succeeds still returns normally, no exception raised."""
    import json

    client = GroqClient(api_keys=["bad_key", "good_key"], max_retries=2)
    call_history = []

    def _urlopen(raw_req, timeout):
        auth = raw_req.headers.get("Authorization", "")
        call_history.append(auth)
        if "bad_key" in auth:
            raise error.HTTPError(raw_req.full_url, 429, "Rate Limit", {"Retry-After": "1"}, None)

        class MockResp:
            def read(self):
                return json.dumps({"choices": [{"message": {"content": json.dumps({"answer": "ok"})}}]}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        return MockResp()

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = client.generate_json("hello")
    assert result == {"answer": "ok"}
