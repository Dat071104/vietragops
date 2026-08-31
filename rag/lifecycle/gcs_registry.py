"""Optimistic, durable lifecycle registry stored in Cloud Storage.

The local product keeps using SQLite.  Gate 09R's cloud shape deliberately
avoids Cloud SQL: registry state is stored in a versioned JSON pointer object,
and every update uses a Cloud Storage generation compare-and-swap.  A
concurrent update therefore retries or returns a typed conflict instead of
silently losing a version transition.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, TypeVar
import uuid

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.gcs_storage import (
    GcsNotFoundError,
    GcsObjectStore,
    GcsPreconditionFailed,
    GcsStorageError,
    ObjectStore,
)
from rag.lifecycle.registry import DocumentRecord, VersionRecord


_T = TypeVar("_T")

STATE_SCHEMA = "vietragops.gcs_registry"
STATE_SCHEMA_VERSION = 1
DEFAULT_STATE_OBJECT = "registry/pointers/state.json"
DEFAULT_SNAPSHOT_PREFIX = "registry/snapshots"
_REVIEW_STATUSES = {"candidate", "reviewed", "published", "superseded", "retired"}
_VERSION_MUTABLE_FIELDS = {
    "fetched_at",
    "published_at",
    "effective_at",
    "parse_status",
    "review_status",
    "candidate_processed_path",
    "candidate_chunks_path",
    "candidate_canonical_path",
    "candidate_extraction_path",
    "parse_warnings",
    "supersedes",
    "superseded_by",
    "updated_at",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GcsRegistryConflictError(GcsStorageError):
    def __init__(self) -> None:
        super().__init__("registry_conflict", "Concurrent Cloud Storage registry update could not be committed safely.")


class GcsLifecycleRegistry:
    """Small registry with the same public operations as ``LifecycleRegistry``."""

    def __init__(
        self,
        objects: ObjectStore | GcsObjectStore,
        *,
        state_object: str = DEFAULT_STATE_OBJECT,
        snapshot_prefix: str = DEFAULT_SNAPSHOT_PREFIX,
        max_retries: int = 5,
    ) -> None:
        self.objects = objects
        self.bucket_name = objects.bucket_name
        self.state_object = state_object.strip("/") or DEFAULT_STATE_OBJECT
        self.snapshot_prefix = snapshot_prefix.strip("/") or DEFAULT_SNAPSHOT_PREFIX
        self.max_retries = max(1, max_retries)
        self._ensure_state()

    def _empty_state(self) -> dict[str, Any]:
        return {
            "schema": STATE_SCHEMA,
            "schema_version": STATE_SCHEMA_VERSION,
            "sources": {},
            "documents": {},
            "versions": {},
            "events": {},
            "web_provenance": {},
            "acquisition_attempts": [],
            "active_release_id": None,
        }

    def _ensure_state(self) -> None:
        try:
            self.objects.get(self.state_object)
            return
        except GcsNotFoundError:
            pass
        try:
            self.objects.put_immutable(
                self.state_object,
                self._serialize_pointer(self._empty_state(), snapshot_object=None),
                content_type="application/json",
            )
        except GcsPreconditionFailed:
            # Another instance initialized it first; the next read is authoritative.
            return

    def _read_state(self) -> tuple[dict[str, Any], int]:
        try:
            pointer = self.objects.get(self.state_object)
        except GcsNotFoundError:
            self._ensure_state()
            pointer = self.objects.get(self.state_object)
        try:
            payload = json.loads(pointer.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GcsStorageError("invalid_registry", "Cloud Storage registry pointer is not valid JSON.") from exc
        if not isinstance(payload, dict) or payload.get("schema") != STATE_SCHEMA:
            raise GcsStorageError("invalid_registry", "Cloud Storage registry schema is invalid.")
        if payload.get("schema_version") != STATE_SCHEMA_VERSION:
            raise GcsStorageError("invalid_registry", "Cloud Storage registry schema version is unsupported.")
        state = {key: value for key, value in payload.items() if not key.startswith("_")}
        for key, default in self._empty_state().items():
            state.setdefault(key, deepcopy(default))
        return state, pointer.generation

    def _write_state(self, state: dict[str, Any], generation: int) -> None:
        serialized_state = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        snapshot_hash = hashlib.sha256(serialized_state).hexdigest()
        snapshot_object = f"{self.snapshot_prefix}/{snapshot_hash}.json"
        try:
            self.objects.put_immutable(
                snapshot_object,
                serialized_state + b"\n",
                content_type="application/json",
            )
        except GcsPreconditionFailed:
            # The same content already exists; immutable snapshots are idempotent.
            pass
        pointer_content = self._serialize_pointer(state, snapshot_object=snapshot_object)
        self.objects.put(
            self.state_object,
            pointer_content,
            if_generation_match=generation,
            content_type="application/json",
        )

    def _mutate(self, mutator: Callable[[dict[str, Any]], _T]) -> _T:
        for _ in range(self.max_retries):
            state, generation = self._read_state()
            candidate = deepcopy(state)
            result = mutator(candidate)
            try:
                self._write_state(candidate, generation)
            except GcsPreconditionFailed:
                continue
            return result
        raise GcsRegistryConflictError()

    @staticmethod
    def _serialize_pointer(state: dict[str, Any], *, snapshot_object: str | None) -> bytes:
        pointer = deepcopy(state)
        if snapshot_object is not None:
            pointer["_snapshot_object"] = snapshot_object
        pointer["_updated_at"] = now_iso()
        return (json.dumps(pointer, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    def get_active_release_id(self) -> str | None:
        state, _ = self._read_state()
        value = state.get("active_release_id")
        return value if isinstance(value, str) and value else None

    # -- sources / documents ---------------------------------------------

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
        def mutate(state: dict[str, Any]) -> DocumentRecord:
            existing = state["documents"].get(document_id)
            if isinstance(existing, dict):
                return self._document_from_state(state, existing)
            source_id = uuid.uuid4().hex
            created_at = now_iso()
            state["sources"][source_id] = {
                "source_id": source_id,
                "source_url": source_url,
                "publisher": publisher,
                "created_at": created_at,
            }
            document = {
                "document_id": document_id,
                "source_id": source_id,
                "title": title,
                "domain": domain,
                "authority_level": authority_level,
                "created_at": created_at,
            }
            state["documents"][document_id] = document
            return self._document_from_state(state, document)

        return self._mutate(mutate)

    def get_document(self, document_id: str) -> DocumentRecord | None:
        state, _ = self._read_state()
        document = state["documents"].get(document_id)
        return self._document_from_state(state, document) if isinstance(document, dict) else None

    def _document_from_state(self, state: dict[str, Any], document: dict[str, Any]) -> DocumentRecord:
        source = state["sources"].get(document.get("source_id"), {})
        return DocumentRecord(
            document_id=str(document.get("document_id", "")),
            source_id=str(document.get("source_id", "")),
            title=document.get("title"),
            domain=document.get("domain"),
            authority_level=document.get("authority_level"),
            created_at=str(document.get("created_at", "")),
            source_url=source.get("source_url"),
            publisher=source.get("publisher"),
        )

    # -- versions ---------------------------------------------------------

    def find_version_by_checksum(self, document_id: str, checksum: str) -> VersionRecord | None:
        state, _ = self._read_state()
        for raw in state["versions"].values():
            if isinstance(raw, dict) and raw.get("document_id") == document_id and raw.get("checksum") == checksum:
                return self._version_from_state(raw)
        return None

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

        def mutate(state: dict[str, Any]) -> VersionRecord:
            for raw in state["versions"].values():
                if isinstance(raw, dict) and raw.get("document_id") == document_id and raw.get("checksum") == checksum:
                    raise LifecycleError(
                        "duplicate_version",
                        f"A version with this checksum already exists for document '{document_id}'.",
                    )
            timestamp = now_iso()
            raw = {
                "version_id": version_id,
                "document_id": document_id,
                "checksum": checksum,
                "extension": extension,
                "original_path": original_path,
                "original_filename": original_filename,
                "content_type": content_type,
                "size_bytes": int(size_bytes),
                "fetched_at": fetched_at or timestamp,
                "published_at": None,
                "effective_at": None,
                "parse_status": "pending",
                "review_status": "candidate",
                "candidate_processed_path": None,
                "candidate_chunks_path": None,
                "candidate_canonical_path": None,
                "candidate_extraction_path": None,
                "parse_warnings": None,
                "supersedes": None,
                "superseded_by": None,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            state["versions"][version_id] = raw
            self._append_event(state, version_id, "intake", None)
            return self._version_from_state(raw)

        return self._mutate(mutate)

    def get_version(self, version_id: str) -> VersionRecord | None:
        state, _ = self._read_state()
        raw = state["versions"].get(version_id)
        return self._version_from_state(raw) if isinstance(raw, dict) else None

    def list_versions(self, document_id: str) -> list[VersionRecord]:
        state, _ = self._read_state()
        records = [
            self._version_from_state(raw)
            for raw in state["versions"].values()
            if isinstance(raw, dict) and raw.get("document_id") == document_id
        ]
        return sorted(records, key=lambda item: item.created_at)

    def get_published_version(self, document_id: str) -> VersionRecord | None:
        records = [version for version in self.list_versions(document_id) if version.review_status == "published"]
        return records[-1] if records else None

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
        def mutate(state: dict[str, Any]) -> VersionRecord:
            raw = self._require_version_dict(state, version_id)
            raw.update(
                {
                    "parse_status": parse_status,
                    "candidate_processed_path": candidate_processed_path,
                    "candidate_chunks_path": candidate_chunks_path,
                    "candidate_canonical_path": candidate_canonical_path,
                    "candidate_extraction_path": candidate_extraction_path,
                    "parse_warnings": parse_warnings,
                    "updated_at": now_iso(),
                }
            )
            self._append_event(state, version_id, f"parsed:{parse_status}", parse_warnings)
            return self._version_from_state(raw)

        return self._mutate(mutate)

    def update_review_status(self, version_id: str, review_status: str, **fields: Any) -> VersionRecord:
        if review_status not in _REVIEW_STATUSES:
            raise LifecycleError("invalid_transition", f"Unsupported review status '{review_status}'.", status_code=409)
        unknown = set(fields) - _VERSION_MUTABLE_FIELDS
        if unknown:
            raise LifecycleError("invalid_registry_update", "Unsupported version update field.", status_code=500)

        def mutate(state: dict[str, Any]) -> VersionRecord:
            raw = self._require_version_dict(state, version_id)
            raw.update(fields)
            raw["review_status"] = review_status
            raw["updated_at"] = now_iso()
            self._append_event(state, version_id, review_status, None)
            return self._version_from_state(raw)

        return self._mutate(mutate)

    def record_note(self, version_id: str, event_type: str, detail: str | None = None) -> None:
        def mutate(state: dict[str, Any]) -> None:
            self._require_version_dict(state, version_id)
            self._append_event(state, version_id, event_type, detail)

        self._mutate(mutate)

    def list_events(self, version_id: str) -> list[dict[str, Any]]:
        state, _ = self._read_state()
        return deepcopy(state["events"].get(version_id, []))

    # -- atomic release transitions --------------------------------------

    def activate_release(
        self,
        *,
        version_id: str,
        release_id: str,
        previous_version_id: str | None,
        published_at: str,
    ) -> VersionRecord:
        def mutate(state: dict[str, Any]) -> VersionRecord:
            raw = self._require_version_dict(state, version_id)
            if previous_version_id and previous_version_id != version_id:
                previous = self._require_version_dict(state, previous_version_id)
                previous["review_status"] = "superseded"
                previous["superseded_by"] = version_id
                previous["updated_at"] = now_iso()
                self._append_event(state, previous_version_id, "superseded", f"by={version_id}")
            raw["review_status"] = "published"
            raw["published_at"] = published_at
            raw["supersedes"] = previous_version_id
            raw["superseded_by"] = None
            raw["updated_at"] = now_iso()
            state["active_release_id"] = release_id
            self._append_event(state, version_id, "published", f"release={release_id}")
            return self._version_from_state(raw)

        return self._mutate(mutate)

    def activate_retired_release(self, *, version_id: str, release_id: str) -> VersionRecord:
        def mutate(state: dict[str, Any]) -> VersionRecord:
            raw = self._require_version_dict(state, version_id)
            raw["review_status"] = "retired"
            raw["updated_at"] = now_iso()
            state["active_release_id"] = release_id
            self._append_event(state, version_id, "retired", f"release={release_id}")
            return self._version_from_state(raw)

        return self._mutate(mutate)

    def activate_rollback_release(
        self,
        *,
        target_version_id: str,
        current_version_id: str | None,
        release_id: str,
    ) -> VersionRecord:
        def mutate(state: dict[str, Any]) -> VersionRecord:
            target = self._require_version_dict(state, target_version_id)
            if current_version_id and current_version_id != target_version_id:
                current = self._require_version_dict(state, current_version_id)
                current["review_status"] = "superseded"
                current["superseded_by"] = target_version_id
                current["updated_at"] = now_iso()
                self._append_event(state, current_version_id, "superseded", f"by={target_version_id}")
            target["review_status"] = "published"
            target["superseded_by"] = None
            target["updated_at"] = now_iso()
            state["active_release_id"] = release_id
            self._append_event(state, target_version_id, "rollback", f"release={release_id}")
            return self._version_from_state(target)

        return self._mutate(mutate)

    # -- web provenance / attempts ---------------------------------------

    def create_web_provenance(self, **fields: Any) -> None:
        version_id = fields.get("version_id")
        if not isinstance(version_id, str):
            raise LifecycleError("invalid_registry_update", "Web provenance requires a version id.", status_code=500)

        def mutate(state: dict[str, Any]) -> None:
            self._require_version_dict(state, version_id)
            state["web_provenance"][version_id] = deepcopy(fields)

        self._mutate(mutate)

    def get_web_provenance(self, version_id: str) -> dict[str, Any] | None:
        state, _ = self._read_state()
        value = state["web_provenance"].get(version_id)
        return deepcopy(value) if isinstance(value, dict) else None

    def record_acquisition_attempt(self, **fields: Any) -> str:
        attempt_id = uuid.uuid4().hex

        def mutate(state: dict[str, Any]) -> str:
            record = {"attempt_id": attempt_id, **deepcopy(fields), "created_at": now_iso()}
            state["acquisition_attempts"].append(record)
            return attempt_id

        return self._mutate(mutate)

    def list_acquisition_attempts(
        self, *, canonical_url: str | None = None, document_id: str | None = None
    ) -> list[dict[str, Any]]:
        state, _ = self._read_state()
        records = []
        for record in state["acquisition_attempts"]:
            if canonical_url is not None and record.get("canonical_url") != canonical_url:
                continue
            if document_id is not None and record.get("document_id") != document_id:
                continue
            records.append(deepcopy(record))
        return records

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _require_version_dict(state: dict[str, Any], version_id: str) -> dict[str, Any]:
        raw = state["versions"].get(version_id)
        if not isinstance(raw, dict):
            raise LifecycleError("version_not_found", f"Version '{version_id}' does not exist.", status_code=404)
        return raw

    @staticmethod
    def _append_event(state: dict[str, Any], version_id: str, event_type: str, detail: str | None) -> None:
        state["events"].setdefault(version_id, []).append(
            {
                "event_id": len(state["events"].get(version_id, [])) + 1,
                "version_id": version_id,
                "event_type": event_type,
                "detail": detail,
                "created_at": now_iso(),
            }
        )

    @staticmethod
    def _version_from_state(raw: dict[str, Any]) -> VersionRecord:
        values = {
            "version_id": raw.get("version_id"),
            "document_id": raw.get("document_id"),
            "checksum": raw.get("checksum"),
            "extension": raw.get("extension"),
            "original_path": raw.get("original_path"),
            "original_filename": raw.get("original_filename"),
            "content_type": raw.get("content_type"),
            "size_bytes": int(raw.get("size_bytes", 0)),
            "fetched_at": raw.get("fetched_at"),
            "published_at": raw.get("published_at"),
            "effective_at": raw.get("effective_at"),
            "parse_status": raw.get("parse_status", "pending"),
            "review_status": raw.get("review_status", "candidate"),
            "candidate_processed_path": raw.get("candidate_processed_path"),
            "candidate_chunks_path": raw.get("candidate_chunks_path"),
            "candidate_canonical_path": raw.get("candidate_canonical_path"),
            "candidate_extraction_path": raw.get("candidate_extraction_path"),
            "parse_warnings": raw.get("parse_warnings"),
            "supersedes": raw.get("supersedes"),
            "superseded_by": raw.get("superseded_by"),
            "created_at": raw.get("created_at"),
            "updated_at": raw.get("updated_at"),
        }
        return VersionRecord(**values)
