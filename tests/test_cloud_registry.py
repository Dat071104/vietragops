from __future__ import annotations

import pytest

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.gcs_registry import GcsLifecycleRegistry, GcsRegistryConflictError
from rag.lifecycle.gcs_storage import MemoryObjectStore


def _registry() -> GcsLifecycleRegistry:
    return GcsLifecycleRegistry(MemoryObjectStore())


def _create_version(registry: GcsLifecycleRegistry, *, version_id: str = "version-one"):
    registry.get_or_create_document(
        document_id="doc-one",
        title="Document One",
        source_url="https://example.edu/doc-one",
        publisher="Example University",
        domain="policy",
        authority_level="official",
    )
    return registry.create_version(
        version_id=version_id,
        document_id="doc-one",
        checksum=version_id * 64,
        extension=".md",
        original_path="gs://test-bucket/sources/original/one.md",
        original_filename="one.md",
        content_type="text/markdown",
        size_bytes=10,
    )


def test_registry_state_is_reconstructed_from_durable_object():
    objects = MemoryObjectStore()
    first = GcsLifecycleRegistry(objects)
    created = _create_version(first)
    first.update_candidate_artifacts(
        created.version_id,
        parse_status="ok",
        candidate_processed_path="gs://test-bucket/candidates/version-one/processed.jsonl",
        candidate_chunks_path="gs://test-bucket/candidates/version-one/chunks_500.jsonl",
        candidate_extraction_path="gs://test-bucket/candidates/version-one/extraction.json",
        parse_warnings=None,
    )

    restarted = GcsLifecycleRegistry(objects)
    restored = restarted.get_version("version-one")
    assert restored is not None
    assert restored.parse_status == "ok"
    assert restored.candidate_chunks_path.endswith("chunks_500.jsonl")
    assert restarted.get_document("doc-one").source_url == "https://example.edu/doc-one"


def test_registry_transition_updates_release_and_version_atomically():
    registry = _registry()
    version = _create_version(registry)
    registry.activate_release(
        version_id=version.version_id,
        release_id="release-one",
        previous_version_id=None,
        published_at="2026-08-31T00:00:00+00:00",
    )

    assert registry.get_active_release_id() == "release-one"
    assert registry.get_published_version("doc-one").version_id == version.version_id
    assert registry.list_events(version.version_id)[-1]["event_type"] == "published"


def test_registry_rejects_duplicate_checksum_and_invalid_update_field():
    registry = _registry()
    version = _create_version(registry)
    with pytest.raises(LifecycleError) as duplicate:
        registry.create_version(
            document_id=version.document_id,
            checksum=version.checksum,
            extension=".md",
            original_path=version.original_path,
            original_filename="duplicate.md",
            content_type="text/markdown",
            size_bytes=10,
        )
    assert duplicate.value.code == "duplicate_version"

    with pytest.raises(LifecycleError) as invalid:
        registry.update_review_status(version.version_id, "reviewed", unsafe_field="x")
    assert invalid.value.code == "invalid_registry_update"


def test_registry_reports_conflict_after_retry_budget_is_exhausted(monkeypatch):
    objects = MemoryObjectStore()
    registry = GcsLifecycleRegistry(objects, max_retries=2)
    version = _create_version(registry)
    original_write = registry._write_state

    def always_conflict(state, generation):
        raise GcsRegistryConflictError()

    monkeypatch.setattr(registry, "_write_state", always_conflict)
    with pytest.raises(GcsRegistryConflictError):
        registry.record_note(version.version_id, "test")
    monkeypatch.setattr(registry, "_write_state", original_write)
