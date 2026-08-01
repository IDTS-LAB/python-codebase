
from pydantic import BaseModel


class UpdatePermissionCommand(BaseModel):
    permission_id: int
    resource: str | None = None
    action: str | None = None
    description: str | None = None
