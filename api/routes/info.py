"""
Info routes for FreeStack API.
"""

from fastapi import APIRouter

from ...core.config import settings

router = APIRouter()


@router.get("")
async def info():
    """Application information."""
    return {
        "name": settings.app.name,
        "version": "0.1.0",
        "environment": settings.app.environment,
        "build_time": "2026-08-30T00:00:00Z",
        "git_commit": "unknown",
    }