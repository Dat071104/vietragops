from __future__ import annotations

from rag.generation.context_builder import ContextBuilder
from rag.retrieval import ChunkIndexStore
from rag.retrieval.version_resolver import VersionResolver


def make_store() -> ChunkIndexStore:
    records = [
        {
            "chunk_id": "email_chunk",
            "doc_id": "email_doc",
            "title": "Email sinh viên",
            "source_url": "https://example.edu/email",
            "source_type": "html",
            "domain": "email_usage",
            "authority_level": "official",
            "heading_path": ["Email sinh viên"],
            "page_start": None,
            "page_end": None,
            "section_id": "email_s001",
            "chunk_index": 1,
            "text": "Cấu trúc email: MSSV@student.tdtu.edu.vn.",
        }
    ]
    return ChunkIndexStore.from_records(records)


def test_context_builder_without_resolver_omits_version_key():
    store = make_store()
    builder = ContextBuilder(store)

    bundle = builder.build("Cấu trúc email sinh viên là gì?", top_k=1)

    assert bundle.chunks
    assert "version" not in bundle.chunks[0]
    assert bundle.retrieval_debug["chunk_versions"] == {}


def test_context_builder_with_resolver_attaches_version_to_each_chunk_and_debug():
    store = make_store()
    manifest_rows = {"email_doc": {"checksum": "abc123", "status": "active"}}
    resolver = VersionResolver(manifest_rows, index_version=store.index_version)
    builder = ContextBuilder(store, version_resolver=resolver)

    bundle = builder.build("Cấu trúc email sinh viên là gì?", top_k=1)

    assert bundle.chunks
    chunk = bundle.chunks[0]
    assert chunk["version"]["source_id"] == "email_doc"
    assert chunk["version"]["source_version"] == "legacy:abc123"
    assert chunk["version"]["index_version"] == store.index_version
    assert chunk["version"]["authority_state"] == "active"

    assert bundle.retrieval_debug["chunk_versions"][chunk["chunk_id"]] == chunk["version"]
