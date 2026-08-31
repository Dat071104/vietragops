from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import get_settings, get_web_import_service
from app.core.errors import AppError
from rag.lifecycle.gcs_storage import GcsStorageError


router = APIRouter(prefix="/admin", tags=["admin"])


class WebImportRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    title: str | None = Field(default=None, max_length=300)


@router.post("/web/import")
def import_web_document(payload: WebImportRequest) -> dict:
    """Import one allowlisted URL into the GCS candidate lifecycle.

    The route is intentionally mounted only on the private API service in the
    Gate 09R deployment. It never reviews or publishes the returned version.
    """

    if get_settings().storage_backend != "gcs":
        raise AppError("Cloud web import is disabled in the local backend.", status_code=404)
    try:
        outcome = get_web_import_service().import_url(payload.url, title=payload.title)
    except GcsStorageError as exc:
        raise AppError(exc.message, status_code=503) from exc
    return asdict(outcome)
