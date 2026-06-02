from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_retrieve_endpoint():
    response = client.post(
        "/retrieve",
        json={
            "question": "C\u1ea5u tr\u00fac email sinh vi\u00ean TDTU l\u00e0 g\u00ec?",
            "top_k": 3,
            "retriever": "hybrid",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"]
    assert data["retriever"] == "hybrid"


def test_retrieve_endpoint_supports_release_smoke_payload():
    response = client.post(
        "/retrieve",
        json={
            "question": "Ng\u00e0nh Khoa h\u1ecdc m\u00e1y t\u00ednh c\u1ea7n bao nhi\u00eau t\u00edn ch\u1ec9 \u0111\u1ec3 t\u1ed1t nghi\u1ec7p?",
            "top_k": 5,
            "use_reranker": True,
            "return_debug": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"]
    assert data["retriever"] == "advanced_hybrid"
    assert data["debug"]["use_reranker"] is True
    assert data["debug"]["result_count"] == 5
