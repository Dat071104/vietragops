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


class DocumentUploadResponse(BaseModel):
    filenames: list[str]
    saved_dir: str


class DocumentIndexResponse(BaseModel):
    chunk_count: int
    document_count: int
