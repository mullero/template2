"""Auth guards for FastAPI routes.

Compose these on routers:

- :func:`require_auth`         — authenticated user only.
- :func:`require_tenant`       — authenticated AND has a non-empty tenant_id
                                 (DEFAULT for data routes).
- :func:`require_tenant_admin` — role in {admin, superadmin} within a tenant.
- :func:`require_superadmin`   — role == superadmin (cross-tenant ops).

``AUTH_ENABLED`` is read from the cached settings singleton (NOT live env) to
prevent runtime bypass. When disabled (local dev only) a stub superadmin with a
sentinel tenant is injected. Production refuses to boot with auth disabled
(enforced in the app lifespan).
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_settings
from src.services.auth_service import (
    AuthenticatedUser,
    AuthError,
    Role,
    dev_stub_user,
    verify_token,
)

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedUser:
    """Resolve the authenticated user from the bearer token.

    Returns the dev stub superadmin when ``AUTH_ENABLED`` is false.
    """
    settings = get_settings()

    if not settings.AUTH_ENABLED:
        # Read from cached settings, never live env, to prevent runtime bypass.
        return dev_stub_user()

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verify_token(credentials.credentials)
    except AuthError as exc:
        logger.info("Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


async def require_auth(user: CurrentUser) -> AuthenticatedUser:
    """Authenticated user only (rarely correct for data routes)."""
    return user


async def require_tenant(user: CurrentUser) -> AuthenticatedUser:
    """Authenticated AND has a non-empty tenant_id. DEFAULT for data routes."""
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant assigned to this account",
        )
    return user


async def require_tenant_admin(user: CurrentUser) -> AuthenticatedUser:
    """Role in {admin, superadmin} within a tenant."""
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant assigned to this account",
        )
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


async def require_superadmin(user: CurrentUser) -> AuthenticatedUser:
    """Role == superadmin (cross-tenant operations)."""
    if not user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required",
        )
    return user


# Alias per the spec.
require_admin = require_superadmin

TenantUser = Annotated[AuthenticatedUser, Depends(require_tenant)]
TenantAdmin = Annotated[AuthenticatedUser, Depends(require_tenant_admin)]
SuperAdmin = Annotated[AuthenticatedUser, Depends(require_superadmin)]

__all__ = [
    "CurrentUser",
    "Role",
    "SuperAdmin",
    "TenantAdmin",
    "TenantUser",
    "get_current_user",
    "require_admin",
    "require_auth",
    "require_superadmin",
    "require_tenant",
    "require_tenant_admin",
]
