"""Integration tests for ProjectRepository against a real PostgreSQL.

Covers tenant isolation explicitly: a query scoped to tenant A must return ZERO
of tenant B's rows.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.project_repository import ProjectRepository

pytestmark = pytest.mark.integration


async def test_create_and_list_scoped_to_tenant(async_db_session: AsyncSession) -> None:
    repo = ProjectRepository(async_db_session)

    a = await repo.create("tenant-a", name="Alpha")
    await repo.create("tenant-b", name="Bravo")
    await async_db_session.commit()

    tenant_a_projects = await repo.list_for_tenant("tenant-a")
    assert [p.id for p in tenant_a_projects] == [a.id]

    tenant_b_projects = await repo.list_for_tenant("tenant-b")
    assert a.id not in {p.id for p in tenant_b_projects}


async def test_get_by_id_rejects_cross_tenant(async_db_session: AsyncSession) -> None:
    repo = ProjectRepository(async_db_session)
    a = await repo.create("tenant-a", name="Alpha")
    await async_db_session.commit()

    # Same id, wrong tenant -> None.
    assert await repo.get_by_id("tenant-b", a.id) is None
    assert await repo.get_by_id("tenant-a", a.id) is not None


async def test_soft_delete_hides_row(async_db_session: AsyncSession) -> None:
    repo = ProjectRepository(async_db_session)
    project = await repo.create("tenant-a", name="Alpha")
    project_id = project.id
    await async_db_session.commit()

    await repo.soft_delete(project)
    await async_db_session.commit()

    assert await repo.get_by_id("tenant-a", project_id) is None


async def test_normalized_name_dedup(async_db_session: AsyncSession) -> None:
    repo = ProjectRepository(async_db_session)
    await repo.create("tenant-a", name="My Project")
    await async_db_session.commit()

    found = await repo.get_by_normalized_name("tenant-a", "  my   PROJECT ")
    assert found is not None
