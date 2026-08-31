from __future__ import annotations

import pytest

from frontend.api_client import ApiClient, ApiClientConfigurationError


def test_local_api_client_does_not_add_cloud_auth(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "ok"}

    def fake_get(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return Response()

    monkeypatch.setattr("frontend.api_client.requests.get", fake_get)
    assert ApiClient("http://127.0.0.1:8000", auth_mode="none").get("/health") == {"status": "ok"}
    assert captured["kwargs"]["headers"] == {}


def test_cloud_iam_client_rejects_local_api_url():
    with pytest.raises(ApiClientConfigurationError):
        ApiClient("http://127.0.0.1:8000", auth_mode="cloud_iam").get("/health")


def test_cloud_iam_client_fetches_id_token_without_logging_or_persisting_it(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "ready"}

    def fake_get(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return Response()

    monkeypatch.setattr("frontend.api_client.requests.get", fake_get)
    monkeypatch.setattr("google.oauth2.id_token.fetch_id_token", lambda request, audience: "test-id-token")

    result = ApiClient("https://api.example.run.app", auth_mode="cloud_iam").get("/health/ready")

    assert result == {"status": "ready"}
    assert captured["kwargs"]["headers"] == {"Authorization": "Bearer test-id-token"}
