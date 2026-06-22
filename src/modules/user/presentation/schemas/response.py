from pydantic import BaseModel

from src.modules.user.domain.entities.user import (
    UserProfile,
    UserSecurity,
    UserSettings,
)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str | None
    auth_provider: str = "local"
    external_id: str | None
    status: str = "pending_verification"
    created_at: str | None
    updated_at: str | None
    profile: UserProfile | None
    settings: UserSettings | None
    security: UserSecurity | None
