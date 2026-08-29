"""
Model mixins for FreeStack.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column


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


class VersionMixin:
    """Mixin for optimistic locking."""

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class MetadataMixin:
    """Mixin for flexible metadata storage."""

    metadata: Mapped[Dict[str, Any]] = mapped_column(default=dict, nullable=False)


class AuditMixin:
    """Mixin for audit fields."""

    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(nullable=True)