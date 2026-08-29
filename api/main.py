"""
FastAPI application factory for FreeStack.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings
from ..core.database import init_db, close_db
from ..core.logging import setup_logging, get_logger, log_request
from ..core.health import health_check, readiness_check
from ..core.events import event_bus
from .routes import auth, users, health as health_routes, info
from .middleware import (
    CorrelationIDMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    LoggingMiddleware,
)

logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics middleware."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response


import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger.info("Starting FreeStack API")

    # Initialize database
    await init_db()

    # Start event bus middleware
    event_bus.add_middleware(logging_middleware)

    yield

    # Shutdown
    logger.info("Shutting down FreeStack API")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app.name,
        version="0.1.0",
        description="FreeStack API",
        docs_url=settings.api.docs_url if settings.app.environment != "production" else None,
        redoc_url=settings.api.redoc_url if settings.app.environment != "production" else None,
        openapi_url=settings.api.openapi_url if settings.app.environment != "production" else None,
        lifespan=lifespan,
    )

    # Middleware (order matters - last added runs first)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Rate limiting
    if settings.api.rate_limit_storage == "redis":
        app.add_middleware(RateLimitMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=settings.api.cors_allow_credentials,
        allow_methods=settings.api.cors_allow_methods,
        allow_headers=settings.api.cors_allow_headers,
    )

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "message": "An unexpected error occurred"},
        )

    # Routes
    app.include_router(health_routes.router, prefix="/health", tags=["health"])
    app.include_router(info.router, prefix="/info", tags=["info"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])

    # Metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        return {"name": settings.app.name, "version": "0.1.0", "status": "running"}

    return app


async def logging_middleware(event):
    """Log events from the event bus."""
    logger.debug("Event published", event_type=event.event_type, event_id=event.event_id)