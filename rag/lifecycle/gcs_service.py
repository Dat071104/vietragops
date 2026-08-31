"""Cloud Storage-backed candidate lifecycle for Gate 09R.

The existing ``LifecycleService`` remains the local/offline implementation.
This sibling service keeps the same public lifecycle contract while storing
originals, candidate artifacts, release bundles, and registry transitions in
Cloud Storage.  Local temporary files are used only while MarkItDown and the
existing validators run inside one request.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import json
from dataclasses import replace
from pathlib import Path
import tempfile
import uuid

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.extraction import validate_candidate_artifacts
from rag.lifecycle.gcs_registry import GcsLifecycleRegistry, GcsRegistryConflictError
from rag.lifecycle.gcs_storage import (
    GcsNotFoundError,
    GcsRelease,
    GcsReleaseStore,
    GcsStorageError,
    ObjectStore,
    object_name_from_uri,
)
from rag.lifecycle.intake import IntakeReceiver
from rag.lifecycle.naming import SOURCE_TYPE_BY_EXTENSION
from rag.lifecycle.pipeline import process_candidate
from rag.lifecycle.registry import DocumentRecord, VersionRecord


MANIFEST_FIELDNAMES = [
    "doc_id",
    "title",
    "source_url",
    "source_type",
    "domain",
    "authority_level",
    "language",
    "published_at",
    "crawled_at",
    "file_path",
    "checksum",
    "status",
    "notes",
]


class GcsLifecycleService:
    """Same lifecycle operations as the local service, backed by GCS CAS."""

    def __init__(
        self,
        *,
        registry: GcsLifecycleRegistry,
        objects: ObjectStore,
        max_upload_bytes: int,
        refresh_live_caches,
        pdf_parser_policy: str = "markitdown",
        bootstrap_release_id: str | None = None,
    ) -> None:
        self._registry = registry
        self._objects = objects
        self._releases = GcsReleaseStore(objects)
        self._max_upload_bytes = max_upload_bytes
        self._refresh_live_caches = refresh_live_caches
        self._pdf_parser_policy = pdf_parser_policy
        self._bootstrap_release_id = (bootstrap_release_id or "").strip() or None

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
    ):
        result = receiver.finalize()
        document_id = result.slug
        title = _stem_for_title(receiver.raw_filename) or document_id
        self._registry.get_or_create_document(
            document_id=document_id,
            title=title,
            source_url=source_url,
            publisher=publisher,
            domain=domain,
            authority_level=authority_level,
        )
        existing = self._registry.find_version_by_checksum(document_id, result.checksum)
        if existing is not None:
            from rag.lifecycle.service import UploadOutcome

            return UploadOutcome(
                document_id=document_id,
                version_id=existing.version_id,
                duplicate=True,
                parse_status=existing.parse_status,
                review_status=existing.review_status,
                warnings=[],
            )

        version_id = uuid.uuid4().hex
        original_name = f"sources/original/{version_id}{result.extension}"
        self._objects.put_immutable(original_name, result.content, content_type=receiver.content_type)
        version = self._registry.create_version(
            version_id=version_id,
            document_id=document_id,
            checksum=result.checksum,
            extension=result.extension,
            original_path=self._releases.uri(original_name),
            original_filename=receiver.raw_filename,
            content_type=receiver.content_type,
            size_bytes=result.size_bytes,
        )

        with tempfile.TemporaryDirectory(prefix="vietragops-gcs-") as temp_root:
            root = Path(temp_root)
            local_originals = root / "originals"
            local_originals.mkdir(parents=True, exist_ok=True)
            local_original = local_originals / f"{version_id}{result.extension}"
            local_original.write_bytes(result.content)
            local_candidate = root / "candidates" / version_id
            candidate_result = process_candidate(
                document_id=document_id,
                version_id=version.version_id,
                original_path=local_original,
                extension=result.extension,
                title=title,
                source_url=source_url,
                domain=domain,
                authority_level=authority_level,
                candidate_dir=local_candidate,
                originals_dir=local_originals,
                pdf_parser=self._pdf_parser_policy,
            )
            extraction_record = json.loads(candidate_result.extraction_path.read_text(encoding="utf-8"))
            extraction_record["original_path"] = self._releases.uri(original_name)
            if candidate_result.canonical_path is not None:
                extraction_record["canonical_path"] = self._releases.uri(
                    f"candidates/{version_id}/canonical.md"
                )
            candidate_result.extraction_path.write_text(
                json.dumps(extraction_record, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            candidate_paths = {
                "processed": candidate_result.processed_path,
                "chunks": candidate_result.chunks_path,
                "extraction": candidate_result.extraction_path,
            }
            if candidate_result.canonical_path is not None:
                candidate_paths["canonical"] = candidate_result.canonical_path
            for label, path in candidate_paths.items():
                self._objects.put_immutable(
                    f"candidates/{version_id}/{_candidate_filename(label)}",
                    path.read_bytes(),
                    content_type=_candidate_content_type(label),
                )

        version = self._registry.update_candidate_artifacts(
            version.version_id,
            parse_status=candidate_result.parse_status,
            candidate_processed_path=self._releases.uri(f"candidates/{version_id}/processed.jsonl"),
            candidate_chunks_path=self._releases.uri(f"candidates/{version_id}/chunks_500.jsonl"),
            candidate_canonical_path=(
                self._releases.uri(f"candidates/{version_id}/canonical.md")
                if candidate_result.canonical_path is not None
                else None
            ),
            candidate_extraction_path=self._releases.uri(f"candidates/{version_id}/extraction.json"),
            parse_warnings=json.dumps(candidate_result.warnings) if candidate_result.warnings else None,
        )
        from rag.lifecycle.service import UploadOutcome

        return UploadOutcome(
            document_id=document_id,
            version_id=version.version_id,
            duplicate=False,
            parse_status=version.parse_status,
            review_status=version.review_status,
            warnings=candidate_result.warnings,
        )

    # -- read ------------------------------------------------------------

    def list_versions(self, document_id: str) -> list[VersionRecord]:
        return self._registry.list_versions(document_id)

    def get_version_or_raise(self, version_id: str) -> VersionRecord:
        version = self._registry.get_version(version_id)
        if version is None:
            raise LifecycleError("version_not_found", f"Version '{version_id}' does not exist.", status_code=404)
        return version

    def load_live_release(self) -> GcsRelease:
        release_id = self._registry.get_active_release_id() or self._bootstrap_release_id
        if not release_id:
            return GcsRelease(release_id="empty", manifest_bytes=_render_manifest([]), chunks_bytes=b"", metadata={})
        try:
            return self._releases.read_release(release_id)
        except GcsStorageError as exc:
            raise LifecycleError("storage_unavailable", exc.message, status_code=503) from exc

    def live_manifest_rows(self) -> list[dict[str, str]]:
        return self.load_live_release().manifest_rows()

    # -- review / publish / retire / rollback ---------------------------

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
        _, issues = self._ensure_candidate_integrity(version)
        if issues:
            raise LifecycleError(
                "candidate_unusable",
                f"Version '{version_id}' has unusable candidate artifacts; it cannot be reviewed.",
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
        version, issues = self._ensure_candidate_integrity(version)
        if issues or version.parse_status != "ok":
            raise LifecycleError(
                "candidate_unusable",
                f"Version '{version_id}' has unusable candidate artifacts; it cannot be published.",
                status_code=409,
            )
        previous = self._registry.get_published_version(version.document_id)
        release = self._write_live_release(version, previous)
        try:
            updated = self._registry.activate_release(
                version_id=version_id,
                release_id=release.release_id,
                previous_version_id=previous.version_id if previous else None,
                published_at=_now_iso(),
            )
        except GcsRegistryConflictError as exc:
            raise LifecycleError("storage_conflict", exc.message, status_code=409) from exc
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
        release = self._write_live_release(version, None, remove_document_id=version.document_id)
        try:
            updated = self._registry.activate_retired_release(version_id=version_id, release_id=release.release_id)
        except GcsRegistryConflictError as exc:
            raise LifecycleError("storage_conflict", exc.message, status_code=409) from exc
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
                f"Version '{to_version_id}' is '{target.review_status}'; only a previously published version can be restored.",
                status_code=409,
            )
        target, issues = self._ensure_candidate_integrity(target)
        if issues or target.parse_status != "ok":
            raise LifecycleError(
                "candidate_unusable",
                f"Version '{to_version_id}' has unusable candidate artifacts; it cannot be restored.",
                status_code=409,
            )
        current = self._registry.get_published_version(document_id)
        if current is not None and current.version_id == to_version_id:
            return target
        release = self._write_live_release(target, current, override_document=target)
        try:
            updated = self._registry.activate_rollback_release(
                target_version_id=to_version_id,
                current_version_id=current.version_id if current else None,
                release_id=release.release_id,
            )
        except GcsRegistryConflictError as exc:
            raise LifecycleError("storage_conflict", exc.message, status_code=409) from exc
        self._refresh_live_caches()
        return updated

    # -- candidate integrity --------------------------------------------

    def _ensure_candidate_integrity(self, version: VersionRecord) -> tuple[VersionRecord, tuple[str, ...]]:
        try:
            with tempfile.TemporaryDirectory(prefix="vietragops-gcs-validate-") as temp_root:
                root = Path(temp_root)
                local_original = self._download_uri(version.original_path, root / f"original{version.extension}")
                local_paths: dict[str, Path | None] = {
                    "candidate_processed_path": self._download_optional_uri(
                        version.candidate_processed_path, root / "processed.jsonl"
                    ),
                    "candidate_chunks_path": self._download_optional_uri(
                        version.candidate_chunks_path, root / "chunks_500.jsonl"
                    ),
                    "candidate_canonical_path": self._download_optional_uri(
                        version.candidate_canonical_path, root / "canonical.md"
                    ),
                    "candidate_extraction_path": self._download_optional_uri(
                        version.candidate_extraction_path, root / "extraction.json"
                    ),
                }
                extraction_path = local_paths["candidate_extraction_path"]
                if extraction_path is not None and extraction_path.is_file():
                    record = json.loads(extraction_path.read_text(encoding="utf-8"))
                    record["original_path"] = str(local_original)
                    canonical_path = local_paths["candidate_canonical_path"]
                    record["canonical_path"] = str(canonical_path) if canonical_path is not None else None
                    extraction_path.write_text(
                        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
                    )
                materialized = replace(
                    version,
                    original_path=str(local_original),
                    **{key: str(value) if value is not None else None for key, value in local_paths.items()},
                )
                issues = validate_candidate_artifacts(materialized)
        except (GcsStorageError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            issues = ("candidate_storage_unavailable",)
        if not issues:
            return version, ()
        warnings: list[str] = []
        if version.parse_warnings:
            try:
                existing = json.loads(version.parse_warnings)
            except json.JSONDecodeError:
                existing = []
            if isinstance(existing, list):
                warnings.extend(item for item in existing if isinstance(item, str))
        warnings.extend(issues)
        failed = self._registry.update_candidate_artifacts(
            version.version_id,
            parse_status="failed",
            candidate_processed_path=version.candidate_processed_path,
            candidate_chunks_path=version.candidate_chunks_path,
            candidate_canonical_path=version.candidate_canonical_path,
            candidate_extraction_path=version.candidate_extraction_path,
            parse_warnings=json.dumps(list(dict.fromkeys(warnings))),
        )
        return failed, tuple(dict.fromkeys(issues))

    def _download_uri(self, uri: str, path: Path) -> Path:
        name = object_name_from_uri(uri, bucket_name=self._objects.bucket_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self._objects.get(name).content)
        return path

    def _download_optional_uri(self, uri: str | None, path: Path) -> Path | None:
        if not uri:
            return None
        return self._download_uri(uri, path)

    # -- release bundles -------------------------------------------------

    def _write_live_release(
        self,
        version: VersionRecord,
        previous: VersionRecord | None,
        *,
        remove_document_id: str | None = None,
        override_document: VersionRecord | None = None,
    ) -> GcsRelease:
        live = self.load_live_release()
        rows = [row for row in live.manifest_rows() if row.get("doc_id") != (remove_document_id or "")]
        chunks = [chunk for chunk in live.chunk_records() if chunk.get("doc_id") != (remove_document_id or "")]
        document_id = version.document_id
        if remove_document_id is None:
            rows = [row for row in rows if row.get("doc_id") != document_id]
            chunks = [chunk for chunk in chunks if chunk.get("doc_id") != document_id]
            target = override_document or version
            document = self._registry.get_document(document_id)
            rows.append(self._manifest_row(document, target))
            chunks.extend(self._read_candidate_chunks(target.candidate_chunks_path))
        manifest_bytes = _render_manifest(rows)
        chunks_bytes = _render_chunks(chunks)
        release_id = f"release-{uuid.uuid4().hex}"
        return self._releases.write_release(
            release_id,
            manifest_bytes=manifest_bytes,
            chunks_bytes=chunks_bytes,
            metadata={
                "document_id": document_id,
                "previous_version_id": previous.version_id if previous else None,
                "operation": "retire" if remove_document_id else "publish_or_rollback",
            },
        )

    def _read_candidate_chunks(self, uri: str | None) -> list[dict]:
        if not uri:
            raise LifecycleError("missing_candidate_artifacts", "Candidate chunks are required.", status_code=409)
        try:
            name = object_name_from_uri(uri, bucket_name=self._objects.bucket_name)
            payload = self._objects.get(name).content.decode("utf-8")
            records = []
            for line in payload.splitlines():
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError("candidate chunk is not an object")
                    records.append(value)
            return records
        except (GcsStorageError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise LifecycleError("candidate_unusable", "Candidate chunks are unavailable or invalid.", status_code=409) from exc

    def _manifest_row(self, document: DocumentRecord | None, version: VersionRecord) -> dict[str, str]:
        return {
            "doc_id": version.document_id,
            "title": (document.title if document and document.title else version.document_id),
            "source_url": (document.source_url if document else None) or "",
            "source_type": SOURCE_TYPE_BY_EXTENSION.get(version.extension.casefold(), "text"),
            "domain": (document.domain if document else None) or "unknown",
            "authority_level": (document.authority_level if document else None) or "unknown",
            "language": "",
            "published_at": _now_iso(),
            "crawled_at": "",
            "file_path": version.original_path,
            "checksum": version.checksum,
            "status": "active",
            "notes": "",
        }


def _render_manifest(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=MANIFEST_FIELDNAMES)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in MANIFEST_FIELDNAMES})
    return buffer.getvalue().encode("utf-8")


def _render_chunks(records: list[dict]) -> bytes:
    from rag.chunking.metadata_builder import json_dumps

    return "".join(json_dumps(record) + "\n" for record in records).encode("utf-8")


def _candidate_filename(label: str) -> str:
    return {
        "processed": "processed.jsonl",
        "chunks": "chunks_500.jsonl",
        "canonical": "canonical.md",
        "extraction": "extraction.json",
    }[label]


def _candidate_content_type(label: str) -> str:
    return {
        "processed": "application/x-ndjson",
        "chunks": "application/x-ndjson",
        "canonical": "text/markdown",
        "extraction": "application/json",
    }[label]


def _stem_for_title(raw_filename: str | None) -> str | None:
    if not raw_filename:
        return None
    stem = raw_filename.rsplit(".", 1)[0].strip()
    return stem or None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
