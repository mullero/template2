"""Document ORM model — the async AI-extraction slice.

An uploaded file becomes a ``Document`` row (``status=processing``); a background
job runs the LLM extraction, stores the structured response, computes a
confidence signal, and either auto-commits (high confidence) or routes to a
human-review queue (low confidence / forced review). ``content_hash`` powers
Layer-1 upload dedup.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.mixins import (
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class DocumentStatus(StrEnum):
    """Lifecycle states for an uploaded document."""

    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    COMMITTED = "committed"
    DUPLICATE = "duplicate"
    FAILED = "failed"


class Document(
    UUIDPrimaryKeyMixin,
    TenantMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    """A tenant-scoped uploaded document flowing through the extraction pipeline."""

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentStatus.PROCESSING,
        index=True,
    )
    extraction: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
