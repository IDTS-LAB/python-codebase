from uuid import UUID

from pydantic import BaseModel


class GetRoleQuery(BaseModel):
    role_id: UUID
