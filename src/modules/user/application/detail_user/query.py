from uuid import UUID

from pydantic import BaseModel


class DetailUserQuery(BaseModel):
    user_id: UUID
