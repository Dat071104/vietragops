"""Minimal Groq API client using only environment variables."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import request


class GroqClient:
    def __init__(self) -> None:
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def available(self) -> bool:
        return bool(self.api_key)

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if not self.available():
            raise RuntimeError("GROQ_API_KEY is not set.")
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
        with request.urlopen(raw_request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
