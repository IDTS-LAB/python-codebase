from pydantic import BaseModel


class GetTodosQuery(BaseModel):
    user_id: int
