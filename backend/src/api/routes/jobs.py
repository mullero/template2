"""Jobs router — tenant-scoped background-job status for polling.

The frontend's global progress provider polls ``GET /api/jobs/{id}`` to render a
progress indicator that survives navigation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import TenantUser
from src.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


class JobResponse(BaseModel):
    """A background job as returned to clients."""

    id: str
    tenant_id: str
    kind: str
    status: str
    attempts: int
    error: str | None
    created_at: datetime
    updated_at: datetime


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, user: TenantUser, session: DbSession) -> JobResponse:
    """Fetch a single job scoped to the tenant."""
    repo = JobRepository(session)
    job = await repo.get_by_id(user.tenant_id or "", job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse.model_validate(job, from_attributes=True)
