"""Background-job worker dispatch.

Both the inline (local) path and the HTTP internal endpoint call
:func:`run_job`. It is IDEMPOTENT: a job already ``succeeded`` is skipped so a
retried Cloud Tasks delivery never re-runs completed work. Unhandled errors are
recorded and re-raised so the HTTP worker returns 5xx and Cloud Tasks retries
with backoff.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job import JobKind, JobStatus
from src.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


class UnknownJobKindError(RuntimeError):
    """Raised when a job's kind has no registered handler."""


async def run_job(session: AsyncSession, job_id: str) -> None:
    """Execute a job by id. Idempotent and self-recording.

    Loads the job WITHOUT tenant scoping (the worker is OIDC-authenticated, not a
    tenant principal) then acts strictly on the job's own ``tenant_id``.
    """
    repo = JobRepository(session)
    job = await repo.get_for_worker(job_id)
    if job is None:
        logger.warning("worker.run_job missing job_id=%s", job_id)
        return

    if job.status == JobStatus.SUCCEEDED:
        # Idempotency guard: a retried task must not re-run completed work.
        logger.info("worker.run_job skip already-succeeded job_id=%s", job_id)
        return

    logger.info(
        "worker.run_job start job_id=%s kind=%s attempt=%d",
        job_id,
        job.kind,
        job.attempts + 1,
    )
    await repo.mark_running(job)
    await session.commit()

    try:
        if job.kind == JobKind.EXTRACT_DOCUMENT:
            from src.services.document_extraction import run_extraction

            await run_extraction(
                session,
                job.tenant_id,
                str(job.payload["document_id"]),
                force_review=bool(job.payload.get("force_review", False)),
            )
        else:
            raise UnknownJobKindError(f"No handler for job kind={job.kind}")
    except Exception as exc:
        await session.rollback()
        job = await repo.get_for_worker(job_id)
        if job is not None:
            await repo.mark_failed(job, str(exc))
            await session.commit()
        logger.exception("worker.run_job failed job_id=%s", job_id)
        raise

    await repo.mark_succeeded(job)
    await session.commit()
    logger.info("worker.run_job success job_id=%s", job_id)
