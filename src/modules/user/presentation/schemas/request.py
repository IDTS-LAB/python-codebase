from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    password: str


class LoginUserRequest(BaseModel):
    username: str
    password: str
