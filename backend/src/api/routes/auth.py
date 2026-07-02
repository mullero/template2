"""Auth routes: current-user sync and first-superadmin bootstrap."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config import get_settings
from src.dependencies.auth import CurrentUser
from src.services.auth_service import Role, set_user_claims

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    """The authenticated user's identity as the frontend needs it."""

    uid: str
    email: str | None
    role: Role
    tenant_id: str | None


class BootstrapRequest(BaseModel):
    """Request body to bootstrap the first superadmin."""

    tenant_id: str = Field(min_length=1, max_length=128)


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser) -> UserResponse:
    """Return the current authenticated user (synced by the frontend on login)."""
    logger.info("auth.me success uid=%s", user.uid)
    return UserResponse(uid=user.uid, email=user.email, role=user.role, tenant_id=user.tenant_id)


@router.post("/bootstrap", response_model=UserResponse)
async def bootstrap(body: BootstrapRequest, user: CurrentUser) -> UserResponse:
    """Promote the caller to superadmin for a tenant.

    Intended for first-run / dev seeding. In auth-disabled dev mode the caller is
    already a stub superadmin, so this is a no-op echo.
    """
    settings = get_settings()

    if not settings.AUTH_ENABLED:
        logger.info("auth.bootstrap noop (auth disabled)")
        return UserResponse(
            uid=user.uid,
            email=user.email,
            role=Role.SUPERADMIN,
            tenant_id=body.tenant_id,
        )

    try:
        set_user_claims(user.uid, role=Role.SUPERADMIN, tenant_id=body.tenant_id)
    except Exception as exc:  # firebase-admin raises concrete types
        logger.exception("auth.bootstrap failed uid=%s", user.uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set user claims",
        ) from exc

    logger.info("auth.bootstrap success uid=%s tenant assigned", user.uid)
    return UserResponse(
        uid=user.uid,
        email=user.email,
        role=Role.SUPERADMIN,
        tenant_id=body.tenant_id,
    )
