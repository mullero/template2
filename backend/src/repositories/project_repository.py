"""Project repository — tenant-scoped data access for :class:`Project`.

EVERY read requires a ``tenant_id`` and filters ``Project.tenant_id == tenant_id``
plus ``Project.deleted_at.is_(None)`` (the latter is also enforced globally by the
soft-delete filter; it is repeated here for defense in depth).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.utils.normalization import normalize_name


class ProjectRepository:
    """Async repository for projects."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        """Return the tenant's projects, newest first."""
        stmt = (
            select(Project)
            .where(Project.tenant_id == tenant_id, Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: str, project_id: str) -> Project | None:
        """Return a single project scoped to the tenant, or ``None``."""
        stmt = select(Project).where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
            Project.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_normalized_name(
        self,
        tenant_id: str,
        name: str,
    ) -> Project | None:
        """Resolve a project by its normalized name within the tenant."""
        stmt = select(Project).where(
            Project.tenant_id == tenant_id,
            Project.normalized_name == normalize_name(name),
            Project.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: str,
        *,
        name: str,
        description: str | None = None,
        status: str = "active",
    ) -> Project:
        """Insert a new project for the tenant. Caller commits."""
        project = Project(
            tenant_id=tenant_id,
            name=name,
            normalized_name=normalize_name(name),
            description=description,
            status=status,
        )
        self._session.add(project)
        await self._session.flush()
        return project

    async def update(
        self,
        project: Project,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Project:
        """Apply partial updates to a project already scoped to the tenant."""
        if name is not None:
            project.name = name
            project.normalized_name = normalize_name(name)
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        await self._session.flush()
        return project

    async def soft_delete(self, project: Project) -> None:
        """Mark a project deleted (sets ``deleted_at``). Caller commits."""
        project.deleted_at = datetime.now(UTC)
        await self._session.flush()
