from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_endpoint():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "VietRAGOps API"


def test_missing_experiment_returns_404():
    response = client.get("/experiments/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found."
