"""Small API client with optional Cloud Run service-to-service auth."""

from __future__ import annotations

import os
from typing import Any

import requests


class ApiClientConfigurationError(RuntimeError):
    """Raised when cloud API authentication is configured unsafely."""


class ApiClient:
    def __init__(self, base_url: str, *, auth_mode: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        configured_mode = (auth_mode or os.environ.get("VIETRAGOPS_API_AUTH_MODE", "none")).strip().casefold()
        self.auth_mode = configured_mode
        if self.auth_mode not in {"none", "cloud_iam", "auto"}:
            raise ApiClientConfigurationError("Unsupported API authentication mode.")

    def _requires_cloud_iam(self) -> bool:
        if self.auth_mode == "cloud_iam":
            return True
        return self.auth_mode == "auto" and bool(os.environ.get("K_SERVICE"))

    def _headers(self) -> dict[str, str]:
        if not self._requires_cloud_iam():
            return {}
        lowered = self.base_url.casefold()
        if not self.base_url.startswith("https://") or "localhost" in lowered or "127.0.0.1" in lowered:
            raise ApiClientConfigurationError("Cloud IAM API mode requires an HTTPS non-local API URL.")
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.id_token import fetch_id_token
        except ImportError as exc:
            raise ApiClientConfigurationError("google-auth is required for Cloud Run API authentication.") from exc
        token = fetch_id_token(Request(), self.base_url)
        return {"Authorization": f"Bearer {token}"}

    def get(self, path: str, *, timeout: float = 8) -> dict | list:
        response = requests.get(f"{self.base_url}{path}", headers=self._headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: dict[str, Any], *, timeout: float = 120) -> dict:
        response = requests.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
