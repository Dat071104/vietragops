"""End-to-end proof of the Gate 01 document lifecycle through the real HTTP API.

Runs against an isolated manifest/chunks/lifecycle-registry under tmp_path
(via VIETRAGOPS_* env overrides) so the real, committed corpus under `data/`
is never read or written by this test. No provider/model is called: `/retrieve`
with the `bm25` retriever is used to inspect deterministic retrieval context.
"""

from __future__ import annotations

import csv
import json

import pytest
from fastapi.testclient import TestClient

import app.core.config as config
from app.main import app


client = TestClient(app)

BASELINE_DOC_ID = "baseline-regression-doc"
BASELINE_MARKER = "Baseline regression marker phrase unique 9931"

MANIFEST_FIELDNAMES = [
    "doc_id", "title", "source_url", "source_type", "domain", "authority_level",
    "language", "published_at", "crawled_at", "file_path", "checksum", "status", "notes",
]


def _seed_baseline(manifest_path, chunks_path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDNAMES)
        writer.writeheader()
        writer.writerow(
            {
                "doc_id": BASELINE_DOC_ID,
                "title": "Baseline",
                "source_url": "https://example.edu/baseline",
                "source_type": "markdown",
                "domain": "student_guide",
                "authority_level": "official",
                "language": "vi",
                "published_at": "",
                "crawled_at": "2026-01-01T00:00:00+00:00",
                "file_path": "data/raw/baseline.md",
                "checksum": "0" * 64,
                "status": "active",
                "notes": "",
            }
        )
    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    chunk = {
        "chunk_id": f"{BASELINE_DOC_ID}_s001_c001",
        "doc_id": BASELINE_DOC_ID,
        "title": "Baseline",
        "source_url": "https://example.edu/baseline",
        "source_type": "markdown",
        "domain": "student_guide",
        "authority_level": "official",
        "heading_path": ["Baseline"],
        "page_start": None,
        "page_end": None,
        "section_id": f"{BASELINE_DOC_ID}_s001",
        "chunk_index": 1,
        "text": f"Baseline\n{BASELINE_MARKER} for the pre-existing corpus.",
    }
    chunks_path.write_text(json.dumps(chunk, ensure_ascii=False) + "\n", encoding="utf-8")


