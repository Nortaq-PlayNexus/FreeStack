"""
Pytest configuration and fixtures for FreeStack.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import Settings
from core.database import Base, DatabaseManager, get_db
from core.auth import create_access_token, get_password_hash
from models.user import User, UserStatus, UserRole
from api.main import create_app


# Test database URL (in-memory SQLite for unit tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        app__environment="testing",
        app__debug=True,
        database__url=TEST_DATABASE_URL,
        redis__url="redis://localhost:6379/1",
        auth__secret_key="test-secret-key-for-testing-only",
    )


@pytest.fixture
def app(test_settings):
    """Create test FastAPI app."""
    from core.config import settings as global_settings
    # Override global settings for testing
    global_settings.app.environment = "testing"
    global_settings.database.url = TEST_DATABASE_URL

    app = create_app()
    return app


@pytest.fixture
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@freestack.local",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        status=UserStatus.ACTIVE,
        roles=["user"],
        permissions=[],
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_session: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        email="admin@freestack.local",
        username="admin",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        status=UserStatus.ACTIVE,
        roles=["superadmin"],
        permissions=[],
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    token = create_access_token(
        subject=str(test_user.id),
        email=test_user.email,
        roles=test_user.roles,
        permissions=test_user.permissions,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Create authentication headers for admin user."""
    token = create_access_token(
        subject=str(admin_user.id),
        email=admin_user.email,
        roles=admin_user.roles,
        permissions=admin_user.permissions,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return MagicMock()


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    return AsyncMock()


# Unit test fixtures
@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "email": "sample@freestack.local",
        "username": "sampleuser",
        "password": "samplepassword123",
        "full_name": "Sample User",
    }


@pytest.fixture
def sample_api_key_data() -> dict:
    """Sample API key data for testing."""
    return {
        "name": "Test API Key",
        "permissions": ["users:read", "api:access"],
    }