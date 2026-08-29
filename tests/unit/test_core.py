"""
Unit tests for FreeStack core modules.
"""

import pytest
from datetime import datetime, timezone, timedelta

from core.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_token,
    get_password_hash,
    verify_password,
    validate_password_strength,
    PermissionChecker,
    expand_roles,
)
from core.config import Settings
from core.events import Event, EventBus, event_handler
from core.health import HealthStatus, HealthCheckResult, DatabaseHealthCheck, HealthChecker
from models.user import User, UserStatus, UserRole, Permission, ROLE_PERMISSIONS


class TestAuth:
    """Tests for authentication module."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword123!", hashed)

    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Valid password
        errors = validate_password_strength("ValidPass123!")
        assert len(errors) == 0

        # Too short
        errors = validate_password_strength("Short1!")
        assert any("at least" in e for e in errors)

        # No uppercase
        errors = validate_password_strength("nouppercase123!")
        assert any("uppercase" in e for e in errors)

        # No lowercase
        errors = validate_password_strength("NOLOWERCASE123!")
        assert any("lowercase" in e for e in errors)

        # No numbers
        errors = validate_password_strength("NoNumbers!")
        assert any("number" in e for e in errors)

        # No symbols
        errors = validate_password_strength("NoSymbols123")
        assert any("symbol" in e for e in errors)

    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token(
            subject="user-123",
            email="test@example.com",
            roles=["user"],
            permissions=["users:read"],
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token(
            subject="user-123",
            email="test@example.com",
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_pair(self):
        """Test token pair creation."""
        pair = create_token_pair(
            subject="user-123",
            email="test@example.com",
            roles=["user"],
            permissions=["users:read"],
        )

        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token = create_access_token(
            subject="user-123",
            email="test@example.com",
        )

        payload = verify_token(token)
        assert payload is not None
        assert payload.sub == "user-123"
        assert payload.email == "test@example.com"
        assert payload.type == "access"

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        payload = verify_token("invalid.token.here")
        assert payload is None

    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        token = create_access_token(
            subject="user-123",
            email="test@example.com",
            expires_delta=timedelta(seconds=-1),
        )

        payload = verify_token(token)
        assert payload is None

    def test_verify_wrong_token_type(self):
        """Test verifying refresh token as access token."""
        refresh_token = create_refresh_token(
            subject="user-123",
            email="test@example.com",
        )

        payload = verify_token(refresh_token, token_type="access")
        assert payload is None


class TestPermissionChecker:
    """Tests for permission checking."""

    def test_has_permission(self):
        """Test checking permissions."""
        checker = PermissionChecker(
            roles=["user"],
            permissions=["users:read", "api:access"],
        )

        assert checker.has_permission("users:read")
        assert checker.has_permission("api:access")
        assert not checker.has_permission("users:delete")

    def test_has_any_permission(self):
        """Test checking any permission."""
        checker = PermissionChecker(
            roles=["user"],
            permissions=["users:read"],
        )

        assert checker.has_any_permission(["users:read", "users:delete"])
        assert not checker.has_any_permission(["users:delete", "users:create"])

    def test_has_all_permissions(self):
        """Test checking all permissions."""
        checker = PermissionChecker(
            roles=["user"],
            permissions=["users:read", "api:access"],
        )

        assert checker.has_all_permissions(["users:read", "api:access"])
        assert not checker.has_all_permissions(["users:read", "users:delete"])

    def test_has_role(self):
        """Test checking roles."""
        checker = PermissionChecker(
            roles=["user", "manager"],
            permissions=[],
        )

        assert checker.has_role("user")
        assert checker.has_role("manager")
        assert not checker.has_role("admin")

    def test_has_any_role(self):
        """Test checking any role."""
        checker = PermissionChecker(
            roles=["user"],
            permissions=[],
        )

        assert checker.has_any_role(["user", "admin"])
        assert not checker.has_any_role(["admin", "superadmin"])

    def test_has_all_roles(self):
        """Test checking all roles."""
        checker = PermissionChecker(
            roles=["user", "manager"],
            permissions=[],
        )

        assert checker.has_all_roles(["user", "manager"])
        assert not checker.has_all_roles(["user", "admin"])


class TestRoleExpansion:
    """Tests for role hierarchy expansion."""

    def test_expand_roles(self):
        """Test role expansion."""
        expanded = expand_roles(["admin"])
        assert "admin" in expanded
        assert "manager" in expanded
        assert "user" in expanded
        assert "viewer" in expanded

    def test_expand_superadmin(self):
        """Test superadmin expansion includes all roles."""
        expanded = expand_roles(["superadmin"])
        assert len(expanded) == 5  # superadmin, admin, manager, user, viewer

    def test_expand_viewer_only(self):
        """Test viewer role doesn't expand."""
        expanded = expand_roles(["viewer"])
        assert expanded == {"viewer"}


