"""Postgres -> Neo4j projection service.

Writes go to Postgres first (system of record). After a successful commit, the
graph is updated best-effort via idempotent MERGE-based projection. On graph
failure we log and continue — the user write already succeeded in Postgres; the
secondary store must never fail a correct write.

Consistency strategy is documented in
``plans/graph-database-architecture.md``.
"""

from __future__ import annotations

import logging

from src.config import get_settings
from src.graph.driver import get_driver
from src.graph.repositories.project_graph_repository import ProjectGraphRepository
from src.models.project import Project

logger = logging.getLogger(__name__)


async def project_project_to_graph(project: Project) -> None:
    """Best-effort idempotent projection of a Project into the graph.

    No-op when ``GRAPH_ENABLED`` is false. Never raises to the caller.
    """
    settings = get_settings()
    if not settings.GRAPH_ENABLED:
        return

    try:
        driver = get_driver()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            repo = ProjectGraphRepository(session)
            await repo.merge_project(
                project.tenant_id,
                project_id=project.id,
                name=project.name,
                status=project.status,
            )
    except Exception:
        # Postgres remains correct; log and continue.
        logger.exception("Graph projection failed for project_id=%s (continuing)", project.id)


async def remove_project_from_graph(tenant_id: str, project_id: str) -> None:
    """Best-effort idempotent removal of a Project node. Never raises."""
    settings = get_settings()
    if not settings.GRAPH_ENABLED:
        return
    try:
        driver = get_driver()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            repo = ProjectGraphRepository(session)
            await repo.delete_project(tenant_id, project_id=project_id)
    except Exception:
        logger.exception("Graph deletion failed for project_id=%s (continuing)", project_id)
