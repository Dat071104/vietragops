"""Small Ollama client for local chat, JSON output, and tool-calling demos."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import httpx


class OllamaClientError(RuntimeError):
    """Raised when the local Ollama API cannot be used successfully."""


@dataclass(frozen=True)
class OllamaStatus:
    available: bool
    model_available: bool
    models: list[str]
    base_url: str
    model: str
    error: str | None = None


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:3b",
        num_ctx: int = 8192,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.num_ctx = num_ctx
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: str | dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_ctx": self.num_ctx,
            },
        }
        if tools:
            payload["tools"] = tools
        if response_format is not None:
            payload["format"] = response_format
        if options:
            payload["options"].update(options)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise OllamaClientError(f"Ollama chat request failed: {exc}") from exc

    def generate_json(self, prompt: str) -> dict[str, Any]:
        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            response_format="json",
        )
        content = response.get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaClientError("Ollama returned non-JSON content for a structured response.") from exc

    def list_models(self) -> list[str]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise OllamaClientError(f"Ollama tags request failed: {exc}") from exc
        models = payload.get("models") or []
        names = [item.get("name", "") for item in models if item.get("name")]
        return sorted(names)

    def status(self) -> OllamaStatus:
        try:
            models = self.list_models()
        except OllamaClientError as exc:
            return OllamaStatus(
                available=False,
                model_available=False,
                models=[],
                base_url=self.base_url,
                model=self.model,
                error=str(exc),
            )
        return OllamaStatus(
            available=True,
            model_available=self.model in models,
            models=models,
            base_url=self.base_url,
            model=self.model,
        )
