"""Document repository — tenant-scoped data access for :class:`Document`.

Every read requires a ``tenant_id`` and filters by it plus ``deleted_at IS NULL``
(the latter is also enforced globally by the soft-delete filter).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document, DocumentStatus


class DocumentRepository:
    """Async repository for uploaded documents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: str,
        *,
        filename: str,
        content_hash: str,
        storage_uri: str | None,
        created_by: str | None = None,
    ) -> Document:
        """Insert a processing document for the tenant. Caller commits."""
        document = Document(
            tenant_id=tenant_id,
            filename=filename,
            content_hash=content_hash,
            storage_uri=storage_uri,
            status=DocumentStatus.PROCESSING,
            created_by=created_by,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_by_id(self, tenant_id: str, document_id: str) -> Document | None:
        """Return a single document scoped to the tenant, or ``None``."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_worker(self, document_id: str) -> Document | None:
        """Return a document by id WITHOUT tenant scoping (internal worker only)."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_hash(self, tenant_id: str, content_hash: str) -> Document | None:
        """Layer-1 dedup: find an existing document with the same content hash."""
        stmt = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.content_hash == content_hash,
            Document.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_for_tenant(
        self,
        tenant_id: str,
        *,
        pending_review: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        """List the tenant's documents, optionally only those needing review."""
        stmt = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
        )
        if pending_review:
            stmt = stmt.where(Document.status == DocumentStatus.NEEDS_REVIEW)
        stmt = stmt.order_by(Document.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def apply_extraction(
        self,
        document: Document,
        *,
        status: DocumentStatus,
        extraction: dict[str, Any] | None,
        confidence: float | None,
    ) -> Document:
        """Persist extraction results + gated status. Caller commits."""
        document.status = status
        document.extraction = extraction
        document.confidence = confidence
        await self._session.flush()
        return document
