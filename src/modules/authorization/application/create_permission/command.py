from pydantic import BaseModel


class CreatePermissionCommand(BaseModel):
    resource: str
    action: str
    description: str | None = None
