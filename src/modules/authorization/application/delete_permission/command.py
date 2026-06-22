from uuid import UUID

from pydantic import BaseModel


class DeletePermissionCommand(BaseModel):
    permission_id: UUID
