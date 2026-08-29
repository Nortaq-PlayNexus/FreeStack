"""
Auth routes for FreeStack API.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_active_user, get_db
from ...core.auth import (
    create_token_pair,
    verify_token,
    get_password_hash,
    verify_password,
    validate_password_strength,
)
from ...models.user import User, UserStatus, UserResponse

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return token pair."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    user = await user_repo.get_by(email=request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        # Increment failed login attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                from datetime import datetime, timezone, timedelta
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to failed login attempts",
        )

    # Check user status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active",
        )

    # Reset failed attempts and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    user.login_count += 1
    await db.commit()

    # Create token pair
    roles = user.roles
    permissions = user.permissions
    tokens = create_token_pair(
        subject=str(user.id),
        email=user.email,
        roles=roles,
        permissions=permissions,
    )

    return TokenResponse(**tokens.model_dump())


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    # Validate password strength
    errors = validate_password_strength(request.password)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password_errors": errors},
        )

    # Check if email exists
    existing = await user_repo.get_by(email=request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check if username exists
    existing = await user_repo.get_by(username=request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # Create user
    user = await user_repo.create(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        status=UserStatus.ACTIVE,  # In production, use PENDING_VERIFICATION
        roles=["user"],
        permissions=[],
    )

    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
):
    """Refresh access token using refresh token."""
    token_data = verify_token(request.refresh_token, token_type="refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Create new token pair
    tokens = create_token_pair(
        subject=token_data.sub,
        email=token_data.email,
        roles=token_data.roles,
        permissions=token_data.permissions,
    )

    return TokenResponse(**tokens.model_dump())


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """Logout user (invalidate refresh token - would need token blacklist in production)."""
    # In production, add refresh token to blacklist/blocklist
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)