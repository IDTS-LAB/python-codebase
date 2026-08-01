
from pydantic import BaseModel


class GetRoleQuery(BaseModel):
    role_id: int
