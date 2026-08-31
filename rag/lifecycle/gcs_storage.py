"""Durable Cloud Storage boundary for Gate 09R.

The application keeps its local file-backed implementation for offline use.
This module adds a deliberately small object boundary for the cloud product:
immutable objects are written once, and mutable pointer objects are updated
with a Cloud Storage generation precondition.  A failed compare-and-swap is a
typed conflict; it is never silently overwritten.

The Google client is imported lazily so the existing offline test and product
paths do not require Google credentials or a network connection.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol


class GcsStorageError(RuntimeError):
    """Stable, non-secret storage failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class GcsNotFoundError(GcsStorageError):
    def __init__(self, message: str = "Cloud Storage object was not found.") -> None:
        super().__init__("not_found", message)


class GcsPreconditionFailed(GcsStorageError):
    def __init__(self, message: str = "Cloud Storage generation precondition failed.") -> None:
        super().__init__("precondition_failed", message)


@dataclass(frozen=True)
class GcsObject:
    name: str
    content: bytes
    generation: int
    content_type: str | None = None


class ObjectStore(Protocol):
    bucket_name: str

    def get(self, name: str) -> GcsObject:
        ...

    def put(
        self,
        name: str,
        content: bytes,
        *,
        if_generation_match: int | None = None,
        content_type: str | None = None,
    ) -> GcsObject:
        ...

    def put_immutable(self, name: str, content: bytes, *, content_type: str | None = None) -> GcsObject:
        ...


class MemoryObjectStore:
    """Deterministic object store used by unit tests and local contract checks."""

    def __init__(self, bucket_name: str = "test-bucket") -> None:
        self.bucket_name = bucket_name
        self._objects: dict[str, GcsObject] = {}

    def get(self, name: str) -> GcsObject:
        try:
            return self._objects[name]
        except KeyError as exc:
            raise GcsNotFoundError() from exc

    def put(
        self,
        name: str,
        content: bytes,
        *,
        if_generation_match: int | None = None,
        content_type: str | None = None,
    ) -> GcsObject:
        current = self._objects.get(name)
        if if_generation_match == 0 and current is not None:
            raise GcsPreconditionFailed()
        if if_generation_match not in (None, 0):
            if current is None or current.generation != if_generation_match:
                raise GcsPreconditionFailed()
        generation = (current.generation + 1) if current is not None else 1
        result = GcsObject(name=name, content=bytes(content), generation=generation, content_type=content_type)
        self._objects[name] = result
        return result

    def put_immutable(self, name: str, content: bytes, *, content_type: str | None = None) -> GcsObject:
        return self.put(name, content, if_generation_match=0, content_type=content_type)

    def exists(self, name: str) -> bool:
        return name in self._objects


class GcsObjectStore:
    """Cloud Storage object store using ADC and a user-managed bucket."""

    def __init__(self, bucket_name: str, *, client: Any | None = None) -> None:
        bucket_name = (bucket_name or "").strip()
        if not bucket_name:
            raise GcsStorageError("missing_bucket", "VIETRAGOPS_GCS_BUCKET is required for the GCS backend.")
        self.bucket_name = bucket_name
        if client is None:
            try:
                from google.cloud import storage
            except ImportError as exc:
                raise GcsStorageError(
                    "google_cloud_storage_unavailable",
                    "google-cloud-storage is required for the GCS backend.",
                ) from exc
            client = storage.Client()
        self._client = client
        self._bucket = client.bucket(bucket_name)

    def get(self, name: str) -> GcsObject:
        blob = self._bucket.blob(name)
        try:
            content = blob.download_as_bytes()
            generation = int(blob.generation or 0)
            if generation <= 0:
                blob.reload()
                generation = int(blob.generation or 0)
            return GcsObject(
                name=name,
                content=content,
                generation=generation,
                content_type=getattr(blob, "content_type", None),
            )
        except Exception as exc:  # noqa: BLE001 - map SDK exceptions to stable codes
            raise _map_gcs_exception(exc) from exc

    def put(
        self,
        name: str,
        content: bytes,
        *,
        if_generation_match: int | None = None,
        content_type: str | None = None,
    ) -> GcsObject:
        blob = self._bucket.blob(name)
        try:
            blob.upload_from_string(
                content,
                content_type=content_type,
                if_generation_match=if_generation_match,
            )
            generation = int(blob.generation or 0)
            if generation <= 0:
                blob.reload()
                generation = int(blob.generation or 0)
            return GcsObject(name=name, content=bytes(content), generation=generation, content_type=content_type)
        except Exception as exc:  # noqa: BLE001 - map SDK exceptions to stable codes
            raise _map_gcs_exception(exc) from exc

    def put_immutable(self, name: str, content: bytes, *, content_type: str | None = None) -> GcsObject:
        return self.put(name, content, if_generation_match=0, content_type=content_type)

    def exists(self, name: str) -> bool:
        try:
            self.get(name)
        except GcsNotFoundError:
            return False
        return True


