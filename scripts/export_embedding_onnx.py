"""Offline-only export of a SentenceTransformer encoder to ONNX.

This script is intentionally outside ``app/`` and ``rag/``.  It may use torch
and sentence-transformers in a local export environment; neither dependency is
part of the product runtime.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a SentenceTransformer encoder to ONNX.")
    parser.add_argument("--model", required=True, help="Hugging Face model identity.")
    parser.add_argument("--output-dir", required=True, help="Directory receiving fp32/int8 artifacts.")
    parser.add_argument("--revision", default=None, help="Optional immutable model revision.")
    parser.add_argument("--query-prefix", default="")
    parser.add_argument("--passage-prefix", default="")
    parser.add_argument("--quantize", action="store_true", help="Also create a dynamic-weight-int8 artifact.")
    return parser.parse_args(argv)


def _load_sentence_transformer(model_id: str, revision: str | None):
    from sentence_transformers import SentenceTransformer

    kwargs: dict[str, Any] = {"device": "cpu", "trust_remote_code": False}
    if revision:
        kwargs["revision"] = revision
    return SentenceTransformer(model_id, **kwargs)


def _export_fp32(model: Any, output_path: Path, max_seq_length: int) -> None:
    import torch

    transformer = model[0]
    pooling = model[1]
    is_mean_pooling = getattr(pooling, "pooling_mode", None) == "mean" or bool(
        getattr(pooling, "pooling_mode_mean_tokens", False)
    )
    if not is_mean_pooling:
        raise RuntimeError("Only mean-pooling SentenceTransformer models are supported by this exporter.")
    encoder = transformer.auto_model

    class EncoderWrapper(torch.nn.Module):
        def __init__(self, wrapped: Any) -> None:
            super().__init__()
            self.wrapped = wrapped

        def forward(self, input_ids: Any, attention_mask: Any) -> Any:
            output = self.wrapped(input_ids=input_ids, attention_mask=attention_mask)
            return output.last_hidden_state if hasattr(output, "last_hidden_state") else output[0]

    wrapper = EncoderWrapper(encoder).eval()
    sample_ids = torch.ones((1, max_seq_length), dtype=torch.long)
    sample_mask = torch.ones((1, max_seq_length), dtype=torch.long)
    with torch.no_grad():
        torch.onnx.export(
            wrapper,
            (sample_ids, sample_mask),
            str(output_path),
            input_names=["input_ids", "attention_mask"],
            output_names=["last_hidden_state"],
            dynamic_axes={
                "input_ids": {0: "batch", 1: "sequence"},
                "attention_mask": {0: "batch", 1: "sequence"},
                "last_hidden_state": {0: "batch", 1: "sequence"},
            },
            opset_version=17,
            do_constant_folding=True,
            dynamo=False,
        )


def _save_tokenizer(model: Any, output_dir: Path) -> dict[str, Any]:
    tokenizer_dir = output_dir / "tokenizer"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)
    model.tokenizer.save_pretrained(str(tokenizer_dir))
    return {
        "pad_token": model.tokenizer.pad_token,
        "pad_token_id": model.tokenizer.pad_token_id,
        "tokenizer_file": "tokenizer/tokenizer.json",
    }


def _write_metadata(
    output_dir: Path,
    *,
    args: argparse.Namespace,
    model: Any,
    precision: str,
    model_file: str,
    tokenizer_metadata: dict[str, Any],
) -> dict[str, Any]:
    metadata = {
        "schema_version": 1,
        "model_id": args.model,
        "model_revision": args.revision,
        "dimension": int(
            model.get_embedding_dimension()
            if hasattr(model, "get_embedding_dimension")
            else model.get_sentence_embedding_dimension()
        ),
        "max_seq_length": int(model.max_seq_length),
        "pooling": "mean",
        "normalized": True,
        "normalization": "l2",
        "query_prefix": args.query_prefix,
        "passage_prefix": args.passage_prefix,
        "precision": precision,
        "onnx_model": model_file,
        **tokenizer_metadata,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def _quantize(fp32_path: Path, int8_path: Path) -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(
        model_input=str(fp32_path),
        model_output=str(int8_path),
        weight_type=QuantType.QInt8,
        per_channel=True,
        reduce_range=False,
    )


def _size(path: Path) -> int:
    return path.stat().st_size


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    started = time.perf_counter()
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    model = _load_sentence_transformer(args.model, args.revision)
    max_seq_length = int(model.max_seq_length)

    fp32_dir = output_root / "fp32"
    fp32_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_metadata = _save_tokenizer(model, fp32_dir)
    fp32_path = fp32_dir / "model.onnx"
    _export_fp32(model, fp32_path, max_seq_length)
    fp32_metadata = _write_metadata(
        fp32_dir,
        args=args,
        model=model,
        precision="fp32",
        model_file=fp32_path.name,
        tokenizer_metadata=tokenizer_metadata,
    )

    result: dict[str, Any] = {
        "model_id": args.model,
        "dimension": fp32_metadata["dimension"],
        "max_seq_length": max_seq_length,
        "export_wall_clock_seconds": None,
        "fp32": {"directory": str(fp32_dir), "model_bytes": _size(fp32_path)},
    }
    if args.quantize:
        int8_dir = output_root / "int8"
        int8_dir.mkdir(parents=True, exist_ok=True)
        tokenizer_metadata = _save_tokenizer(model, int8_dir)
        int8_path = int8_dir / "model.onnx"
        _quantize(fp32_path, int8_path)
        _write_metadata(
            int8_dir,
            args=args,
            model=model,
            precision="int8_dynamic_weight",
            model_file=int8_path.name,
            tokenizer_metadata=tokenizer_metadata,
        )
        result["int8"] = {"directory": str(int8_dir), "model_bytes": _size(int8_path)}
    result["export_wall_clock_seconds"] = round(time.perf_counter() - started, 3)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
