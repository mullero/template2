"""Dev-only routes, mounted only when ``ENABLE_DEV_ROUTES`` is true.

Never mounted in production.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.config import get_settings

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/config")
async def dev_config() -> dict[str, object]:
    """Echo a safe, non-secret subset of the active config for debugging."""
    settings = get_settings()
    return {
        "environment": settings.DEPLOYMENT_ENVIRONMENT,
        "auth_enabled": settings.AUTH_ENABLED,
        "graph_enabled": settings.GRAPH_ENABLED,
        "ai_enabled": settings.AI_ENABLED,
        "features": {
            "projects": settings.FEATURE_PROJECTS,
            "tasks": settings.FEATURE_TASKS,
        },
    }
