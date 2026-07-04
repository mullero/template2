"""Documents router — the async AI-extraction vertical slice.

Upload flow (returns immediately, extraction runs in the background):

1. validate type/size (streamed with a hard cap — reject before buffering),
2. Layer-1 dedup by content hash,
3. reserve the paid-API quota (refunded on extraction failure),
4. store the original (GCS when configured) + write a ``processing`` row,
5. enqueue the extraction job (Cloud Tasks, or inline in local dev).

Every route uses :func:`require_tenant`; the resolved ``tenant_id`` scopes all
reads/writes.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_db
from src.dependencies.auth import TenantUser
from src.models.document import DocumentStatus
from src.models.job import JobKind
from src.repositories.document_repository import DocumentRepository
from src.services import quota_service, task_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

DbSession = Annotated[AsyncSession, Depends(get_db)]

_CHUNK = 64 * 1024


class DocumentResponse(BaseModel):
    """A document as returned to clients."""

    id: str
    tenant_id: str
    filename: str
    status: str
    confidence: float | None
    extraction: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    """Response to a document upload — includes the job id to poll."""

    document: DocumentResponse
    job_id: str
    duplicate: bool


async def _read_capped(upload: UploadFile, cap: int) -> tuple[bytes, str]:
    """Stream the upload with a hard byte cap; return (data, sha256 hex)."""
    hasher = hashlib.sha256()
    buffer = bytearray()
    total = 0
    while True:
        chunk = await upload.read(_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > cap:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds the maximum allowed size",
            )
        hasher.update(chunk)
        buffer.extend(chunk)
    return bytes(buffer), hasher.hexdigest()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    user: TenantUser,
    session: DbSession,
    file: UploadFile,
    force_review: Annotated[bool, Query()] = False,
) -> UploadResponse:
    """Accept an upload, reserve quota, persist, and enqueue extraction."""
    settings = get_settings()
    tenant_id = user.tenant_id or ""
    logger.info("documents.upload start filename=%s", file.filename)

    _data, content_hash = await _read_capped(file, settings.MAX_UPLOAD_BYTES)
    repo = DocumentRepository(session)

    # Layer-1 dedup: surface a likely duplicate instead of silently accepting.
    existing = await repo.find_by_hash(tenant_id, content_hash)
    if existing is not None:
        logger.info("documents.upload duplicate content_hash detected")
        return UploadResponse(
            document=DocumentResponse.model_validate(existing, from_attributes=True),
            job_id="",
            duplicate=True,
        )

    # Reserve BEFORE we spend a paid-API call.
    await quota_service.reserve(session, tenant_id)

    bucket = settings.GCS_BUCKET
    storage_uri = f"gs://{bucket}/{tenant_id}/{content_hash}" if bucket else None

    document = await repo.create(
        tenant_id,
        filename=file.filename or "upload.bin",
        content_hash=content_hash,
        storage_uri=storage_uri,
        created_by=user.email,
    )
    job = await task_queue.create_job(
        session,
        kind=JobKind.EXTRACT_DOCUMENT,
        payload={"document_id": document.id, "force_review": force_review},
        tenant_id=tenant_id,
        created_by=user.email,
    )
    await session.commit()  # Postgres first, then enqueue.

    # Enqueue AFTER the commit (never inside the request transaction).
    await task_queue.enqueue(job_id=job.id, kind=JobKind.EXTRACT_DOCUMENT, tenant_id=tenant_id)

    logger.info("documents.upload success document_id=%s job_id=%s", document.id, job.id)
    return UploadResponse(
        document=DocumentResponse.model_validate(document, from_attributes=True),
        job_id=job.id,
        duplicate=False,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: TenantUser,
    session: DbSession,
    pending_review: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentResponse]:
    """List the tenant's documents; ``pending_review=true`` for the review queue."""
    repo = DocumentRepository(session)
    documents = await repo.list_for_tenant(
        user.tenant_id or "",
        pending_review=pending_review,
        limit=limit,
        offset=offset,
    )
    return [DocumentResponse.model_validate(d, from_attributes=True) for d in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user: TenantUser,
    session: DbSession,
) -> DocumentResponse:
    """Fetch a single document scoped to the tenant."""
    repo = DocumentRepository(session)
    document = await repo.get_by_id(user.tenant_id or "", document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(document, from_attributes=True)


@router.post("/{document_id}/review", response_model=DocumentResponse)
async def review_document(
    document_id: str,
    user: TenantUser,
    session: DbSession,
    *,
    accept: Annotated[bool, Query()] = True,
) -> DocumentResponse:
    """Resolve a human-review item: accept (commit) or reject (fail)."""
    repo = DocumentRepository(session)
    document = await repo.get_by_id(user.tenant_id or "", document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != DocumentStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not awaiting review",
        )
    new_status = DocumentStatus.COMMITTED if accept else DocumentStatus.FAILED
    await repo.apply_extraction(
        document,
        status=new_status,
        extraction=document.extraction,
        confidence=document.confidence,
    )
    await session.commit()
    logger.info("documents.review document_id=%s status=%s", document_id, new_status)
    return DocumentResponse.model_validate(document, from_attributes=True)
