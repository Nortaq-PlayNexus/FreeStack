"""
Shared data models for FreeStack.

Base models, user/role models, and common mixins.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .core.database import Base


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class UserRole(str, Enum):
    """System roles."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions."""
    # User management
    USERS_CREATE = "users:create"
    USERS_READ = "users:read"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    USERS_LIST = "users:list"

    # Role management
    ROLES_CREATE = "roles:create"
    ROLES_READ = "roles:read"
    ROLES_UPDATE = "roles:update"
    ROLES_DELETE = "roles:delete"
    ROLES_ASSIGN = "roles:assign"

    # System
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_LOGS = "system:logs"

    # API
    API_ACCESS = "api:access"
    API_ADMIN = "api:admin"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPERADMIN: set(Permission),
    UserRole.ADMIN: {
        Permission.USERS_CREATE,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.USERS_LIST,
        Permission.ROLES_READ,
        Permission.ROLES_ASSIGN,
        Permission.SYSTEM_MONITOR,
        Permission.SYSTEM_LOGS,
        Permission.API_ACCESS,
        Permission.API_ADMIN,
    },
    UserRole.MANAGER: {
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_LIST,
        Permission.ROLES_READ,
        Permission.SYSTEM_MONITOR,
        Permission.API_ACCESS,
    },
    UserRole.USER: {
        Permission.USERS_READ,
        Permission.API_ACCESS,
    },
    UserRole.VIEWER: {
        Permission.USERS_READ,
        Permission.API_ACCESS,
    },
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
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class IDMixin:
    """Mixin for UUID primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class User(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    """User model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.PENDING_VERIFICATION,
        nullable=False,
    )
    roles: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    permissions: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("ix_users_email_status", "email", "status"),
        Index("ix_users_username_status", "username", "status"),
    )

    def get_permissions(self) -> Set[Permission]:
        """Get all permissions for this user (role-based + explicit)."""
        permissions = set(self.permissions)
        for role_str in self.roles:
            try:
                role = UserRole(role_str)
                permissions.update(ROLE_PERMISSIONS.get(role, set()))
            except ValueError:
                pass
        return permissions

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.get_permissions()

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return role.value in self.roles

    def add_role(self, role: UserRole) -> None:
        """Add a role to the user."""
        if role.value not in self.roles:
            self.roles.append(role.value)

    def remove_role(self, role: UserRole) -> None:
        """Remove a role from the user."""
        if role.value in self.roles:
            self.roles.remove(role.value)


class UserSession(Base, IDMixin, TimestampMixin):
    """User session model."""

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_user_sessions_user_expires", "user_id", "expires_at"),
        Index("ix_user_sessions_token_revoked", "session_token", "revoked"),
    )


class APIKey(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    """API key model."""

    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_keys_user_deleted", "user_id", "is_deleted"),
        UniqueConstraint("user_id", "name", name="uq_api_keys_user_name"),
    )


class AuditLog(Base, IDMixin):
    """Audit log model."""

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_user_action", "user_id", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_timestamp", "created_at"),
    )


# Pydantic models for API
class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(min_length=12)
    roles: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    status: Optional[UserStatus] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class UserResponse(UserBase):
    """User response model."""
    id: uuid.UUID
    status: UserStatus
    roles: List[str]
    permissions: List[str]
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    login_count: int

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""
    items: List[UserResponse]
    total: int
    offset: int
    limit: int


class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str = Field(min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response model (without full key)."""
    id: uuid.UUID
    name: str
    key_prefix: str
    permissions: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(APIKeyResponse):
    """API key creation response (includes full key)."""
    key: str


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: Optional[str]
    request_id: Optional[str]
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True