"""Bounded, streaming, checksummed intake for one uploaded document."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.naming import normalize_filename, validate_content_type, validate_format


@dataclass(frozen=True)
class IntakeResult:
    slug: str
    extension: str
    checksum: str
    size_bytes: int
    content: bytes


class IntakeReceiver:
    """Stateful receiver that enforces the size bound WHILE bytes arrive.

    Feed it chunks as they are read from the wire; it raises as soon as the
    configured maximum is exceeded, so an oversized upload is never fully
    buffered just to be rejected afterward.
    """

    def __init__(self, *, filename: str | None, content_type: str | None, max_bytes: int) -> None:
        if max_bytes <= 0:
            raise LifecycleError("invalid_configuration", "max_bytes must be positive.", status_code=500)
        self.slug, self.extension = normalize_filename(filename)
        validate_content_type(content_type, self.extension)
        self._max_bytes = max_bytes
        self._hasher = hashlib.sha256()
        self._chunks: list[bytes] = []
        self._size = 0
        self._finalized = False

    @property
    def size_bytes(self) -> int:
        return self._size

    def feed(self, chunk: bytes) -> None:
        if self._finalized:
            raise LifecycleError("intake_closed", "Cannot feed bytes after finalize().", status_code=500)
        if not chunk:
            return
        self._size += len(chunk)
        if self._size > self._max_bytes:
            raise LifecycleError(
                "file_too_large",
                f"Upload exceeds the {self._max_bytes}-byte limit.",
            )
        self._hasher.update(chunk)
        self._chunks.append(chunk)

    def finalize(self) -> IntakeResult:
        if self._finalized:
            raise LifecycleError("intake_closed", "finalize() already called.", status_code=500)
        self._finalized = True
        if self._size == 0:
            raise LifecycleError("empty_upload", "Upload contained no bytes.")
        content = b"".join(self._chunks)
        validate_format(self.extension, content)
        return IntakeResult(
            slug=self.slug,
            extension=self.extension,
            checksum=self._hasher.hexdigest(),
            size_bytes=self._size,
            content=content,
        )
