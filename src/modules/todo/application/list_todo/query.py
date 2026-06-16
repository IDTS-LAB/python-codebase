from uuid import UUID

from pydantic import BaseModel


class GetTodosQuery(BaseModel):
    user_id: UUID
