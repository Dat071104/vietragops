"""Candidate-only processing and parser policy for lifecycle versions."""

from __future__ import annotations

import json
import io
import time
import warnings as python_warnings
from contextlib import redirect_stderr
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader

from rag.chunking.metadata_builder import CHUNK_CONFIGS, json_dumps
from rag.chunking.section_chunker import chunk_document
from rag.ingestion.markitdown import (
    MARKITDOWN_PARSER_NAME,
    MARKITDOWN_PROVENANCE,
    MARKITDOWN_VERSION,
    LocalMarkItDownAdapter,
    MarkItDownInputError,
)
from rag.lifecycle.extraction import (
    EXTRACTION_SCHEMA,
    EXTRACTION_SCHEMA_VERSION,
    TABLE_COUNT_RULE,
    count_markdown_tables,
    package_version,
    sha256_file,
    sha256_text,
    write_extraction_record,
)
from rag.lifecycle.naming import SOURCE_TYPE_BY_EXTENSION
from rag.lifecycle.storage import write_bytes_atomic
from rag.loaders.docx_loader import load_docx
from rag.loaders.html_loader import load_html
from rag.loaders.markdown_loader import load_markdown_or_text
from rag.loaders.pdf_loader import load_pdf
from rag.preprocessing.section_detector import build_sections


PDF_PARSER_MARKITDOWN = "markitdown"
PDF_PARSER_PYPDF = "pypdf"
SUPPORTED_PDF_PARSERS = {PDF_PARSER_MARKITDOWN, PDF_PARSER_PYPDF}


def normalize_pdf_parser_policy(value: str | None) -> str:
    normalized = (value or PDF_PARSER_MARKITDOWN).strip().casefold()
    if normalized not in SUPPORTED_PDF_PARSERS:
        raise ValueError(f"Unsupported PDF parser policy: {normalized!r}")
    return normalized


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
    canonical_path: Path | None
    extraction_path: Path
    extraction_record: dict


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
    originals_dir: Path | None = None,
    pdf_parser: str = PDF_PARSER_MARKITDOWN,
) -> CandidateResult:
    """Parse one immutable original into isolated candidate artifacts.

    PDF candidates use MarkItDown by default. The only alternate policy is an
    explicit server-owned pypdf fallback; a failed MarkItDown conversion never
    switches parsers. Both successful and failed attempts receive durable
    extraction telemetry under the version's candidate directory.
    """

    extension = extension.casefold()
    candidate_dir = Path(candidate_dir)
    original_path = Path(original_path)
    selected_pdf_parser = normalize_pdf_parser_policy(pdf_parser)
    source_type = SOURCE_TYPE_BY_EXTENSION.get(extension, "text")
    warnings: list[str] = []
    sections: list[dict] = []
    resolved_title = title
    parse_status = "ok"
    canonical_path: Path | None = None
    canonical_text: str | None = None
    parser_name = "legacy_loader"
    parser_version = "builtin"
    parser_provenance = "vietragops"
    parser_policy = "legacy_loader"
    conversion_status = "legacy"
    conversion_duration_ms = 0.0

    try:
        original_sha256 = sha256_file(original_path)
    except (OSError, UnicodeDecodeError):
        original_sha256 = None
        warnings.append("original_checksum_unavailable")

    loaded: dict = {"title": title, "blocks": [], "warnings": []}
    if extension == ".pdf" and not _valid_pdf_structure(original_path):
        parser_name, parser_version, parser_provenance, parser_policy = _pdf_metadata(selected_pdf_parser)
        conversion_status = "failed"
        parse_status = "failed"
        warnings.append("malformed_pdf")
    elif extension == ".docx" and not _valid_docx_structure(original_path):
        parser_name = MARKITDOWN_PARSER_NAME
        parser_version = MARKITDOWN_VERSION
        parser_provenance = MARKITDOWN_PROVENANCE
        parser_policy = "markitdown_docx"
        conversion_status = "failed"
        parse_status = "failed"
        warnings.append("malformed_docx")
    elif extension in {".pdf", ".docx"} and (
        extension == ".docx" or selected_pdf_parser == PDF_PARSER_MARKITDOWN
    ):
        try:
            adapter = LocalMarkItDownAdapter(originals_dir=Path(originals_dir or original_path.parent))
            conversion = adapter.convert(original_path)
            parser_name = conversion.parser_name
            parser_version = conversion.parser_version
            parser_provenance = conversion.parser_provenance
            parser_policy = "markitdown_default" if extension == ".pdf" else "markitdown_docx"
            conversion_status = conversion.status
            conversion_duration_ms = conversion.duration_ms
            warnings.extend(conversion.warnings)
            if conversion.markdown is not None:
                canonical_text = conversion.markdown
                canonical_path = candidate_dir / "canonical.md"
                write_bytes_atomic(canonical_path, canonical_text.encode("utf-8"))
            if conversion.status != "ok":
                parse_status = "failed"
            else:
                loaded = load_markdown_or_text(canonical_path)  # type: ignore[arg-type]
                loaded["title"] = title
        except MarkItDownInputError as exc:
            parser_name = MARKITDOWN_PARSER_NAME
            parser_version = MARKITDOWN_VERSION
            parser_provenance = MARKITDOWN_PROVENANCE
            parser_policy = "markitdown_default" if extension == ".pdf" else "markitdown_docx"
            conversion_status = "failed"
            parse_status = "failed"
            warnings.append(f"adapter_input:{exc.code}")
        except Exception as exc:  # noqa: BLE001 - candidate failure is recorded, never promoted
            parser_name = MARKITDOWN_PARSER_NAME
            parser_version = MARKITDOWN_VERSION
            parser_provenance = MARKITDOWN_PROVENANCE
            parser_policy = "markitdown_default" if extension == ".pdf" else "markitdown_docx"
            conversion_status = "failed"
            parse_status = "failed"
            warnings.append(f"pipeline_exception:{type(exc).__name__}")
    elif extension == ".pdf":
        parser_name = "pypdf"
        parser_version = package_version("pypdf")
        parser_provenance = "application-requirement:pypdf>=4.2"
        parser_policy = "pypdf_explicit_fallback"
        warnings.append("explicit_pypdf_fallback")
        loaded, conversion_duration_ms, load_warning = _load_legacy(load_pdf, original_path)
        warnings.extend(load_warning)
    else:
        loader = pick_loader(extension)
        parser_name = getattr(loader, "__name__", "legacy_loader")
        loaded, conversion_duration_ms, load_warning = _load_legacy(loader, original_path)
        warnings.extend(load_warning)

    if parse_status == "ok":
        resolved_title = loaded.get("title") or title
        warnings.extend(_safe_warnings(loaded.get("warnings", [])))
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
        "source_url": source_url or "",
        "source_type": source_type,
        "sections": sections,
        "parse_status": parse_status,
        "warnings": _unique(warnings),
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
        "parser_name": parser_name,
        "parser_version": parser_version,
        "parser_provenance": parser_provenance,
        "parser_policy": parser_policy,
        "original_path": str(original_path),
        "original_sha256": original_sha256,
        "canonical_path": str(canonical_path) if canonical_path is not None else None,
        "canonical_sha256": sha256_text(canonical_text) if canonical_text is not None else None,
        "character_count": len(canonical_text) if canonical_text is not None else 0,
        "section_count": len(sections),
        "table_count": count_markdown_tables(canonical_text) if canonical_text is not None else 0,
        "table_count_rule": TABLE_COUNT_RULE,
        "conversion_duration_ms": conversion_duration_ms,
        "warnings": _unique(warnings),
    }
    write_extraction_record(extraction_path, extraction_record)

    return CandidateResult(
        parse_status=parse_status,
        warnings=extraction_record["warnings"],
        processed_doc=processed_doc,
        chunks=chunks,
        processed_path=processed_path,
        chunks_path=chunks_path,
        canonical_path=canonical_path,
        extraction_path=extraction_path,
        extraction_record=extraction_record,
    )


