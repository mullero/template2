"""Job repository — tenant-scoped data access for :class:`Job`.

Every read requires a ``tenant_id`` and filters ``Job.tenant_id == tenant_id``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job import Job, JobStatus


class JobRepository:
    """Async repository for background jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: str,
        *,
        kind: str,
        payload: dict[str, Any],
        created_by: str | None = None,
    ) -> Job:
        """Insert a queued job for the tenant. Caller commits."""
        job = Job(
            tenant_id=tenant_id,
            kind=kind,
            status=JobStatus.QUEUED,
            payload=payload,
            created_by=created_by,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_by_id(self, tenant_id: str, job_id: str) -> Job | None:
        """Return a single job scoped to the tenant, or ``None``."""
        stmt = select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_worker(self, job_id: str) -> Job | None:
        """Return a job by id WITHOUT tenant scoping (internal worker only).

        The worker is authenticated by the Cloud Tasks OIDC token, not a tenant
        principal; it then acts strictly on the job's own ``tenant_id``.
        """
        stmt = select(Job).where(Job.id == job_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_running(self, job: Job) -> Job:
        """Transition a job to ``running`` and bump ``attempts``. Caller commits."""
        job.status = JobStatus.RUNNING
        job.attempts += 1
        await self._session.flush()
        return job

    async def mark_succeeded(self, job: Job) -> Job:
        """Transition a job to ``succeeded``. Caller commits."""
        job.status = JobStatus.SUCCEEDED
        job.error = None
        await self._session.flush()
        return job

    async def mark_failed(self, job: Job, error: str) -> Job:
        """Transition a job to ``failed`` with a truncated error. Caller commits."""
        job.status = JobStatus.FAILED
        job.error = error[:2000]
        await self._session.flush()
        return job

    @staticmethod
    def touch(job: Job) -> None:
        """Mark the job row updated (helper for callers doing raw updates)."""
        job.updated_at = datetime.now(UTC)
