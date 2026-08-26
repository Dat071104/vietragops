"""Candidate-only processing for Firecrawl-sourced web Markdown.

Reuses the existing Markdown loader, section builder, and chunker -- the
same ones ``rag/lifecycle/pipeline.py`` uses for local Markdown originals --
and produces an extraction record in the exact same schema so the existing
``LifecycleService.review``/``publish``/``rollback`` integrity checks
(``rag/lifecycle/extraction.py::validate_candidate_artifacts``) accept it
without any change to that shared code path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag.chunking.metadata_builder import CHUNK_CONFIGS, json_dumps
from rag.chunking.section_chunker import chunk_document
from rag.lifecycle.extraction import (
    EXTRACTION_SCHEMA,
    EXTRACTION_SCHEMA_VERSION,
    TABLE_COUNT_RULE,
    count_markdown_tables,
    sha256_file,
    sha256_text,
    write_extraction_record,
)
from rag.lifecycle.storage import write_bytes_atomic
from rag.loaders.markdown_loader import load_markdown_or_text
from rag.preprocessing.section_detector import build_sections


WEB_PARSER_NAME = "firecrawl"
WEB_PARSER_POLICY = "firecrawl_scrape_markdown_v2"


def normalize_web_markdown(raw_markdown: str) -> str:
    """Deterministic canonical-Markdown normalization for web content.

    Line-ending normalization and trailing-whitespace trimming only; no
    content rewriting, so recrawl checksums stay meaningful across
    whitespace-insignificant re-fetches of unchanged pages.
    """

    normalized = raw_markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    text = "\n".join(lines).strip()
    return f"{text}\n" if text else ""


@dataclass(frozen=True)
class WebCandidateResult:
    parse_status: str
    warnings: list[str]
    processed_doc: dict
    chunks: list[dict]
    processed_path: Path
    chunks_path: Path
    raw_original_path: Path
    original_sha256: str
    canonical_path: Path
    canonical_sha256: str
    extraction_path: Path
    extraction_record: dict


def process_web_candidate(
    *,
    document_id: str,
    version_id: str,
    canonical_url: str,
    raw_markdown: str,
    title: str,
    domain: str,
    parser_provenance: str,
    candidate_dir: Path,
    originals_dir: Path,
    adapter_version: str,
) -> WebCandidateResult:
    candidate_dir = Path(candidate_dir)
    originals_dir = Path(originals_dir)
    warnings: list[str] = []

    raw_original_path = originals_dir / f"{version_id}.md"
    write_bytes_atomic(raw_original_path, raw_markdown.encode("utf-8"))
    original_sha256 = sha256_file(raw_original_path)

    canonical_text = normalize_web_markdown(raw_markdown)
    canonical_path = candidate_dir / "canonical.md"
    write_bytes_atomic(canonical_path, canonical_text.encode("utf-8"))
    canonical_sha256 = sha256_text(canonical_text)

    parse_status = "ok"
    conversion_status = "ok"
    sections: list[dict] = []
    resolved_title = title
    if not canonical_text.strip():
        parse_status = "failed"
        conversion_status = "empty"
        warnings.append("empty_markdown")
    else:
        loaded = load_markdown_or_text(canonical_path)
        loaded["title"] = title
        resolved_title = loaded.get("title") or title
        warnings.extend(item for item in loaded.get("warnings", []) if isinstance(item, str))
        try:
            sections = build_sections(loaded.get("blocks", []), document_id, resolved_title)
        except Exception as exc:  # noqa: BLE001 - malformed candidate remains unreviewable
            parse_status = "failed"
            warnings.append(f"section_builder_exception:{type(exc).__name__}")
        if not sections and parse_status == "ok":
            parse_status = "failed"
            warnings.append("no_sections_built")

    processed_doc = {
        "doc_id": document_id,
        "version_id": version_id,
        "title": resolved_title,
        "source_url": canonical_url,
        "source_type": "web",
        "sections": sections,
        "parse_status": parse_status,
        "warnings": _unique(warnings),
    }

    chunks: list[dict] = []
    if parse_status == "ok":
        manifest_row = {
            "title": resolved_title,
            "source_url": canonical_url,
            "source_type": "web",
            "domain": domain,
            "authority_level": "unknown",
        }
        chunks = chunk_document(
            {"doc_id": document_id, "sections": sections}, manifest_row, CHUNK_CONFIGS["medium"]
        )
        if not chunks:
            parse_status = "failed"
            warnings.append("no_chunks_built")
            processed_doc["parse_status"] = parse_status
            processed_doc["warnings"] = _unique(warnings)

    processed_path = candidate_dir / "processed.jsonl"
    chunks_path = candidate_dir / "chunks_500.jsonl"
    extraction_path = candidate_dir / "extraction.json"
    write_bytes_atomic(processed_path, (json_dumps(processed_doc) + "\n").encode("utf-8"))
    chunk_lines = "".join(json_dumps(chunk) + "\n" for chunk in chunks)
    write_bytes_atomic(chunks_path, chunk_lines.encode("utf-8"))

    extraction_record = {
        "schema": EXTRACTION_SCHEMA,
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "document_id": document_id,
        "version_id": version_id,
        "parse_status": parse_status,
        "conversion_status": conversion_status,
        "parser_name": WEB_PARSER_NAME,
        "parser_version": adapter_version,
        "parser_provenance": parser_provenance,
        "parser_policy": WEB_PARSER_POLICY,
        "original_path": str(raw_original_path),
        "original_sha256": original_sha256,
        "canonical_path": str(canonical_path),
        "canonical_sha256": canonical_sha256,
        "character_count": len(canonical_text),
        "section_count": len(sections),
        "table_count": count_markdown_tables(canonical_text),
        "table_count_rule": TABLE_COUNT_RULE,
        "conversion_duration_ms": 0.0,
        "warnings": _unique(warnings),
    }
    write_extraction_record(extraction_path, extraction_record)

    return WebCandidateResult(
        parse_status=parse_status,
        warnings=extraction_record["warnings"],
        processed_doc=processed_doc,
        chunks=chunks,
        processed_path=processed_path,
        chunks_path=chunks_path,
        raw_original_path=raw_original_path,
        original_sha256=original_sha256,
        canonical_path=canonical_path,
        canonical_sha256=canonical_sha256,
        extraction_path=extraction_path,
        extraction_record=extraction_record,
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
