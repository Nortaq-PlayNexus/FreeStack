"""
User management routes for FreeStack API.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import (
    get_current_active_user,
    require_permission,
    get_pagination_params,
    get_db,
    PaginationParams,
)
from ...models.user import (
    User,
    UserStatus,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    Permission,
)

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    status: Optional[UserStatus] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_permission(Permission.USERS_LIST)),
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination and filtering."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    # Build filters
    filters = {}
    if status:
        filters["status"] = status

    users = await user_repo.list(
        offset=pagination.offset,
        limit=pagination.limit,
        order_by=User.created_at.desc(),
        **filters,
    )

    total = await user_repo.count(**filters)

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission(Permission.USERS_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    from ...core.auth import get_password_hash, validate_password_strength
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    # Validate password
    errors = validate_password_strength(user_data.password)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password_errors": errors},
        )

    # Check email uniqueness
    existing = await user_repo.get_by(email=user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check username uniqueness
    existing = await user_repo.get_by(username=user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # Create user
    user = await user_repo.create(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        status=UserStatus.ACTIVE,
        roles=user_data.roles,
        permissions=[],
    )

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.USERS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get a user by ID."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission(Permission.USERS_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Update a user."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check email uniqueness if changing
    if user_data.email and user_data.email != user.email:
        existing = await user_repo.get_by(email=user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )

    # Check username uniqueness if changing
    if user_data.username and user_data.username != user.username:
        existing = await user_repo.get_by(username=user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    # Update user
    update_data = user_data.model_dump(exclude_unset=True)
    user = await user_repo.update(user_id, **update_data)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.USERS_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a user."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    await user_repo.delete(user_id)


@router.post("/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(
    user_id: UUID,
    role: str,
    current_user: User = Depends(require_permission(Permission.ROLES_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    """Assign a role to a user."""
    from ...core.database import BaseRepository
    from ...models.user import UserRole
    user_repo = BaseRepository(db, User)

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate role
    try:
        UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}",
        )

    if role not in user.roles:
        user.roles.append(role)
        await db.commit()


@router.delete("/{user_id}/roles/{role}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role(
    user_id: UUID,
    role: str,
    current_user: User = Depends(require_permission(Permission.ROLES_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    """Remove a role from a user."""
    from ...core.database import BaseRepository
    user_repo = BaseRepository(db, User)

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if role in user.roles:
        user.roles.remove(role)
        await db.commit()