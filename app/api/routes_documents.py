from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import get_lifecycle_service, get_live_manifest_rows, get_store
from app.core.errors import AppError
from app.schemas.document import (
    DocumentDetail,
    DocumentIndexResponse,
    DocumentIntakeItem,
    DocumentSummary,
    DocumentUploadResponse,
    RollbackRequest,
    VersionSummary,
)
from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.gcs_storage import GcsStorageError
from rag.lifecycle.registry import VersionRecord


router = APIRouter(prefix="/documents", tags=["documents"])

_UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


def _load_manifest_rows() -> list[dict]:
    return get_live_manifest_rows()


def _version_summary(version: VersionRecord) -> VersionSummary:
    return VersionSummary(
        document_id=version.document_id,
        version_id=version.version_id,
        checksum=version.checksum,
        extension=version.extension,
        original_filename=version.original_filename,
        size_bytes=version.size_bytes,
        parse_status=version.parse_status,
        review_status=version.review_status,
        parse_warnings=version.parse_warnings,
        candidate_canonical_path=version.candidate_canonical_path,
        candidate_extraction_path=version.candidate_extraction_path,
        supersedes=version.supersedes,
        superseded_by=version.superseded_by,
        created_at=version.created_at,
        updated_at=version.updated_at,
        published_at=version.published_at,
    )


def _raise_app_error(exc: LifecycleError) -> None:
    raise AppError(exc.message, status_code=exc.status_code) from exc


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    source_url: str | None = Form(None),
    publisher: str | None = Form(None),
    domain: str | None = Form(None),
    authority_level: str | None = Form(None),
) -> DocumentUploadResponse:
    """Governed intake: validate, checksum, store the original immutably, and
    run candidate-only parsing/chunking. Nothing here touches the live
    manifest or chunk index -- that only happens through an explicit
    review -> publish transition on the returned version_id.
    """
    service = get_lifecycle_service()
    results: list[DocumentIntakeItem] = []

    for file in files:
        try:
            receiver = service.begin_intake(filename=file.filename, content_type=file.content_type)
            while True:
                chunk = await file.read(_UPLOAD_READ_CHUNK_BYTES)
                if not chunk:
                    break
                receiver.feed(chunk)
            outcome = service.complete_intake(
                receiver,
                source_url=source_url,
                publisher=publisher,
                domain=domain,
                authority_level=authority_level,
            )
            results.append(
                DocumentIntakeItem(
                    filename=file.filename or "",
                    accepted=True,
                    document_id=outcome.document_id,
                    version_id=outcome.version_id,
                    parse_status=outcome.parse_status,
                    review_status=outcome.review_status,
                    duplicate=outcome.duplicate,
                    warnings=outcome.warnings,
                )
            )
        except LifecycleError as exc:
            results.append(
                DocumentIntakeItem(
                    filename=file.filename or "",
                    accepted=False,
                    error_code=exc.code,
                    error_message=exc.message,
                )
            )
        except GcsStorageError as exc:
            results.append(
                DocumentIntakeItem(
                    filename=file.filename or "",
                    accepted=False,
                    error_code=exc.code,
                    error_message=exc.message,
                )
            )
        finally:
            await file.close()

    return DocumentUploadResponse(results=results)


@router.post("/index", response_model=DocumentIndexResponse)
def index_documents() -> DocumentIndexResponse:
    store = get_store()
    doc_count = len({chunk.doc_id for chunk in store})
    return DocumentIndexResponse(chunk_count=len(store), document_count=doc_count)


@router.get("", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    store = get_store()
    counts = {}
    for chunk in store:
        counts[chunk.doc_id] = counts.get(chunk.doc_id, 0) + 1
    return [
        DocumentSummary(
            doc_id=row["doc_id"],
            title=row["title"],
            source_url=row["source_url"],
            domain=row["domain"],
            authority_level=row["authority_level"],
            parse_status="ok",
            chunk_count=counts.get(row["doc_id"], 0),
        )
        for row in _load_manifest_rows()
    ]


@router.get("/{doc_id}/versions", response_model=list[VersionSummary])
def list_document_versions(doc_id: str) -> list[VersionSummary]:
    service = get_lifecycle_service()
    return [_version_summary(version) for version in service.list_versions(doc_id)]


@router.post("/versions/{version_id}/review", response_model=VersionSummary)
def review_document_version(version_id: str) -> VersionSummary:
    service = get_lifecycle_service()
    try:
        return _version_summary(service.review(version_id))
    except LifecycleError as exc:
        _raise_app_error(exc)


@router.post("/versions/{version_id}/publish", response_model=VersionSummary)
def publish_document_version(version_id: str) -> VersionSummary:
    service = get_lifecycle_service()
    try:
        return _version_summary(service.publish(version_id))
    except LifecycleError as exc:
        _raise_app_error(exc)


@router.post("/versions/{version_id}/retire", response_model=VersionSummary)
def retire_document_version(version_id: str) -> VersionSummary:
    service = get_lifecycle_service()
    try:
        return _version_summary(service.retire(version_id))
    except LifecycleError as exc:
        _raise_app_error(exc)


@router.post("/{doc_id}/rollback", response_model=VersionSummary)
def rollback_document(doc_id: str, request: RollbackRequest) -> VersionSummary:
    service = get_lifecycle_service()
    try:
        return _version_summary(service.rollback(doc_id, request.to_version_id))
    except LifecycleError as exc:
        _raise_app_error(exc)


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: str) -> DocumentDetail:
    store = get_store()
    counts = {}
    for chunk in store:
        counts[chunk.doc_id] = counts.get(chunk.doc_id, 0) + 1
    for row in _load_manifest_rows():
        if row["doc_id"] == doc_id:
            return DocumentDetail(
                doc_id=row["doc_id"],
                title=row["title"],
                source_url=row["source_url"],
                domain=row["domain"],
                authority_level=row["authority_level"],
                parse_status="ok",
                chunk_count=counts.get(row["doc_id"], 0),
                source_type=row["source_type"],
                file_path=row["file_path"],
                checksum=row["checksum"],
                notes=row.get("notes"),
            )
    raise AppError(f"Document '{doc_id}' not found.", status_code=404)
