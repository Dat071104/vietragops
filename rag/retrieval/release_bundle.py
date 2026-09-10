"""Validate a local copy of an immutable corpus release bundle.

The deployment and embedding tools receive a release directory explicitly.
This module validates the release identity and byte hashes before any derived
artifact is built or used.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from rag.retrieval.index_store import ChunkIndexStore


@dataclass(frozen=True)
class CorpusRelease:
    """A verified, local copy of one immutable release bundle."""

    root: Path
    metadata_path: Path
    chunks_path: Path
    manifest_path: Path
    metadata: dict[str, Any]
    chunks_sha256: str
    manifest_sha256: str
    store: ChunkIndexStore

    @property
    def release_id(self) -> str:
        return str(self.metadata["release_id"])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _required_file(root: Path, object_name: Any, expected_basename: str) -> Path:
    if not isinstance(object_name, str) or Path(object_name).name != expected_basename:
        raise ValueError(f"release metadata must name {expected_basename!r} as its object basename")
    path = (root / expected_basename).resolve()
    if path.parent != root or not path.is_file():
        raise ValueError(f"release bundle is missing {expected_basename}")
    return path


def load_corpus_release(release_dir: str | Path) -> CorpusRelease:
    """Load and verify ``release.json``, ``manifest.csv``, and chunks JSONL."""

    root = Path(release_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"corpus release directory does not exist: {root}")
    metadata_path = root / "release.json"
    if not metadata_path.is_file():
        raise ValueError(f"corpus release is missing {metadata_path.name}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("corpus release metadata is not valid UTF-8 JSON") from exc
    if not isinstance(metadata, dict):
        raise ValueError("corpus release metadata must be a JSON object")
    release_id = metadata.get("release_id")
    if not isinstance(release_id, str) or not release_id.strip():
        raise ValueError("corpus release metadata has no release_id")

    chunks_path = _required_file(root, metadata.get("chunks_object"), "chunks_500.jsonl")
    manifest_path = _required_file(root, metadata.get("manifest_object"), "manifest.csv")
    expected_chunks_sha256 = metadata.get("chunks_sha256")
    expected_manifest_sha256 = metadata.get("manifest_sha256")
    if not isinstance(expected_chunks_sha256, str) or not expected_chunks_sha256:
        raise ValueError("corpus release metadata has no chunks_sha256")
    if not isinstance(expected_manifest_sha256, str) or not expected_manifest_sha256:
        raise ValueError("corpus release metadata has no manifest_sha256")
    chunks_sha256 = _sha256(chunks_path)
    manifest_sha256 = _sha256(manifest_path)
    if chunks_sha256 != expected_chunks_sha256:
        raise ValueError("corpus release chunks_sha256 does not match chunks_500.jsonl")
    if manifest_sha256 != expected_manifest_sha256:
        raise ValueError("corpus release manifest_sha256 does not match manifest.csv")

    try:
        store = ChunkIndexStore.from_jsonl(chunks_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError("corpus release chunks_500.jsonl is not a valid chunk store") from exc
    chunk_ids = [chunk.chunk_id for chunk in store]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("corpus release contains duplicate chunk IDs")
    if store.content_hash() != chunks_sha256:
        raise ValueError("corpus release store content hash does not match chunks_sha256")

    try:
        with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
            manifest_rows = list(csv.DictReader(handle))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("corpus release manifest.csv is not valid CSV") from exc
    manifest_doc_ids = [str(row.get("doc_id") or "") for row in manifest_rows]
    if any(not value for value in manifest_doc_ids):
        raise ValueError("corpus release manifest.csv has a row without doc_id")
    if len(manifest_doc_ids) != len(set(manifest_doc_ids)):
        raise ValueError("corpus release manifest.csv contains duplicate doc_id values")
    chunk_doc_ids = {chunk.doc_id for chunk in store}
    if not chunk_doc_ids.issubset(set(manifest_doc_ids)):
        raise ValueError("corpus release contains a chunk whose doc_id is absent from manifest.csv")

    return CorpusRelease(
        root=root,
        metadata_path=metadata_path,
        chunks_path=chunks_path,
        manifest_path=manifest_path,
        metadata=metadata,
        chunks_sha256=chunks_sha256,
        manifest_sha256=manifest_sha256,
        store=store,
    )


__all__ = ["CorpusRelease", "load_corpus_release"]
