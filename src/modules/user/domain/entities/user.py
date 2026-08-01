from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class UserProfile:
    """User profile containing personal information."""

    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    birth_date: Optional[date] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class UserSettings:
    """User preferences and settings."""

    user_id: int
    preferences: dict = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class UserSecurity:
    """User security configuration and state."""

    user_id: int
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    two_factor_backup_codes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(kw_only=True)
class User:
    """Core user identity and authentication aggregate root."""

    id: int | None = None
    email: str
    password_hash: str

    # Identity
    username: Optional[str] = None
    auth_provider: str = "local"
    external_id: Optional[str] = None
    status: str = "pending_verification"

    # Related entities (loaded separately via repository methods)
    profile: Optional[UserProfile] = None
    settings: Optional[UserSettings] = None
    security: Optional[UserSecurity] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def create(
        cls,
        email: str,
        password_hash: str,
        username: Optional[str] = None,
        auth_provider: str = "local",
    ) -> User:
        return cls(
            id=None,
            email=email,
            password_hash=password_hash,
            username=username,
            auth_provider=auth_provider,
            status="pending_verification",
        )
