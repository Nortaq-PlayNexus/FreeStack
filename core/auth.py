"""
Authentication and authorization for FreeStack.

Provides JWT token management, password hashing, and RBAC utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Set

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from .config import settings


# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.auth.bcrypt_rounds,
)


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # subject (user ID)
    email: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str = "access"  # access | refresh
    jti: Optional[str] = None  # JWT ID for revocation


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime in seconds


def create_access_token(
    subject: str,
    email: str,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.auth.access_token_expire_minutes))

    payload = TokenPayload(
        sub=subject,
        email=email,
        roles=roles or [],
        permissions=permissions or [],
        exp=int(expire.timestamp()),
        iat=int(now.timestamp()),
        type="access",
    )

    return jwt.encode(
        payload.model_dump(),
        settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    )


def create_refresh_token(
    subject: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.auth.refresh_token_expire_days))

    payload = TokenPayload(
        sub=subject,
        email=email,
        exp=int(expire.timestamp()),
        iat=int(now.timestamp()),
        type="refresh",
    )

    return jwt.encode(
        payload.model_dump(),
        settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    )


def create_token_pair(
    subject: str,
    email: str,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
) -> TokenPair:
    """Create both access and refresh tokens."""
    access_token = create_access_token(subject, email, roles, permissions)
    refresh_token = create_refresh_token(subject, email)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.auth.access_token_expire_minutes * 60,
    )


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.auth.secret_key,
            algorithms=[settings.auth.algorithm],
        )

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return TokenPayload(**payload)

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """Decode token without verification (for debugging)."""
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False},
        )
    except jwt.InvalidTokenError:
        return None


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> List[str]:
    """Validate password meets policy requirements. Returns list of violations."""
    errors = []

    if len(password) < settings.auth.password_min_length:
        errors.append(f"Password must be at least {settings.auth.password_min_length} characters")

    if settings.auth.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.auth.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if settings.auth.password_require_numbers and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    if settings.auth.password_require_symbols and not any(not c.isalnum() for c in password):
        errors.append("Password must contain at least one symbol")

    return errors


class PermissionChecker:
    """Check user permissions and roles."""

    def __init__(self, roles: List[str], permissions: List[str]) -> None:
        self.roles = set(roles)
        self.permissions = set(permissions)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return bool(self.roles.intersection(roles))

    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if user has all specified roles."""
        return set(roles).issubset(self.roles)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return bool(self.permissions.intersection(permissions))

    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all specified permissions."""
        return set(permissions).issubset(self.permissions)


# Role hierarchy (higher roles inherit lower role permissions)
ROLE_HIERARCHY = {
    "superadmin": {"admin", "manager", "user", "viewer"},
    "admin": {"manager", "user", "viewer"},
    "manager": {"user", "viewer"},
    "user": {"viewer"},
    "viewer": set(),
}


def expand_roles(roles: List[str]) -> Set[str]:
    """Expand roles to include inherited roles."""
    expanded = set(roles)
    for role in roles:
        expanded.update(ROLE_HIERARCHY.get(role, set()))
    return expanded


def create_permission_checker(token: TokenPayload) -> PermissionChecker:
    """Create a PermissionChecker from a token payload."""
    expanded_roles = expand_roles(token.roles)
    return PermissionChecker(list(expanded_roles), token.permissions)