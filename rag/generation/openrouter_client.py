"""Single-key OpenRouter client for the explicitly approved free product lane.

The adapter is deliberately independent from Groq, Ollama, and DeepSeek.  It
uses the catalog snapshot observed in Gate 11-OR-I plus a live catalog check
before each completion request, so a model is rejected when its current
catalog pricing is missing, non-zero, or otherwise unverified.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import logging
import os
import threading
import time
from typing import Any
from urllib import error, request


logger = logging.getLogger("rag.generation.openrouter")

I2_CATALOG_SNAPSHOT_UTC = "2026-09-08T08:29:45.883697+00:00"


def _catalog_row(context_length: int, parameters: Sequence[str]) -> dict[str, Any]:
    return {
        "free_variant": True,
        "context_length": context_length,
        "pricing": {"prompt": "0", "completion": "0"},
        "supported_parameters": tuple(parameters),
    }


I2_FREE_MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "cohere/north-mini-code:free": _catalog_row(256000, ("tools",)),
    "dots-studio/dots-3-note-preview:free": _catalog_row(
        512000, ("response_format", "structured_outputs", "tools")
    ),
    "google/gemma-4-26b-a4b-it:free": _catalog_row(262144, ("response_format", "tools")),
    "google/gemma-4-31b-it:free": _catalog_row(262144, ("response_format", "tools")),
    "inclusionai/ling-3.0-flash-fin:free": _catalog_row(262144, ("tools",)),
    "inclusionai/ling-3.0-flash-sante:free": _catalog_row(262144, ("tools",)),
    "liquid/lfm-2.5-2.6b:free": _catalog_row(
        65536, ("response_format", "structured_outputs", "tools")
    ),
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": _catalog_row(
        256000, ("tools",)
    ),
    "nvidia/nemotron-3-super-120b-a12b:free": _catalog_row(
        262144, ("response_format", "structured_outputs", "tools")
    ),
    "nvidia/nemotron-3-ultra-550b-a55b:free": _catalog_row(1000000, ("tools",)),
    "nvidia/nemotron-3.5-content-safety:free": _catalog_row(128000, ()),
    "nvidia/nemotron-3.5-lightning:free": _catalog_row(1000000, ("tools",)),
    "poolside/laguna-s-2.1:free": _catalog_row(262144, ("tools",)),
    "poolside/laguna-xs-2.1:free": _catalog_row(262144, ("tools",)),
    "thinkingmachines/inkling-small:free": _catalog_row(1048576, ("tools",)),
    "thinkingmachines/inkling:free": _catalog_row(1048576, ("tools",)),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _day_key(value: datetime) -> str:
    return value.astimezone(timezone.utc).date().isoformat()


@dataclass(frozen=True)
class _Reservation:
    token: int
    day: str


class DailyRequestLedger:
    """A per-process UTC-day reserve/settle ledger for completion requests."""

    def __init__(self, ceiling: int, *, clock: Callable[[], datetime] | None = None) -> None:
        if ceiling <= 0:
            raise ValueError("The OpenRouter daily request ceiling must be positive.")
        self.ceiling = ceiling
        self._clock = clock or _utc_now
        self._lock = threading.Lock()
        self._day = _day_key(self._clock())
        self._used = 0
        self._reserved = 0
        self._next_token = 1
        self._active: dict[int, _Reservation] = {}

    def _rollover_locked(self) -> None:
        current_day = _day_key(self._clock())
        if current_day != self._day:
            self._day = current_day
            self._used = 0
            self._reserved = 0
            self._active.clear()

    def reserve(self) -> _Reservation:
        with self._lock:
            self._rollover_locked()
            if self._used + self._reserved >= self.ceiling:
                raise OpenRouterRateLimitError(
                    f"OpenRouter daily request ceiling reached for UTC day {self._day}.",
                    status_code=429,
                    local_budget=True,
                )
            reservation = _Reservation(self._next_token, self._day)
            self._next_token += 1
            self._active[reservation.token] = reservation
            self._reserved += 1
            return reservation

    def settle(self, reservation: _Reservation, *, consumed: bool) -> None:
        with self._lock:
            self._rollover_locked()
            active = self._active.pop(reservation.token, None)
            if active is None:
                return
            self._reserved = max(0, self._reserved - 1)
            if consumed and active.day == self._day:
                self._used += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._rollover_locked()
            return {
                "utc_day": self._day,
                "ceiling": self.ceiling,
                "used": self._used,
                "reserved": self._reserved,
                "remaining": max(0, self.ceiling - self._used - self._reserved),
            }


class OpenRouterRequestError(RuntimeError):
    """Base for an OpenRouter request that failed after the guard ran."""

    failure_kind = "provider_error"

    def __init__(
        self,
        message: str,
        *,
        provider_error_body: str | None = None,
        usage: dict[str, int] | None = None,
        status_code: int | None = None,
        retry_after: float | None = None,
        served_provider: str | None = None,
        served_model: str | None = None,
        local_budget: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider_error_body = provider_error_body
        self.usage = usage
        self.status_code = status_code
        self.retry_after = retry_after
        self.served_provider = served_provider
        self.served_model = served_model
        self.local_budget = local_budget


class OpenRouterRateLimitError(OpenRouterRequestError):
    failure_kind = "rate_limited"


class OpenRouterAuthError(OpenRouterRequestError):
    failure_kind = "auth_failure"


class OpenRouterTimeoutError(OpenRouterRequestError):
    failure_kind = "timeout"


class OpenRouterNetworkError(OpenRouterRequestError):
    failure_kind = "network_failure"


class OpenRouterProviderError(OpenRouterRequestError):
    failure_kind = "provider_error"


class OpenRouterConfigError(OpenRouterRequestError):
    failure_kind = "config_error"


def _redact_text(value: Any, secret: str | None) -> str:
    text = str(value)
    if secret:
        text = text.replace(secret, "<redacted>")
    return text


def _extract_usage(body: Any) -> dict[str, int] | None:
    if not isinstance(body, dict) or not isinstance(body.get("usage"), dict):
        return None
    usage = body["usage"]
    details = usage.get("completion_tokens_details")
    values = {
        "input_tokens_actual": usage.get("prompt_tokens", usage.get("input_tokens")),
        "output_tokens_actual": usage.get("completion_tokens", usage.get("output_tokens")),
        "total_tokens_actual": usage.get("total_tokens"),
        "reasoning_tokens_actual": details.get("reasoning_tokens") if isinstance(details, dict) else None,
    }
    normalized = {
        key: int(value)
        for key, value in values.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }
    if "total_tokens_actual" not in normalized and {
        "input_tokens_actual",
        "output_tokens_actual",
    } <= normalized.keys():
        normalized["total_tokens_actual"] = normalized["input_tokens_actual"] + normalized["output_tokens_actual"]
    return normalized or None


def _parse_retry_after(value: str | None, *, now: datetime | None = None) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
        return seconds if seconds >= 0 else None
    except (TypeError, ValueError):
        pass
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        current = now or _utc_now()
        return max(0.0, (parsed - current).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def _normalize_catalog(catalog: Any) -> dict[str, dict[str, Any]]:
    if isinstance(catalog, Mapping) and isinstance(catalog.get("data"), list):
        catalog = catalog["data"]
    if isinstance(catalog, Mapping):
        rows = []
        for model_id, entry in catalog.items():
            if isinstance(entry, Mapping):
                row = dict(entry)
                row.setdefault("id", model_id)
                rows.append(row)
    elif isinstance(catalog, Sequence) and not isinstance(catalog, (str, bytes, bytearray)):
        rows = [dict(entry) for entry in catalog if isinstance(entry, Mapping)]
    else:
        rows = []
    return {str(row["id"]): row for row in rows if row.get("id")}


def _is_zero_price(value: Any) -> bool:
    return value == 0 or str(value) == "0"


def _catalog_entry_is_free(model: str, entry: Mapping[str, Any] | None) -> bool:
    if not isinstance(entry, Mapping):
        return False
    if entry.get("free_variant") is False:
        return False
    pricing = entry.get("pricing")
    if not isinstance(pricing, Mapping):
        return False
    if not _is_zero_price(pricing.get("prompt")) or not _is_zero_price(pricing.get("completion")):
        return False
    for key, value in pricing.items():
        if key != "overrides" and not _is_zero_price(value):
            return False
    return bool(entry.get("free_variant", model.endswith(":free")))


def _classify_exhausted_request_error(exc: Exception, attempts: int) -> OpenRouterRequestError:
    if isinstance(exc, OpenRouterRequestError):
        return exc
    message = f"OpenRouter request failed after {attempts} attempts: {exc}"
    if isinstance(exc, error.HTTPError):
        if exc.code == 429:
            return OpenRouterRateLimitError(message, status_code=exc.code)
        if exc.code in {401, 403}:
            return OpenRouterAuthError(message, status_code=exc.code)
        return OpenRouterProviderError(message, status_code=exc.code)
    if isinstance(exc, TimeoutError):
        return OpenRouterTimeoutError(message)
    if isinstance(exc, error.URLError):
        reason = exc.reason
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).casefold():
            return OpenRouterTimeoutError(message)
        return OpenRouterNetworkError(message)
    return OpenRouterProviderError(message)


class OpenRouterClient:
    """Single-key, catalog-guarded OpenRouter chat-completions client."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        base_url: str | None = None,
        catalog_url: str | None = None,
        timeout: float | None = None,
        max_requests_per_day: int | None = None,
        max_retries: int | None = None,
        max_backoff_seconds: float | None = None,
        allow_paid_models: bool | None = None,
        http_referer: str | None = None,
        x_title: str | None = None,
        free_catalog: Mapping[str, Mapping[str, Any]] | None = None,
        catalog_loader: Callable[[], Any] | None = None,
        clock: Callable[[], datetime] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        ledger: DailyRequestLedger | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.model = model if model is not None else os.environ.get("OPENROUTER_MODEL", "").strip()
        self.fallback_model = (
            fallback_model
            if fallback_model is not None
            else os.environ.get("OPENROUTER_MODEL_FALLBACK", "").strip()
        )
        self.base_url = (base_url or os.environ.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")
        self.endpoint = f"{self.base_url}/chat/completions"
        self.catalog_url = catalog_url or os.environ.get("OPENROUTER_CATALOG_URL") or "https://openrouter.ai/api/v1/models"
        self.timeout = timeout if timeout is not None else float(os.environ.get("OPENROUTER_REQUEST_TIMEOUT_SECONDS", "90"))
        self.max_retries = max_retries if max_retries is not None else int(os.environ.get("OPENROUTER_MAX_RETRIES", "1"))
        self.max_backoff_seconds = (
            max_backoff_seconds
            if max_backoff_seconds is not None
            else float(os.environ.get("OPENROUTER_MAX_BACKOFF_SECONDS", "60"))
        )
        self.allow_paid_models = (
            allow_paid_models
            if allow_paid_models is not None
            else os.environ.get("OPENROUTER_ALLOW_PAID_MODELS", "").strip().casefold() in {"1", "true", "yes", "on"}
        )
        self.http_referer = http_referer if http_referer is not None else os.environ.get("OPENROUTER_HTTP_REFERER", "").strip()
        self.x_title = x_title if x_title is not None else os.environ.get("OPENROUTER_X_TITLE", "").strip()
        self._catalog_snapshot = _normalize_catalog(
            free_catalog if free_catalog is not None else I2_FREE_MODEL_CATALOG
        )
        self._catalog_loader = catalog_loader or self._fetch_live_catalog
        self._sleep = sleep_fn or time.sleep
        self.ledger = ledger or DailyRequestLedger(
            max_requests_per_day
            if max_requests_per_day is not None
            else int(os.environ.get("OPENROUTER_MAX_REQUESTS_PER_DAY", "1000")),
            clock=clock,
        )
        self.last_usage: dict[str, int] | None = None
        self.last_provider_error_body: str | None = None
        self.last_http_status: int | None = None
        self.last_served_model: str | None = None
        self.last_served_provider: str | None = None
        self.last_error_kind: str | None = None
        if self.allow_paid_models:
            logger.warning("OpenRouter paid-model override enabled; free catalog guard is bypassed.")

    def available(self) -> bool:
        return bool(self.api_key)

    def _model_chain(self, requested_model: str | None = None) -> list[str]:
        primary = (requested_model or self.model).strip()
        chain = [primary] if primary else []
        if self.fallback_model and self.fallback_model not in chain:
            chain.append(self.fallback_model)
        return chain

    @property
    def effective_model(self) -> str:
        try:
            chain = self._model_chain()
        except OpenRouterConfigError:
            return self.model
        return chain[0] if chain else self.model

    def _validate_catalog(self, model_chain: Sequence[str], catalog: Mapping[str, Mapping[str, Any]], source: str) -> None:
        if self.allow_paid_models:
            return
        for model in model_chain:
            entry = catalog.get(model)
            if not _catalog_entry_is_free(model, entry):
                raise OpenRouterConfigError(
                    f"OpenRouter model '{model}' is not confirmed as a zero-priced free variant by the {source} catalog."
                )

    def _fetch_live_catalog(self) -> dict[str, dict[str, Any]]:
        raw_request = request.Request(self.catalog_url, headers={"Accept": "application/json"}, method="GET")
        try:
            with request.urlopen(raw_request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise OpenRouterConfigError(f"OpenRouter free catalog lookup failed: HTTP {exc.code}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise OpenRouterConfigError(f"OpenRouter free catalog lookup failed: {_redact_text(exc, self.api_key)}") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise OpenRouterConfigError("OpenRouter free catalog lookup returned invalid JSON.") from exc
        return _normalize_catalog(body)

    def _guard_before_completion(self, model_chain: Sequence[str]) -> None:
        if not model_chain:
            raise OpenRouterConfigError("OPENROUTER_MODEL is not configured.")
        self._validate_catalog(model_chain, self._catalog_snapshot, "frozen I2")
        if self.allow_paid_models:
            return
        live_catalog = _normalize_catalog(self._catalog_loader())
        self._validate_catalog(model_chain, live_catalog, "live")

    def _headers(self) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            headers["X-Title"] = self.x_title
        return headers

    def _retry_delay(self, attempt: int, retry_after: float | None) -> float:
        if retry_after is not None:
            return min(max(0.0, retry_after), self.max_backoff_seconds)
        return min(float(2**attempt), self.max_backoff_seconds)

    def _error_from_body(
        self,
        body: Mapping[str, Any],
        *,
        status_code: int,
        retry_after: float | None = None,
    ) -> OpenRouterRequestError:
        error_payload = body.get("error") if isinstance(body, Mapping) else None
        error_payload = error_payload if isinstance(error_payload, Mapping) else {}
        code = error_payload.get("code", status_code)
        metadata = error_payload.get("metadata") if isinstance(error_payload.get("metadata"), Mapping) else {}
        error_type = str(metadata.get("error_type", "")).casefold()
        message = _redact_text(error_payload.get("message", f"HTTP {status_code}"), self.api_key)
        body_text = _redact_text(json.dumps(error_payload, ensure_ascii=False, sort_keys=True), self.api_key)
        usage = _extract_usage(body)
        served_provider = body.get("provider") if isinstance(body.get("provider"), str) else metadata.get("provider_name")
        served_model = body.get("model") if isinstance(body.get("model"), str) else None
        if retry_after is None:
            candidate = metadata.get("retry_after_seconds")
            retry_after = float(candidate) if isinstance(candidate, (int, float)) and candidate >= 0 else None
        try:
            numeric_code = int(code)
        except (TypeError, ValueError):
            numeric_code = status_code
        if numeric_code == 429 or error_type in {"rate_limit_exceeded", "provider_overloaded"}:
            cls: type[OpenRouterRequestError] = OpenRouterRateLimitError
        elif numeric_code in {401, 403} or error_type in {"authentication", "permission_denied"}:
            cls = OpenRouterAuthError
        elif numeric_code == 408 or error_type == "timeout":
            cls = OpenRouterTimeoutError
        elif numeric_code >= 500 or error_type in {"provider_unavailable", "server", "unmapped"}:
            cls = OpenRouterProviderError
        else:
            cls = OpenRouterProviderError
        return cls(
            f"OpenRouter request failed: {message}",
            provider_error_body=body_text,
            usage=usage,
            status_code=numeric_code,
            retry_after=retry_after,
            served_provider=str(served_provider) if served_provider else None,
            served_model=served_model,
        )

    def _record_response(self, body: Mapping[str, Any], status_code: int) -> None:
        self.last_http_status = status_code
        self.last_usage = _extract_usage(body)
        self.last_served_model = body.get("model") if isinstance(body.get("model"), str) else None
        self.last_served_provider = body.get("provider") if isinstance(body.get("provider"), str) else None
        self.last_provider_error_body = None
        self.last_error_kind = None

    def _log_request(self, *, status_code: int | None, error_kind: str | None, remaining: int) -> None:
        logger.info(
            "OpenRouter request requested_model=%s served_model=%s served_upstream=%s http_status=%s usage=%s error_kind=%s remaining=%s",
            self.model,
            self.last_served_model,
            self.last_served_provider,
            status_code,
            self.last_usage,
            error_kind,
            remaining,
        )

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Generate JSON after the free catalog guard and daily reservation."""
        if not self.available():
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        model_chain = self._model_chain(kwargs.get("model"))
        self._guard_before_completion(model_chain)
        self.last_usage = None
        self.last_provider_error_body = None
        self.last_http_status = None
        self.last_served_model = None
        self.last_served_provider = None
        self.last_error_kind = None
        payload: dict[str, Any] = {
            "models": model_chain,
            "temperature": kwargs.get("temperature", 0.1),
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        attempts = max(1, self.max_retries + 1)
        last_exception: Exception | None = None
        for attempt in range(attempts):
            reservation = self.ledger.reserve()
            dispatched = False
            try:
                raw_request = request.Request(
                    self.endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=self._headers(),
                    method="POST",
                )
                dispatched = True
                with request.urlopen(raw_request, timeout=self.timeout) as response:
                    status_code = response.status
                    raw_body = response.read().decode("utf-8")
                self.ledger.settle(reservation, consumed=True)
                body = json.loads(raw_body)
                if not isinstance(body, Mapping):
                    raise OpenRouterProviderError(
                        "OpenRouter response body was not a JSON object.",
                        status_code=status_code,
                    )
                self._record_response(body, status_code)
                if isinstance(body.get("error"), Mapping):
                    raise self._error_from_body(body, status_code=status_code)
                choices = body.get("choices") if isinstance(body, Mapping) else None
                choice = choices[0] if isinstance(choices, list) and choices else None
                if not isinstance(choice, Mapping):
                    raise OpenRouterProviderError(
                        "OpenRouter response did not contain a choice.",
                        usage=self.last_usage,
                        status_code=status_code,
                        served_provider=self.last_served_provider,
                        served_model=self.last_served_model,
                    )
                if choice.get("finish_reason") == "length":
                    raise OpenRouterProviderError(
                        "OpenRouter response was truncated (finish_reason=length); refusing to parse incomplete JSON.",
                        usage=self.last_usage,
                        status_code=status_code,
                        served_provider=self.last_served_provider,
                        served_model=self.last_served_model,
                    )
                message = choice.get("message")
                content = message.get("content") if isinstance(message, Mapping) else None
                if not isinstance(content, str):
                    raise OpenRouterProviderError(
                        "OpenRouter response did not contain a textual JSON content field.",
                        usage=self.last_usage,
                        status_code=status_code,
                        served_provider=self.last_served_provider,
                        served_model=self.last_served_model,
                    )
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise OpenRouterProviderError(
                        "OpenRouter response JSON content was not an object.",
                        usage=self.last_usage,
                        status_code=status_code,
                        served_provider=self.last_served_provider,
                        served_model=self.last_served_model,
                    )
                self._log_request(status_code=status_code, error_kind=None, remaining=self.ledger.snapshot()["remaining"])
                return parsed
            except error.HTTPError as exc:
                if dispatched:
                    self.ledger.settle(reservation, consumed=True)
                else:
                    self.ledger.settle(reservation, consumed=False)
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    body = json.loads(raw)
                except (TypeError, ValueError, json.JSONDecodeError):
                    body = {"error": {"code": exc.code, "message": "non-JSON HTTP error body"}}
                retry_after = _parse_retry_after(exc.headers.get("Retry-After"))
                current = self._error_from_body(body, status_code=exc.code, retry_after=retry_after)
                self.last_http_status = exc.code
                self.last_provider_error_body = current.provider_error_body
                self.last_error_kind = current.failure_kind
                self.last_usage = current.usage
                last_exception = current
                if attempt + 1 < attempts and current.failure_kind in {"rate_limited", "timeout", "provider_error", "network_failure"}:
                    self._sleep(self._retry_delay(attempt, current.retry_after))
                    continue
                self._log_request(status_code=exc.code, error_kind=current.failure_kind, remaining=self.ledger.snapshot()["remaining"])
                raise current from exc
            except (error.URLError, TimeoutError) as exc:
                self.ledger.settle(reservation, consumed=True)
                current = _classify_exhausted_request_error(exc, attempts)
                self.last_error_kind = current.failure_kind
                last_exception = current
                if attempt + 1 < attempts:
                    self._sleep(self._retry_delay(attempt, None))
                    continue
                self._log_request(status_code=None, error_kind=current.failure_kind, remaining=self.ledger.snapshot()["remaining"])
                raise current from exc
            except (json.JSONDecodeError, OpenRouterRequestError) as exc:
                if isinstance(exc, OpenRouterRequestError):
                    current = exc
                else:
                    current = OpenRouterProviderError(
                        "OpenRouter returned invalid JSON.",
                        usage=self.last_usage,
                        status_code=self.last_http_status,
                        served_provider=self.last_served_provider,
                        served_model=self.last_served_model,
                    )
                self.last_error_kind = current.failure_kind
                self.last_provider_error_body = current.provider_error_body
                last_exception = current
                if attempt + 1 < attempts and current.failure_kind in {"rate_limited", "timeout", "provider_error", "network_failure"}:
                    self._sleep(self._retry_delay(attempt, current.retry_after))
                    continue
                self._log_request(
                    status_code=self.last_http_status,
                    error_kind=current.failure_kind,
                    remaining=self.ledger.snapshot()["remaining"],
                )
                raise current
        raise _classify_exhausted_request_error(last_exception or RuntimeError("unknown"), attempts)

    def status(self) -> dict[str, Any]:
        ledger = self.ledger.snapshot()
        try:
            routing_models = self._model_chain()
        except OpenRouterConfigError:
            routing_models = []
        return {
            "provider": "openrouter",
            "model": self.effective_model,
            "configured_model": self.model,
            "fallback_model": self.fallback_model,
            "routing_models": routing_models,
            "available": self.available(),
            "daily_request_ceiling": ledger["ceiling"],
            "daily_requests_used": ledger["used"],
            "daily_requests_remaining": ledger["remaining"],
            "daily_ledger_utc_day": ledger["utc_day"],
            "free_guard_override": self.allow_paid_models,
            "catalog_snapshot_utc": I2_CATALOG_SNAPSHOT_UTC,
            "last_http_status": self.last_http_status,
            "last_served_model": self.last_served_model,
            "last_served_provider": self.last_served_provider,
            "last_error_kind": self.last_error_kind,
        }


__all__ = [
    "DailyRequestLedger",
    "I2_CATALOG_SNAPSHOT_UTC",
    "I2_FREE_MODEL_CATALOG",
    "OpenRouterAuthError",
    "OpenRouterClient",
    "OpenRouterConfigError",
    "OpenRouterNetworkError",
    "OpenRouterProviderError",
    "OpenRouterRateLimitError",
    "OpenRouterRequestError",
    "OpenRouterTimeoutError",
    "_classify_exhausted_request_error",
]
