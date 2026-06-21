from pydantic import BaseModel


class CreateRoleCommand(BaseModel):
    name: str
    description: str | None = None
