from uuid import UUID

from pydantic import BaseModel


class LogoutUserCommand(BaseModel):
    user_id: str
