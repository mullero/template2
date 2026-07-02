"""Idempotent Neo4j schema setup.

Runs at startup when ``GRAPH_ENABLED`` is true. Every statement uses
``IF NOT EXISTS`` so replays are safe. Each node label gets a composite
uniqueness constraint on ``(tenant_id, id)``; the constraint's backing range
index also serves tenant-scoped lookups, so no separate index is needed.

Composite uniqueness constraints are available in Neo4j Community Edition.
``NODE KEY`` / existence constraints are intentionally avoided because they
require Enterprise Edition.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j import AsyncDriver

logger = logging.getLogger(__name__)

# One statement per entry; all idempotent. Composite uniqueness constraints work
# on Community Edition and create a backing index used for tenant-scoped reads.
_CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT project_tenant_id_unique IF NOT EXISTS "
    "FOR (p:Project) REQUIRE (p.tenant_id, p.id) IS UNIQUE",
    "CREATE CONSTRAINT task_tenant_id_unique IF NOT EXISTS "
    "FOR (t:Task) REQUIRE (t.tenant_id, t.id) IS UNIQUE",
)


async def apply_constraints(driver: AsyncDriver, *, database: str) -> None:
    """Apply all constraints/indexes idempotently."""
    async with driver.session(database=database) as session:
        for statement in _CONSTRAINTS:
            await session.run(statement)
    logger.info("Neo4j constraints/indexes applied (%d statements)", len(_CONSTRAINTS))
