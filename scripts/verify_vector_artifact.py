"""Fail-closed vector-space verification for the API build boundary.

The dense retriever remains the single owner of vector-space validation. This
command only loads the explicit release bundle, invokes that existing runtime
contract, and exits non-zero when the dense backend is not active.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from rag.retrieval.dense_retriever import DenseConfig, DenseRetriever, VectorSpaceMismatchError
from rag.retrieval.release_bundle import CorpusRelease, load_corpus_release


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a dense artifact against one explicit corpus release.")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--release-dir", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    return parser.parse_args(argv)


def _read_metadata(artifact_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VectorSpaceMismatchError("dense artifact metadata is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise VectorSpaceMismatchError("dense artifact metadata must be a JSON object")
    return payload


def _verify_provenance(metadata: dict[str, Any], release: CorpusRelease) -> None:
    expected_release_metadata_sha256 = hashlib.sha256(release.metadata_path.read_bytes()).hexdigest()
    if metadata.get("corpus_release_metadata_sha256") != expected_release_metadata_sha256:
        raise VectorSpaceMismatchError("persisted corpus release metadata hash does not match the target release")
    if metadata.get("corpus_release_id") != release.release_id:
        raise VectorSpaceMismatchError("persisted corpus release identity does not match the target release")
    if metadata.get("corpus_manifest_sha256") != release.manifest_sha256:
        raise VectorSpaceMismatchError("persisted corpus manifest hash does not match the target release")
    if metadata.get("corpus_chunks_object") != release.metadata.get("chunks_object"):
        raise VectorSpaceMismatchError("persisted corpus chunks object does not match the target release")
    if metadata.get("corpus_manifest_object") != release.metadata.get("manifest_object"):
        raise VectorSpaceMismatchError("persisted corpus manifest object does not match the target release")
    if metadata.get("chunk_count") != len(release.store):
        raise VectorSpaceMismatchError("persisted corpus chunk count does not match the target release")


def verify_vector_artifact(
    *,
    artifact_dir: str | Path,
    release_dir: str | Path,
    model_id: str,
    model_revision: str,
) -> dict[str, Any]:
    """Return a success receipt or raise on any provenance/vector mismatch."""

    artifact_path = Path(artifact_dir).expanduser().resolve()
    release = load_corpus_release(release_dir)
    metadata = _read_metadata(artifact_path)
    _verify_provenance(metadata, release)
    retriever = DenseRetriever(
        release.store,
        config=DenseConfig(
            model_name=model_id,
            model_revision=model_revision,
            onnx_artifact_dir=artifact_path,
        ),
    )
    status = retriever.status()
    if status.get("state") != "active" or status.get("backend") == "sparse_semantic_fallback":
        reason = status.get("degradation_reason") or "dense backend did not initialize as active"
        raise VectorSpaceMismatchError(str(reason))
    return {
        "status": "ok",
        "artifact_dir": str(artifact_path),
        "release_dir": str(release.root),
        "corpus_release_id": release.release_id,
        "chunk_count": len(release.store),
        "chunk_store_sha256": release.chunks_sha256,
        "model_id": model_id,
        "model_revision": model_revision,
        "backend_status": status,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = verify_vector_artifact(
            artifact_dir=args.artifact_dir,
            release_dir=args.release_dir,
            model_id=args.model_id,
            model_revision=args.model_revision,
        )
    except Exception as exc:  # noqa: BLE001 - the build boundary must fail loudly and uniformly
        print(f"VECTOR_SPACE_VERIFICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
