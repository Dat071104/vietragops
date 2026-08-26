"""Filename normalization and format allowlists for document intake.

Never trust a caller-supplied filename as a filesystem path. This module only
derives a safe identity slug and a validated extension from it; storage paths
are built elsewhere from server-owned identifiers.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

from rag.lifecycle.errors import LifecycleError


ALLOWED_EXTENSIONS = {".pdf", ".html", ".htm", ".docx", ".md", ".txt"}

MIME_BY_EXTENSION: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".html": {"text/html"},
    ".htm": {"text/html"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".md": {"text/markdown", "text/x-markdown"},
    ".txt": {"text/plain"},
}

SOURCE_TYPE_BY_EXTENSION = {
    ".pdf": "pdf",
    ".html": "html",
    ".htm": "html",
    ".docx": "docx",
    ".md": "markdown",
    ".txt": "text",
}

_RESERVED_WINDOWS_STEMS = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

_MAX_FILENAME_BYTES = 200
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(stem: str) -> str:
    normalized = _NON_SLUG_CHARS.sub("-", stem.strip().casefold()).strip("-")
    return normalized[:120]


def normalize_filename(raw_filename: str | None) -> tuple[str, str]:
    """Validate a caller-supplied filename and return (identity_slug, extension).

    Raises LifecycleError deterministically for traversal, separators, empty
    names, reserved/unsafe names, and malformed or unsupported extensions.
    """
    if raw_filename is None:
        raise LifecycleError("empty_filename", "Filename must not be empty.")
    name = raw_filename.strip()
    if not name:
        raise LifecycleError("empty_filename", "Filename must not be empty.")
    if "\x00" in name:
        raise LifecycleError("invalid_filename", "Filename must not contain a null byte.")
    if name in {".", ".."}:
        raise LifecycleError("path_traversal", "Filename must not be '.' or '..'.")
    if "/" in name or "\\" in name:
        raise LifecycleError("path_traversal", "Filename must not contain a path separator.")
    if ":" in name:
        raise LifecycleError("invalid_filename", "Filename must not contain ':'.")
    # A bare basename must be unchanged when parsed as either path convention;
    # this rejects drive letters, UNC-style prefixes, and any residual traversal.
    if PurePosixPath(name).name != name or PureWindowsPath(name).name != name:
        raise LifecycleError("path_traversal", "Filename must be a bare basename.")
    if len(name.encode("utf-8")) > _MAX_FILENAME_BYTES:
        raise LifecycleError("name_too_long", f"Filename must be at most {_MAX_FILENAME_BYTES} bytes.")

    stem, dot, ext = name.rpartition(".")
    if not dot or not stem.strip():
        raise LifecycleError("missing_extension", "Filename must include a supported extension.")

    extension = "." + ext.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise LifecycleError(
            "unsupported_extension",
            f"Extension '{extension}' is not supported. Allowed: {sorted(ALLOWED_EXTENSIONS)}.",
        )

    if stem.strip(" .").casefold() in _RESERVED_WINDOWS_STEMS:
        raise LifecycleError("reserved_name", f"Filename stem '{stem}' is a reserved device name.")

    slug = slugify(stem)
    if not slug:
        raise LifecycleError("invalid_filename", "Filename has no usable identity characters.")

    return slug, extension


def validate_content_type(content_type: str | None, extension: str) -> None:
    allowed = MIME_BY_EXTENSION[extension]
    declared = (content_type or "").split(";", 1)[0].strip().casefold()
    if declared not in allowed:
        raise LifecycleError(
            "unsupported_content_type",
            f"Content-Type '{content_type}' is not allowed for extension '{extension}'.",
        )


def validate_format(extension: str, content: bytes) -> None:
    """Cheap deterministic magic-byte / decode check per allowed extension."""
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise LifecycleError("format_validation_failed", "File does not start with a PDF header.")
        return
    if extension == ".docx":
        if not content.startswith(b"PK\x03\x04"):
            raise LifecycleError("format_validation_failed", "File is not a valid DOCX (zip) container.")
        return
    # .html, .htm, .md, .txt: must be null-free, decodable UTF-8 text.
    if b"\x00" in content:
        raise LifecycleError("format_validation_failed", "Text file must not contain a null byte.")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LifecycleError("format_validation_failed", f"File is not valid UTF-8 text: {exc}") from exc
