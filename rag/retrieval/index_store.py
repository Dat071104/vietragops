"""Chunk loading helpers for retrieval and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "doc_id",
    "title",
    "source_url",
    "source_type",
    "domain",
    "authority_level",
    "heading_path",
    "section_id",
    "chunk_index",
    "text",
}


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    doc_id: str
    title: str
    source_url: str
    source_type: str
    domain: str
    authority_level: str
    heading_path: list[str]
    page_start: int | None
    page_end: int | None
    section_id: str
    chunk_index: int
    text: str
    token_count: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    checksum: str | None = None
    chunk_config: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChunkRecord":
        missing = REQUIRED_CHUNK_FIELDS - set(payload)
        if missing:
            raise ValueError(f"Chunk payload missing required fields: {sorted(missing)}")
        return cls(
            chunk_id=payload["chunk_id"],
            doc_id=payload["doc_id"],
            title=payload["title"],
            source_url=payload["source_url"],
            source_type=payload["source_type"],
            domain=payload["domain"],
            authority_level=payload["authority_level"],
            heading_path=list(payload["heading_path"]),
            page_start=payload.get("page_start"),
            page_end=payload.get("page_end"),
            section_id=payload["section_id"],
            chunk_index=int(payload["chunk_index"]),
            text=payload["text"],
            token_count=payload.get("token_count"),
            char_start=payload.get("char_start"),
            char_end=payload.get("char_end"),
            checksum=payload.get("checksum"),
            chunk_config=payload.get("chunk_config"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "domain": self.domain,
            "authority_level": self.authority_level,
            "heading_path": list(self.heading_path),
            "page_start": self.page_start,
            "page_end": self.page_end,
            "section_id": self.section_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "token_count": self.token_count,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "checksum": self.checksum,
            "chunk_config": dict(self.chunk_config or {}),
        }


class ChunkIndexStore:
    def __init__(self, records: Iterable[ChunkRecord], source_path: str | None = None) -> None:
        self.chunks = list(records)
        self.source_path = source_path
        self._by_id = {chunk.chunk_id: chunk for chunk in self.chunks}

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "ChunkIndexStore":
        chunk_path = Path(path)
        lines = chunk_path.read_text(encoding="utf-8").splitlines()
        records = [ChunkRecord.from_dict(json.loads(line)) for line in lines if line.strip()]
        return cls(records, source_path=str(chunk_path))

    @classmethod
    def from_records(cls, records: Iterable[dict[str, Any] | ChunkRecord]) -> "ChunkIndexStore":
        normalized: list[ChunkRecord] = []
        for record in records:
            normalized.append(record if isinstance(record, ChunkRecord) else ChunkRecord.from_dict(record))
        return cls(normalized)

    def get(self, chunk_id: str) -> ChunkRecord:
        return self._by_id[chunk_id]

    def __len__(self) -> int:
        return len(self.chunks)

    def __iter__(self):
        return iter(self.chunks)
