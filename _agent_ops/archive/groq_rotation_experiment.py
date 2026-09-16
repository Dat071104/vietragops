from __future__ import annotations

import json
from urllib import error

import pytest

from rag.generation.groq_client import GroqClient, redact_api_key


def test_redact_api_key():
    assert redact_api_key(None) == "<none>"
    assert redact_api_key("") == "<none>"
    assert redact_api_key("12345") == "****"
    assert redact_api_key("gsk_1234567890abcdef") == "gsk_...cdef"


def test_groq_client_discovers_multi_keys(monkeypatch):
    monkeypatch.setenv("GROQ_KEY_COUNT", "4")
    monkeypatch.setenv("GROQ_API_KEY_1", "key_one")
    monkeypatch.setenv("GROQ_API_KEY_2", "key_two")
    monkeypatch.setenv("GROQ_API_KEY_3", "")
    monkeypatch.setenv("GROQ_API_KEY_4", "key_four")
    monkeypatch.setenv("GROQ_API_KEY", "legacy_key")

    client = GroqClient()

    assert client.available() is True
    assert client.key_count == 4
    assert client._keys == ["key_one", "key_two", "key_four", "legacy_key"]


def test_groq_client_round_robin_selection():
    client = GroqClient(api_keys=["key_a", "key_b", "key_c"])

    k1, i1 = client._get_next_key()
    k2, i2 = client._get_next_key()
    k3, i3 = client._get_next_key()
    k4, i4 = client._get_next_key()

    assert (k1, i1) == ("key_a", 0)
    assert (k2, i2) == ("key_b", 1)
    assert (k3, i3) == ("key_c", 2)
    assert (k4, i4) == ("key_a", 0)


def test_groq_client_skips_key_in_cooldown():
    client = GroqClient(api_keys=["key_a", "key_b", "key_c"])

    # Mark key_a in cooldown
    client._mark_cooldown("key_a", duration=100.0)

    # Next key should skip key_a and give key_b, then key_c
    k1, i1 = client._get_next_key()
    k2, i2 = client._get_next_key()
    k3, i3 = client._get_next_key()

    assert k1 == "key_b"
    assert k2 == "key_c"
    assert k3 == "key_b"


def test_groq_client_retries_and_rotates_on_429(monkeypatch):
    client = GroqClient(api_keys=["bad_key", "good_key"], max_retries=2)

    call_history = []

    def mock_urlopen(raw_req, timeout):
        auth = raw_req.headers.get("Authorization", "")
        call_history.append(auth)
        if "bad_key" in auth:
            # Simulate 429 Rate Limit
            fp = None
            hdrs = {"Retry-After": "5"}
            raise error.HTTPError(raw_req.full_url, 429, "Rate Limit Exceeded", hdrs, fp)

        # Successful response for good_key
        class MockResp:
            def read(self):
                return json.dumps({
                    "choices": [{"message": {"content": json.dumps({"answer": "hello rotated"})}}]
                }).encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                pass

        return MockResp()

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    res = client.generate_json("test prompt")

    assert res == {"answer": "hello rotated"}
    assert len(call_history) == 2
    assert "Bearer bad_key" in call_history[0]
    assert "Bearer good_key" in call_history[1]


def test_groq_client_stats_reporting():
    client = GroqClient(api_keys=["key_1", "key_2"])
    stats = client.stats()

    assert stats["total_keys"] == 2
    assert len(stats["keys_status"]) == 2
    assert stats["keys_status"][0]["requests"] == 0
