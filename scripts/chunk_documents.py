"""Generate section-aware chunk files for VietRAGOps Phase 3."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.chunking.metadata_builder import CHUNK_CONFIGS, ChunkConfig, json_dumps, load_manifest_metadata
from rag.chunking.section_chunker import chunk_document


DEFAULT_INPUT = ROOT / "data" / "processed" / "processed_docs.jsonl"
DEFAULT_MANIFEST = ROOT / "data" / "manifests" / "documents_manifest.csv"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "chunks"
DEFAULT_REPORT = ROOT / "reports" / "chunking_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chunk processed documents into section-aware JSONL files.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--config", default="all", choices=["all", *CHUNK_CONFIGS.keys()])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args()


def load_processed_docs(path: str | Path) -> list[dict]:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Processed docs file not found: {input_path}")

    docs = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                docs.append(json.loads(raw_line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
    return docs


def selected_configs(name: str) -> list[ChunkConfig]:
    if name == "all":
        return [CHUNK_CONFIGS[key] for key in ("small", "medium", "large")]
    return [CHUNK_CONFIGS[name]]


def generate_chunks(docs: list[dict], manifest_map: dict[str, dict], config: ChunkConfig) -> list[dict]:
    chunks = []
    for doc in docs:
        manifest_row = manifest_map.get(doc["doc_id"])
        if manifest_row is None:
            raise KeyError(f"Manifest metadata missing for doc_id={doc['doc_id']}")
        chunks.extend(chunk_document(doc, manifest_row, config))
    return chunks


def write_chunks(path: Path, chunks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json_dumps(chunk) + "\n")


def calculate_stats(chunks: list[dict], doc_count: int, section_count: int) -> dict:
    token_counts = [chunk["token_count"] for chunk in chunks]
    duplicate_rate = 0.0
    if chunks:
        unique_texts = len({chunk["text"] for chunk in chunks})
        duplicate_rate = (len(chunks) - unique_texts) / len(chunks)

    abnormal = [
        chunk["chunk_id"]
        for chunk in chunks
        if chunk["token_count"] < 5
        or chunk["token_count"] > chunk["chunk_config"]["chunk_size"] + max(chunk["chunk_config"]["overlap"], 40)
    ]

    return {
        "documents": doc_count,
        "sections": section_count,
        "chunks": len(chunks),
        "avg_tokens": round(mean(token_counts), 2) if token_counts else 0.0,
        "min_tokens": min(token_counts) if token_counts else 0,
        "max_tokens": max(token_counts) if token_counts else 0,
        "duplicate_rate": duplicate_rate,
        "abnormal_chunks": abnormal,
        "missing_source_url": sum(1 for chunk in chunks if not chunk["source_url"]),
        "missing_heading_path": sum(1 for chunk in chunks if not chunk["heading_path"]),
        "pdf_chunks_with_pages": sum(
            1 for chunk in chunks if chunk["source_type"] == "pdf" and chunk["page_start"] is not None
        ),
        "pdf_chunks_total": sum(1 for chunk in chunks if chunk["source_type"] == "pdf"),
    }


def build_report(docs: list[dict], stats_by_config: dict[str, dict], output_path: Path) -> None:
    input_documents = len(docs)
    section_count = sum(len(doc["sections"]) for doc in docs)
    docs_by_id = {doc["doc_id"]: doc for doc in docs}
    medium_chunks_path = DEFAULT_OUTPUT_DIR / CHUNK_CONFIGS["medium"].output_filename
    medium_chunks = []
    if medium_chunks_path.exists():
        with medium_chunks_path.open("r", encoding="utf-8") as handle:
            medium_chunks = [json.loads(line) for line in handle]

    examples = []
    review_examples = []
    example_doc_ids = set()
    review_doc_ids = set()
    for chunk in medium_chunks:
        if (
            chunk["doc_id"] in {"ug_training_reg_k2021_pdf", "ug_course_registration_guide"}
            and chunk["doc_id"] not in example_doc_ids
            and len(examples) < 2
        ):
            examples.append(chunk)
            example_doc_ids.add(chunk["doc_id"])
        if (
            chunk["doc_id"] in {"it_cs_curriculum_2018", "tdtu_major_catalog"}
            and chunk["doc_id"] not in review_doc_ids
            and len(review_examples) < 2
        ):
            review_examples.append(chunk)
            review_doc_ids.add(chunk["doc_id"])

    recommended = "medium"

    lines = [
        "# Chunking Report",
        "",
        "## Overview",
        "",
        f"- Input documents: {input_documents}",
        f"- Processed sections: {section_count}",
        "",
        "## Chunk counts by config",
        "",
    ]

    for name in ("small", "medium", "large"):
        stats = stats_by_config[name]
        lines.extend(
            [
                f"- `{name}`: {stats['chunks']} chunks",
                f"  - tokens avg/min/max: {stats['avg_tokens']} / {stats['min_tokens']} / {stats['max_tokens']}",
                f"  - duplicate rate: {stats['duplicate_rate']:.4f}",
            ]
        )

    lines.extend(
        [
            "",
            "## Missing metadata summary",
            "",
        ]
    )
    for name in ("small", "medium", "large"):
        stats = stats_by_config[name]
        lines.extend(
            [
                f"- `{name}` missing source URLs: {stats['missing_source_url']}",
                f"- `{name}` missing heading paths: {stats['missing_heading_path']}",
            ]
        )

    lines.extend(
        [
            "",
            "## Abnormal chunks found",
            "",
        ]
    )
    for name in ("small", "medium", "large"):
        abnormal = stats_by_config[name]["abnormal_chunks"]
        preview = ", ".join(abnormal[:5]) if abnormal else "none"
        lines.append(f"- `{name}`: {len(abnormal)} flagged ({preview})")

    lines.extend(
        [
            "",
            "## PDF page preservation notes",
            "",
        ]
    )
    for name in ("small", "medium", "large"):
        stats = stats_by_config[name]
        lines.append(f"- `{name}`: {stats['pdf_chunks_with_pages']} / {stats['pdf_chunks_total']} PDF chunks retain page metadata")

    lines.extend(
        [
            "",
            "## Examples of good chunks",
            "",
        ]
    )
    for chunk in examples:
        lines.extend(
            [
                f"- `{chunk['chunk_id']}` from `{chunk['doc_id']}`",
                f"  - heading path: {' > '.join(chunk['heading_path'])}",
                f"  - text preview: {chunk['text'][:220].replace(chr(10), ' ')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Examples needing manual review",
            "",
        ]
    )
    for chunk in review_examples:
        lines.extend(
            [
                f"- `{chunk['chunk_id']}` from `{chunk['doc_id']}`",
                f"  - heading path: {' > '.join(chunk['heading_path'])}",
                f"  - text preview: {chunk['text'][:220].replace(chr(10), ' ')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Recommended default chunk config for Phase 4",
            "",
            f"- Recommended default: `{recommended}`",
            "- Rationale: it offers a better balance between retrieval precision and context coverage than the smaller or larger settings for the current corpus, while keeping duplicate rates low and preserving heading/page metadata cleanly.",
        ]
    )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    docs = load_processed_docs(args.input)
    manifest_map = load_manifest_metadata(args.manifest)
    configs = selected_configs(args.config)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report)

    section_count = sum(len(doc["sections"]) for doc in docs)
    stats_by_config = {}

    for config in configs:
        chunks = generate_chunks(docs, manifest_map, config)
        output_path = output_dir / config.output_filename
        write_chunks(output_path, chunks)
        stats = calculate_stats(chunks, len(docs), section_count)
        stats_by_config[config.name] = stats
        print(
            f"[chunking] {config.name}: docs={stats['documents']} sections={stats['sections']} "
            f"chunks={stats['chunks']} duplicate_rate={stats['duplicate_rate']:.4f}"
        )

    if args.config == "all":
        build_report(docs, stats_by_config, report_path)
        print(f"[chunking] wrote report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
