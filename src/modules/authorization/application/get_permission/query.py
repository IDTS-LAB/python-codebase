from uuid import UUID

from pydantic import BaseModel


class GetPermissionQuery(BaseModel):
    permission_id: UUID