def _pdf_metadata(pdf_parser: str) -> tuple[str, str, str, str]:
    if pdf_parser == PDF_PARSER_PYPDF:
        return (
            "pypdf",
            package_version("pypdf"),
            "application-requirement:pypdf>=4.2",
            "pypdf_explicit_fallback",
        )
    return MARKITDOWN_PARSER_NAME, MARKITDOWN_VERSION, MARKITDOWN_PROVENANCE, "markitdown_default"


def _valid_pdf_structure(path: Path) -> bool:
    """Reject header-only or otherwise malformed PDFs before conversion."""
    try:
        with redirect_stderr(io.StringIO()), python_warnings.catch_warnings():
            python_warnings.simplefilter("ignore")
            reader = PdfReader(str(path), strict=False)
            return len(reader.pages) > 0
    except Exception:  # noqa: BLE001 - malformed candidates become failed records
        return False


def _valid_docx_structure(path: Path) -> bool:
    """Reject a ZIP header without the required DOCX package parts."""
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and "word/document.xml" in names and archive.testzip() is None
    except (BadZipFile, OSError, RuntimeError):
        return False


def _load_legacy(loader, path: Path) -> tuple[dict, float, list[str]]:
    started = time.monotonic()
    try:
        loaded = loader(path)
        return loaded, _duration_ms(started), []
    except Exception as exc:  # noqa: BLE001 - preserve the existing failed-candidate contract
        return (
            {"title": path.stem, "blocks": [], "warnings": [f"parser_exception:{type(exc).__name__}"]},
            _duration_ms(started),
            [f"parser_exception:{type(exc).__name__}"],
        )


def _duration_ms(started: float) -> float:
    return round(max(0.0, (time.monotonic() - started) * 1000), 3)


def _safe_warnings(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str)]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
