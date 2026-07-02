"""OpenTelemetry setup. A no-op when ``OTEL_ENABLED`` is false."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.config import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

_configured = False


def configure_telemetry(engine: AsyncEngine | None = None) -> None:
    """Configure OTEL tracing + instrumentation when enabled.

    Safe to call when OTEL is disabled or the OTEL packages are not installed —
    it logs and returns without raising.
    """
    global _configured
    settings = get_settings()

    if not settings.OTEL_ENABLED:
        logger.debug("OTEL disabled; telemetry not configured")
        return
    if _configured:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning("OTEL_ENABLED=true but OpenTelemetry packages are not installed")
        return

    resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    LoggingInstrumentor().instrument(set_logging_format=False)
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    _configured = True
    logger.info("OTEL configured (service=%s)", settings.OTEL_SERVICE_NAME)


def instrument_fastapi(app: FastAPI) -> None:
    """Instrument the FastAPI app when OTEL is enabled and available."""
    settings = get_settings()
    if not settings.OTEL_ENABLED:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    except ImportError:  # pragma: no cover - optional dependency
        return
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()


def span_attributes(**attributes: Any) -> None:
    """Attach attributes to the current span when tracing is active.

    Never pass secrets, tokens or ``tenant_id`` here.
    """
    if not get_settings().OTEL_ENABLED:
        return
    try:
        from opentelemetry import trace
    except ImportError:  # pragma: no cover - optional dependency
        return
    span = trace.get_current_span()
    if span is None:
        return
    for key, value in attributes.items():
        span.set_attribute(key, value)
