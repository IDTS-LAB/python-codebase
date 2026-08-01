
from pydantic import BaseModel


class DeletePermissionCommand(BaseModel):
    permission_id: int
