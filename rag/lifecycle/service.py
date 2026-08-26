"""Orchestrates intake -> registry -> candidate processing -> publish/retire/rollback.

This is the single entry point routes (and tests) use; it owns the write
ordering that keeps the original artifact, the registry, and the live
manifest/chunks consistent across an interrupted operation:

1. write the immutable original to disk (atomic replace) BEFORE the registry
   commits a version row referencing it;
2. write candidate artifacts (atomic replace) BEFORE the registry marks
   parse_status for them;
3. swap the live manifest/chunks (atomic replace, per Phase 1.4) BEFORE the
   registry commits the published/retired/superseded transition;
4. clear the in-process read caches (`refresh_live_caches`) last, after the
   registry commit, so a reader is never handed a state the registry doesn't
   yet agree with.

If a step fails, everything committed so far is still individually valid; the
next call (a retry, or a fresh review/publish attempt) picks up from
whatever the registry actually recorded.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.intake import IntakeReceiver
from rag.lifecycle.pipeline import process_candidate
from rag.lifecycle.publish import apply_live_state
from rag.lifecycle.registry import LifecycleRegistry, VersionRecord
from rag.lifecycle.storage import write_bytes_atomic


@dataclass(frozen=True)
class UploadOutcome:
    document_id: str
    version_id: str
    duplicate: bool
    parse_status: str
    review_status: str
    warnings: list[str]


class LifecycleService:
    def __init__(
        self,
        *,
        registry: LifecycleRegistry,
        originals_dir: Path,
        candidates_dir: Path,
        live_manifest_path: Path,
        live_chunks_path: Path,
        max_upload_bytes: int,
        refresh_live_caches: Callable[[], None] = lambda: None,
    ) -> None:
        self._registry = registry
        self._originals_dir = Path(originals_dir)
        self._candidates_dir = Path(candidates_dir)
        self._live_manifest_path = Path(live_manifest_path)
        self._live_chunks_path = Path(live_chunks_path)
        self._max_upload_bytes = max_upload_bytes
        self._refresh_live_caches = refresh_live_caches

    # -- intake ----------------------------------------------------------

    def begin_intake(self, *, filename: str | None, content_type: str | None) -> IntakeReceiver:
        return IntakeReceiver(filename=filename, content_type=content_type, max_bytes=self._max_upload_bytes)

    def complete_intake(
        self,
        receiver: IntakeReceiver,
        *,
        source_url: str | None = None,
        publisher: str | None = None,
        domain: str | None = None,
        authority_level: str | None = None,
    ) -> UploadOutcome:
        result = receiver.finalize()
        document_id = result.slug
        display_title = _stem_for_title(receiver.raw_filename) or document_id

        self._registry.get_or_create_document(
            document_id=document_id,
            title=display_title,
            source_url=source_url,
            publisher=publisher,
            domain=domain,
            authority_level=authority_level,
        )

        existing = self._registry.find_version_by_checksum(document_id, result.checksum)
        if existing is not None:
            return UploadOutcome(
                document_id=document_id,
                version_id=existing.version_id,
                duplicate=True,
                parse_status=existing.parse_status,
                review_status=existing.review_status,
                warnings=[],
            )

        # version_id is server-owned (never derived from caller input) so the
        # storage name below cannot be influenced by the caller's filename.
        # The original is written to disk BEFORE the registry row is created,
        # so a crash here leaves at most an unreferenced file, never a
        # registry row pointing at a missing/partial original.
        version_id = uuid.uuid4().hex
        final_original_path = self._originals_dir / f"{version_id}{result.extension}"
        write_bytes_atomic(final_original_path, result.content)
        version = self._registry.create_version(
            version_id=version_id,
            document_id=document_id,
            checksum=result.checksum,
            extension=result.extension,
            original_path=str(final_original_path),
            original_filename=receiver.raw_filename,
            content_type=receiver.content_type,
            size_bytes=result.size_bytes,
        )

        candidate_result = process_candidate(
            document_id=document_id,
            version_id=version.version_id,
            original_path=final_original_path,
            extension=result.extension,
            title=display_title,
            source_url=source_url,
            domain=domain,
            authority_level=authority_level,
            candidate_dir=self._candidates_dir / version.version_id,
        )
        version = self._registry.update_candidate_artifacts(
            version.version_id,
            parse_status=candidate_result.parse_status,
            candidate_processed_path=str(candidate_result.processed_path),
            candidate_chunks_path=str(candidate_result.chunks_path),
            parse_warnings=json.dumps(candidate_result.warnings) if candidate_result.warnings else None,
        )

        return UploadOutcome(
            document_id=document_id,
            version_id=version.version_id,
            duplicate=False,
            parse_status=version.parse_status,
            review_status=version.review_status,
            warnings=candidate_result.warnings,
        )

    # -- read ---------------------------------------------------------------

    def list_versions(self, document_id: str) -> list[VersionRecord]:
        return self._registry.list_versions(document_id)

    def get_version_or_raise(self, version_id: str) -> VersionRecord:
        version = self._registry.get_version(version_id)
        if version is None:
            raise LifecycleError("version_not_found", f"Version '{version_id}' does not exist.", status_code=404)
        return version

    # -- review / publish / retire / rollback --------------------------------

    def review(self, version_id: str) -> VersionRecord:
        version = self.get_version_or_raise(version_id)
        if version.review_status == "reviewed":
            return version
        if version.review_status != "candidate":
            raise LifecycleError(
                "invalid_transition",
                f"Version '{version_id}' is '{version.review_status}', not eligible for review.",
                status_code=409,
            )
        if version.parse_status != "ok":
            raise LifecycleError(
                "not_parsed",
                f"Version '{version_id}' has parse_status '{version.parse_status}'; it cannot be reviewed.",
                status_code=409,
            )
        return self._registry.update_review_status(version_id, "reviewed")

    def publish(self, version_id: str) -> VersionRecord:
        version = self.get_version_or_raise(version_id)
        if version.review_status == "published":
            return version
        if version.review_status != "reviewed":
            raise LifecycleError(
                "invalid_transition",
                f"Version '{version_id}' is '{version.review_status}', not eligible for publish.",
                status_code=409,
            )
        if not version.candidate_chunks_path:
            raise LifecycleError(
                "missing_candidate_artifacts",
                f"Version '{version_id}' has no candidate chunks to publish.",
                status_code=409,
            )

        document = self._registry.get_document(version.document_id)
        manifest_row = self._build_manifest_row(document, version)
        chunk_records = self._read_candidate_chunks(version.candidate_chunks_path)

        previous = self._registry.get_published_version(version.document_id)
        apply_live_state(
            manifest_path=self._live_manifest_path,
            chunks_path=self._live_chunks_path,
            document_id=version.document_id,
            manifest_row=manifest_row,
            chunk_records=chunk_records,
        )

        if previous is not None and previous.version_id != version_id:
            self._registry.update_review_status(previous.version_id, "superseded", superseded_by=version_id)
        updated = self._registry.update_review_status(
            version_id,
            "published",
            supersedes=previous.version_id if previous else None,
            published_at=self._now(),
        )
        self._refresh_live_caches()
        return updated

    def retire(self, version_id: str) -> VersionRecord:
        version = self.get_version_or_raise(version_id)
        if version.review_status == "retired":
            return version
        if version.review_status != "published":
            raise LifecycleError(
                "invalid_transition",
                f"Version '{version_id}' is '{version.review_status}', not eligible for retire.",
                status_code=409,
            )

        apply_live_state(
            manifest_path=self._live_manifest_path,
            chunks_path=self._live_chunks_path,
            document_id=version.document_id,
            manifest_row=None,
            chunk_records=[],
        )
        updated = self._registry.update_review_status(version_id, "retired")
        self._refresh_live_caches()
        return updated

    def rollback(self, document_id: str, to_version_id: str) -> VersionRecord:
        target = self.get_version_or_raise(to_version_id)
        if target.document_id != document_id:
            raise LifecycleError(
                "mismatched_document",
                f"Version '{to_version_id}' does not belong to document '{document_id}'.",
                status_code=400,
            )
        if target.review_status not in {"published", "superseded", "retired"}:
            raise LifecycleError(
                "invalid_rollback_target",
                f"Version '{to_version_id}' is '{target.review_status}'; only a previously published "
                "version can be restored.",
                status_code=409,
            )
        if target.parse_status != "ok" or not target.candidate_chunks_path:
            raise LifecycleError(
                "missing_candidate_artifacts",
                f"Version '{to_version_id}' has no usable candidate chunks to restore.",
                status_code=409,
            )

        current = self._registry.get_published_version(document_id)
        if current is not None and current.version_id == to_version_id:
            return target  # already live: idempotent no-op

        document = self._registry.get_document(document_id)
        manifest_row = self._build_manifest_row(document, target)
        chunk_records = self._read_candidate_chunks(target.candidate_chunks_path)

        apply_live_state(
            manifest_path=self._live_manifest_path,
            chunks_path=self._live_chunks_path,
            document_id=document_id,
            manifest_row=manifest_row,
            chunk_records=chunk_records,
        )

        if current is not None:
            self._registry.update_review_status(current.version_id, "superseded", superseded_by=to_version_id)
        updated = self._registry.update_review_status(
            to_version_id,
            "published",
            superseded_by=None,
            supersedes=current.version_id if current else target.supersedes,
        )
        self._registry.record_note(
            to_version_id, "rollback", f"restored_over={current.version_id if current else None}"
        )
        self._refresh_live_caches()
        return updated

    # -- helpers --------------------------------------------------------------

    @staticmethod
    def _now() -> str:
        from rag.lifecycle.registry import now_iso

        return now_iso()

    @staticmethod
    def _read_candidate_chunks(chunks_path: str) -> list[dict]:
        path = Path(chunks_path)
        if not path.exists():
            return []
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return [json.loads(line) for line in lines]

    @staticmethod
    def _build_manifest_row(document, version: VersionRecord) -> dict:
        return {
            "doc_id": version.document_id,
            "title": (document.title if document and document.title else version.document_id),
            "source_url": (document.source_url if document else None) or "",
            "source_type": _source_type_for_extension(version.extension),
            "domain": (document.domain if document else None) or "unknown",
            "authority_level": (document.authority_level if document else None) or "unknown",
            "language": "",
            "published_at": LifecycleService._now(),
            "crawled_at": "",
            "file_path": version.original_path,
            "checksum": version.checksum,
            "status": "active",
            "notes": "",
        }


def _source_type_for_extension(extension: str) -> str:
    from rag.lifecycle.naming import SOURCE_TYPE_BY_EXTENSION

    return SOURCE_TYPE_BY_EXTENSION.get(extension.casefold(), "text")


def _stem_for_title(raw_filename: str | None) -> str | None:
    if not raw_filename:
        return None
    stem = raw_filename.rsplit(".", 1)[0].strip()
    return stem or None
