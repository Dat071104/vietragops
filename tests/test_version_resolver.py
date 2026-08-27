from __future__ import annotations

from datetime import datetime, timezone
import json

from rag.lifecycle.registry import LifecycleRegistry
from rag.retrieval.index_store import ChunkIndexStore
from rag.retrieval.version_resolver import (
    AUTHORITY_ACTIVE,
    AUTHORITY_RETIRED,
    FRESHNESS_CURRENT,
    FRESHNESS_STALE,
    UNKNOWN,
    VersionResolver,
)


CHUNK_RECORD = {
    "chunk_id": "doc1_chunk1",
    "doc_id": "doc1",
    "title": "Doc 1",
    "source_url": "https://example.edu/doc1",
    "source_type": "html",
    "domain": "student_guide",
    "authority_level": "official",
    "heading_path": ["Doc 1"],
    "page_start": None,
    "page_end": None,
    "section_id": "doc1_s001",
    "chunk_index": 1,
    "text": "Nội dung doc 1.",
}


# --- ChunkIndexStore.index_version -----------------------------------------


def test_index_version_is_deterministic_for_same_file(tmp_path):
    chunks_path = tmp_path / "chunks.jsonl"
    chunks_path.write_text(json.dumps(CHUNK_RECORD, ensure_ascii=False) + "\n", encoding="utf-8")

    store_a = ChunkIndexStore.from_jsonl(chunks_path)
    store_b = ChunkIndexStore.from_jsonl(chunks_path)

    assert store_a.index_version == store_b.index_version
    assert store_a.index_version.startswith("sha256:")


def test_index_version_changes_when_file_content_changes(tmp_path):
    chunks_path = tmp_path / "chunks.jsonl"
    chunks_path.write_text(json.dumps(CHUNK_RECORD, ensure_ascii=False) + "\n", encoding="utf-8")
    store_before = ChunkIndexStore.from_jsonl(chunks_path)

    changed = dict(CHUNK_RECORD, text="Nội dung đã thay đổi.")
    chunks_path.write_text(json.dumps(changed, ensure_ascii=False) + "\n", encoding="utf-8")
    store_after = ChunkIndexStore.from_jsonl(chunks_path)

    assert store_before.index_version != store_after.index_version


def test_index_version_is_deterministic_for_in_memory_records():
    store_a = ChunkIndexStore.from_records([CHUNK_RECORD])
    store_b = ChunkIndexStore.from_records([CHUNK_RECORD])

    assert store_a.index_version == store_b.index_version
    assert store_a.index_version.startswith("sha256:")


# --- VersionResolver: legacy manifest-only resolution -----------------------