def _clear_caches() -> None:
    config.get_settings.cache_clear()
    config.get_store.cache_clear()
    config.get_context_builder.cache_clear()
    config.get_answer_generator.cache_clear()
    config.get_agent_answer_generator.cache_clear()
    config.get_provider_router.cache_clear()
    config.get_agent_provider_router.cache_clear()
    config.get_lifecycle_service.cache_clear()


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    manifest_path = tmp_path / "live" / "manifest.csv"
    chunks_path = tmp_path / "live" / "chunks_500.jsonl"
    _seed_baseline(manifest_path, chunks_path)

    monkeypatch.setenv("VIETRAGOPS_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("VIETRAGOPS_CHUNKS_PATH", str(chunks_path))
    monkeypatch.setenv("VIETRAGOPS_LIFECYCLE_ROOT", str(tmp_path / "lifecycle"))
    monkeypatch.setenv("VIETRAGOPS_LIFECYCLE_MAX_UPLOAD_BYTES", "4096")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_caches()
    try:
        yield manifest_path, chunks_path
    finally:
        _clear_caches()


def _retrieve_doc_ids(question: str) -> set[str]:
    response = client.post("/retrieve", json={"question": question, "retriever": "bm25", "top_k": 10})
    assert response.status_code == 200
    return {result["doc_id"] for result in response.json()["results"]}


def test_baseline_corpus_is_retrievable_before_any_lifecycle_action(isolated_env):
    doc_ids = _retrieve_doc_ids(BASELINE_MARKER)
    assert BASELINE_DOC_ID in doc_ids


def test_upload_rejects_path_traversal_filename(isolated_env):
    response = client.post(
        "/documents/upload",
        files={"files": ("../evil.html", b"<p>x</p>", "text/html")},
    )
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["accepted"] is False
    assert item["error_code"] == "path_traversal"


def test_upload_rejects_oversized_file(isolated_env):
    oversized = b"#Title\n" + b"x" * 5000
    response = client.post(
        "/documents/upload",
        files={"files": ("too-big.md", oversized, "text/markdown")},
    )
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["accepted"] is False
    assert item["error_code"] == "file_too_large"


def test_full_lifecycle_publish_retire_rollback_via_http(isolated_env):
    manifest_path, chunks_path = isolated_env
    marker_v1 = "Quokka wombat lighthouse xyzzyplugh 4471"
    marker_v2 = "Falcon meadow lantern brontosaurus 4472"

    # 1. Upload v1 -> candidate only.
    upload_v1 = client.post(
        "/documents/upload",
        files={"files": ("candidate-policy.md", f"# Candidate\n\n{marker_v1}\n".encode("utf-8"), "text/markdown")},
    )
    assert upload_v1.status_code == 200
    item_v1 = upload_v1.json()["results"][0]
    assert item_v1["accepted"] is True
    assert item_v1["parse_status"] == "ok"
    assert item_v1["review_status"] == "candidate"
    assert item_v1["duplicate"] is False
    document_id = item_v1["document_id"]
    version_v1 = item_v1["version_id"]

    # 2. Re-upload identical content -> idempotent duplicate, no new version.
    dup = client.post(
        "/documents/upload",
        files={"files": ("candidate-policy.md", f"# Candidate\n\n{marker_v1}\n".encode("utf-8"), "text/markdown")},
    )
    dup_item = dup.json()["results"][0]
    assert dup_item["duplicate"] is True
    assert dup_item["version_id"] == version_v1

    # 3. Publishing before review is rejected deterministically.
    premature_publish = client.post(f"/documents/versions/{version_v1}/publish")
    assert premature_publish.status_code == 409

    # 4. Candidate cannot affect live retrieval before publish.
    assert document_id not in _retrieve_doc_ids(marker_v1)
    assert not any(document_id in row["doc_id"] for row in csv.DictReader(manifest_path.open(encoding="utf-8-sig")))

    # 5. Review, then publish -> live.
    review_resp = client.post(f"/documents/versions/{version_v1}/review")
    assert review_resp.status_code == 200
    assert review_resp.json()["review_status"] == "reviewed"

    publish_resp = client.post(f"/documents/versions/{version_v1}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json()["review_status"] == "published"

    listed = client.get("/documents").json()
    assert any(row["doc_id"] == document_id for row in listed)
    assert document_id in _retrieve_doc_ids(marker_v1)
    # Baseline corpus is unaffected by publishing an unrelated document.
    assert BASELINE_DOC_ID in _retrieve_doc_ids(BASELINE_MARKER)

    # 6. Upload + review + publish v2 -> supersedes v1 live.
    upload_v2 = client.post(
        "/documents/upload",
        files={"files": ("candidate-policy.md", f"# Candidate\n\n{marker_v2}\n".encode("utf-8"), "text/markdown")},
    )
    item_v2 = upload_v2.json()["results"][0]
    version_v2 = item_v2["version_id"]
    assert version_v2 != version_v1
    client.post(f"/documents/versions/{version_v2}/review")
    publish_v2 = client.post(f"/documents/versions/{version_v2}/publish")
    assert publish_v2.status_code == 200

    versions = client.get(f"/documents/{document_id}/versions").json()
    by_id = {v["version_id"]: v for v in versions}
    assert by_id[version_v1]["review_status"] == "superseded"
    assert by_id[version_v2]["review_status"] == "published"
    assert document_id in _retrieve_doc_ids(marker_v2)
    assert document_id not in _retrieve_doc_ids(marker_v1)  # v1 text no longer live

    # 7. Retire v2 -> removed from live entirely, provenance kept.
    retire_resp = client.post(f"/documents/versions/{version_v2}/retire")
    assert retire_resp.status_code == 200
    assert retire_resp.json()["review_status"] == "retired"
    assert document_id not in {row["doc_id"] for row in client.get("/documents").json()}
    assert document_id not in _retrieve_doc_ids(marker_v2)

    # 8. Rollback to v1 -> restored live without re-parsing (v1's original text).
    rollback_resp = client.post(f"/documents/{document_id}/rollback", json={"to_version_id": version_v1})
    assert rollback_resp.status_code == 200
    assert rollback_resp.json()["review_status"] == "published"
    assert document_id in _retrieve_doc_ids(marker_v1)
    assert document_id not in _retrieve_doc_ids(marker_v2)

    # Baseline corpus survived the entire sequence untouched.
    assert BASELINE_DOC_ID in _retrieve_doc_ids(BASELINE_MARKER)
