"""Graph session dependency (async, context-managed).

Gated on ``GRAPH_ENABLED``; raises a clear error when the graph is disabled so
graph-backed routes can surface a 501/404.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from src.config import get_settings
from src.graph.driver import GraphDisabledError, get_driver

if TYPE_CHECKING:
    from neo4j import AsyncSession


async def get_graph_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async Neo4j session.

    Raises :class:`GraphDisabledError` when ``GRAPH_ENABLED`` is false.
    """
    settings = get_settings()
    if not settings.GRAPH_ENABLED:
        raise GraphDisabledError("Graph features are disabled (GRAPH_ENABLED=false)")

    driver = get_driver()
    session = driver.session(database=settings.NEO4J_DATABASE)
    try:
        yield session
    finally:
        await session.close()
