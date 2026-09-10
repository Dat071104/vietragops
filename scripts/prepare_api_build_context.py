"""Prepare a clean API build context after the mandatory vector verification."""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any

from rag.retrieval.dense_retriever import PRODUCT_MODEL_NAME, PRODUCT_MODEL_REVISION
from rag.retrieval.release_bundle import load_corpus_release
from scripts.verify_vector_artifact import verify_vector_artifact


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a clean, release-bound Cloud Build context.")
    parser.add_argument("--source-root", required=True, help="Repository root whose committed HEAD is archived.")
    parser.add_argument("--release-dir", required=True, help="Verified local copy of the target corpus release.")
    parser.add_argument("--artifact-dir", required=True, help="Rebuilt ONNX artifact directory.")
    parser.add_argument("--output-dir", required=True, help="New external directory receiving the build context.")
    parser.add_argument("--model-id", default=PRODUCT_MODEL_NAME)
    parser.add_argument("--model-revision", default=PRODUCT_MODEL_REVISION)
    return parser.parse_args(argv)


def _archive_head(source_root: Path, output_dir: Path) -> str:
    commit = subprocess.check_output(
        ["git", "-c", "http.sslBackend=openssl", "rev-parse", "HEAD"],
        cwd=source_root,
        text=True,
    ).strip()
    archive = subprocess.check_output(
        ["git", "-c", "http.sslBackend=openssl", "archive", "--format=tar", "HEAD"],
        cwd=source_root,
    )
    with tarfile.open(fileobj=BytesIO(archive), mode="r:") as handle:
        for member in handle.getmembers():
            target = (output_dir / member.name).resolve()
            if output_dir not in target.parents and target != output_dir:
                raise ValueError(f"git archive member escapes build context: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = handle.extractfile(member)
                if extracted is None:
                    raise ValueError(f"git archive member could not be read: {member.name}")
                target.write_bytes(extracted.read())
            else:
                raise ValueError(f"unsupported git archive member type: {member.name}")
    return commit


def prepare_context(
    *,
    source_root: str | Path,
    release_dir: str | Path,
    artifact_dir: str | Path,
    output_dir: str | Path,
    model_id: str = PRODUCT_MODEL_NAME,
    model_revision: str = PRODUCT_MODEL_REVISION,
) -> dict[str, Any]:
    source = Path(source_root).expanduser().resolve()
    release = load_corpus_release(release_dir)
    verification = verify_vector_artifact(
        artifact_dir=artifact_dir,
        release_dir=release.root,
        model_id=model_id,
        model_revision=model_revision,
    )
    output = Path(output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing build context: {output}")
    output.mkdir(parents=True)
    commit = _archive_head(source, output)

    artifact_target = output / "data" / "chunks" / "embeddings" / "active"
    release_target = output / "deploy" / "corpus-release"
    shutil.copytree(Path(artifact_dir).expanduser().resolve(), artifact_target)
    shutil.copytree(release.root, release_target)
    return {
        "status": "ok",
        "source_commit": commit,
        "output_dir": str(output),
        "release_id": release.release_id,
        "artifact_dir": str(artifact_target),
        "release_dir": str(release_target),
        "verification": verification,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = prepare_context(
        source_root=args.source_root,
        release_dir=args.release_dir,
        artifact_dir=args.artifact_dir,
        output_dir=args.output_dir,
        model_id=args.model_id,
        model_revision=args.model_revision,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
