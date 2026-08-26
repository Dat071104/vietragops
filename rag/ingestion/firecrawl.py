"""Narrow, bounded Firecrawl v2 HTTP adapter.

Deliberately small surface: a bounded search preview (descriptors only, never
an automatic scrape) and a single-URL markdown scrape. No map, crawl,
interact, actions, custom headers/cookies, proxy, OCR, or cloud-parser
arguments are ever sent. The API key is read from the environment at call
time and is never accepted as a parameter, logged, or embedded in an
exception message.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

import httpx


FIRECRAWL_BASE_URL = "https://api.firecrawl.dev"
FIRECRAWL_API_VERSION = "v2"
ADAPTER_VERSION = "vietragops-firecrawl-adapter@1"

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

FirecrawlStatus = Literal[
    "ok",
    "unauthorized",
    "credit_exhausted",
    "rate_limited",
    "timeout",
    "upstream_error",
    "invalid_response",
    "blocked_target",
]


def _read_api_key() -> str | None:
    value = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    return value or None


@dataclass(frozen=True)
class SearchDescriptor:
    title: str
    url: str
    description: str
    source_metadata: dict[str, Any]


@dataclass(frozen=True)
class FirecrawlSearchResult:
    status: FirecrawlStatus
    descriptors: tuple[SearchDescriptor, ...] = ()
    http_status: int | None = None
    retry_after_seconds: float | None = None
    credits_used: int | None = None
    error_code: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True)
class FirecrawlScrapeResult:
    status: FirecrawlStatus
    markdown: str | None = None
    action_id: str | None = None
    http_status: int | None = None
    retry_after_seconds: float | None = None
    credits_used: int | None = None
    error_code: str | None = None
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "ok" and bool(self.markdown)


@dataclass(frozen=True)
class _RawResponse:
    """A successfully read (bounded) 2xx response, parsed as JSON."""

    body: Any
    http_status: int
    credits_used: int | None = None
    malformed_json: bool = False
    truncated: bool = False


@dataclass(frozen=True)
class _ClassifiedFailure:
    """A terminal (non-retryable, or retries-exhausted) failure outcome."""

    status: FirecrawlStatus
    http_status: int | None
    retry_after_seconds: float | None = None
    credits_used: int | None = None
    error_code: str | None = None
    truncated: bool = False


_RequestOutcome = _RawResponse | _ClassifiedFailure


class FirecrawlAdapter:
    """Bounded search/scrape client for the Firecrawl v2 hosted API."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        max_response_bytes: int = 2 * 1024 * 1024,
        max_search_results: int = 5,
        max_retries: int = 2,
        api_key_reader: Callable[[], str | None] = _read_api_key,
        transport: httpx.BaseTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock_fn: Callable[[], float] = time.monotonic,
        base_url: str = FIRECRAWL_BASE_URL,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._max_search_results = max_search_results
        self._max_retries = max(0, min(max_retries, 2))
        self._api_key_reader = api_key_reader
        self._transport = transport
        self._sleep_fn = sleep_fn
        self._clock_fn = clock_fn
        self._base_url = base_url.rstrip("/")

    def __repr__(self) -> str:  # never expose the key via repr/logging
        return "FirecrawlAdapter(...)"

    # -- public API -----------------------------------------------------

    def search_preview(self, query: str, *, limit: int | None = None) -> FirecrawlSearchResult:
        """Return descriptors only. Never scrapes any result automatically."""

        bounded_limit = min(max(1, limit or self._max_search_results), self._max_search_results)
        api_key = self._api_key_reader()
        if not api_key:
            return FirecrawlSearchResult(status="unauthorized", error_code="missing_api_key")

        outcome = self._request(
            "POST", "/search", api_key=api_key, json_body={"query": query, "limit": bounded_limit}
        )
        if isinstance(outcome, _ClassifiedFailure):
            return FirecrawlSearchResult(
                status=outcome.status,
                http_status=outcome.http_status,
                retry_after_seconds=outcome.retry_after_seconds,
                credits_used=outcome.credits_used,
                error_code=outcome.error_code,
            )
        if outcome.malformed_json:
            return FirecrawlSearchResult(
                status="invalid_response",
                http_status=outcome.http_status,
                credits_used=outcome.credits_used,
                error_code="malformed_json",
            )
        descriptors = _parse_search_descriptors(outcome.body)
        if descriptors is None:
            return FirecrawlSearchResult(
                status="invalid_response",
                http_status=outcome.http_status,
                credits_used=outcome.credits_used,
                error_code="malformed_search_response",
            )
        return FirecrawlSearchResult(
            status="ok",
            descriptors=tuple(descriptors[:bounded_limit]),
            http_status=outcome.http_status,
            credits_used=outcome.credits_used,
        )

    def scrape_markdown(self, url: str) -> FirecrawlScrapeResult:
        """Scrape exactly one already-validated URL as bounded markdown only."""

        api_key = self._api_key_reader()
        if not api_key:
            return FirecrawlScrapeResult(status="unauthorized", error_code="missing_api_key")

        payload = {"url": url, "formats": ["markdown"], "onlyMainContent": True}
        outcome = self._request("POST", "/scrape", api_key=api_key, json_body=payload)
        if isinstance(outcome, _ClassifiedFailure):
            return FirecrawlScrapeResult(
                status=outcome.status,
                http_status=outcome.http_status,
                retry_after_seconds=outcome.retry_after_seconds,
                credits_used=outcome.credits_used,
                error_code=outcome.error_code,
                truncated=outcome.truncated,
            )
        if outcome.malformed_json:
            return FirecrawlScrapeResult(
                status="invalid_response",
                http_status=outcome.http_status,
                credits_used=outcome.credits_used,
                error_code="malformed_json",
            )
        parsed = _parse_scrape_body(outcome.body)
        if parsed is None:
            return FirecrawlScrapeResult(
                status="invalid_response",
                http_status=outcome.http_status,
                credits_used=outcome.credits_used,
                error_code="malformed_scrape_response",
            )
        markdown, action_id = parsed
        return FirecrawlScrapeResult(
            status="ok",
            markdown=markdown,
            action_id=action_id,
            http_status=outcome.http_status,
            credits_used=outcome.credits_used,
        )

    # -- transport --------------------------------------------------------

    def _request(self, method: str, path: str, *, api_key: str, json_body: dict[str, Any]) -> _RequestOutcome:
        url = f"{self._base_url}/{FIRECRAWL_API_VERSION}{path}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        attempt = 0
        while True:
            try:
                with httpx.Client(transport=self._transport, timeout=self._timeout_seconds) as client:
                    with client.stream(method, url, headers=headers, json=json_body) as response:
                        result = self._read_response(response)
            except httpx.TimeoutException:
                return _ClassifiedFailure(status="timeout", http_status=None, error_code="request_timeout")
            except httpx.HTTPError:
                return _ClassifiedFailure(status="upstream_error", http_status=None, error_code="transport_error")

            if isinstance(result, _RawResponse):
                return result

            # result is a terminal-or-retryable failure candidate.
            if result.http_status in _RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                attempt += 1
                self._sleep_fn(result.retry_after_seconds or 0.0)
                continue
            return result

    def _read_response(self, response: httpx.Response) -> _RequestOutcome:
        if response.status_code >= 400:
            response.read()
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            return _ClassifiedFailure(
                status=_classify_status(response.status_code),
                http_status=response.status_code,
                retry_after_seconds=retry_after,
                credits_used=_extract_credits(response.headers),
                error_code=f"http_{response.status_code}",
            )

        declared_length = response.headers.get("Content-Length")
        if declared_length is not None:
            try:
                if int(declared_length) > self._max_response_bytes:
                    return _ClassifiedFailure(
                        status="invalid_response",
                        http_status=response.status_code,
                        error_code="response_too_large",
                        truncated=True,
                    )
            except ValueError:
                pass

        buffer = bytearray()
        deadline = self._clock_fn() + self._timeout_seconds
        for chunk in response.iter_bytes():
            if len(buffer) + len(chunk) > self._max_response_bytes:
                return _ClassifiedFailure(
                    status="invalid_response",
                    http_status=response.status_code,
                    error_code="response_too_large",
                    truncated=True,
                )
            buffer.extend(chunk)
            if self._clock_fn() > deadline:
                # A slow-drip body can otherwise stay under the per-chunk
                # I/O timeout indefinitely; enforce a wall-clock deadline
                # across the whole streamed read as well.
                return _ClassifiedFailure(status="timeout", http_status=response.status_code, error_code="stream_deadline_exceeded")

        credits_used = _extract_credits(response.headers)
        try:
            body = json.loads(bytes(buffer).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return _RawResponse(
                body=None, http_status=response.status_code, credits_used=credits_used, malformed_json=True
            )
        return _RawResponse(body=body, http_status=response.status_code, credits_used=credits_used)


def _classify_status(status_code: int) -> FirecrawlStatus:
    if status_code in {401, 403}:
        return "unauthorized"
    if status_code == 402:
        return "credit_exhausted"
    if status_code == 429:
        return "rate_limited"
    if status_code == 408:
        return "timeout"
    if status_code in {500, 502, 503, 504}:
        return "upstream_error"
    if status_code == 400:
        return "blocked_target"
    return "upstream_error"


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    stripped = value.strip()
    try:
        return max(0.0, float(stripped))
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime

        parsed = parsedate_to_datetime(stripped)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = (parsed - datetime.now(timezone.utc)).total_seconds()
    return max(0.0, delta)


def _extract_credits(headers: httpx.Headers) -> int | None:
    for key in ("x-credits-used", "x-firecrawl-credits-used"):
        raw = headers.get(key)
        if raw is None:
            continue
        try:
            return int(raw)
        except ValueError:
            continue
    return None


def _parse_search_descriptors(body: Any) -> list[SearchDescriptor] | None:
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and isinstance(data.get("web"), list):
        items = data["web"]
    else:
        return None

    descriptors: list[SearchDescriptor] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url:
            continue
        title = item.get("title") if isinstance(item.get("title"), str) else ""
        description = item.get("description") if isinstance(item.get("description"), str) else ""
        metadata = {
            key: value
            for key, value in item.items()
            if key not in {"url", "title", "description"} and isinstance(value, (str, int, float, bool))
        }
        descriptors.append(SearchDescriptor(title=title, url=url, description=description, source_metadata=metadata))
    return descriptors


def _parse_scrape_body(body: Any) -> tuple[str, str | None] | None:
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        return None
    markdown = data.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        return None
    action_id = body.get("id") if isinstance(body.get("id"), str) else None
    return markdown, action_id
