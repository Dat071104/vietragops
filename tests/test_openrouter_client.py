from __future__ import annotations

from io import BytesIO
import json
from urllib import error

import pytest

from rag.generation.openrouter_client import (
    I2_FREE_MODEL_CATALOG,
    OpenRouterAuthError,
    OpenRouterClient,
    OpenRouterConfigError,
    OpenRouterNetworkError,
    OpenRouterProviderError,
    OpenRouterRateLimitError,
    OpenRouterTimeoutError,
)


PRIMARY = "nvidia/nemotron-3-super-120b-a12b:free"
FALLBACK = "google/gemma-4-31b-it:free"
SECRET = "openrouter-test-secret"


class FakeResponse:
    def __init__(self, body: dict, status: int = 200, headers: dict[str, str] | None = None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.body).encode("utf-8")


def success_body(model: str = FALLBACK) -> dict:
    return {
        "id": "gen-test",
        "model": model,
        "provider": "TestUpstream",
        "choices": [{"message": {"role": "assistant", "content": '{"ok": true}'}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
    }


def make_client(*, catalog=None, loader=None, **kwargs) -> OpenRouterClient:
    catalog = I2_FREE_MODEL_CATALOG if catalog is None else catalog
    options = {
        "api_key": SECRET,
        "model": PRIMARY,
        "fallback_model": FALLBACK,
        "free_catalog": catalog,
        "catalog_loader": loader or (lambda: catalog),
        "timeout": 90,
        "max_retries": kwargs.pop("max_retries", 0),
        "sleep_fn": kwargs.pop("sleep_fn", lambda _seconds: None),
    }
    options.update(kwargs)
    return OpenRouterClient(**options)


def test_available_and_unavailable_without_exposing_key():
    unavailable = OpenRouterClient(api_key="", model=PRIMARY)
    assert unavailable.available() is False
    assert unavailable.status()["available"] is False
    assert SECRET not in repr(unavailable.status())

    available = make_client()
    assert available.available() is True
    assert SECRET not in repr(available.status())


def test_success_parse_uses_catalog_guard_and_models_array(monkeypatch):
    captured = []

    def fake_urlopen(raw_request, timeout):
        captured.append((json.loads(raw_request.data.decode("utf-8")), timeout))
        return FakeResponse(success_body())

    monkeypatch.setattr("rag.generation.openrouter_client.request.urlopen", fake_urlopen)
    client = make_client()

    assert client.generate_json("synthetic prompt") == {"ok": True}
    payload, timeout = captured[0]
    assert payload["models"] == [PRIMARY, FALLBACK]
    assert payload["response_format"] == {"type": "json_object"}
    assert timeout == 90
    assert client.last_served_provider == "TestUpstream"
    assert client.status()["daily_requests_used"] == 1


def test_measured_primary_is_in_default_routing_array(monkeypatch):
    captured = []

    def fake_urlopen(raw_request, timeout):
        captured.append(json.loads(raw_request.data.decode("utf-8")))
        return FakeResponse(success_body(FALLBACK))

    monkeypatch.setattr("rag.generation.openrouter_client.request.urlopen", fake_urlopen)
    client = make_client()

    assert client.generate_json("synthetic prompt") == {"ok": True}
    assert captured[0]["models"] == [PRIMARY, FALLBACK]
    assert client.status()["model"] == PRIMARY
    assert client.status()["routing_models"] == [PRIMARY, FALLBACK]
    assert "unverified_primary_enabled" not in client.status()


def test_exact_http_200_nvidia_error_envelope_is_typed(monkeypatch):
    body = {
        "error": {
            "message": "Upstream error from Nvidia: Service temporarily overloaded",
            "code": 502,
        }
    }
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: FakeResponse(body),
    )
    client = make_client()

    with pytest.raises(OpenRouterProviderError) as exc_info:
        client.generate_json("synthetic prompt")

    assert exc_info.value.status_code == 502
    assert client.last_http_status == 200
    assert client.status()["last_http_status"] == 200
    assert "choices" not in body
    assert "Service temporarily overloaded" in str(exc_info.value)
    assert client.status()["last_error_kind"] == "provider_error"


def test_finish_length_is_typed_before_content_json_parse(monkeypatch):
    body = success_body(PRIMARY)
    body["choices"][0]["finish_reason"] = "length"
    body["choices"][0]["message"]["content"] = "{not valid JSON"
    captured = []

    def fake_urlopen(raw_request, timeout):
        captured.append(json.loads(raw_request.data.decode("utf-8")))
        return FakeResponse(body)

    monkeypatch.setattr("rag.generation.openrouter_client.request.urlopen", fake_urlopen)
    client = make_client()

    with pytest.raises(OpenRouterProviderError, match="finish_reason=length"):
        client.generate_json("synthetic prompt")

    assert captured[0]["models"] == [PRIMARY, FALLBACK]
    assert client.status()["last_error_kind"] == "provider_error"


@pytest.mark.parametrize(
    ("status", "exception_type"),
    [
        (429, OpenRouterRateLimitError),
        (401, OpenRouterAuthError),
        (408, OpenRouterTimeoutError),
        (503, OpenRouterProviderError),
    ],
)
def test_http_error_paths_are_typed(monkeypatch, status, exception_type):
    def fake_urlopen(raw_request, timeout):
        raise error.HTTPError(
            raw_request.full_url,
            status,
            "provider error",
            {},
            BytesIO(json.dumps({"error": {"code": status, "message": "synthetic"}}).encode()),
        )

    monkeypatch.setattr("rag.generation.openrouter_client.request.urlopen", fake_urlopen)
    client = make_client()

    with pytest.raises(exception_type):
        client.generate_json("synthetic prompt")


def test_network_and_timeout_paths_are_typed(monkeypatch):
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: (_ for _ in ()).throw(error.URLError("down")),
    )
    with pytest.raises(OpenRouterNetworkError):
        make_client().generate_json("synthetic prompt")

    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: (_ for _ in ()).throw(TimeoutError("slow")),
    )
    with pytest.raises(OpenRouterTimeoutError):
        make_client().generate_json("synthetic prompt")


