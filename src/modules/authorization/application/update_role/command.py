
from pydantic import BaseModel


class UpdateRoleCommand(BaseModel):
    role_id: int
    name: str | None = None
    description: str | None = None
