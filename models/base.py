"""
Base model classes for FreeStack.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

T = TypeVar("T")


class BaseModelMixin:
    """Mixin for Pydantic models with common configuration."""

    class Config:
        from_attributes = True
        populate_by_name = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v),
        }


class TimestampMixin:
    """Mixin for created_at/updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete support."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)


class IDMixin:
    """Mixin for UUID primary key."""
    # Defined in each model to allow custom column names
    pass


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: List[T]
    total: int
    offset: int
    limit: int
    has_more: bool = Field(default=False)

    @classmethod
    def create(cls, items: List[T], total: int, offset: int, limit: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
            has_more=offset + limit < total,
        )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response."""

    success: bool = True
    data: T
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    checks: List[Dict[str, Any]]


class InfoResponse(BaseModel):
    """Application info response."""

    name: str
    version: str
    environment: str
    build_time: Optional[str] = None
    git_commit: Optional[str] = None