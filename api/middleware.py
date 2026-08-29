"""
API middleware for FreeStack.
"""

import uuid
import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.config import settings
from ..core.logging import get_logger, bind_context, clear_context

logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Bind to context for logging
        bind_context(correlation_id=correlation_id)

        # Add to request state
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            clear_context()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Log request
        logger.info(
            "http_request_start",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "http_request_complete",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        headers = settings.security.headers
        response.headers["X-Content-Type-Options"] = headers.x_content_type_options
        response.headers["X-Frame-Options"] = headers.x_frame_options
        response.headers["X-XSS-Protection"] = headers.x_xss_protection
        response.headers["Strict-Transport-Security"] = headers.strict_transport_security
        response.headers["Content-Security-Policy"] = headers.content_security_policy
        response.headers["Referrer-Policy"] = headers.referrer_policy
        response.headers["Permissions-Policy"] = headers.permissions_policy

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, app, rate_limit: str = "100/minute"):
        super().__init__(app)
        self.rate_limit = rate_limit
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as redis
            from ..core.config import settings
            self._redis = redis.from_url(settings.redis.url)
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/ready", "/metrics"]:
            return await call_next(request)

        redis_client = await self._get_redis()

        # Get client identifier (IP + user if authenticated)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        key = f"ratelimit:{user_id or client_ip}"

        # Parse rate limit (format: "100/minute")
        try:
            limit, window = self.rate_limit.split("/")
            limit = int(limit)
            window_seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}.get(window, 60)
        except ValueError:
            limit, window_seconds = 100, 60

        # Check rate limit
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)

        if current > limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Limit: {limit} requests per {window}",
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window_seconds),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current))
        response.headers["X-RateLimit-Reset"] = str(window_seconds)

        return response