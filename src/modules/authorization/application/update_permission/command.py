from uuid import UUID

from pydantic import BaseModel


class UpdatePermissionCommand(BaseModel):
    permission_id: UUID
    resource: str | None = None
    action: str | None = None
    description: str | None = None
