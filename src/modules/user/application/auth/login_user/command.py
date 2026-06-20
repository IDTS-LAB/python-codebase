from pydantic import BaseModel


class LoginUserCommand(BaseModel):
    username: str
    password: str
