"""Job ORM model — durable background work tracked in Postgres.

Cloud Tasks pushes each queued job to an internal worker endpoint. The row here
is the authoritative record of ``status``/``attempts`` so a retried task can be
made idempotent (skip when already ``succeeded``). Jobs are never soft-deleted,
so this model intentionally omits :class:`SoftDeleteMixin`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.mixins import TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class JobStatus(StrEnum):
    """Lifecycle states for a background job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobKind(StrEnum):
    """Kinds of background jobs the worker knows how to run."""

    EXTRACT_DOCUMENT = "extract_document"


class Job(
    UUIDPrimaryKeyMixin,
    TenantMixin,
    TimestampMixin,
    Base,
):
    """A tenant-scoped unit of durable background work."""

    __tablename__ = "jobs"

    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JobStatus.QUEUED,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
