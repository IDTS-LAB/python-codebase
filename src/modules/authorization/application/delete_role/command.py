
from pydantic import BaseModel


class DeleteRoleCommand(BaseModel):
    role_id: int
