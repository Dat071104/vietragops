from __future__ import annotations

import json

import httpx
import pytest

from rag.ingestion.firecrawl import FirecrawlAdapter


def _fake_key() -> str:
    return "test-key-not-real"


def _adapter(handler, **kwargs) -> FirecrawlAdapter:
    transport = httpx.MockTransport(handler)
    return FirecrawlAdapter(
        transport=transport,
        api_key_reader=_fake_key,
        sleep_fn=lambda _seconds: None,
        **kwargs,
    )


def test_scrape_uses_expected_endpoint_method_and_bearer_header_without_asserting_real_key():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"markdown": "# Title\n\nBody text."}, "id": "job-1"})

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/policy")

    assert result.ok
    assert result.markdown == "# Title\n\nBody text."
    assert result.action_id == "job-1"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.firecrawl.dev/v2/scrape"
    assert captured["authorization"] == "Bearer test-key-not-real"
    assert captured["authorization"] != "Bearer "
    assert captured["body"] == {"url": "https://example.gov.vn/policy", "formats": ["markdown"], "onlyMainContent": True}


def test_search_preview_returns_descriptors_only_and_never_scrapes():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.firecrawl.dev/v2/search"
        return httpx.Response(
            200,
            json={
                "data": {
                    "web": [
                        {"title": "Policy A", "url": "https://example.gov.vn/a", "description": "desc a"},
                        {"title": "Policy B", "url": "https://example.gov.vn/b", "description": "desc b"},
                    ]
                }
            },
        )

    adapter = _adapter(handler)
    result = adapter.search_preview("education policy", limit=5)

    assert result.ok
    assert len(result.descriptors) == 2
    assert result.descriptors[0].url == "https://example.gov.vn/a"
    assert result.descriptors[0].title == "Policy A"
    assert not hasattr(result.descriptors[0], "markdown")


def test_search_preview_limit_is_bounded_by_adapter_max():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["limit"] == 3  # adapter max, even though caller asked for 100
        return httpx.Response(200, json={"data": {"web": []}})

    adapter = _adapter(handler, max_search_results=3)
    adapter.search_preview("q", limit=100)


def test_missing_api_key_returns_unauthorized_without_network_call():
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, json={"data": {"web": []}})

    adapter = FirecrawlAdapter(
        transport=httpx.MockTransport(handler),
        api_key_reader=lambda: None,
        sleep_fn=lambda _s: None,
    )
    result = adapter.search_preview("q")

    assert result.status == "unauthorized"
    assert result.error_code == "missing_api_key"
    assert called["count"] == 0


def test_timeout_is_classified_and_not_retried():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        raise httpx.ReadTimeout("timed out", request=request)

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "timeout"
    assert attempts["count"] == 1


def test_429_retries_with_retry_after_then_succeeds():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "rate_limited"})
        return httpx.Response(200, json={"data": {"markdown": "ok content"}})

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.ok
    assert attempts["count"] == 2


def test_429_exhausts_retries_and_reports_rate_limited():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(429, headers={"Retry-After": "2"}, json={"error": "rate_limited"})

    adapter = _adapter(handler, max_retries=2)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "rate_limited"
    assert result.retry_after_seconds == 2.0
    assert attempts["count"] == 3  # first attempt + 2 retries


def test_402_credit_exhaustion_is_not_retried():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(402, json={"error": "insufficient credits"})

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "credit_exhausted"
    assert attempts["count"] == 1


def test_401_unauthorized_is_not_retried():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(401, json={"error": "invalid api key"})

    adapter = _adapter(handler)
    result = adapter.search_preview("q")

    assert result.status == "unauthorized"
    assert attempts["count"] == 1


def test_malformed_response_is_invalid_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json at all")

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "invalid_response"
    assert result.error_code == "malformed_json"


def test_response_missing_expected_fields_is_invalid_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"not_markdown": "x"}})

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "invalid_response"
    assert result.error_code == "malformed_scrape_response"


def test_response_over_byte_budget_is_rejected():
    big_markdown = "x" * 5000

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"markdown": big_markdown}})

    adapter = _adapter(handler, max_response_bytes=100)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "invalid_response"
    assert result.error_code == "response_too_large"
    assert result.truncated is True


def test_500_upstream_error_retries_then_reports_upstream_error():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(500, json={"error": "internal"})

    adapter = _adapter(handler, max_retries=1)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "upstream_error"
    assert attempts["count"] == 2  # first attempt + 1 retry


def test_exception_message_never_contains_api_key():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    adapter = _adapter(handler)
    result = adapter.scrape_markdown("https://example.gov.vn/x")

    assert result.status == "upstream_error"
    assert "test-key-not-real" not in repr(result)
    assert "test-key-not-real" not in repr(adapter)
