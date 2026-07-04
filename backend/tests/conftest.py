"""Shared pytest fixtures.

Test environment variables are set BEFORE any application import so the cached
settings singleton is built with test values. Integration fixtures target a REAL
PostgreSQL; when it is unreachable they skip cleanly so ``pytest -q`` stays green
on a machine without a database.
"""

from __future__ import annotations

import os

# --- Set the test environment BEFORE importing application modules ----------
os.environ.setdefault("DEPLOYMENT_ENVIRONMENT", "testing")
os.environ["AUTH_ENABLED"] = "true"  # ALWAYS true in tests
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["GRAPH_ENABLED"] = os.environ.get("GRAPH_ENABLED", "false")
os.environ["AI_ENABLED"] = "false"
os.environ["OTEL_ENABLED"] = "false"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
os.environ.setdefault("NEO4J_PASSWORD", "test-neo4j-password")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://app_skeleton:app_skeleton@localhost:5432/app_skeleton_test",
)
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import reset_settings_cache  # noqa: E402
from src.database import Base  # noqa: E402
from src.db.soft_delete import install_soft_delete_filter  # noqa: E402
from src.models import import_all_models  # noqa: E402

reset_settings_cache()
import_all_models()


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    """Ensure each test sees a fresh settings singleton."""
    reset_settings_cache()


async def _postgres_reachable(url: str) -> bool:
    engine = create_async_engine(url)
    try:
        async with engine.connect():
            return True
    except Exception:
        return False
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session against a real PostgreSQL.

    Creates all tables on setup and drops the public schema on teardown. Skips
    the test when Postgres is unreachable.
    """
    url = os.environ["TEST_DATABASE_URL"]
    if not await _postgres_reachable(url):
        pytest.skip("PostgreSQL not reachable; skipping integration test")

    engine = create_async_engine(url, poolclass=__import__("sqlalchemy").pool.NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    install_soft_delete_filter(sessionmaker)

    session = sessionmaker()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.exec_driver_sql("DROP SCHEMA public CASCADE")
            await conn.exec_driver_sql("CREATE SCHEMA public")
        await engine.dispose()
