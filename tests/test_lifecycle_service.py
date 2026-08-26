from __future__ import annotations

import json

import pytest

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.publish import read_chunk_lines, read_manifest_rows
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService


MARKDOWN_V1 = "# Quy dinh\n\nPhien ban mot cua quy dinh hoc vu.\n"
MARKDOWN_V2 = "# Quy dinh\n\nPhien ban hai, da cap nhat dieu 5.\n"


def _make_service(tmp_path, refresh_calls: list[str] | None = None) -> LifecycleService:
    registry = LifecycleRegistry(tmp_path / "registry.db")
    return LifecycleService(
        registry=registry,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=tmp_path / "live" / "manifest.csv",
        live_chunks_path=tmp_path / "live" / "chunks.jsonl",
        max_upload_bytes=1_000_000,
        refresh_live_caches=(lambda: refresh_calls.append("refresh")) if refresh_calls is not None else (lambda: None),
    )


def _upload(service: LifecycleService, filename: str, content: bytes, content_type: str = "text/markdown", **kwargs):
    receiver = service.begin_intake(filename=filename, content_type=content_type)
    receiver.feed(content)
    return service.complete_intake(receiver, **kwargs)


# --- upload / duplicate / new-version behavior ---


def test_upload_creates_candidate_version_with_ok_parse_status(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))

    assert outcome.duplicate is False
    assert outcome.parse_status == "ok"
    assert outcome.review_status == "candidate"
    assert outcome.document_id == "quy-dinh"

    version = service.get_version_or_raise(outcome.version_id)
    assert version.candidate_chunks_path is not None
    assert len(read_manifest_rows(tmp_path / "live" / "manifest.csv")) == 0  # not live yet


def test_reuploading_identical_content_is_idempotent(tmp_path):
    service = _make_service(tmp_path)
    first = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    second = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))

    assert second.duplicate is True
    assert second.version_id == first.version_id
    assert len(service.list_versions("quy-dinh")) == 1


def test_reuploading_different_content_same_filename_creates_new_version(tmp_path):
    service = _make_service(tmp_path)
    first = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    second = _upload(service, "quy-dinh.md", MARKDOWN_V2.encode("utf-8"))

    assert second.duplicate is False
    assert second.version_id != first.version_id
    versions = {v.version_id: v for v in service.list_versions("quy-dinh")}
    assert set(versions) == {first.version_id, second.version_id}
    # v1's stored original is untouched by v2's upload.
    assert versions[first.version_id].checksum != versions[second.version_id].checksum
    from pathlib import Path

    assert Path(versions[first.version_id].original_path).read_bytes().decode("utf-8") == MARKDOWN_V1


