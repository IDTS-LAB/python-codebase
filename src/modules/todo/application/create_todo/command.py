from pydantic import BaseModel


class CreateTodoCommand(BaseModel):
    title: str
    description: str | None = None