class TestEvents:
    """Tests for event system."""

    @pytest.mark.asyncio
    async def test_event_bus_publish(self):
        """Test publishing events."""
        bus = EventBus()
        received = []

        def handler(event: Event):
            received.append(event)

        bus.subscribe_sync("test.event", handler)

        event = Event(event_type="test.event", payload={"data": "test"})
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].event_type == "test.event"
        assert received[0].payload["data"] == "test"

    @pytest.mark.asyncio
    async def test_event_bus_async_handler(self):
        """Test async event handler."""
        bus = EventBus()
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe_async("test.async", handler)

        event = Event(event_type="test.async", payload={"data": "async"})
        await bus.publish(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_event_bus_multiple_handlers(self):
        """Test multiple handlers for same event."""
        bus = EventBus()
        received = []

        def handler1(event: Event):
            received.append(("handler1", event))

        def handler2(event: Event):
            received.append(("handler2", event))

        bus.subscribe_sync("test.multi", handler1)
        bus.subscribe_sync("test.multi", handler2)

        event = Event(event_type="test.multi")
        await bus.publish(event)

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_event_correlation_id(self):
        """Test event correlation IDs."""
        event = Event(event_type="test").with_correlation("corr-123")
        assert event.correlation_id == "corr-123"

    @pytest.mark.asyncio
    async def test_event_causation_id(self):
        """Test event causation IDs."""
        event = Event(event_type="test").caused_by("cause-456")
        assert event.causation_id == "cause-456"


class TestHealthChecks:
    """Tests for health checks."""

    def test_health_check_result(self):
        """Test health check result creation."""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            duration_ms=10.5,
        )

        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"
        assert result.duration_ms == 10.5

    def test_health_status_enum(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"


class TestUserModel:
    """Tests for user model."""

    def test_user_permissions(self):
        """Test user permission calculation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            roles=["admin"],
            permissions=["custom:permission"],
        )

        perms = user.get_permissions()
        # Should have admin permissions + custom
        assert "users:read" in perms
        assert "custom:permission" in perms

    def test_user_has_permission(self):
        """Test user has_permission method."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            roles=["user"],
            permissions=[],
        )

        assert user.has_permission(Permission.USERS_READ)
        assert user.has_permission(Permission.API_ACCESS)
        assert not user.has_permission(Permission.USERS_DELETE)

    def test_user_has_role(self):
        """Test user has_role method."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            roles=["admin", "user"],
            permissions=[],
        )

        assert user.has_role(UserRole.ADMIN)
        assert user.has_role(UserRole.USER)
        assert not user.has_role(UserRole.SUPERADMIN)

    def test_user_add_remove_role(self):
        """Test adding and removing roles."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            roles=["user"],
            permissions=[],
        )

        user.add_role(UserRole.ADMIN)
        assert UserRole.ADMIN.value in user.roles

        user.remove_role(UserRole.ADMIN)
        assert UserRole.ADMIN.value not in user.roles


class TestRolePermissions:
    """Tests for role-permission mapping."""

    def test_superadmin_has_all_permissions(self):
        """Test superadmin has all permissions."""
        perms = ROLE_PERMISSIONS[UserRole.SUPERADMIN]
        assert len(perms) == len(Permission)

    def test_admin_permissions(self):
        """Test admin permissions."""
        perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert Permission.USERS_CREATE in perms
        assert Permission.USERS_DELETE in perms
        assert Permission.SYSTEM_CONFIG not in perms

    def test_viewer_permissions(self):
        """Test viewer permissions."""
        perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert Permission.USERS_READ in perms
        assert Permission.API_ACCESS in perms
        assert Permission.USERS_CREATE not in perms


class TestConfig:
    """Tests for configuration."""

    def test_settings_load(self):
        """Test settings can be loaded."""
        settings = Settings(
            auth__secret_key="test-secret-key-minimum-32-chars-long",
        )

        assert settings.app.name == "freestack"
        assert settings.database.pool_size == 20
        assert settings.auth.algorithm == "HS256"

    def test_settings_env_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("FREESTACK_APP__NAME", "custom-app")
        monkeypatch.setenv("FREESTACK_DATABASE__POOL_SIZE", "50")

        settings = Settings(
            auth__secret_key="test-secret-key-minimum-32-chars-long",
        )

        assert settings.app.name == "custom-app"
        assert settings.database.pool_size == 50