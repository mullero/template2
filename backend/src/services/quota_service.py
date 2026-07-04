"""AI quota service — reserve-before-spend, refund-on-failure.

Atomically reserves one paid-API call per ``(tenant_id, day)`` before an upload
is accepted, so a tenant can never exceed ``AI_DAILY_QUOTA_PER_TENANT``. The
reservation is an ``INSERT ... ON CONFLICT DO UPDATE ... WHERE used < cap`` so
the check-and-increment is a single atomic statement. Failed extractions refund
their reservation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.quota import QuotaUsage

logger = logging.getLogger(__name__)


class QuotaExceededError(RuntimeError):
    """Raised when a tenant has exhausted its daily paid-API quota."""


async def reserve(session: AsyncSession, tenant_id: str) -> None:
    """Atomically reserve one call for the tenant today. Caller commits.

    Raises :class:`QuotaExceededError` when the daily cap is reached.
    """
    settings = get_settings()
    cap = settings.AI_DAILY_QUOTA_PER_TENANT
    today = datetime.now(UTC).date()

    stmt = (
        pg_insert(QuotaUsage)
        .values(tenant_id=tenant_id, usage_date=today, used=1)
        .on_conflict_do_update(
            constraint="uq_quota_usage_tenant_id_usage_date",
            set_={"used": QuotaUsage.used + 1},
            where=QuotaUsage.used < cap,
        )
        .returning(QuotaUsage.used)
    )
    result = await session.execute(stmt)
    reserved = result.scalar_one_or_none()
    if reserved is None:
        logger.info("quota.reserve denied tenant cap=%d", cap)
        raise QuotaExceededError("Daily AI quota exceeded")
    logger.info("quota.reserve ok used=%d cap=%d", reserved, cap)


async def refund(session: AsyncSession, tenant_id: str) -> None:
    """Refund one reservation for the tenant today (best-effort). Caller commits."""
    today = datetime.now(UTC).date()
    stmt = (
        update(QuotaUsage)
        .where(
            QuotaUsage.tenant_id == tenant_id,
            QuotaUsage.usage_date == today,
            QuotaUsage.used > 0,
        )
        .values(used=QuotaUsage.used - 1)
    )
    await session.execute(stmt)
    logger.info("quota.refund applied")
