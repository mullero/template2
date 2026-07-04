"""Cloud Tasks enqueue + inline dispatch.

Durable background work runs on Google Cloud Tasks (NOT in-process
``BackgroundTasks``, which die on Cloud Run instance recycle). The flow:

1. The request handler creates the ``Job`` row and commits (Postgres first).
2. AFTER the commit it calls :func:`enqueue`, which — when ``TASKS_ENABLED`` —
   creates a Cloud Tasks task targeting ``POST /api/internal/tasks/{kind}`` with
   an OIDC token minted for the queue's service account.
3. In local dev (``TASKS_ENABLED=false``) the worker runs inline/synchronously in
   a fresh DB session, so no emulator is needed.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.job import Job
from src.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


async def create_job(
    session: AsyncSession,
    *,
    kind: str,
    payload: dict[str, Any],
    tenant_id: str,
    created_by: str | None = None,
) -> Job:
    """Create (flush) a queued job row. The caller commits before enqueuing."""
    repo = JobRepository(session)
    return await repo.create(
        tenant_id,
        kind=kind,
        payload=payload,
        created_by=created_by,
    )


async def enqueue(*, job_id: str, kind: str, tenant_id: str) -> None:
    """Enqueue a committed job. Runs inline when Cloud Tasks is disabled.

    MUST be called AFTER the enqueuing request has committed its transaction.
    """
    settings = get_settings()
    body = {"job_id": job_id, "tenant_id": tenant_id}

    if not settings.TASKS_ENABLED:
        logger.info("tasks.enqueue inline kind=%s", kind)
        await _run_inline(job_id)
        return

    logger.info("tasks.enqueue cloud kind=%s queue=%s", kind, settings.CLOUD_TASKS_QUEUE)
    from google.cloud import tasks_v2

    client = tasks_v2.CloudTasksAsyncClient()
    parent = client.queue_path(
        settings.GCP_PROJECT_ID,
        settings.CLOUD_TASKS_LOCATION,
        settings.CLOUD_TASKS_QUEUE,
    )
    task: dict[str, Any] = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{settings.INTERNAL_BASE_URL}/api/internal/tasks/{kind}",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body).encode(),
            "oidc_token": {
                "service_account_email": settings.TASKS_SERVICE_ACCOUNT,
                "audience": settings.tasks_oidc_audience,
            },
        },
    }
    await client.create_task(parent=parent, task=task)  # type: ignore[arg-type]
    logger.info("tasks.enqueue cloud created job_id=%s", job_id)


async def _run_inline(job_id: str) -> None:
    """Run the worker synchronously in a fresh session (local dev path)."""
    from src.database import get_sessionmaker
    from src.services.worker import run_job

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        await run_job(session, job_id)
