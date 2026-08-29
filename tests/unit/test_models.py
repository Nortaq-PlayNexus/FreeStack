"""
Unit tests for FreeStack models.
"""

import pytest
from uuid import UUID
from datetime import datetime, timezone

from models.user import (
    User,
    UserStatus,
    UserRole,
    Permission,
    UserSession,
    APIKey,
    AuditLog,
    UserCreate,
    UserUpdate,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse,
)
from models.base import PaginatedResponse, ErrorResponse, SuccessResponse


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """Test creating a user model."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            full_name="Test User",
            status=UserStatus.ACTIVE,
            roles=["user"],
            permissions=[],
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.status == UserStatus.ACTIVE
        assert user.roles == ["user"]
        assert isinstance(user.id, UUID)
        assert isinstance(user.created_at, datetime)

    def test_user_default_values(self):
        """Test user default values."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
        )

        assert user.status == UserStatus.PENDING_VERIFICATION
        assert user.roles == []
        assert user.permissions == []
        assert user.login_count == 0
        assert user.failed_login_attempts == 0
        assert user.email_verified is False

    def test_user_soft_delete(self):
        """Test soft delete fields."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
        )

        assert user.is_deleted is False
        assert user.deleted_at is None


class TestUserSessionModel:
    """Tests for UserSession model."""

    def test_session_creation(self):
        """Test creating a session."""
        session = UserSession(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            session_token="session_token_123",
            refresh_token="refresh_token_123",
            expires_at=datetime.now(timezone.utc),
        )

        assert session.session_token == "session_token_123"
        assert session.refresh_token == "refresh_token_123"
        assert session.revoked is False


class TestAPIKeyModel:
    """Tests for APIKey model."""

    def test_api_key_creation(self):
        """Test creating an API key."""
        api_key = APIKey(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Test Key",
            key_hash="hashed_key",
            key_prefix="fs_abc123",
            permissions=["users:read"],
        )

        assert api_key.name == "Test Key"
        assert api_key.key_prefix == "fs_abc123"
        assert api_key.permissions == ["users:read"]
        assert api_key.usage_count == 0


class TestAuditLogModel:
    """Tests for AuditLog model."""

    def test_audit_log_creation(self):
        """Test creating an audit log."""
        log = AuditLog(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            action="user.created",
            resource_type="user",
            resource_id="12345678-1234-5678-1234-567812345678",
            ip_address="192.168.1.1",
            details={"source": "api"},
            success=True,
        )

        assert log.action == "user.created"
        assert log.resource_type == "user"
        assert log.success is True


class TestPydanticModels:
    """Tests for Pydantic request/response models."""

    def test_user_create_validation(self):
        """Test UserCreate validation."""
        # Valid data
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="ValidPass123!",
        )
        assert user.email == "test@example.com"

        # Invalid email
        with pytest.raises(ValueError):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="ValidPass123!",
            )

        # Invalid username (too short)
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="ValidPass123!",
            )

        # Invalid username (special chars)
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                username="user@name",
                password="ValidPass123!",
            )

    def test_user_update_partial(self):
        """Test UserUpdate allows partial updates."""
        update = UserUpdate(full_name="New Name")
        assert update.full_name == "New Name"
        assert update.email is None
        assert update.roles is None

    def test_user_response_from_orm(self):
        """Test UserResponse from ORM model."""
        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            full_name="Test User",
            status=UserStatus.ACTIVE,
            roles=["user"],
            permissions=["api:access"],
            email_verified=True,
            login_count=5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        response = UserResponse.model_validate(user)
        assert response.email == "test@example.com"
        assert response.roles == ["user"]
        assert response.permissions == ["api:access"]

    def test_paginated_response(self):
        """Test PaginatedResponse."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse.create(items, total=100, offset=0, limit=10)

        assert response.items == items
        assert response.total == 100
        assert response.offset == 0
        assert response.limit == 10
        assert response.has_more is True

    def test_paginated_response_no_more(self):
        """Test PaginatedResponse when no more pages."""
        items = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse.create(items, total=2, offset=0, limit=10)

        assert response.has_more is False

    def test_error_response(self):
        """Test ErrorResponse."""
        error = ErrorResponse(
            error="validation_error",
            message="Invalid input",
            details={"field": "email"},
            request_id="req-123",
        )

        assert error.error == "validation_error"
        assert error.details["field"] == "email"

    def test_success_response(self):
        """Test SuccessResponse."""
        success = SuccessResponse(data={"result": "ok"}, message="Operation successful")

        assert success.success is True
        assert success.data["result"] == "ok"

    def test_api_key_create(self):
        """Test APIKeyCreate model."""
        key = APIKeyCreate(
            name="My Key",
            permissions=["users:read"],
        )

        assert key.name == "My Key"
        assert key.permissions == ["users:read"]
        assert key.expires_at is None

    def test_api_key_response(self):
        """Test APIKeyResponse."""
        response = APIKeyResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="My Key",
            key_prefix="fs_abc",
            permissions=["users:read"],
            created_at=datetime.now(timezone.utc),
        )

        assert response.key_prefix == "fs_abc"