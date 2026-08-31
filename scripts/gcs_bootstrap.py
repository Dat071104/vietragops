"""Upload an immutable baseline release bundle to the approved GCS bucket."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.lifecycle.gcs_storage import GcsObjectStore, GcsReleaseStore, GcsStorageError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap one immutable VietRAGOps release in Cloud Storage.")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = args.manifest.read_bytes()
    chunks = args.chunks.read_bytes()
    release = GcsReleaseStore(GcsObjectStore(args.bucket)).write_release(
        args.release_id,
        manifest_bytes=manifest,
        chunks_bytes=chunks,
        metadata={"source_commit": args.source_commit, "operation": "bootstrap"},
    )
    print(f"release_id={release.release_id}")
    print(f"manifest_sha256={release.metadata['manifest_sha256']}")
    print(f"chunks_sha256={release.metadata['chunks_sha256']}")
    print("secret_values=not_read")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GcsStorageError as exc:
        print(f"storage_error={exc.code}", file=sys.stderr)
        raise SystemExit(1) from exc
