"""Minimal, isolated DeepSeek API client.

Optional external research baseline only (Gate 05). Never wired as a silent
rescue path for Groq or any other provider -- `ProviderRouter` only calls
this when `provider="deepseek"` is explicitly selected.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class DeepSeekRequestError(RuntimeError):
    """Raised when a DeepSeek request fails."""


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = (base_url or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/")
        self.endpoint = f"{self.base_url}/chat/completions"
        self.timeout = timeout or int(os.environ.get("DEEPSEEK_REQUEST_TIMEOUT_SECONDS", "60"))

    def available(self) -> bool:
        return bool(self.api_key)

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if not self.available():
            raise RuntimeError("DEEPSEEK_API_KEY is not set.")
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        raw_request = request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(raw_request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise DeepSeekRequestError(f"DeepSeek request failed: HTTP {exc.code}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise DeepSeekRequestError(f"DeepSeek request failed: {exc}") from exc
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
