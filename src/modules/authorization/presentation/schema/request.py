from pydantic import BaseModel


class CreateRoleRequest(BaseModel):
    name: str
    description: str | None = None


class UpdateRoleRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class CreatePermissionRequest(BaseModel):
    resource: str
    action: str
    description: str | None = None


class UpdatePermissionRequest(BaseModel):
    resource: str | None = None
    action: str | None = None
    description: str | None = None
