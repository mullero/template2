"""APScheduler lifecycle for periodic in-process work.

Started/stopped in the app lifespan when ``SCHEDULER_ENABLED``. Each job is
wrapped so a failure can NEVER crash the worker (log + continue).

NOTE: Cloud Run scales to zero — an in-process scheduler only ticks while an
instance is warm. For guaranteed cadence, use Cloud Scheduler hitting an
internal endpoint instead (documented in ``plans/background-jobs.md``).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _guarded(job: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
    """Wrap a job so an exception is logged and swallowed, never propagated."""

    async def _runner() -> None:
        try:
            await job()
        except Exception:
            logger.exception("scheduler job failed (continuing)")

    return _runner


async def _heartbeat() -> None:
    """Sample periodic job. Replace with digests / cache refresh / alert sweeps."""
    logger.info("scheduler.heartbeat tick")


def start_scheduler() -> None:
    """Create and start the scheduler (idempotent)."""
    global _scheduler
    if _scheduler is not None:
        return
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_guarded(_heartbeat), "interval", minutes=5, id="heartbeat")
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    """Stop the scheduler if running (idempotent)."""
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Scheduler stopped")
