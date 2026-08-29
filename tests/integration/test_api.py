"""
Integration tests for FreeStack API.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserStatus


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            json={"email": "test@freestack.local", "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/auth/login",
            json={"email": "test@freestack.local", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user."""
        response = await client.post(
            "/auth/login",
            json={"email": "nonexistent@freestack.local", "password": "password"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful registration."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@freestack.local",
                "username": "newuser",
                "password": "NewPassword123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@freestack.local"
        assert data["username"] == "newuser"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@freestack.local",
                "username": "anotheruser",
                "password": "Password123!",
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "weak@freestack.local",
                "username": "weakuser",
                "password": "weak",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "password_errors" in data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        """Test token refresh."""
        # First login
        login_response = await client.post(
            "/auth/login",
            json={"email": "test@freestack.local", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user info."""
        response = await client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@freestack.local"
        assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth."""
        response = await client.get("/auth/me")

        assert response.status_code == 401


class TestUserEndpoints:
    """Tests for user management endpoints."""

    @pytest.mark.asyncio
    async def test_list_users(self, client: AsyncClient, admin_auth_headers: dict):
        """Test listing users."""
        response = await client.get("/users", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, client: AsyncClient, auth_headers: dict):
        """Test listing users without admin permission."""
        response = await client.get("/users", headers=auth_headers)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, admin_auth_headers: dict):
        """Test creating a user."""
        response = await client.post(
            "/users",
            headers=admin_auth_headers,
            json={
                "email": "created@freestack.local",
                "username": "createduser",
                "password": "CreatedPass123!",
                "roles": ["user"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "created@freestack.local"
        assert data["username"] == "createduser"

    @pytest.mark.asyncio
    async def test_get_user(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Test getting a user by ID."""
        response = await client.get(f"/users/{test_user.id}", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Test getting non-existent user."""
        import uuid
        response = await client.get(f"/users/{uuid.uuid4()}", headers=admin_auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Test updating a user."""
        response = await client.patch(
            f"/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"full_name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, admin_auth_headers: dict, test_session: AsyncSession):
        """Test deleting a user."""
        # Create a user to delete
        from core.auth import get_password_hash
        from core.database import BaseRepository
        user_repo = BaseRepository(test_session, User)

        to_delete = await user_repo.create(
            email="todelete@freestack.local",
            username="todelete",
            hashed_password=get_password_hash("password"),
            status=UserStatus.ACTIVE,
            roles=["user"],
        )

        response = await client.delete(f"/users/{to_delete.id}", headers=admin_auth_headers)

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_self_forbidden(self, client: AsyncClient, admin_auth_headers: dict, admin_user: User):
        """Test that users cannot delete themselves."""
        response = await client.delete(f"/users/{admin_user.id}", headers=admin_auth_headers)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_assign_role(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Test assigning a role."""
        response = await client.post(
            f"/users/{test_user.id}/roles",
            headers=admin_auth_headers,
            json={"role": "manager"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_role(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Test removing a role."""
        # First add role
        from core.database import BaseRepository
        user_repo = BaseRepository(test_session, User)
        user = await user_repo.get(test_user.id)
        user.roles.append("manager")
        await test_session.commit()

        response = await client.delete(
            f"/users/{test_user.id}/roles/manager",
            headers=admin_auth_headers,
        )

        assert response.status_code == 204


class TestHealthEndpoints:
    """Tests for health endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data