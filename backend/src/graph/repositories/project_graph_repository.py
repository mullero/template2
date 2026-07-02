"""Project graph repository.

Projects the Postgres ``Project``/``Task`` records into Neo4j as
``(:Project)-[:HAS_TASK]->(:Task)`` and exposes a tenant-scoped traversal.

Non-negotiables:
- Every MATCH/MERGE pins ``{tenant_id: $tenant_id}``.
- Relationships only ever connect nodes of the SAME tenant.
- All Cypher is parameterized ($param) — never string-interpolate user input.
- Projection uses MERGE (idempotent), never CREATE.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from neo4j import AsyncSession

logger = logging.getLogger(__name__)


class ProjectGraphRepository:
    """Tenant-scoped graph access for projects and their tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def merge_project(
        self,
        tenant_id: str,
        *,
        project_id: str,
        name: str,
        status: str,
    ) -> None:
        """Idempotently upsert a Project node for the tenant."""
        logger.info("graph.merge_project start tenant_scoped project_id=%s", project_id)
        query = (
            "MERGE (p:Project {tenant_id: $tenant_id, id: $project_id}) "
            "SET p.name = $name, p.status = $status"
        )
        await self._session.run(
            query,
            tenant_id=tenant_id,
            project_id=project_id,
            name=name,
            status=status,
        )
        logger.info("graph.merge_project success project_id=%s", project_id)

    async def merge_task_edge(
        self,
        tenant_id: str,
        *,
        project_id: str,
        task_id: str,
        title: str,
    ) -> None:
        """Idempotently upsert a Task node and its HAS_TASK edge (same tenant)."""
        query = (
            "MERGE (p:Project {tenant_id: $tenant_id, id: $project_id}) "
            "MERGE (t:Task {tenant_id: $tenant_id, id: $task_id}) "
            "SET t.title = $title "
            "MERGE (p)-[:HAS_TASK]->(t)"
        )
        await self._session.run(
            query,
            tenant_id=tenant_id,
            project_id=project_id,
            task_id=task_id,
            title=title,
        )

    async def delete_project(self, tenant_id: str, *, project_id: str) -> None:
        """Remove a Project node (and detach its edges) for the tenant."""
        query = (
            "MATCH (p:Project {tenant_id: $tenant_id, id: $project_id}) "
            "DETACH DELETE p"
        )
        await self._session.run(
            query,
            tenant_id=tenant_id,
            project_id=project_id,
        )

    async def list_project_tasks(
        self,
        tenant_id: str,
        *,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """Traverse a project's tasks — scoped strictly to the tenant.

        A traversal scoped to tenant A must NEVER reach tenant B's nodes.
        """
        logger.info("graph.list_project_tasks start project_id=%s", project_id)
        query = (
            "MATCH (p:Project {tenant_id: $tenant_id, id: $project_id})"
            "-[:HAS_TASK]->(t:Task {tenant_id: $tenant_id}) "
            "RETURN t.id AS id, t.title AS title "
            "ORDER BY t.title"
        )
        result = await self._session.run(
            query,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        records = [dict(record) async for record in result]
        logger.info("graph.list_project_tasks success count=%d", len(records))
        return records
