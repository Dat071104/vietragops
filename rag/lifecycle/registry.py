"""Durable local source/document/version registry backed by SQLite (stdlib).

Every write happens inside one transaction (`with self._connect() as conn:`
commits on success, rolls back on exception), so a crash mid-write leaves the
registry exactly as it was before the write started -- never half-applied.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag.lifecycle.errors import LifecycleError


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    source_url TEXT,
    publisher TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    title TEXT,
    domain TEXT,
    authority_level TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    checksum TEXT NOT NULL,
    extension TEXT NOT NULL,
    original_path TEXT NOT NULL,
    original_filename TEXT,
    content_type TEXT,
    size_bytes INTEGER NOT NULL,
    fetched_at TEXT,
    published_at TEXT,
    effective_at TEXT,
    parse_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (parse_status IN ('pending', 'ok', 'failed')),
    review_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (review_status IN ('candidate', 'reviewed', 'published', 'superseded', 'retired')),
    candidate_processed_path TEXT,
    candidate_chunks_path TEXT,
    parse_warnings TEXT,
    supersedes TEXT REFERENCES versions(version_id),
    superseded_by TEXT REFERENCES versions(version_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_versions_document_checksum
    ON versions(document_id, checksum);

CREATE INDEX IF NOT EXISTS idx_versions_document
    ON versions(document_id);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class VersionRecord:
    version_id: str
    document_id: str
    checksum: str
    extension: str
    original_path: str
    original_filename: str | None
    content_type: str | None
    size_bytes: int
    fetched_at: str | None
    published_at: str | None
    effective_at: str | None
    parse_status: str
    review_status: str
    candidate_processed_path: str | None
    candidate_chunks_path: str | None
    parse_warnings: str | None
    supersedes: str | None
    superseded_by: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "VersionRecord":
        return cls(**{key: row[key] for key in row.keys()})


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    source_id: str
    title: str | None
    domain: str | None
    authority_level: str | None
    created_at: str
    source_url: str | None = None
    publisher: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "DocumentRecord":
        return cls(**{key: row[key] for key in row.keys()})


_DOCUMENT_WITH_SOURCE_SQL = """
    SELECT documents.document_id, documents.source_id, documents.title,
           documents.domain, documents.authority_level, documents.created_at,
           sources.source_url, sources.publisher
    FROM documents JOIN sources ON documents.source_id = sources.source_id
    WHERE documents.document_id = ?
"""


class LifecycleRegistry:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # -- sources / documents -------------------------------------------------

    def get_or_create_document(
        self,
        *,
        document_id: str,
        title: str | None,
        source_url: str | None,
        publisher: str | None,
        domain: str | None,
        authority_level: str | None,
    ) -> DocumentRecord:
        with self._connect() as conn:
            row = conn.execute(_DOCUMENT_WITH_SOURCE_SQL, (document_id,)).fetchone()
            if row is not None:
                return DocumentRecord.from_row(row)

            source_id = uuid.uuid4().hex
            created_at = now_iso()
            conn.execute(
                "INSERT INTO sources (source_id, source_url, publisher, created_at) VALUES (?, ?, ?, ?)",
                (source_id, source_url, publisher, created_at),
            )
            conn.execute(
                """
                INSERT INTO documents (document_id, source_id, title, domain, authority_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (document_id, source_id, title, domain, authority_level, created_at),
            )
            row = conn.execute(_DOCUMENT_WITH_SOURCE_SQL, (document_id,)).fetchone()
            return DocumentRecord.from_row(row)

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._connect() as conn:
            row = conn.execute(_DOCUMENT_WITH_SOURCE_SQL, (document_id,)).fetchone()
            return DocumentRecord.from_row(row) if row is not None else None

    # -- versions -------------------------------------------------------------

    def find_version_by_checksum(self, document_id: str, checksum: str) -> VersionRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM versions WHERE document_id = ? AND checksum = ?",
                (document_id, checksum),
            ).fetchone()
            return VersionRecord.from_row(row) if row is not None else None

    def create_version(
        self,
        *,
        document_id: str,
        checksum: str,
        extension: str,
        original_path: str,
        original_filename: str | None,
        content_type: str | None,
        size_bytes: int,
        fetched_at: str | None = None,
        version_id: str | None = None,
    ) -> VersionRecord:
        version_id = version_id or uuid.uuid4().hex
        timestamp = now_iso()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO versions (
                        version_id, document_id, checksum, extension, original_path,
                        original_filename, content_type, size_bytes, fetched_at,
                        parse_status, review_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'candidate', ?, ?)
                    """,
                    (
                        version_id,
                        document_id,
                        checksum,
                        extension,
                        original_path,
                        original_filename,
                        content_type,
                        size_bytes,
                        fetched_at or timestamp,
                        timestamp,
                        timestamp,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise LifecycleError(
                "duplicate_version",
                f"A version with this checksum already exists for document '{document_id}'.",
            ) from exc
        self._record_event(version_id, "intake", None)
        return self.get_version(version_id)  # type: ignore[return-value]

    def get_version(self, version_id: str) -> VersionRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM versions WHERE version_id = ?", (version_id,)).fetchone()
            return VersionRecord.from_row(row) if row is not None else None

    def list_versions(self, document_id: str) -> list[VersionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM versions WHERE document_id = ? ORDER BY created_at ASC",
                (document_id,),
            ).fetchall()
            return [VersionRecord.from_row(row) for row in rows]

    def get_published_version(self, document_id: str) -> VersionRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM versions WHERE document_id = ? AND review_status = 'published'",
                (document_id,),
            ).fetchone()
            return VersionRecord.from_row(row) if row is not None else None

    def update_candidate_artifacts(
        self,
        version_id: str,
        *,
        parse_status: str,
        candidate_processed_path: str | None,
        candidate_chunks_path: str | None,
        parse_warnings: str | None,
    ) -> VersionRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE versions
                SET parse_status = ?, candidate_processed_path = ?, candidate_chunks_path = ?,
                    parse_warnings = ?, updated_at = ?
                WHERE version_id = ?
                """,
                (parse_status, candidate_processed_path, candidate_chunks_path, parse_warnings, now_iso(), version_id),
            )
        self._record_event(version_id, f"parsed:{parse_status}", parse_warnings)
        return self.get_version(version_id)  # type: ignore[return-value]

    def update_review_status(self, version_id: str, review_status: str, **fields: Any) -> VersionRecord:
        columns = ["review_status = ?", "updated_at = ?"]
        values: list[Any] = [review_status, now_iso()]
        for key, value in fields.items():
            columns.append(f"{key} = ?")
            values.append(value)
        values.append(version_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE versions SET {', '.join(columns)} WHERE version_id = ?", values)
        self._record_event(version_id, review_status, None)
        return self.get_version(version_id)  # type: ignore[return-value]

    def record_note(self, version_id: str, event_type: str, detail: str | None = None) -> None:
        """Append a standalone audit event not tied to a review_status column update."""
        self._record_event(version_id, event_type, detail)

    def _record_event(self, version_id: str, event_type: str, detail: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (version_id, event_type, detail, created_at) VALUES (?, ?, ?, ?)",
                (version_id, event_type, detail, now_iso()),
            )

    def list_events(self, version_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE version_id = ? ORDER BY event_id ASC",
                (version_id,),
            ).fetchall()
            return [dict(row) for row in rows]
