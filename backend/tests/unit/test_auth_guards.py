"""Unit tests for auth guards (mocking the token boundary)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.dependencies.auth import (
    get_current_user,
    require_superadmin,
    require_tenant,
    require_tenant_admin,
)
from src.services.auth_service import AuthenticatedUser, Role


def _user(role: Role = Role.VIEWER, tenant_id: str | None = "t-1") -> AuthenticatedUser:
    return AuthenticatedUser(uid="u-1", email="u@test", role=role, tenant_id=tenant_id)


async def test_require_tenant_rejects_missing_tenant() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_tenant(_user(tenant_id=None))
    assert exc.value.status_code == 403


async def test_require_tenant_allows_tenant_user() -> None:
    user = _user()
    assert await require_tenant(user) is user


async def test_require_tenant_admin_rejects_viewer() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_tenant_admin(_user(role=Role.VIEWER))
    assert exc.value.status_code == 403


async def test_require_superadmin_rejects_admin() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_superadmin(_user(role=Role.ADMIN))
    assert exc.value.status_code == 403


async def test_get_current_user_requires_credentials_when_auth_enabled() -> None:
    # AUTH_ENABLED is true in tests; missing credentials -> 401.
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None)
    assert exc.value.status_code == 401
