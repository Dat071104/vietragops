"""Deterministic source/version/authority/freshness resolution for retrieved chunks.

Every retrieved chunk must resolve to an explicit `source_id`, `source_version`,
`index_version`, `authority_state`, and `freshness_state` -- never a silently
invented value. Unknown evidence stays `UNKNOWN`, it is never upgraded to a
guessed authority or freshness.

Resolution reuses metadata that already exists rather than inventing a new
source-of-truth:

- `source_version` prefers the lifecycle registry's published `version_id`
  (Gate 01/03) when the document is registry-tracked and the manifest row's
  checksum agrees with it; otherwise it falls back to a deterministic
  `legacy:{checksum}` derived from the existing manifest `checksum` column
  (Gate 00 corpus), so every legacy chunk still gets a stable, auditable
  identity without the registry ever having seen it.
- `authority_state` prefers the registry's `review_status` (published ->
  active; every version retired -> retired, a diagnostic-only case since a
  fully retired document's chunks are already removed from the live corpus
  by `rag.lifecycle.publish.apply_live_state`); otherwise it falls back to
  the manifest's existing `status` column.
- `freshness_state` is opt-in: it only reacts to an explicit `stale_after`
  key on the manifest row (real corpus rows never carry one, so real
  freshness stays `unknown` -- this is a deliberate no-op on baseline data,
  not a gap). Fixtures inject `stale_after` directly into a synthetic
  manifest-row dict; the real `documents_manifest.csv` schema is untouched.
- `conflict_key` is the same opt-in mechanism, consumed by
  `rag.generation.evidence_state` to detect `source_conflict`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

UNKNOWN = "unknown"
AUTHORITY_ACTIVE = "active"
AUTHORITY_RETIRED = "retired"
FRESHNESS_CURRENT = "current"
FRESHNESS_STALE = "stale"

_RETIRED_STATUS_VALUES = {"retired", "inactive"}


@dataclass(frozen=True)
class ChunkVersionInfo:
    source_id: str
    source_version: str
    index_version: str
    authority_state: str
    freshness_state: str
    conflict_key: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_version": self.source_version,
            "index_version": self.index_version,
            "authority_state": self.authority_state,
            "freshness_state": self.freshness_state,
            "conflict_key": self.conflict_key,
        }


class VersionResolver:
    """Resolves one `ChunkVersionInfo` per `doc_id`.

    `manifest_rows` is a `doc_id -> row dict` mapping, exactly the shape
    `rag.retrieval.source_priority.load_manifest_rows` already returns.
    `registry` is optional; pass a `rag.lifecycle.registry.LifecycleRegistry`
    to enable registry-aware resolution for lifecycle-managed documents.
    `as_of` is an injectable clock so freshness resolution is deterministic
    in tests; it defaults to the current UTC time.
    """

    def __init__(
        self,
        manifest_rows: dict[str, dict[str, str]],
        index_version: str,
        *,
        registry: Any | None = None,
        as_of: datetime | None = None,
    ) -> None:
        self._manifest_rows = manifest_rows
        self._index_version = index_version
        self._registry = registry
        self._as_of = as_of or datetime.now(timezone.utc)

    def resolve(self, doc_id: str) -> ChunkVersionInfo:
        row = self._manifest_rows.get(doc_id) or {}
        source_version = self._resolve_source_version(doc_id, row)
        authority_state = self._resolve_authority_state(doc_id, row)
        freshness_state = self._resolve_freshness_state(row)
        conflict_key = (row.get("conflict_key") or "").strip() or None
        return ChunkVersionInfo(
            source_id=doc_id,
            source_version=source_version,
            index_version=self._index_version,
            authority_state=authority_state,
            freshness_state=freshness_state,
            conflict_key=conflict_key,
        )

    def _resolve_source_version(self, doc_id: str, row: dict[str, str]) -> str:
        published = self._registry_published_version(doc_id)
        if published is not None:
            checksum = (row.get("checksum") or "").strip()
            if not checksum or published.checksum == checksum:
                return published.version_id
        checksum = (row.get("checksum") or "").strip()
        if checksum:
            return f"legacy:{checksum[:16]}"
        return UNKNOWN

    def _resolve_authority_state(self, doc_id: str, row: dict[str, str]) -> str:
        if self._registry is not None:
            document = self._registry.get_document(doc_id)
            if document is not None:
                if self._registry_published_version(doc_id) is not None:
                    return AUTHORITY_ACTIVE
                versions = self._registry.list_versions(doc_id)
                if versions and all(version.review_status == "retired" for version in versions):
                    return AUTHORITY_RETIRED
                return UNKNOWN
        status = (row.get("status") or "").strip().casefold()
        if status == "active":
            return AUTHORITY_ACTIVE
        if status in _RETIRED_STATUS_VALUES:
            return AUTHORITY_RETIRED
        return UNKNOWN

    def _resolve_freshness_state(self, row: dict[str, str]) -> str:
        stale_after = (row.get("stale_after") or "").strip()
        if stale_after:
            stale_at = _parse_datetime(stale_after)
            if stale_at is None:
                return UNKNOWN
            return FRESHNESS_STALE if stale_at <= self._as_of else FRESHNESS_CURRENT
        if (row.get("published_at") or "").strip():
            return FRESHNESS_CURRENT
        return UNKNOWN

    def _registry_published_version(self, doc_id: str):
        if self._registry is None:
            return None
        return self._registry.get_published_version(doc_id)


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
