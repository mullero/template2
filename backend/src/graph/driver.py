"""Async Neo4j driver singleton.

The driver is created lazily and only when ``GRAPH_ENABLED`` is true. It is
closed in the app lifespan shutdown.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from src.config import get_settings

if TYPE_CHECKING:
    from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


class GraphDisabledError(RuntimeError):
    """Raised when graph access is attempted while ``GRAPH_ENABLED`` is false."""


@lru_cache(maxsize=1)
def get_driver() -> AsyncDriver:
    """Return the cached async Neo4j driver.

    Raises :class:`GraphDisabledError` when the graph is disabled.
    """
    settings = get_settings()
    if not settings.GRAPH_ENABLED:
        raise GraphDisabledError("GRAPH_ENABLED is false; the graph driver is not available")

    from neo4j import AsyncGraphDatabase

    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        max_connection_pool_size=settings.NEO4J_MAX_POOL_SIZE,
    )
    logger.info("Neo4j async driver created (uri=%s)", settings.NEO4J_URI)
    return driver


async def verify_connectivity() -> None:
    """Verify the driver can reach Neo4j. Raises on failure."""
    driver = get_driver()
    await driver.verify_connectivity()
    logger.info("Neo4j connectivity verified")


async def close_driver() -> None:
    """Close the driver on shutdown (no-op if never created)."""
    settings = get_settings()
    if not settings.GRAPH_ENABLED:
        return
    # Avoid instantiating a new driver just to close it.
    if get_driver.cache_info().currsize == 0:
        return
    driver = get_driver()
    await driver.close()
    get_driver.cache_clear()
    logger.info("Neo4j async driver closed")
