from uuid import UUID

from pydantic import BaseModel


class UpdateRoleCommand(BaseModel):
    role_id: UUID
    name: str | None = None
    description: str | None = None
