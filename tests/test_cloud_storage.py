from __future__ import annotations

import pytest

from rag.lifecycle.gcs_storage import (
    GcsPreconditionFailed,
    GcsReleaseStore,
    GcsStorageError,
    MemoryObjectStore,
    object_name_from_uri,
)
from rag.lifecycle.gcs_registry import GcsLifecycleRegistry
from rag.lifecycle.gcs_service import GcsLifecycleService


def test_memory_object_store_enforces_immutable_and_generation_preconditions():
    objects = MemoryObjectStore()

    first = objects.put_immutable("sources/original/a.md", b"one")
    assert first.generation == 1
    assert objects.get("sources/original/a.md").content == b"one"

    with pytest.raises(GcsPreconditionFailed):
        objects.put_immutable("sources/original/a.md", b"two")

    second = objects.put("registry/pointers/state.json", b"v1", if_generation_match=0)
    assert second.generation == 1
    updated = objects.put("registry/pointers/state.json", b"v2", if_generation_match=second.generation)
    assert updated.generation == 2
    with pytest.raises(GcsPreconditionFailed):
        objects.put("registry/pointers/state.json", b"v3", if_generation_match=second.generation)


def test_release_bundle_is_immutable_and_checksum_verified():
    objects = MemoryObjectStore()
    releases = GcsReleaseStore(objects)
    release = releases.write_release(
        "release-one",
        manifest_bytes=b"doc_id,title\nalpha,Alpha\n",
        chunks_bytes=b'{"doc_id":"alpha","chunk_id":"a1"}\n',
        metadata={"source_commit": "abc123"},
    )

    assert release.metadata["source_commit"] == "abc123"
    loaded = releases.read_release("release-one")
    assert loaded.manifest_rows() == [{"doc_id": "alpha", "title": "Alpha"}]
    assert loaded.chunk_records() == [{"doc_id": "alpha", "chunk_id": "a1"}]

    with pytest.raises(GcsPreconditionFailed):
        releases.write_release(
            "release-one",
            manifest_bytes=b"changed",
            chunks_bytes=b"changed",
        )


def test_release_uri_is_limited_to_configured_bucket():
    objects = MemoryObjectStore(bucket_name="approved-bucket")
    releases = GcsReleaseStore(objects)
    uri = releases.uri("releases/release-one/release.json")
    assert object_name_from_uri(uri, bucket_name="approved-bucket") == "releases/release-one/release.json"
    with pytest.raises(GcsStorageError):
        object_name_from_uri(uri, bucket_name="other-bucket")


def test_gcs_lifecycle_publishes_and_rolls_back_durable_release_objects():
    objects = MemoryObjectStore()
    GcsReleaseStore(objects).write_release(
        "bootstrap",
        manifest_bytes=(
            b"doc_id,title,source_url,source_type,domain,authority_level,language,published_at,"
            b"crawled_at,file_path,checksum,status,notes\n"
        ),
        chunks_bytes=b"",
    )
    registry = GcsLifecycleRegistry(objects)
    refresh_calls: list[str] = []
    service = GcsLifecycleService(
        registry=registry,
        objects=objects,
        max_upload_bytes=1_000_000,
        refresh_live_caches=lambda: refresh_calls.append("refresh"),
        bootstrap_release_id="bootstrap",
    )

    receiver_v1 = service.begin_intake(filename="policy.md", content_type="text/markdown")
    receiver_v1.feed(b"# Policy\n\nVersion one durable marker.")
    uploaded_v1 = service.complete_intake(receiver_v1, domain="policy", authority_level="official")
    assert uploaded_v1.review_status == "candidate"
    service.review(uploaded_v1.version_id)
    published_v1 = service.publish(uploaded_v1.version_id)
    assert published_v1.review_status == "published"
    release_v1 = service.load_live_release()
    assert "Version one durable marker" in release_v1.chunks_bytes.decode("utf-8")

    receiver_v2 = service.begin_intake(filename="policy.md", content_type="text/markdown")
    receiver_v2.feed(b"# Policy\n\nVersion two durable marker.")
    uploaded_v2 = service.complete_intake(receiver_v2, domain="policy", authority_level="official")
    service.review(uploaded_v2.version_id)
    service.publish(uploaded_v2.version_id)
    assert "Version two durable marker" in service.load_live_release().chunks_bytes.decode("utf-8")

    restarted = GcsLifecycleService(
        registry=GcsLifecycleRegistry(objects),
        objects=objects,
        max_upload_bytes=1_000_000,
        refresh_live_caches=lambda: None,
    )
    assert "Version two durable marker" in restarted.load_live_release().chunks_bytes.decode("utf-8")

    rolled_back = restarted.rollback("policy", uploaded_v1.version_id)
    assert rolled_back.version_id == uploaded_v1.version_id
    assert "Version one durable marker" in restarted.load_live_release().chunks_bytes.decode("utf-8")
    assert refresh_calls
