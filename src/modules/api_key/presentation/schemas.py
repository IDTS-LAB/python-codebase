from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    permissions: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    permissions: list[str]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    key: str
    expires_at: Optional[datetime]
    created_at: datetime


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyResponse]
    total: int