def test_legacy_document_resolves_to_checksum_derived_source_version():
    manifest_rows = {"doc1": {"checksum": "abc123def4567890", "status": "active", "published_at": ""}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef")

    info = resolver.resolve("doc1")

    assert info.source_id == "doc1"
    assert info.source_version == "legacy:abc123def4567890"
    assert info.index_version == "sha256:deadbeef"
    assert info.authority_state == AUTHORITY_ACTIVE
    assert info.freshness_state == UNKNOWN  # no stale_after, no published_at -> unknown, never invented
    assert info.conflict_key is None


def test_document_missing_from_manifest_resolves_unknown():
    resolver = VersionResolver({}, index_version="sha256:deadbeef")

    info = resolver.resolve("ghost_doc")

    assert info.source_version == UNKNOWN
    assert info.authority_state == UNKNOWN
    assert info.freshness_state == UNKNOWN


def test_retired_status_in_manifest_resolves_retired_authority():
    manifest_rows = {"doc1": {"checksum": "abc123", "status": "retired"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef")

    info = resolver.resolve("doc1")

    assert info.authority_state == AUTHORITY_RETIRED


def test_published_at_present_resolves_current_freshness():
    manifest_rows = {"doc1": {"checksum": "abc123", "status": "active", "published_at": "2026-01-01T00:00:00+00:00"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef")

    info = resolver.resolve("doc1")

    assert info.freshness_state == FRESHNESS_CURRENT


def test_stale_after_in_the_past_resolves_stale_freshness():
    as_of = datetime(2026, 6, 1, tzinfo=timezone.utc)
    manifest_rows = {"doc1": {"checksum": "abc123", "status": "active", "stale_after": "2026-01-01T00:00:00+00:00"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef", as_of=as_of)

    info = resolver.resolve("doc1")

    assert info.freshness_state == FRESHNESS_STALE


def test_stale_after_in_the_future_resolves_current_freshness():
    as_of = datetime(2026, 1, 1, tzinfo=timezone.utc)
    manifest_rows = {"doc1": {"checksum": "abc123", "status": "active", "stale_after": "2026-06-01T00:00:00+00:00"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef", as_of=as_of)

    info = resolver.resolve("doc1")

    assert info.freshness_state == FRESHNESS_CURRENT


def test_conflict_key_is_passed_through_when_present():
    manifest_rows = {"doc1": {"checksum": "abc123", "status": "active", "conflict_key": "tuition_2026"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef")

    info = resolver.resolve("doc1")

    assert info.conflict_key == "tuition_2026"


# --- VersionResolver: registry-aware resolution -----------------------------


def _publish_version(registry: LifecycleRegistry, *, document_id: str, checksum: str) -> str:
    registry.get_or_create_document(
        document_id=document_id,
        title=document_id,
        source_url=None,
        publisher=None,
        domain="student_guide",
        authority_level="official",
    )
    version = registry.create_version(
        document_id=document_id,
        checksum=checksum,
        extension=".md",
        original_path=f"/tmp/{document_id}.md",
        original_filename=f"{document_id}.md",
        content_type="text/markdown",
        size_bytes=10,
    )
    registry.update_review_status(version.version_id, "reviewed")
    registry.update_review_status(version.version_id, "published", published_at="2026-01-01T00:00:00+00:00")
    return version.version_id


def test_registry_tracked_document_resolves_to_real_version_id(tmp_path):
    registry = LifecycleRegistry(tmp_path / "registry.db")
    version_id = _publish_version(registry, document_id="doc1", checksum="cafebabe")
    manifest_rows = {"doc1": {"checksum": "cafebabe", "status": "active"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef", registry=registry)

    info = resolver.resolve("doc1")

    assert info.source_version == version_id
    assert info.authority_state == AUTHORITY_ACTIVE


def test_registry_checksum_mismatch_falls_back_to_legacy_identity(tmp_path):
    """A stale manifest row (checksum drifted from the registry) must not be
    silently matched to the wrong registry version."""
    registry = LifecycleRegistry(tmp_path / "registry.db")
    _publish_version(registry, document_id="doc1", checksum="cafebabe")
    manifest_rows = {"doc1": {"checksum": "different_checksum_value", "status": "active"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef", registry=registry)

    info = resolver.resolve("doc1")

    assert info.source_version == f"legacy:{'different_checksum_value'[:16]}"


def test_fully_retired_registry_document_resolves_retired_authority_diagnostically(tmp_path):
    """Proves the diagnostic path: even though a fully-retired document's
    chunks can never appear in the live corpus (apply_live_state removes
    them), a resolver with direct registry access still classifies it
    correctly rather than reporting it as active or unknown."""
    registry = LifecycleRegistry(tmp_path / "registry.db")
    version_id = _publish_version(registry, document_id="doc1", checksum="cafebabe")
    registry.update_review_status(version_id, "retired")
    manifest_rows = {"doc1": {"checksum": "cafebabe", "status": "active"}}
    resolver = VersionResolver(manifest_rows, index_version="sha256:deadbeef", registry=registry)

    info = resolver.resolve("doc1")

    assert info.authority_state == AUTHORITY_RETIRED
