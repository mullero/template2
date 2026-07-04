"""Quota-usage ORM model — per-tenant, per-day paid-API reservations.

The quota service atomically reserves a call BEFORE the upload is accepted (so a
tenant can't blow the daily budget) and refunds on failure. One row per
``(tenant_id, usage_date)`` holds the running ``used`` counter.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.mixins import TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class QuotaUsage(
    UUIDPrimaryKeyMixin,
    TenantMixin,
    TimestampMixin,
    Base,
):
    """A tenant's paid-API usage counter for a single day."""

    __tablename__ = "quota_usage"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "usage_date",
            name="uq_quota_usage_tenant_id_usage_date",
        ),
    )

    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
