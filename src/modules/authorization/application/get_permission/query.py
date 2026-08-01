
from pydantic import BaseModel


class GetPermissionQuery(BaseModel):
    permission_id: int
