"""Unit test for the health endpoint (Postgres probe mocked)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src import main as main_module


@pytest.fixture
def app_no_lifespan(monkeypatch: pytest.MonkeyPatch) -> object:
    """Build the app but stub the lifespan so tests don't need real services."""

    @asynccontextmanager
    async def _noop_lifespan(app: object) -> AsyncIterator[None]:
        yield

    monkeypatch.setattr(main_module, "lifespan", _noop_lifespan)
    return main_module.create_app()


async def test_health_ok_when_db_reachable(
    app_no_lifespan: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()

    @asynccontextmanager
    async def _fake_session_ctx() -> AsyncIterator[AsyncMock]:
        yield session

    def _fake_sessionmaker() -> object:
        return lambda: _fake_session_ctx()

    monkeypatch.setattr(main_module, "get_sessionmaker", _fake_sessionmaker)

    transport = ASGITransport(app=app_no_lifespan)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


async def test_root_endpoint(app_no_lifespan: object) -> None:
    transport = ASGITransport(app=app_no_lifespan)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