@dataclass(frozen=True)
class GcsRelease:
    release_id: str
    manifest_bytes: bytes
    chunks_bytes: bytes
    metadata: dict[str, Any]

    def manifest_rows(self) -> list[dict[str, str]]:
        import csv
        import io

        with io.StringIO(self.manifest_bytes.decode("utf-8-sig", errors="strict"), newline="") as handle:
            return list(csv.DictReader(handle))

    def chunk_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for line in self.chunks_bytes.decode("utf-8", errors="strict").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise GcsStorageError("invalid_release", "Release chunk object must be a JSON object.")
                records.append(value)
        return records


class GcsReleaseStore:
    """Read and write immutable release bundles in one approved bucket."""

    def __init__(self, objects: ObjectStore, *, prefix: str = "releases") -> None:
        self._objects = objects
        self._prefix = prefix.strip("/") or "releases"

    def object_name(self, release_id: str, filename: str) -> str:
        safe_release = _safe_component(release_id)
        safe_filename = _safe_component(filename)
        return f"{self._prefix}/{safe_release}/{safe_filename}"

    def write_release(
        self,
        release_id: str,
        *,
        manifest_bytes: bytes,
        chunks_bytes: bytes,
        metadata: dict[str, Any] | None = None,
    ) -> GcsRelease:
        manifest_name = self.object_name(release_id, "manifest.csv")
        chunks_name = self.object_name(release_id, "chunks_500.jsonl")
        release_metadata = {
            "schema": "vietragops.release",
            "schema_version": 1,
            "release_id": release_id,
            "manifest_object": manifest_name,
            "chunks_object": chunks_name,
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "chunks_sha256": hashlib.sha256(chunks_bytes).hexdigest(),
            **(metadata or {}),
        }
        self._objects.put_immutable(manifest_name, manifest_bytes, content_type="text/csv")
        self._objects.put_immutable(chunks_name, chunks_bytes, content_type="application/x-ndjson")
        self._objects.put_immutable(
            self.object_name(release_id, "release.json"),
            (json.dumps(release_metadata, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"),
            content_type="application/json",
        )
        return GcsRelease(
            release_id=release_id,
            manifest_bytes=manifest_bytes,
            chunks_bytes=chunks_bytes,
            metadata=release_metadata,
        )

    def read_release(self, release_id: str) -> GcsRelease:
        metadata_obj = self._objects.get(self.object_name(release_id, "release.json"))
        try:
            metadata = json.loads(metadata_obj.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GcsStorageError("invalid_release", "Release metadata is not valid JSON.") from exc
        if not isinstance(metadata, dict) or metadata.get("release_id") != release_id:
            raise GcsStorageError("invalid_release", "Release metadata identity is invalid.")
        manifest_name = metadata.get("manifest_object")
        chunks_name = metadata.get("chunks_object")
        if not isinstance(manifest_name, str) or not isinstance(chunks_name, str):
            raise GcsStorageError("invalid_release", "Release metadata lacks object names.")
        manifest = self._objects.get(manifest_name).content
        chunks = self._objects.get(chunks_name).content
        if metadata.get("manifest_sha256") != hashlib.sha256(manifest).hexdigest():
            raise GcsStorageError("release_checksum_mismatch", "Release manifest checksum does not match metadata.")
        if metadata.get("chunks_sha256") != hashlib.sha256(chunks).hexdigest():
            raise GcsStorageError("release_checksum_mismatch", "Release chunks checksum does not match metadata.")
        return GcsRelease(release_id=release_id, manifest_bytes=manifest, chunks_bytes=chunks, metadata=metadata)

    def uri(self, name: str) -> str:
        return f"gs://{self._objects.bucket_name}/{name}"


def object_name_from_uri(uri: str, *, bucket_name: str) -> str:
    prefix = f"gs://{bucket_name}/"
    if not isinstance(uri, str) or not uri.startswith(prefix):
        raise GcsStorageError("invalid_object_uri", "Object URI is outside the configured bucket.")
    name = uri[len(prefix):].strip("/")
    if not name:
        raise GcsStorageError("invalid_object_uri", "Object URI has no object name.")
    return name


def _safe_component(value: str) -> str:
    if not isinstance(value, str) or not value or "/" in value or "\\" in value or value in {".", ".."}:
        raise GcsStorageError("invalid_object_name", "Object name component is invalid.")
    return value


def _map_gcs_exception(exc: Exception) -> GcsStorageError:
    code = getattr(exc, "code", None)
    name = type(exc).__name__.casefold()
    if code == 404 or "notfound" in name:
        return GcsNotFoundError()
    if code == 412 or "precondition" in name:
        return GcsPreconditionFailed()
    return GcsStorageError("storage_error", "Cloud Storage operation failed.")
