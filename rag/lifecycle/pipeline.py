"""Candidate-only processing: immutable original -> parse -> candidate chunks.

Reuses the same loaders/section-detector/chunker that
`scripts/run_phase2_processing.py` and `scripts/chunk_documents.py` already
use for the live corpus. Writes only under the caller-supplied candidate
directory; never touches a live manifest or chunk file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag.chunking.metadata_builder import CHUNK_CONFIGS, json_dumps
from rag.chunking.section_chunker import chunk_document
from rag.lifecycle.naming import SOURCE_TYPE_BY_EXTENSION
from rag.lifecycle.storage import write_bytes_atomic
from rag.loaders.docx_loader import load_docx
from rag.loaders.html_loader import load_html
from rag.loaders.markdown_loader import load_markdown_or_text
from rag.loaders.pdf_loader import load_pdf
from rag.preprocessing.section_detector import build_sections


def pick_loader(extension: str):
    ext = extension.casefold()
    if ext in {".html", ".htm"}:
        return load_html
    if ext == ".pdf":
        return load_pdf
    if ext == ".docx":
        return load_docx
    return load_markdown_or_text


@dataclass(frozen=True)
class CandidateResult:
    parse_status: str
    warnings: list[str]
    processed_doc: dict
    chunks: list[dict]
    processed_path: Path
    chunks_path: Path


def process_candidate(
    *,
    document_id: str,
    version_id: str,
    original_path: Path,
    extension: str,
    title: str,
    source_url: str | None,
    domain: str | None,
    authority_level: str | None,
    candidate_dir: Path,
) -> CandidateResult:
    """Parse the immutable original and build candidate chunks.

    Safe to call more than once for the same version (e.g. to retry a failed
    parse): it only reads `original_path` and overwrites files under
    `candidate_dir` atomically. It never raises on a parser failure -- it
    records `parse_status="failed"` instead, so a bad input cannot corrupt the
    original artifact or leave the caller's transaction half-done.
    """
    loader = pick_loader(extension)
    source_type = SOURCE_TYPE_BY_EXTENSION.get(extension.casefold(), "text")
    warnings: list[str] = []
    parse_status = "ok"
    sections: list[dict] = []
    resolved_title = title

    try:
        loaded = loader(original_path)
        resolved_title = loaded.get("title") or title
        warnings.extend(loaded.get("warnings", []))
        sections = build_sections(loaded.get("blocks", []), document_id, resolved_title)
        if not sections:
            parse_status = "failed"
            warnings.append("no_sections_built")
    except Exception as exc:  # noqa: BLE001 - a bad candidate file must never crash intake
        parse_status = "failed"
        warnings.append(f"parser_exception:{exc}")

    processed_doc = {
        "doc_id": document_id,
        "version_id": version_id,
        "title": resolved_title,
        "source_url": source_url or "",
        "source_type": source_type,
        "sections": sections,
        "parse_status": parse_status,
        "warnings": warnings,
    }

    chunks: list[dict] = []
    if parse_status == "ok":
        manifest_row = {
            "title": resolved_title,
            "source_url": source_url or "",
            "source_type": source_type,
            "domain": domain or "unknown",
            "authority_level": authority_level or "unknown",
        }
        chunks = chunk_document(
            {"doc_id": document_id, "sections": sections}, manifest_row, CHUNK_CONFIGS["medium"]
        )

    processed_path = candidate_dir / "processed.jsonl"
    chunks_path = candidate_dir / "chunks_500.jsonl"
    write_bytes_atomic(processed_path, (json_dumps(processed_doc) + "\n").encode("utf-8"))
    chunk_lines = "".join(json_dumps(chunk) + "\n" for chunk in chunks)
    write_bytes_atomic(chunks_path, chunk_lines.encode("utf-8"))

    return CandidateResult(
        parse_status=parse_status,
        warnings=warnings,
        processed_doc=processed_doc,
        chunks=chunks,
        processed_path=processed_path,
        chunks_path=chunks_path,
    )
