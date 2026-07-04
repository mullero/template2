"""Integration tests for the async subsystems against a real PostgreSQL.

Covers: the quota reserve/refund cap, the extraction confidence gate, worker
idempotency, and tenant isolation for jobs/documents.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import reset_settings_cache
from src.models.document import DocumentStatus
from src.models.job import JobKind, JobStatus
from src.repositories.document_repository import DocumentRepository
from src.repositories.job_repository import JobRepository
from src.services import quota_service, task_queue
from src.services.quota_service import QuotaExceededError
from src.services.worker import run_job

pytestmark = pytest.mark.integration


def _set_env(**kwargs: str) -> None:
    for key, value in kwargs.items():
        os.environ[key] = value
    reset_settings_cache()


async def _seed_job(session: AsyncSession, tenant_id: str, content_hash: str) -> tuple[str, str]:
    doc_repo = DocumentRepository(session)
    document = await doc_repo.create(
        tenant_id,
        filename="invoice.pdf",
        content_hash=content_hash,
        storage_uri=None,
        created_by="user@test",
    )
    job = await task_queue.create_job(
        session,
        kind=JobKind.EXTRACT_DOCUMENT,
        payload={"document_id": document.id, "force_review": False},
        tenant_id=tenant_id,
    )
    await session.commit()
    return document.id, job.id


async def test_quota_reserve_and_cap(async_db_session: AsyncSession) -> None:
    _set_env(AI_DAILY_QUOTA_PER_TENANT="1")
    try:
        await quota_service.reserve(async_db_session, "tenant-a")
        await async_db_session.commit()
        with pytest.raises(QuotaExceededError):
            await quota_service.reserve(async_db_session, "tenant-a")
        await async_db_session.commit()
        # A different tenant is unaffected.
        await quota_service.reserve(async_db_session, "tenant-b")
        await async_db_session.commit()
    finally:
        os.environ.pop("AI_DAILY_QUOTA_PER_TENANT", None)
        reset_settings_cache()


async def test_worker_autocommits_and_is_idempotent(async_db_session: AsyncSession) -> None:
    _set_env(EXTRACTION_AUTOCOMMIT_THRESHOLD="0.0")  # any confidence -> auto-commit
    try:
        document_id, job_id = await _seed_job(async_db_session, "tenant-a", "a" * 64)

        await run_job(async_db_session, job_id)

        doc_repo = DocumentRepository(async_db_session)
        job_repo = JobRepository(async_db_session)
        document = await doc_repo.get_by_id("tenant-a", document_id)
        job = await job_repo.get_by_id("tenant-a", job_id)
        assert document is not None
        assert document.status == DocumentStatus.COMMITTED
        assert job is not None
        assert job.status == JobStatus.SUCCEEDED
        assert job.attempts == 1

        # Idempotency: a retried delivery must NOT re-run completed work.
        await run_job(async_db_session, job_id)
        job = await job_repo.get_by_id("tenant-a", job_id)
        assert job is not None
        assert job.attempts == 1
    finally:
        os.environ.pop("EXTRACTION_AUTOCOMMIT_THRESHOLD", None)
        reset_settings_cache()


async def test_worker_routes_low_confidence_to_review(async_db_session: AsyncSession) -> None:
    _set_env(EXTRACTION_AUTOCOMMIT_THRESHOLD="1.1")  # nothing clears the bar
    try:
        document_id, job_id = await _seed_job(async_db_session, "tenant-a", "b" * 64)
        await run_job(async_db_session, job_id)

        doc_repo = DocumentRepository(async_db_session)
        document = await doc_repo.get_by_id("tenant-a", document_id)
        assert document is not None
        assert document.status == DocumentStatus.NEEDS_REVIEW

        pending = await doc_repo.list_for_tenant("tenant-a", pending_review=True)
        assert document_id in {d.id for d in pending}
    finally:
        os.environ.pop("EXTRACTION_AUTOCOMMIT_THRESHOLD", None)
        reset_settings_cache()


async def test_jobs_and_documents_tenant_isolation(async_db_session: AsyncSession) -> None:
    document_id, job_id = await _seed_job(async_db_session, "tenant-a", "c" * 64)

    doc_repo = DocumentRepository(async_db_session)
    job_repo = JobRepository(async_db_session)

    # Tenant B must never see tenant A's rows.
    assert await doc_repo.get_by_id("tenant-b", document_id) is None
    assert await job_repo.get_by_id("tenant-b", job_id) is None
    assert await doc_repo.get_by_id("tenant-a", document_id) is not None
    assert await job_repo.get_by_id("tenant-a", job_id) is not None
