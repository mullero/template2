"""Internal worker routes — the Cloud Tasks push targets.

Auth is the Cloud Tasks OIDC token (see :mod:`src.dependencies.internal_auth`),
NOT the Firebase user flow. Handlers are IDEMPOTENT (guarded on job status) so a
retried delivery never re-runs completed work. Unhandled errors return 5xx so
Cloud Tasks retries with backoff.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.internal_auth import verify_cloud_tasks_oidc
from src.models.job import JobKind
from src.services.worker import run_job

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_cloud_tasks_oidc)],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


class TaskEnvelope(BaseModel):
    """Body Cloud Tasks POSTs to the worker."""

    job_id: str
    tenant_id: str


class TaskAck(BaseModel):
    """Worker acknowledgement."""

    job_id: str
    processed: bool


@router.post("/tasks/{kind}", response_model=TaskAck)
async def run_task(kind: JobKind, body: TaskEnvelope, session: DbSession) -> TaskAck:
    """Execute a queued job. 5xx (uncaught) triggers a Cloud Tasks retry."""
    logger.info("internal.run_task start kind=%s", kind)
    await run_job(session, body.job_id)
    logger.info("internal.run_task done kind=%s", kind)
    return TaskAck(job_id=body.job_id, processed=True)
