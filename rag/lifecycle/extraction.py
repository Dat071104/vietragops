"""Checksums, telemetry, and restart-time validation for candidate extraction."""

from __future__ import annotations

import hashlib
import json
import re
from importlib import metadata
from pathlib import Path
from typing import Any

from rag.lifecycle.storage import write_bytes_atomic


EXTRACTION_SCHEMA = "vietragops.candidate_extraction"
EXTRACTION_SCHEMA_VERSION = 1
TABLE_COUNT_RULE = (
    "Count one table for each Markdown table separator row that follows a row containing '|'; "
    "one separator row equals one table block."
)
_TABLE_SEPARATOR = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def package_version(package_name: str, fallback: str = "unknown") -> str:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return fallback


def count_markdown_tables(markdown: str) -> int:
    lines = markdown.splitlines()
    return sum(
        1
        for index, line in enumerate(lines)
        if index > 0 and "|" in lines[index - 1] and _TABLE_SEPARATOR.match(line)
    )


def write_extraction_record(path: Path, record: dict[str, Any]) -> None:
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    write_bytes_atomic(Path(path), serialized.encode("utf-8"))


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def validate_candidate_artifacts(version: Any) -> tuple[str, ...]:
    """Return stable warnings when a supposedly successful candidate is unusable."""

    issues: list[str] = []
    extraction_path = _path_or_none(getattr(version, "candidate_extraction_path", None))
    if extraction_path is None:
        return ("missing_extraction_record",)
    record = read_json_object(extraction_path)
    if record is None:
        return ("corrupt_extraction_record",)

    expected_pairs = {
        "document_id": getattr(version, "document_id", None),
        "version_id": getattr(version, "version_id", None),
        "original_path": str(getattr(version, "original_path", "")),
        "original_sha256": getattr(version, "checksum", None),
    }
    for key, expected in expected_pairs.items():
        if record.get(key) != expected:
            issues.append(f"extraction_{key}_mismatch")

    if record.get("schema") != EXTRACTION_SCHEMA or record.get("schema_version") != EXTRACTION_SCHEMA_VERSION:
        issues.append("extraction_schema_invalid")
    if record.get("parse_status") != "ok":
        issues.append("extraction_parse_failed")
    if record.get("conversion_status") not in {"ok", "legacy"}:
        issues.append("extraction_conversion_failed")
    if not isinstance(record.get("parser_name"), str) or not record["parser_name"]:
        issues.append("extraction_parser_missing")
    if not isinstance(record.get("parser_version"), str) or not record["parser_version"]:
        issues.append("extraction_parser_version_missing")
    if not isinstance(record.get("warnings"), list) or not all(
        isinstance(item, str) for item in record["warnings"]
    ):
        issues.append("extraction_warnings_invalid")

    original_path = _path_or_none(getattr(version, "original_path", None))
    if original_path is None or not original_path.is_file():
        issues.append("original_missing")
    else:
        try:
            if sha256_file(original_path) != getattr(version, "checksum", None):
                issues.append("original_checksum_mismatch")
        except OSError:
            issues.append("original_unreadable")

    canonical_path = _path_or_none(getattr(version, "candidate_canonical_path", None))
    record_canonical_path = _path_or_none(record.get("canonical_path"))
    if canonical_path is None:
        if record_canonical_path is not None:
            issues.append("canonical_registry_path_missing")
    elif record_canonical_path is None or _same_path(record_canonical_path, canonical_path) is False:
        issues.append("canonical_path_mismatch")
    elif not canonical_path.is_file():
        issues.append("canonical_missing")
    else:
        try:
            canonical_text = canonical_path.read_text(encoding="utf-8")
            expected_checksum = record.get("canonical_sha256")
            if not isinstance(expected_checksum, str) or sha256_text(canonical_text) != expected_checksum:
                issues.append("canonical_checksum_mismatch")
            if record.get("character_count") != len(canonical_text):
                issues.append("canonical_character_count_mismatch")
            if record.get("table_count") != count_markdown_tables(canonical_text):
                issues.append("canonical_table_count_mismatch")
        except (OSError, UnicodeDecodeError):
            issues.append("canonical_unreadable")

    _validate_nonnegative_number(record, "conversion_duration_ms", issues)
    _validate_nonnegative_integer(record, "section_count", issues)
    _validate_nonnegative_integer(record, "table_count", issues)
    if record.get("section_count", 0) == 0:
        issues.append("no_sections_built")

    chunks_path = _path_or_none(getattr(version, "candidate_chunks_path", None))
    if chunks_path is None or not chunks_path.is_file():
        issues.append("candidate_chunks_missing")
    else:
        try:
            lines = [line for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                issues.append("candidate_chunks_empty")
            for line in lines:
                chunk = json.loads(line)
                if not isinstance(chunk, dict) or chunk.get("doc_id") != getattr(version, "document_id", None):
                    issues.append("candidate_chunk_invalid")
                    break
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            issues.append("candidate_chunks_corrupt")

    processed_path = _path_or_none(getattr(version, "candidate_processed_path", None))
    processed = read_json_object(processed_path) if processed_path is not None and processed_path.is_file() else None
    if processed is None:
        issues.append("candidate_processed_corrupt")
    else:
        if processed.get("doc_id") != getattr(version, "document_id", None):
            issues.append("processed_document_id_mismatch")
        if processed.get("version_id") != getattr(version, "version_id", None):
            issues.append("processed_version_id_mismatch")
        if processed.get("parse_status") != "ok":
            issues.append("processed_parse_failed")

    return tuple(dict.fromkeys(issues))


def _path_or_none(value: object) -> Path | None:
    if not isinstance(value, (str, Path)) or not str(value):
        return None
    return Path(value)


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=False) == right.resolve(strict=False)
    except (OSError, RuntimeError):
        return False


def _validate_nonnegative_number(record: dict[str, Any], key: str, issues: list[str]) -> None:
    value = record.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        issues.append(f"{key}_invalid")


def _validate_nonnegative_integer(record: dict[str, Any], key: str, issues: list[str]) -> None:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        issues.append(f"{key}_invalid")
