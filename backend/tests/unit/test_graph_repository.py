"""Unit tests for the graph layer with the driver/session boundary mocked.

These do not require a live Neo4j and skip cleanly when graph is disabled.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.graph.repositories.project_graph_repository import ProjectGraphRepository
from src.services.graph_projection import project_project_to_graph


async def test_merge_project_is_tenant_scoped_and_parameterized() -> None:
    session = AsyncMock()
    repo = ProjectGraphRepository(session)

    await repo.merge_project("tenant-a", project_id="p-1", name="Alpha", status="active")

    session.run.assert_awaited_once()
    args, kwargs = session.run.await_args
    cypher = args[0]
    # Parameterized, never string-interpolated.
    assert "$tenant_id" in cypher
    assert "$project_id" in cypher
    assert "MERGE" in cypher
    assert kwargs["tenant_id"] == "tenant-a"
    assert kwargs["project_id"] == "p-1"


async def test_merge_task_edge_pins_tenant_on_both_nodes() -> None:
    session = AsyncMock()
    repo = ProjectGraphRepository(session)

    await repo.merge_task_edge(
        "tenant-a",
        project_id="p-1",
        task_id="t-1",
        title="Do it",
    )

    cypher = session.run.await_args.args[0]
    # Both node patterns carry {tenant_id: $tenant_id}.
    assert cypher.count("{tenant_id: $tenant_id") >= 2
    assert "HAS_TASK" in cypher


async def test_projection_is_noop_when_graph_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.config import reset_settings_cache

    monkeypatch.setenv("GRAPH_ENABLED", "false")
    reset_settings_cache()

    class _Project:
        id = "p-1"
        tenant_id = "tenant-a"
        name = "Alpha"
        status = "active"

    # Should return without touching any driver.
    await project_project_to_graph(_Project())  # type: ignore[arg-type]
    reset_settings_cache()