def test_upload_preserves_original_bytes_immutably(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    version = service.get_version_or_raise(outcome.version_id)
    from pathlib import Path

    original_bytes = Path(version.original_path).read_bytes()
    assert original_bytes.decode("utf-8") == MARKDOWN_V1


# --- review ---


def test_review_requires_ok_parse_status(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "empty.md", b"   ")  # parses to no sections -> failed
    with pytest.raises(LifecycleError) as excinfo:
        service.review(outcome.version_id)
    assert excinfo.value.code == "not_parsed"


def test_review_is_idempotent(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    once = service.review(outcome.version_id)
    twice = service.review(outcome.version_id)
    assert once.review_status == "reviewed"
    assert twice.review_status == "reviewed"


# --- publish: atomic, cache-refreshing, blocks unreviewed candidates ---


def test_publish_requires_review_first(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    with pytest.raises(LifecycleError) as excinfo:
        service.publish(outcome.version_id)
    assert excinfo.value.code == "invalid_transition"


def test_publish_switches_live_manifest_and_chunks_and_refreshes_cache(tmp_path):
    refresh_calls: list[str] = []
    service = _make_service(tmp_path, refresh_calls=refresh_calls)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(outcome.version_id)
    published = service.publish(outcome.version_id)

    assert published.review_status == "published"
    assert refresh_calls == ["refresh"]

    manifest_rows = read_manifest_rows(tmp_path / "live" / "manifest.csv")
    assert [row["doc_id"] for row in manifest_rows] == ["quy-dinh"]
    chunk_lines = read_chunk_lines(tmp_path / "live" / "chunks.jsonl")
    assert len(chunk_lines) >= 1
    assert all(json.loads(line)["doc_id"] == "quy-dinh" for line in chunk_lines)


def test_publish_is_idempotent(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(outcome.version_id)
    service.publish(outcome.version_id)
    again = service.publish(outcome.version_id)
    assert again.review_status == "published"
    assert len(read_manifest_rows(tmp_path / "live" / "manifest.csv")) == 1


def test_publishing_a_new_version_supersedes_the_previous_live_version(tmp_path):
    service = _make_service(tmp_path)
    v1 = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(v1.version_id)
    service.publish(v1.version_id)

    v2 = _upload(service, "quy-dinh.md", MARKDOWN_V2.encode("utf-8"))
    service.review(v2.version_id)
    service.publish(v2.version_id)

    manifest_rows = read_manifest_rows(tmp_path / "live" / "manifest.csv")
    assert len(manifest_rows) == 1  # still one row for this doc_id, not two
    refreshed_v1 = service.get_version_or_raise(v1.version_id)
    refreshed_v2 = service.get_version_or_raise(v2.version_id)
    assert refreshed_v1.review_status == "superseded"
    assert refreshed_v1.superseded_by == v2.version_id
    assert refreshed_v2.review_status == "published"
    assert refreshed_v2.supersedes == v1.version_id

    chunk_lines = read_chunk_lines(tmp_path / "live" / "chunks.jsonl")
    joined = " ".join(chunk_lines)
    assert "dieu 5" in joined  # v2 content is live
    assert "Phien ban mot" not in joined  # v1 content is gone from live


# --- retire ---


def test_retire_requires_published(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    with pytest.raises(LifecycleError) as excinfo:
        service.retire(outcome.version_id)
    assert excinfo.value.code == "invalid_transition"


def test_retire_removes_from_live_but_keeps_provenance(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(outcome.version_id)
    service.publish(outcome.version_id)

    retired = service.retire(outcome.version_id)
    assert retired.review_status == "retired"
    assert read_manifest_rows(tmp_path / "live" / "manifest.csv") == []
    assert read_chunk_lines(tmp_path / "live" / "chunks.jsonl") == []

    # Provenance/original untouched.
    still_there = service.get_version_or_raise(outcome.version_id)
    from pathlib import Path

    assert Path(still_there.original_path).exists()


def test_retire_is_idempotent(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(outcome.version_id)
    service.publish(outcome.version_id)
    service.retire(outcome.version_id)
    again = service.retire(outcome.version_id)
    assert again.review_status == "retired"


# --- rollback: restores without re-parsing or mutating the original ---


def test_rollback_restores_prior_version_without_reparsing(tmp_path, monkeypatch):
    service = _make_service(tmp_path)
    v1 = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(v1.version_id)
    service.publish(v1.version_id)

    v2 = _upload(service, "quy-dinh.md", MARKDOWN_V2.encode("utf-8"))
    service.review(v2.version_id)
    service.publish(v2.version_id)

    # Prove rollback does not call the parser again: if it did, this would raise.
    def _forbidden(*args, **kwargs):
        raise AssertionError("rollback must not re-parse; it must reuse stored candidate chunks")

    monkeypatch.setattr("rag.lifecycle.service.process_candidate", _forbidden)

    restored = service.rollback("quy-dinh", v1.version_id)
    assert restored.review_status == "published"

    refreshed_v1 = service.get_version_or_raise(v1.version_id)
    refreshed_v2 = service.get_version_or_raise(v2.version_id)
    assert refreshed_v1.review_status == "published"
    assert refreshed_v2.review_status == "superseded"
    assert refreshed_v2.superseded_by == v1.version_id

    chunk_lines = read_chunk_lines(tmp_path / "live" / "chunks.jsonl")
    joined = " ".join(chunk_lines)
    assert "Phien ban mot" in joined
    assert "dieu 5" not in joined


def test_rollback_rejects_mismatched_document(tmp_path):
    service = _make_service(tmp_path)
    v1 = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(v1.version_id)
    service.publish(v1.version_id)
    other = _upload(service, "khac.md", b"# Khac\n\nTai lieu khac.\n")

    with pytest.raises(LifecycleError) as excinfo:
        service.rollback("quy-dinh", other.version_id)
    assert excinfo.value.code == "mismatched_document"


def test_rollback_to_currently_live_version_is_idempotent_noop(tmp_path):
    service = _make_service(tmp_path)
    v1 = _upload(service, "quy-dinh.md", MARKDOWN_V1.encode("utf-8"))
    service.review(v1.version_id)
    service.publish(v1.version_id)

    result = service.rollback("quy-dinh", v1.version_id)
    assert result.review_status == "published"
    assert len(read_manifest_rows(tmp_path / "live" / "manifest.csv")) == 1
