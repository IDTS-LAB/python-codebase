from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: str
    updated_at: str


class PermissionResponse(BaseModel):
    id: int
    key: str
    resource: str
    action: str
    description: str | None
    created_at: str
    updated_at: str
