from __future__ import annotations

import sqlite3

import pytest

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.registry import SCHEMA, LifecycleRegistry


def _make_registry(tmp_path):
    return LifecycleRegistry(tmp_path / "sub" / "registry.db")


def _create_document(registry: LifecycleRegistry, document_id: str = "policy-a"):
    return registry.get_or_create_document(
        document_id=document_id,
        title="Policy A",
        source_url="https://example.edu/policy-a",
        publisher="Example University",
        domain="student_guide",
        authority_level="official",
    )


def test_db_file_created_under_nested_missing_directory(tmp_path):
    registry = _make_registry(tmp_path)
    assert registry.db_path.exists()


def test_get_or_create_document_is_idempotent(tmp_path):
    registry = _make_registry(tmp_path)
    first = _create_document(registry)
    second = _create_document(registry)
    assert first.document_id == second.document_id
    assert first.created_at == second.created_at


def test_unknown_provenance_fields_stay_none_not_invented(tmp_path):
    registry = _make_registry(tmp_path)
    doc = registry.get_or_create_document(
        document_id="mystery-doc",
        title=None,
        source_url=None,
        publisher=None,
        domain=None,
        authority_level=None,
    )
    assert doc.title is None
    assert doc.domain is None
    assert doc.authority_level is None


def test_create_version_persists_all_fields(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    version = registry.create_version(
        document_id="policy-a",
        checksum="a" * 64,
        extension=".html",
        original_path="data/lifecycle/originals/v1.html",
        original_filename="Policy A.html",
        content_type="text/html",
        size_bytes=123,
    )
    assert version.parse_status == "pending"
    assert version.review_status == "candidate"
    assert version.checksum == "a" * 64
    assert version.supersedes is None
    assert version.superseded_by is None
    assert version.candidate_canonical_path is None
    assert version.candidate_extraction_path is None

    fetched = registry.get_version(version.version_id)
    assert fetched == version


def test_duplicate_checksum_for_same_document_is_rejected_deterministically(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    registry.create_version(
        document_id="policy-a",
        checksum="b" * 64,
        extension=".html",
        original_path="data/lifecycle/originals/v1.html",
        original_filename="Policy A.html",
        content_type="text/html",
        size_bytes=10,
    )
    with pytest.raises(LifecycleError) as excinfo:
        registry.create_version(
            document_id="policy-a",
            checksum="b" * 64,
            extension=".html",
            original_path="data/lifecycle/originals/v2.html",
            original_filename="Policy A.html",
            content_type="text/html",
            size_bytes=10,
        )
    assert excinfo.value.code == "duplicate_version"
    # Interrupted-write safety: the failed insert must not have created a second row.
    assert len(registry.list_versions("policy-a")) == 1


def test_different_checksum_same_document_creates_a_new_version_not_overwrite(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    v1 = registry.create_version(
        document_id="policy-a",
        checksum="c" * 64,
        extension=".html",
        original_path="data/lifecycle/originals/v1.html",
        original_filename="Policy A.html",
        content_type="text/html",
        size_bytes=10,
    )
    v2 = registry.create_version(
        document_id="policy-a",
        checksum="d" * 64,
        extension=".html",
        original_path="data/lifecycle/originals/v2.html",
        original_filename="Policy A.html",
        content_type="text/html",
        size_bytes=20,
    )
    versions = registry.list_versions("policy-a")
    assert {v.version_id for v in versions} == {v1.version_id, v2.version_id}
    assert v1.version_id != v2.version_id
    # v1's stored path must be untouched by v2's creation.
    assert registry.get_version(v1.version_id).original_path == "data/lifecycle/originals/v1.html"


def test_find_version_by_checksum_supports_idempotent_reupload(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    created = registry.create_version(
        document_id="policy-a",
        checksum="e" * 64,
        extension=".html",
        original_path="data/lifecycle/originals/v1.html",
        original_filename="Policy A.html",
        content_type="text/html",
        size_bytes=10,
    )
    found = registry.find_version_by_checksum("policy-a", "e" * 64)
    assert found is not None
    assert found.version_id == created.version_id
    assert registry.find_version_by_checksum("policy-a", "f" * 64) is None


def test_review_status_transition_and_supersession_links(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    v1 = registry.create_version(
        document_id="policy-a",
        checksum="1" * 64,
        extension=".html",
        original_path="p1.html",
        original_filename="p1.html",
        content_type="text/html",
        size_bytes=10,
    )
    v2 = registry.create_version(
        document_id="policy-a",
        checksum="2" * 64,
        extension=".html",
        original_path="p2.html",
        original_filename="p2.html",
        content_type="text/html",
        size_bytes=10,
    )
    registry.update_review_status(v1.version_id, "published")
    registry.update_review_status(v1.version_id, "superseded", superseded_by=v2.version_id)
    registry.update_review_status(v2.version_id, "published", supersedes=v1.version_id)

    refreshed_v1 = registry.get_version(v1.version_id)
    refreshed_v2 = registry.get_version(v2.version_id)
    assert refreshed_v1.review_status == "superseded"
    assert refreshed_v1.superseded_by == v2.version_id
    assert refreshed_v2.review_status == "published"
    assert refreshed_v2.supersedes == v1.version_id


def test_invalid_review_status_is_rejected_by_schema_constraint(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    version = registry.create_version(
        document_id="policy-a",
        checksum="9" * 64,
        extension=".html",
        original_path="p.html",
        original_filename="p.html",
        content_type="text/html",
        size_bytes=10,
    )
    with pytest.raises(sqlite3.IntegrityError):
        registry.update_review_status(version.version_id, "not_a_real_status")


def test_events_are_recorded_append_only(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    version = registry.create_version(
        document_id="policy-a",
        checksum="7" * 64,
        extension=".html",
        original_path="p.html",
        original_filename="p.html",
        content_type="text/html",
        size_bytes=10,
    )
    registry.update_candidate_artifacts(
        version.version_id,
        parse_status="ok",
        candidate_processed_path="data/lifecycle/candidates/x/processed.jsonl",
        candidate_chunks_path="data/lifecycle/candidates/x/chunks_500.jsonl",
        parse_warnings=None,
    )
    registry.update_review_status(version.version_id, "reviewed")
    events = registry.list_events(version.version_id)
    event_types = [event["event_type"] for event in events]
    assert event_types == ["intake", "parsed:ok", "reviewed"]


def test_get_document_joins_source_url_and_publisher(tmp_path):
    registry = _make_registry(tmp_path)
    _create_document(registry)
    doc = registry.get_document("policy-a")
    assert doc is not None
    assert doc.source_url == "https://example.edu/policy-a"
    assert doc.publisher == "Example University"
    assert registry.get_document("does-not-exist") is None


def test_registry_survives_reopen_against_same_db_path(tmp_path):
    db_path = tmp_path / "registry.db"
    registry_a = LifecycleRegistry(db_path)
    _create_document(registry_a)
    version = registry_a.create_version(
        document_id="policy-a",
        checksum="8" * 64,
        extension=".html",
        original_path="p.html",
        original_filename="p.html",
        content_type="text/html",
        size_bytes=10,
    )
    del registry_a  # simulate process exit; no explicit close/flush performed

    registry_b = LifecycleRegistry(db_path)
    reopened = registry_b.get_version(version.version_id)
    assert reopened is not None
    assert reopened.checksum == "8" * 64
    assert reopened.original_path == "p.html"


def test_gate02_candidate_location_columns_migrate_gate01_registry(tmp_path):
    db_path = tmp_path / "legacy-registry.db"
    legacy_schema = SCHEMA.replace(
        "    candidate_canonical_path TEXT,\n    candidate_extraction_path TEXT,\n",
        "",
    )
    with sqlite3.connect(db_path) as connection:
        connection.executescript(legacy_schema)

    registry = LifecycleRegistry(db_path)
    _create_document(registry)
    version = registry.create_version(
        document_id="policy-a",
        checksum="a" * 64,
        extension=".pdf",
        original_path="original.pdf",
        original_filename="original.pdf",
        content_type="application/pdf",
        size_bytes=10,
    )

    assert version.candidate_canonical_path is None
    assert version.candidate_extraction_path is None
    updated = registry.update_candidate_artifacts(
        version.version_id,
        parse_status="failed",
        candidate_processed_path="processed.jsonl",
        candidate_chunks_path="chunks_500.jsonl",
        candidate_canonical_path="canonical.md",
        candidate_extraction_path="extraction.json",
        parse_warnings='["malformed_pdf"]',
    )
    assert updated.candidate_canonical_path == "canonical.md"
    assert updated.candidate_extraction_path == "extraction.json"
