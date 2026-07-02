"""FastAPI application factory + lifespan.

Schema management is the ENTRYPOINT's job, not the app's — no drop/create here.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import auth as auth_routes
from src.api.routes import dev as dev_routes
from src.api.routes import projects as projects_routes
from src.config import get_settings, validate_config
from src.database import dispose_engine, get_engine, get_sessionmaker
from src.db.soft_delete import install_soft_delete_filter
from src.graph.constraints import apply_constraints
from src.graph.driver import close_driver, get_driver, verify_connectivity
from src.models import import_all_models
from src.rate_limit import limiter
from src.telemetry import configure_telemetry, instrument_fastapi
from src.utils.logging import configure_logging, get_logger

logger = logging.getLogger(__name__)


def _log_config_banner() -> None:
    settings = get_settings()
    banner = get_logger("startup")
    banner.info("=" * 60)
    banner.info("%s (%s)", settings.PRODUCT_NAME, settings.API_VERSION)
    banner.info("environment=%s", settings.DEPLOYMENT_ENVIRONMENT)
    banner.info("auth_enabled=%s graph_enabled=%s ai_enabled=%s",
                settings.AUTH_ENABLED, settings.GRAPH_ENABLED, settings.AI_ENABLED)
    banner.info("=" * 60)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup/shutdown. No schema drop/create — that is the entrypoint's job."""
    configure_logging()
    settings = get_settings()

    _log_config_banner()
    validate_config()

    # Fail-closed: production must never run with auth disabled.
    if settings.is_production and not settings.AUTH_ENABLED:
        logger.critical("AUTH_ENABLED=false is not permitted in production. Refusing to boot.")
        raise SystemExit(1)

    # Register the global soft-delete filter on the session factory.
    import_all_models()
    install_soft_delete_filter(get_sessionmaker())

    engine = get_engine()
    configure_telemetry(engine)

    # Graph: verify connectivity and apply idempotent constraints.
    if settings.GRAPH_ENABLED:
        await verify_connectivity()
        await apply_constraints(get_driver(), database=settings.NEO4J_DATABASE)

    logger.info("Application startup complete")
    try:
        yield
    finally:
        if settings.GRAPH_ENABLED:
            await close_driver()
        await dispose_engine()
        logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PRODUCT_NAME,
        version=settings.API_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_SWAGGER else None,
        redoc_url="/redoc" if settings.ENABLE_SWAGGER else None,
        openapi_url="/openapi.json" if settings.ENABLE_SWAGGER else None,
    )

    # --- Middleware ---------------------------------------------------------
    instrument_fastapi(app)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    # SlowAPIMiddleware enforces the limiter's default_limits on every route.
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # --- Exception handler --------------------------------------------------
    app.add_exception_handler(Exception, _unhandled_exception_handler)

    # --- Routers (all under /api) -------------------------------------------
    app.include_router(auth_routes.router, prefix="/api")
    app.include_router(projects_routes.router, prefix="/api")
    if settings.ENABLE_DEV_ROUTES and not settings.is_production:
        app.include_router(dev_routes.router, prefix="/api")

    # --- Health / root ------------------------------------------------------
    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {"name": settings.PRODUCT_NAME, "version": settings.API_VERSION, "status": "ok"}

    @app.get("/health", tags=["meta"])
    async def health() -> JSONResponse:
        """Liveness/readiness probe: pings Postgres (and Neo4j when enabled)."""
        checks: dict[str, str] = {}
        healthy = True

        try:
            session_factory = get_sessionmaker()
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
        except Exception:  # pragma: no cover - failure path
            logger.exception("Health check: Postgres probe failed")
            checks["postgres"] = "error"
            healthy = False

        if settings.GRAPH_ENABLED:
            try:
                driver = get_driver()
                async with driver.session(database=settings.NEO4J_DATABASE) as gs:
                    await gs.run("RETURN 1")
                checks["neo4j"] = "ok"
            except Exception:  # pragma: no cover - failure path
                logger.exception("Health check: Neo4j probe failed")
                checks["neo4j"] = "error"
                healthy = False

        status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            status_code=status_code,
            content={"status": "healthy" if healthy else "unhealthy", "checks": checks},
        )

    return app


async def _rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return 429 on rate-limit breaches."""
    del request, exc
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded"},
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler. Leaks details only when ENABLE_DETAILED_ERRORS is true."""
    del request
    settings = get_settings()
    logger.exception("Unhandled exception")
    detail = str(exc) if settings.ENABLE_DETAILED_ERRORS else "Internal server error"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    _settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=_settings.API_HOST,
        port=_settings.API_PORT,
        reload=_settings.is_development,
    )
    sys.exit(0)
