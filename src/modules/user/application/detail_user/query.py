from pydantic import BaseModel


class DetailUserQuery(BaseModel):
    user_id: int
