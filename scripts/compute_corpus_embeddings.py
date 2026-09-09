"""Offline ONNX corpus embedding materialization.

The output is a self-contained artifact directory containing the query encoder,
tokenizer, normalized corpus vectors, row IDs, and a hash-bound metadata file.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
from typing import Any

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute normalized corpus vectors with an ONNX encoder.")
    parser.add_argument("--chunks", required=True)
    parser.add_argument("--encoder-dir", required=True, help="Self-contained fp32 or int8 export directory.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args(argv)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_chunks(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _encode_batch(
    session: ort.InferenceSession,
    tokenizer: Tokenizer,
    metadata: dict[str, Any],
    texts: list[str],
) -> np.ndarray:
    prefix = str(metadata.get("passage_prefix", ""))
    encodings = tokenizer.encode_batch([f"{prefix}{text}" for text in texts])
    input_ids = np.asarray([encoding.ids for encoding in encodings], dtype=np.int64)
    attention_mask = np.asarray([encoding.attention_mask for encoding in encodings], dtype=np.int64)
    feeds: dict[str, np.ndarray] = {}
    for input_spec in session.get_inputs():
        name = input_spec.name.casefold()
        if "input_ids" in name:
            feeds[input_spec.name] = input_ids
        elif "attention_mask" in name:
            feeds[input_spec.name] = attention_mask
        elif "token_type_ids" in name:
            feeds[input_spec.name] = np.zeros_like(input_ids)
    output = session.run(None, feeds)[0]
    mask = attention_mask[..., None].astype(np.float32)
    pooled = (output * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    return (pooled / np.clip(norms, 1e-12, None)).astype(np.float32)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    chunks_path = Path(args.chunks)
    encoder_dir = Path(args.encoder_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((encoder_dir / "metadata.json").read_text(encoding="utf-8"))
    chunks = _load_chunks(chunks_path)

    tokenizer = Tokenizer.from_file(str(encoder_dir / metadata["tokenizer_file"]))
    tokenizer.enable_truncation(max_length=int(metadata["max_seq_length"]))
    pad_token = metadata.get("pad_token", "[PAD]")
    pad_id = metadata.get("pad_token_id")
    if pad_id is None:
        pad_id = tokenizer.token_to_id(pad_token)
    if pad_id is None:
        raise ValueError("Encoder metadata does not identify a tokenizer padding ID")
    tokenizer.enable_padding(length=int(metadata["max_seq_length"]), pad_id=int(pad_id), pad_token=pad_token)
    session = ort.InferenceSession(
        str(encoder_dir / metadata["onnx_model"]),
        providers=["CPUExecutionProvider"],
    )

    started = time.perf_counter()
    vectors = []
    for start in range(0, len(chunks), args.batch_size):
        batch = chunks[start : start + args.batch_size]
        vectors.append(_encode_batch(session, tokenizer, metadata, [str(row["text"]) for row in batch]))
    embeddings = np.concatenate(vectors, axis=0) if vectors else np.empty((0, int(metadata["dimension"])), dtype=np.float32)

    shutil.copy2(encoder_dir / metadata["onnx_model"], output_dir / "model.onnx")
    shutil.copytree(encoder_dir / "tokenizer", output_dir / "tokenizer", dirs_exist_ok=True)
    np.save(output_dir / "embeddings.npy", embeddings)
    chunk_ids = [str(row["chunk_id"]) for row in chunks]
    (output_dir / "chunk_ids.json").write_text(json.dumps(chunk_ids, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result_metadata = {
        **metadata,
        "onnx_model": "model.onnx",
        "embeddings_file": "embeddings.npy",
        "chunk_ids_file": "chunk_ids.json",
        "chunk_count": len(chunks),
        "chunk_store_sha256": _sha256(chunks_path),
        "chunk_ids_sha256": hashlib.sha256("\n".join(chunk_ids).encode("utf-8")).hexdigest(),
        "embedding_sha256": _sha256(output_dir / "embeddings.npy"),
        "materialized_at": datetime.now(timezone.utc).isoformat(),
        "materialization_seconds": round(time.perf_counter() - started, 3),
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(result_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "model_id": result_metadata["model_id"],
                "precision": result_metadata["precision"],
                "dimension": result_metadata["dimension"],
                "chunk_count": len(chunks),
                "embedding_bytes": (output_dir / "embeddings.npy").stat().st_size,
                "wall_clock_seconds": result_metadata["materialization_seconds"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
