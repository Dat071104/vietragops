from __future__ import annotations

import csv
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.config import get_settings, get_store
from app.core.errors import AppError
from app.schemas.document import DocumentDetail, DocumentIndexResponse, DocumentSummary, DocumentUploadResponse


router = APIRouter(prefix="/documents", tags=["documents"])


def _load_manifest_rows() -> list[dict]:
    settings = get_settings()
    with settings.manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)) -> DocumentUploadResponse:
    settings = get_settings()
    settings.raw_upload_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for file in files:
        target = settings.raw_upload_dir / file.filename
        target.write_bytes(await file.read())
        saved.append(file.filename)
    return DocumentUploadResponse(filenames=saved, saved_dir=str(settings.raw_upload_dir))


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
