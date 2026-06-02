from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ask_endpoint():
    response = client.post(
        "/ask",
        json={
            "question": "S\u1ed1 \u0111i\u1ec7n tho\u1ea1i c\u00e1 nh\u00e2n c\u1ee7a m\u1ed9t sinh vi\u00ean c\u1ee5 th\u1ec3 l\u00e0 g\u00ec?",
            "debug": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["refusal"] is True


def test_ask_endpoint_supports_release_smoke_payload():
    response = client.post(
        "/ask",
        json={
            "question": "Ng\u00e0nh Khoa h\u1ecdc m\u00e1y t\u00ednh c\u1ea7n bao nhi\u00eau t\u00edn ch\u1ec9 \u0111\u1ec3 t\u1ed1t nghi\u1ec7p?",
            "top_k": 5,
            "use_reranker": True,
            "use_guardrail": True,
            "return_debug": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "retrieval_debug" in data
    assert data["retrieval_debug"]["top_k"] == 5


def test_ask_endpoint_rejects_guardrail_disable():
    response = client.post(
        "/ask",
        json={
            "question": "C\u1ea5u tr\u00fac email sinh vi\u00ean l\u00e0 g\u00ec?",
            "use_guardrail": False,
        },
    )
    assert response.status_code == 400
