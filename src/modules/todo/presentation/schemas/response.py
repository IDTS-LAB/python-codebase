from pydantic import BaseModel

from src.modules.user import UserProfile


class TodoResponse(BaseModel):
    id: int
    title: str
    is_completed: bool


class TodoWithOwnerResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    is_completed: bool
    owner: UserProfile
