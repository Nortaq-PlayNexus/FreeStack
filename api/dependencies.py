"""
API dependencies for FreeStack.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import TokenPayload, verify_token, create_permission_checker, PermissionChecker
from ..core.database import get_db
from ..models.user import User, UserStatus, Permission
from ..core.database import BaseRepository

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user from JWT token."""
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials)
    if not token_data:
        return None

    user_repo = BaseRepository(db, User)
    user = await user_repo.get(token_data.sub)

    if not user or user.is_deleted or user.status != UserStatus.ACTIVE:
        return None

    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Get current active user (raises if not authenticated)."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_permission(permission: Permission):
    """Dependency to require a specific permission."""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}",
            )
        return current_user
    return permission_checker


def require_role(role: str):
    """Dependency to require a specific role."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not current_user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}",
            )
        return current_user
    return role_checker


def require_any_role(roles: list[str]):
    """Dependency to require any of the specified roles."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not current_user.has_any_role(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles required: {', '.join(roles)}",
            )
        return current_user
    return role_checker


class PaginationParams:
    """Pagination parameters."""

    def __init__(
        self,
        offset: int = 0,
        limit: int = 100,
    ):
        self.offset = max(0, offset)
        self.limit = min(max(1, limit), 1000)


async def get_pagination_params(
    offset: int = 0,
    limit: int = 100,
) -> PaginationParams:
    """Get pagination parameters."""
    return PaginationParams(offset=offset, limit=limit)