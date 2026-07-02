"""Projects router — the end-to-end vertical slice.

Every route uses :func:`require_tenant`; the resolved ``tenant_id`` flows into
every repository read/write and every graph query. A request scoped to tenant A
can never see tenant B's data.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_db
from src.dependencies.auth import TenantUser
from src.graph.driver import GraphDisabledError, get_driver
from src.graph.repositories.project_graph_repository import ProjectGraphRepository
from src.repositories.project_repository import ProjectRepository
from src.services.graph_projection import (
    project_project_to_graph,
    remove_project_from_graph,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


# --- Schemas ----------------------------------------------------------------
class ProjectCreate(BaseModel):
    """Request body to create a project."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    status: str = Field(default="active", max_length=32)


class ProjectUpdate(BaseModel):
    """Request body to update a project (partial)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    status: str | None = Field(default=None, max_length=32)


class ProjectResponse(BaseModel):
    """A project as returned to clients."""

    id: str
    tenant_id: str
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class GraphTaskResponse(BaseModel):
    """A task node returned from the graph traversal."""

    id: str
    title: str


# --- Routes -----------------------------------------------------------------
@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: TenantUser,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectResponse]:
    """List the tenant's projects."""
    logger.info("projects.list start")
    repo = ProjectRepository(session)
    projects = await repo.list_for_tenant(user.tenant_id or "", limit=limit, offset=offset)
    logger.info("projects.list success count=%d", len(projects))
    return [ProjectResponse.model_validate(p, from_attributes=True) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: TenantUser,
    session: DbSession,
) -> ProjectResponse:
    """Fetch a single project scoped to the tenant."""
    repo = ProjectRepository(session)
    project = await repo.get_by_id(user.tenant_id or "", project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: TenantUser,
    session: DbSession,
) -> ProjectResponse:
    """Create a project, then project it into the graph (best-effort)."""
    logger.info("projects.create start")
    repo = ProjectRepository(session)

    existing = await repo.get_by_normalized_name(user.tenant_id or "", body.name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this name already exists",
        )

    project = await repo.create(
        user.tenant_id or "",
        name=body.name,
        description=body.description,
        status=body.status,
    )
    await session.commit()  # Postgres is the system of record — commit first.

    # After commit: best-effort idempotent graph projection.
    await project_project_to_graph(project)

    logger.info("projects.create success project_id=%s", project.id)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    user: TenantUser,
    session: DbSession,
) -> ProjectResponse:
    """Update a project scoped to the tenant."""
    repo = ProjectRepository(session)
    project = await repo.get_by_id(user.tenant_id or "", project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    await repo.update(
        project,
        name=body.name,
        description=body.description,
        status=body.status,
    )
    await session.commit()
    await project_project_to_graph(project)
    logger.info("projects.update success project_id=%s", project.id)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: TenantUser,
    session: DbSession,
) -> Response:
    """Soft-delete a project scoped to the tenant."""
    repo = ProjectRepository(session)
    project = await repo.get_by_id(user.tenant_id or "", project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    tenant_id = project.tenant_id
    await repo.soft_delete(project)
    await session.commit()
    await remove_project_from_graph(tenant_id, project_id)
    logger.info("projects.delete success project_id=%s", project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/graph/tasks", response_model=list[GraphTaskResponse])
async def list_project_graph_tasks(
    project_id: str,
    user: TenantUser,
    session: DbSession,
) -> list[GraphTaskResponse]:
    """Tenant-scoped graph traversal: the project's task nodes.

    Returns 501 when the graph is disabled.
    """
    # Confirm the project belongs to the tenant before traversing the graph.
    repo = ProjectRepository(session)
    project = await repo.get_by_id(user.tenant_id or "", project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        settings = get_settings()
        driver = get_driver()
        async with driver.session(database=settings.NEO4J_DATABASE) as graph_session:
            graph_repo = ProjectGraphRepository(graph_session)
            tasks = await graph_repo.list_project_tasks(
                user.tenant_id or "",
                project_id=project_id,
            )
    except GraphDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Graph features are disabled",
        ) from exc

    return [GraphTaskResponse(id=t["id"], title=t["title"]) for t in tasks]
