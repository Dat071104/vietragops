"""Multi-Account Groq API Client with Round-Robin Rotation and 429 Cooldown."""

from __future__ import annotations

import json
import logging
import os
import random
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
    message = f"Groq request failed after {attempts} attempts across available keys. Last error: {last_exception}"
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


def redact_api_key(key: str | None) -> str:
    """Mask API key for safe logging."""
    if not key:
        return "<none>"
    stripped = key.strip()
    if len(stripped) <= 8:
        return "****"
    return f"{stripped[:4]}...{stripped[-4:]}"


class GroqClient:
    """Groq API client supporting multi-key rotation, 429 backoff/cooldown, and single-key fallback."""

    def __init__(
        self,
        api_keys: list[str] | None = None,
        model: str | None = None,
        base_url: str | None = None,
        strategy: str | None = None,
        max_retries: int | None = None,
        timeout: int | None = None,
    ) -> None:
        self.model = model or os.environ.get("GROQ_MODEL") or os.environ.get("RAG_MODEL") or "qwen/qwen3.6-27b"
        self.base_url = (base_url or os.environ.get("GROQ_BASE_URL") or "https://api.groq.com/openai/v1").rstrip("/")
        self.endpoint = f"{self.base_url}/chat/completions"
        self.strategy = (strategy or os.environ.get("GROQ_ROUTER_STRATEGY") or "round_robin_cooldown").casefold()

        # Timeout & retry policies
        self.timeout = timeout or int(os.environ.get("GROQ_REQUEST_TIMEOUT_SECONDS", "120"))
        self.max_retries = max_retries if max_retries is not None else int(os.environ.get("GROQ_MAX_RETRIES", "2"))
        self.jitter_seconds = float(os.environ.get("GROQ_429_JITTER_SECONDS", "1.5"))

        # Discover API keys
        if api_keys is not None:
            self._keys = [k.strip() for k in api_keys if k and k.strip()]
        else:
            self._keys = self._discover_keys()

        self._lock = threading.Lock()
        self._key_index = 0
        self._cooldown_until: dict[str, float] = {k: 0.0 for k in self._keys}
        self.last_usage: dict[str, int] | None = None
        self.last_provider_error_body: str | None = None
        self._key_stats: dict[str, dict[str, int]] = {
            k: {"requests": 0, "failures": 0, "429_hits": 0} for k in self._keys
        }

    @property
    def api_key(self) -> str | None:
        """Backward compatibility: returns current primary key or first discovered key."""
        if not self._keys:
            return None
        with self._lock:
            idx = self._key_index % len(self._keys)
            return self._keys[idx]

    @property
    def key_count(self) -> int:
        return len(self._keys)

    def _discover_keys(self) -> list[str]:
        # Cloud releases are explicitly single-key.  The legacy indexed-key
        # path remains available only for local compatibility tests and is
        # never activated by the Gate 09R cloud configuration.
        if os.environ.get("PROVIDER_MODE", "").strip().casefold() == "cloud":
            legacy_key = os.environ.get("GROQ_API_KEY", "").strip()
            return [legacy_key] if legacy_key else []
        keys: list[str] = []
        max_count = int(os.environ.get("GROQ_KEY_COUNT", "20"))

        # 1. Scan GROQ_API_KEY_1 .. GROQ_API_KEY_N
        for i in range(1, max_count + 1):
            val = os.environ.get(f"GROQ_API_KEY_{i}", "").strip()
            if val and val not in keys:
                keys.append(val)

        # 2. Check single legacy / fallback key
        legacy_key = os.environ.get("GROQ_API_KEY", "").strip()
        if legacy_key and legacy_key not in keys:
            keys.append(legacy_key)

        return keys

    def available(self) -> bool:
        return len(self._keys) > 0

    def _get_next_key(self) -> tuple[str, int]:
        """Select next active key skipping those currently in cooldown."""
        with self._lock:
            if not self._keys:
                raise RuntimeError("No Groq API keys configured.")

            now = time.time()
            total = len(self._keys)

            # Look for an available key starting from current index
            for offset in range(total):
                idx = (self._key_index + offset) % total
                candidate_key = self._keys[idx]
                if now >= self._cooldown_until.get(candidate_key, 0.0):
                    self._key_index = (idx + 1) % total
                    return candidate_key, idx

            # If all keys are cooling down, pick the one that expires soonest
            best_idx = 0
            earliest_expiry = float("inf")
            for idx, k in enumerate(self._keys):
                exp = self._cooldown_until.get(k, 0.0)
                if exp < earliest_expiry:
                    earliest_expiry = exp
                    best_idx = idx

            self._key_index = (best_idx + 1) % total
            return self._keys[best_idx], best_idx

    def _mark_cooldown(self, key: str, duration: float, reason: str = "429") -> None:
        with self._lock:
            jitter = random.uniform(0.1, self.jitter_seconds)
            until = time.time() + duration + jitter
            self._cooldown_until[key] = max(self._cooldown_until.get(key, 0.0), until)
            if key in self._key_stats:
                if reason == "429":
                    self._key_stats[key]["429_hits"] += 1
                self._key_stats[key]["failures"] += 1
            logger.warning(
                "Groq key %s put in cooldown for %.1fs (reason: %s)",
                redact_api_key(key),
                duration + jitter,
                reason,
            )

    def _record_success(self, key: str) -> None:
        with self._lock:
            if key in self._key_stats:
                self._key_stats[key]["requests"] += 1

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a structured JSON completion request with key rotation and retry on 429."""
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
            key, key_idx = self._get_next_key()
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

                self._record_success(key)
                self.last_usage = _extract_usage(body)
                content = body["choices"][0]["message"]["content"]
                return json.loads(content)

            except error.HTTPError as http_err:
                last_exception = http_err
                provider_error_body = _read_http_error_body(http_err)
                self.last_provider_error_body = provider_error_body
                setattr(http_err, "provider_error_body", provider_error_body)
                if http_err.code == 429:
                    retry_after_header = http_err.headers.get("Retry-After")
                    try:
                        cooldown_secs = float(retry_after_header) if retry_after_header else 15.0
                    except (ValueError, TypeError):
                        cooldown_secs = 15.0
                    self._mark_cooldown(key, cooldown_secs, reason="429 RateLimit")
                    continue
                elif http_err.code == 401:
                    self._mark_cooldown(key, 3600.0, reason="401 Unauthorized")
                    continue
                elif http_err.code in {500, 502, 503, 504}:
                    self._mark_cooldown(key, 5.0, reason=f"{http_err.code} ServerError")
                    continue
                else:
                    raise http_err

            except (error.URLError, TimeoutError) as net_err:
                last_exception = net_err
                self._mark_cooldown(key, 5.0, reason="Network/Timeout")
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
        """Return operational statistics for key rotation monitoring."""
        with self._lock:
            now = time.time()
            return {
                "total_keys": len(self._keys),
                "model": self.model,
                "endpoint": self.endpoint,
                "strategy": self.strategy,
                "keys_status": [
                    {
                        "index": idx + 1,
                        "key_redacted": redact_api_key(k),
                        "in_cooldown": now < self._cooldown_until.get(k, 0.0),
                        "cooldown_remaining_sec": max(0.0, round(self._cooldown_until.get(k, 0.0) - now, 1)),
                        "requests": self._key_stats[k]["requests"],
                        "429_hits": self._key_stats[k]["429_hits"],
                        "failures": self._key_stats[k]["failures"],
                    }
                    for idx, k in enumerate(self._keys)
                ],
            }

