from __future__ import annotations

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    doc_id: str
    title: str
    source_url: str
    domain: str
    authority_level: str
    parse_status: str
    chunk_count: int


class DocumentDetail(DocumentSummary):
    source_type: str
    file_path: str
    checksum: str
    notes: str | None = None


class DocumentIndexResponse(BaseModel):
    chunk_count: int
    document_count: int


class DocumentIntakeItem(BaseModel):
    filename: str
    accepted: bool
    document_id: str | None = None
    version_id: str | None = None
    parse_status: str | None = None
    review_status: str | None = None
    duplicate: bool = False
    warnings: list[str] = []
    error_code: str | None = None
    error_message: str | None = None


class DocumentUploadResponse(BaseModel):
    results: list[DocumentIntakeItem]


class VersionSummary(BaseModel):
    document_id: str
    version_id: str
    checksum: str
    extension: str
    original_filename: str | None = None
    size_bytes: int
    parse_status: str
    review_status: str
    parse_warnings: str | None = None
    supersedes: str | None = None
    superseded_by: str | None = None
    created_at: str
    updated_at: str
    published_at: str | None = None


class RollbackRequest(BaseModel):
    to_version_id: str
