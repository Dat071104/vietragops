"""Single-key Groq API client with typed errors and bounded backoff."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any
from urllib import error, request

logger = logging.getLogger("rag.generation.groq")


class GroqRequestError(RuntimeError):
    """Base for a Groq request that failed after all keys/retries were exhausted."""

    def __init__(
        self,
        message: str,
        *,
        provider_error_body: str | None = None,
        usage: dict[str, int] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_error_body = provider_error_body
        self.usage = usage


class GroqRateLimitError(GroqRequestError):
    """Every attempt hit HTTP 429 (rate limited)."""


class GroqAuthError(GroqRequestError):
    """Every attempt hit HTTP 401 (invalid/expired credentials)."""


class GroqTimeoutError(GroqRequestError):
    """Every attempt timed out."""


class GroqNetworkError(GroqRequestError):
    """Every attempt failed due to a network/connection error (not a timeout)."""


class GroqProviderError(GroqRequestError):
    """Every attempt hit a provider-side HTTP error (e.g. 5xx)."""


def _classify_exhausted_request_error(
    last_exception: Exception,
    attempts: int,
    *,
    provider_error_body: str | None = None,
    usage: dict[str, int] | None = None,
) -> GroqRequestError:
    """Map the last raw exception from an exhausted retry loop to a typed outcome.

    Only reachable with a `urllib.error.HTTPError`, `urllib.error.URLError`, or
    `TimeoutError` -- the only exception types the retry loop's except clauses
    catch before falling through to this final classification.
    """
    message = f"Groq request failed after {attempts} attempts. Last error: {last_exception}"
    if isinstance(last_exception, error.HTTPError):
        if last_exception.code == 429:
            return GroqRateLimitError(message, provider_error_body=provider_error_body, usage=usage)
        if last_exception.code == 401:
            return GroqAuthError(message, provider_error_body=provider_error_body, usage=usage)
        return GroqProviderError(message, provider_error_body=provider_error_body, usage=usage)
    if isinstance(last_exception, TimeoutError):
        return GroqTimeoutError(message, provider_error_body=provider_error_body, usage=usage)
    if isinstance(last_exception, error.URLError):
        reason = last_exception.reason
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).casefold():
            return GroqTimeoutError(message, provider_error_body=provider_error_body, usage=usage)
        return GroqNetworkError(message, provider_error_body=provider_error_body, usage=usage)
    return GroqProviderError(message, provider_error_body=provider_error_body, usage=usage)


def _read_http_error_body(http_err: error.HTTPError) -> str | None:
    try:
        body = http_err.read()
    except (OSError, ValueError):
        return None
    if body is None:
        return None
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    return str(body)


def _extract_usage(body: Any) -> dict[str, int] | None:
    if not isinstance(body, dict) or not isinstance(body.get("usage"), dict):
        return None
    usage = body["usage"]
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    values = {
        "input_tokens_actual": input_tokens,
        "output_tokens_actual": output_tokens,
        "total_tokens_actual": total_tokens,
    }
    normalized = {
        key: int(value)
        for key, value in values.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }
    if "total_tokens_actual" not in normalized and {"input_tokens_actual", "output_tokens_actual"} <= normalized.keys():
        normalized["total_tokens_actual"] = normalized["input_tokens_actual"] + normalized["output_tokens_actual"]
    return normalized or None


class GroqClient:
    """Groq client using exactly one authorized key and no key-pool behavior."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_retries: int | None = None,
        timeout: int | None = None,
        sleep_fn: Any | None = None,
    ) -> None:
        self.model = model or os.environ.get("GROQ_MODEL") or os.environ.get("RAG_MODEL") or "qwen/qwen3.6-27b"
        self.base_url = (base_url or os.environ.get("GROQ_BASE_URL") or "https://api.groq.com/openai/v1").rstrip("/")
        self.endpoint = f"{self.base_url}/chat/completions"
        self.timeout = timeout if timeout is not None else int(os.environ.get("GROQ_REQUEST_TIMEOUT_SECONDS", "120"))
        self.max_retries = max_retries if max_retries is not None else int(os.environ.get("GROQ_MAX_RETRIES", "2"))
        self.jitter_seconds = float(os.environ.get("GROQ_429_JITTER_SECONDS", "1.5"))
        self._key = (api_key if api_key is not None else os.environ.get("GROQ_API_KEY", "")).strip()
        # `_keys` remains as a one-item compatibility view for existing status
        # checks; it is never discovered, rotated, cooled down, or pooled.
        self._keys = [self._key] if self._key else []
        self._lock = threading.Lock()
        self._sleep = sleep_fn or time.sleep
        self.last_usage: dict[str, int] | None = None
        self.last_provider_error_body: str | None = None
        self._requests = 0
        self._failures = 0
        self._429_hits = 0

    @property
    def api_key(self) -> str | None:
        """Return the one configured key for the request path."""
        return self._key or None

    @property
    def key_count(self) -> int:
        return len(self._keys)

    def available(self) -> bool:
        return len(self._keys) > 0

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a structured JSON completion request with one-key backoff."""
        if not self.available():
            raise RuntimeError("GROQ_API_KEY is not set.")

        self.last_usage = None
        self.last_provider_error_body = None

        payload = {
            "model": kwargs.get("model") or self.model,
            "temperature": kwargs.get("temperature", 0.1),
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        attempts = max(1, self.max_retries + 1)
        last_exception: Exception | None = None

        for attempt in range(attempts):
            key = self._key
            try:
                raw_request = request.Request(
                    self.endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "User-Agent": "VietRAGOps-GroqRouter/1.0",
                    },
                    method="POST",
                )
                with request.urlopen(raw_request, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))

                with self._lock:
                    self._requests += 1
                self.last_usage = _extract_usage(body)
                content = body["choices"][0]["message"]["content"]
                return json.loads(content)

            except error.HTTPError as http_err:
                last_exception = http_err
                with self._lock:
                    self._failures += 1
                    if http_err.code == 429:
                        self._429_hits += 1
                provider_error_body = _read_http_error_body(http_err)
                self.last_provider_error_body = provider_error_body
                setattr(http_err, "provider_error_body", provider_error_body)
                if http_err.code == 429:
                    retry_after_header = http_err.headers.get("Retry-After")
                    try:
                        backoff_secs = float(retry_after_header) if retry_after_header else 15.0
                    except (ValueError, TypeError):
                        backoff_secs = 15.0
                    if attempt + 1 < attempts:
                        self._sleep(min(backoff_secs + self.jitter_seconds, 60.0))
                        continue
                elif http_err.code == 401:
                    break
                elif http_err.code in {500, 502, 503, 504}:
                    if attempt + 1 < attempts:
                        self._sleep(min(5.0 + self.jitter_seconds, 60.0))
                        continue
                else:
                    raise http_err

            except (error.URLError, TimeoutError) as net_err:
                last_exception = net_err
                with self._lock:
                    self._failures += 1
                if attempt + 1 < attempts:
                    self._sleep(min(5.0 + self.jitter_seconds, 60.0))
                    continue

            except json.JSONDecodeError as json_err:
                raise RuntimeError(f"Failed to parse model JSON output: {json_err}") from json_err

        if last_exception is None:
            raise GroqRequestError(f"Groq request failed after {attempts} attempts across available keys.")
        raise _classify_exhausted_request_error(
            last_exception,
            attempts,
            provider_error_body=self.last_provider_error_body,
            usage=self.last_usage,
        ) from last_exception

    def stats(self) -> dict[str, Any]:
        """Return aggregate single-key statistics without exposing credentials."""
        with self._lock:
            return {
                "total_keys": len(self._keys),
                "model": self.model,
                "endpoint": self.endpoint,
                "key_configured": self.available(),
                "requests": self._requests,
                "429_hits": self._429_hits,
                "failures": self._failures,
            }

