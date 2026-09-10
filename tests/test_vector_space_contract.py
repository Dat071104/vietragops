import numpy as np
import pytest

import rag.retrieval.dense_retriever as dense_retriever_module
from rag.retrieval.index_store import ChunkIndexStore
from rag.retrieval.dense_retriever import VectorSpaceMismatchError


def make_store() -> ChunkIndexStore:
    records = []
    for index in range(2):
        records.append(
            {
                "chunk_id": f"doc_s00{index + 1}_c001",
                "doc_id": "doc",
                "title": "Fixture",
                "source_url": "https://example.test/fixture",
                "source_type": "html",
                "domain": "fixture",
                "authority_level": "official",
                "heading_path": ["Fixture"],
                "page_start": None,
                "page_end": None,
                "section_id": f"doc_s00{index + 1}",
                "chunk_index": 1,
                "text": f"Fixture text {index}.",
            }
        )
    return ChunkIndexStore.from_records(records)


def make_metadata(store: ChunkIndexStore, *, model_id: str = "expected/model") -> dict:
    return {
        "model_id": model_id,
        "dimension": 2,
        "normalized": True,
        "normalization": "l2",
        "chunk_store_sha256": store.content_hash(),
    }


def test_matching_vector_space_contract_passes():
    store = make_store()
    metadata = make_metadata(store)

    dense_retriever_module._validate_vector_space(
        metadata,
        np.zeros((2, 2), dtype=np.float32),
        [chunk.chunk_id for chunk in store],
        store,
        expected_model_name="expected/model",
        expected_model_revision=None,
        session_dimension=2,
    )


def test_vector_space_contract_rejects_count_mismatch():
    store = make_store()
    with pytest.raises(VectorSpaceMismatchError, match="row count"):
        dense_retriever_module._validate_vector_space(
            make_metadata(store),
            np.zeros((1, 2), dtype=np.float32),
            [chunk.chunk_id for chunk in store],
            store,
            expected_model_name="expected/model",
            expected_model_revision=None,
            session_dimension=2,
        )


def test_vector_space_contract_rejects_ordering_mismatch():
    store = make_store()
    with pytest.raises(VectorSpaceMismatchError, match="chunk ID order"):
        dense_retriever_module._validate_vector_space(
            make_metadata(store),
            np.zeros((2, 2), dtype=np.float32),
            [chunk.chunk_id for chunk in reversed(store.chunks)],
            store,
            expected_model_name="expected/model",
            expected_model_revision=None,
            session_dimension=2,
        )


def test_vector_space_contract_rejects_content_hash_mismatch():
    store = make_store()
    metadata = make_metadata(store)
    metadata["chunk_store_sha256"] = "wrong-hash"
    with pytest.raises(VectorSpaceMismatchError, match="content hash"):
        dense_retriever_module._validate_vector_space(
            metadata,
            np.zeros((2, 2), dtype=np.float32),
            [chunk.chunk_id for chunk in store],
            store,
            expected_model_name="expected/model",
            expected_model_revision=None,
            session_dimension=2,
        )


def test_vector_space_contract_rejects_model_identity_mismatch():
    store = make_store()
    with pytest.raises(VectorSpaceMismatchError, match="model identity"):
        dense_retriever_module._validate_vector_space(
            make_metadata(store, model_id="wrong/model"),
            np.zeros((2, 2), dtype=np.float32),
            [chunk.chunk_id for chunk in store],
            store,
            expected_model_name="expected/model",
            expected_model_revision=None,
            session_dimension=2,
        )