def test_retry_after_is_honored_with_bounded_retry(monkeypatch):
    responses = [
        error.HTTPError(
            "https://example.test",
            429,
            "rate limited",
            {"Retry-After": "2"},
            BytesIO(b'{"error":{"code":429,"message":"slow"}}'),
        ),
        FakeResponse(success_body()),
    ]
    sleeps = []

    def fake_urlopen(raw_request, timeout):
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr("rag.generation.openrouter_client.request.urlopen", fake_urlopen)
    client = make_client(max_retries=1, sleep_fn=sleeps.append)

    assert client.generate_json("synthetic prompt") == {"ok": True}
    assert sleeps == [2.0]
    assert client.status()["daily_requests_used"] == 2


def test_free_catalog_accepts_known_free_slug(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: (calls.append(raw_request) or FakeResponse(success_body(FALLBACK))),
    )
    client = make_client(model=FALLBACK, fallback_model="")

    client.generate_json("synthetic prompt")

    assert calls


def test_free_catalog_blocks_paid_slug_before_transport(monkeypatch):
    paid_catalog = {
        "vendor/model:free": {
            "free_variant": True,
            "pricing": {"prompt": "0.000001", "completion": "0"},
        }
    }
    calls = []
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: calls.append(raw_request),
    )
    client = OpenRouterClient(
        api_key=SECRET,
        model="vendor/model:free",
        free_catalog=paid_catalog,
        catalog_loader=lambda: paid_catalog,
    )

    with pytest.raises(OpenRouterConfigError, match="vendor/model:free"):
        client.generate_json("synthetic prompt")
    assert calls == []


def test_free_catalog_blocks_unknown_slug_before_transport(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: calls.append(raw_request),
    )
    client = make_client(model="vendor/unknown:free", fallback_model="")

    with pytest.raises(OpenRouterConfigError, match="vendor/unknown:free"):
        client.generate_json("synthetic prompt")
    assert calls == []


def test_free_guard_override_is_explicit_and_allows_paid_catalog(monkeypatch, caplog):
    paid_catalog = {
        "vendor/model": {
            "free_variant": False,
            "pricing": {"prompt": "0.000001", "completion": "0.000002"},
        }
    }
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: FakeResponse(success_body("vendor/model")),
    )
    with caplog.at_level("WARNING", logger="rag.generation.openrouter"):
        client = OpenRouterClient(
            api_key=SECRET,
            model="vendor/model",
            free_catalog=paid_catalog,
            catalog_loader=lambda: paid_catalog,
            allow_paid_models=True,
        )
    assert client.generate_json("synthetic prompt") == {"ok": True}
    assert "paid-model override enabled" in caplog.text
    assert client.status()["free_guard_override"] is True


def test_every_model_in_models_array_is_guarded(monkeypatch):
    paid_fallback = dict(I2_FREE_MODEL_CATALOG[FALLBACK])
    paid_fallback["pricing"] = {"prompt": "0.000001", "completion": "0"}
    catalog = dict(I2_FREE_MODEL_CATALOG)
    catalog[FALLBACK] = paid_fallback
    calls = []
    monkeypatch.setattr(
        "rag.generation.openrouter_client.request.urlopen",
        lambda raw_request, timeout: calls.append(raw_request),
    )
    client = make_client(catalog=catalog, loader=lambda: catalog)

    with pytest.raises(OpenRouterConfigError, match=FALLBACK):
        client.generate_json("synthetic prompt")
    assert calls == []
