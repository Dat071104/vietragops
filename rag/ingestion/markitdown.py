"""Small, local-only MarkItDown boundary for validated candidate originals.

The adapter deliberately exposes neither URLs nor arbitrary path strings. A
path is accepted only after it resolves to a regular file below the configured
lifecycle originals directory. A stream is accepted only when its ``name``
points to that same server-owned original. The adapter itself never writes;
the lifecycle pipeline owns atomic candidate-artifact writes.
"""

from __future__ import annotations

import importlib.metadata
import io
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Literal

from markitdown import MarkItDown, StreamInfo


MARKITDOWN_PARSER_NAME = "markitdown"
MARKITDOWN_VERSION = "0.1.7"
MARKITDOWN_SOURCE_REVISION = "9dc0d6579b8739c9d0671ff205e071e3053c7df1"
MARKITDOWN_PROVENANCE = f"{MARKITDOWN_PARSER_NAME}@{MARKITDOWN_SOURCE_REVISION}"

_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
_MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_URI_PREFIX = re.compile(r"^(?:file|https?|data):", re.IGNORECASE)

ConversionStatus = Literal["ok", "failed", "empty"]


class MarkItDownInputError(ValueError):
    """Stable rejection for an untrusted source or invalid adapter setup."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class MarkItDownConversion:
    """Conversion result with safe telemetry for the lifecycle pipeline."""

    status: ConversionStatus
    markdown: str | None
    parser_name: str
    parser_version: str
    parser_provenance: str
    duration_ms: float
    warnings: tuple[str, ...] = ()
    error_code: str | None = None

    @property
    def usable(self) -> bool:
        return self.status == "ok" and bool(self.markdown)


class LocalMarkItDownAdapter:
    """Convert only server-owned PDF/DOCX originals through local MarkItDown."""

    def __init__(
        self,
        *,
        originals_dir: Path,
        converter_factory: Callable[..., Any] = MarkItDown,
    ) -> None:
        self._originals_dir = Path(originals_dir)
        self._converter_factory = converter_factory
        try:
            installed_version = importlib.metadata.version("markitdown")
        except importlib.metadata.PackageNotFoundError as exc:
            raise MarkItDownInputError("markitdown_not_installed", "MarkItDown is not installed.") from exc
        if installed_version != MARKITDOWN_VERSION:
            raise MarkItDownInputError(
                "markitdown_version_mismatch",
                f"Expected MarkItDown {MARKITDOWN_VERSION}; found {installed_version}.",
            )
        self._parser_version = installed_version
        self._converter: Any | None = None

    @property
    def parser_name(self) -> str:
        return MARKITDOWN_PARSER_NAME

    @property
    def parser_version(self) -> str:
        return self._parser_version

    @property
    def parser_provenance(self) -> str:
        return MARKITDOWN_PROVENANCE

    def convert(self, source: Path | BinaryIO, *, extension: str | None = None) -> MarkItDownConversion:
        """Convert a validated original using only MarkItDown local/stream APIs.

        ``source`` is intentionally not ``str | PathLike``: caller path strings,
        URI strings, responses, and arbitrary file-like buffers are rejected
        before MarkItDown can inspect them.
        """

        if isinstance(source, str):
            code = "uri_input_rejected" if _looks_like_uri(source) else "path_string_rejected"
            raise MarkItDownInputError(code, "MarkItDown input must be a server-owned Path or original stream.")
        if isinstance(source, Path):
            if _looks_like_uri(source.as_posix()):
                raise MarkItDownInputError("uri_input_rejected", "URI input is not allowed.")
            verified_path = self._verify_original_path(source)
            selected_extension = self._validate_extension(extension or verified_path.suffix)
            if extension is not None and selected_extension != verified_path.suffix.casefold():
                raise MarkItDownInputError("extension_mismatch", "Original extension does not match the server policy.")
            return self._convert_local(verified_path)
        if _is_binary_stream(source):
            origin_path = self._stream_origin_path(source)
            verified_path = self._verify_original_path(origin_path)
            selected_extension = self._validate_extension(extension or verified_path.suffix)
            if extension is not None and selected_extension != verified_path.suffix.casefold():
                raise MarkItDownInputError("extension_mismatch", "Original extension does not match the server policy.")
            return self._convert_stream(source, selected_extension)
        raise MarkItDownInputError("source_type_rejected", "Unsupported MarkItDown input type.")

    def _verify_original_path(self, source: Path) -> Path:
        if not source.is_absolute():
            raise MarkItDownInputError("path_not_absolute", "Original path must be absolute.")
        try:
            originals_root = self._originals_dir.resolve(strict=True)
        except (FileNotFoundError, OSError, RuntimeError) as exc:
            raise MarkItDownInputError("originals_root_invalid", "Lifecycle originals directory is unavailable.") from exc
        if not originals_root.is_dir():
            raise MarkItDownInputError("originals_root_invalid", "Lifecycle originals directory is not a directory.")

        # Reject the final file and every existing ancestor symlink before
        # resolving. A resolved path check alone would allow a symlink that
        # happens to point back inside the originals root.
        for ancestor in (source, *source.parents):
            if ancestor == originals_root:
                break
            try:
                if ancestor.is_symlink():
                    raise MarkItDownInputError("symlink_rejected", "Symlink originals are not allowed.")
            except OSError as exc:
                raise MarkItDownInputError("original_path_unreadable", "Original path cannot be inspected.") from exc

        try:
            resolved = source.resolve(strict=True)
        except FileNotFoundError as exc:
            raise MarkItDownInputError("original_not_found", "Server-owned original does not exist.") from exc
        except (OSError, RuntimeError) as exc:
            raise MarkItDownInputError("original_path_unreadable", "Original path cannot be resolved.") from exc

        try:
            resolved.relative_to(originals_root)
        except ValueError as exc:
            raise MarkItDownInputError("path_outside_originals", "Original path is outside lifecycle originals.") from exc
        if not resolved.is_file():
            raise MarkItDownInputError("original_not_regular_file", "Original must be a regular file.")
        return resolved

    @staticmethod
    def _validate_extension(extension: str) -> str:
        normalized = (extension or "").casefold()
        if normalized not in _SUPPORTED_EXTENSIONS:
            raise MarkItDownInputError("unsupported_extension", "Only validated PDF and DOCX originals are enabled.")
        return normalized

    def _stream_origin_path(self, source: BinaryIO) -> Path:
        raw_name = getattr(source, "name", None)
        if isinstance(raw_name, int) or not isinstance(raw_name, (str, Path)):
            raise MarkItDownInputError(
                "stream_origin_unverifiable",
                "Binary stream must identify a server-owned original file.",
            )
        origin = Path(raw_name)
        if _looks_like_uri(origin.as_posix()):
            raise MarkItDownInputError("uri_input_rejected", "URI input is not allowed.")
        return origin

    def _get_converter(self) -> Any:
        if self._converter is None:
            # No URL, endpoint, client, or plugin arguments are accepted here.
            self._converter = self._converter_factory(enable_plugins=False)
        return self._converter

    def _convert_local(self, source: Path) -> MarkItDownConversion:
        started = time.monotonic()
        try:
            converted = self._get_converter().convert_local(source)
            markdown = _canonicalize_markdown(getattr(converted, "markdown", None))
        except Exception as exc:  # noqa: BLE001 - safe stable failure is the adapter contract
            return self._failure(started, "converter_exception", exc)
        return self._result_from_markdown(started, markdown)

    def _convert_stream(self, source: BinaryIO, extension: str) -> MarkItDownConversion:
        started = time.monotonic()
        stream_info = StreamInfo(
            extension=extension,
            mimetype=_MIME_BY_EXTENSION[extension],
            filename=f"validated-original{extension}",
        )
        try:
            converted = self._get_converter().convert_stream(source, stream_info=stream_info)
            markdown = _canonicalize_markdown(getattr(converted, "markdown", None))
        except Exception as exc:  # noqa: BLE001 - safe stable failure is the adapter contract
            return self._failure(started, "converter_exception", exc)
        return self._result_from_markdown(started, markdown)

    def _result_from_markdown(self, started: float, markdown: str) -> MarkItDownConversion:
        duration_ms = _duration_ms(started)
        if not markdown:
            return MarkItDownConversion(
                status="empty",
                markdown="",
                parser_name=self.parser_name,
                parser_version=self.parser_version,
                parser_provenance=self.parser_provenance,
                duration_ms=duration_ms,
                warnings=("empty_markdown",),
                error_code="empty_markdown",
            )
        return MarkItDownConversion(
            status="ok",
            markdown=markdown,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            parser_provenance=self.parser_provenance,
            duration_ms=duration_ms,
        )

    def _failure(self, started: float, error_code: str, _exc: Exception) -> MarkItDownConversion:
        # Exception text can contain paths or document-derived data. Only a
        # stable code is retained in lifecycle evidence.
        return MarkItDownConversion(
            status="failed",
            markdown=None,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            parser_provenance=self.parser_provenance,
            duration_ms=_duration_ms(started),
            warnings=(error_code,),
            error_code=error_code,
        )


def _is_binary_stream(source: object) -> bool:
    return (
        hasattr(source, "read")
        and callable(source.read)
        and not isinstance(source, io.TextIOBase)
    )


def _looks_like_uri(value: str) -> bool:
    return bool(_URI_PREFIX.match(value.strip()))


def _canonicalize_markdown(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return f"{normalized}\n" if normalized else ""


def _duration_ms(started: float) -> float:
    return round(max(0.0, (time.monotonic() - started) * 1000), 3)
