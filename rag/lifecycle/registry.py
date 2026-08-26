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
    candidate_canonical_path TEXT,
    candidate_extraction_path TEXT,
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

CREATE TABLE IF NOT EXISTS web_provenance (
    version_id TEXT PRIMARY KEY REFERENCES versions(version_id),
    canonical_url TEXT NOT NULL,
    url_hash TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    firecrawl_action_id TEXT,
    http_status INTEGER,
    status_class TEXT NOT NULL,
    credits_used INTEGER,
    content_checksum TEXT NOT NULL,
    domain TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    parser_policy TEXT NOT NULL,
    prior_version_id TEXT REFERENCES versions(version_id),
    diff_path TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_web_provenance_url_hash ON web_provenance(url_hash);

CREATE TABLE IF NOT EXISTS acquisition_attempts (
    attempt_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    canonical_url TEXT,
    domain TEXT,
    status_class TEXT NOT NULL,
    error_code TEXT,
    http_status INTEGER,
    retry_after_seconds REAL,
    credits_used INTEGER,
    document_id TEXT,
    version_id TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_acquisition_attempts_url ON acquisition_attempts(canonical_url);
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
    candidate_canonical_path: str | None
    candidate_extraction_path: str | None
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
            self._migrate_versions(conn)
            self._migrate_web_provenance(conn)

    @staticmethod
    def _migrate_versions(conn: sqlite3.Connection) -> None:
        """Add Gate 02 candidate locations to registries created by Gate 01."""
        columns = {row[1] for row in conn.execute("PRAGMA table_info(versions)")}
        for column in ("candidate_canonical_path", "candidate_extraction_path"):
            if column not in columns:
                conn.execute(f"ALTER TABLE versions ADD COLUMN {column} TEXT")

    @staticmethod
    def _migrate_web_provenance(conn: sqlite3.Connection) -> None:
        """Add the Gate 03 recrawl-diff link to registries created before it existed."""
        columns = {row[1] for row in conn.execute("PRAGMA table_info(web_provenance)")}
        if "diff_path" not in columns:
            conn.execute("ALTER TABLE web_provenance ADD COLUMN diff_path TEXT")

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
        candidate_canonical_path: str | None = None,
        candidate_extraction_path: str | None = None,
    ) -> VersionRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE versions
                SET parse_status = ?, candidate_processed_path = ?, candidate_chunks_path = ?,
                    candidate_canonical_path = ?, candidate_extraction_path = ?,
                    parse_warnings = ?, updated_at = ?
                WHERE version_id = ?
                """,
                (
                    parse_status,
                    candidate_processed_path,
                    candidate_chunks_path,
                    candidate_canonical_path,
                    candidate_extraction_path,
                    parse_warnings,
                    now_iso(),
                    version_id,
                ),
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

    # -- web provenance -------------------------------------------------------

    def create_web_provenance(
        self,
        *,
        version_id: str,
        canonical_url: str,
        url_hash: str,
        retrieved_at: str,
        firecrawl_action_id: str | None,
        http_status: int | None,
        status_class: str,
        credits_used: int | None,
        content_checksum: str,
        domain: str,
        adapter_version: str,
        parser_policy: str,
        prior_version_id: str | None,
        diff_path: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO web_provenance (
                    version_id, canonical_url, url_hash, retrieved_at,
                    firecrawl_action_id, http_status, status_class, credits_used,
                    content_checksum, domain, adapter_version, parser_policy,
                    prior_version_id, diff_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    canonical_url,
                    url_hash,
                    retrieved_at,
                    firecrawl_action_id,
                    http_status,
                    status_class,
                    credits_used,
                    content_checksum,
                    domain,
                    adapter_version,
                    parser_policy,
                    prior_version_id,
                    diff_path,
                    now_iso(),
                ),
            )

    def get_web_provenance(self, version_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM web_provenance WHERE version_id = ?", (version_id,)).fetchone()
            return dict(row) if row is not None else None

    # -- acquisition attempts ---------------------------------------------------

    def record_acquisition_attempt(
        self,
        *,
        action: str,
        status_class: str,
        canonical_url: str | None = None,
        domain: str | None = None,
        error_code: str | None = None,
        http_status: int | None = None,
        retry_after_seconds: float | None = None,
        credits_used: int | None = None,
        document_id: str | None = None,
        version_id: str | None = None,
    ) -> str:
        attempt_id = uuid.uuid4().hex
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO acquisition_attempts (
                    attempt_id, action, canonical_url, domain, status_class,
                    error_code, http_status, retry_after_seconds, credits_used,
                    document_id, version_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    action,
                    canonical_url,
                    domain,
                    status_class,
                    error_code,
                    http_status,
                    retry_after_seconds,
                    credits_used,
                    document_id,
                    version_id,
                    now_iso(),
                ),
            )
        return attempt_id

    def list_acquisition_attempts(
        self, *, canonical_url: str | None = None, document_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if canonical_url is not None:
            clauses.append("canonical_url = ?")
            params.append(canonical_url)
        if document_id is not None:
            clauses.append("document_id = ?")
            params.append(document_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM acquisition_attempts {where} ORDER BY created_at ASC", params
            ).fetchall()
            return [dict(row) for row in rows]
