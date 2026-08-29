"""
Health check routes for FreeStack API.
"""

from fastapi import APIRouter

from ...core.health import health_check, readiness_check

router = APIRouter()


@router.get("")
async def health():
    """Liveness probe - basic health check."""
    return await health_check()


@router.get("/ready")
async def ready():
    """Readiness probe - critical dependencies only."""
    return await readiness_check()