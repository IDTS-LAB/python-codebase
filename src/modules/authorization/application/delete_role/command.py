from uuid import UUID

from pydantic import BaseModel


class DeleteRoleCommand(BaseModel):
    role_id: UUID
