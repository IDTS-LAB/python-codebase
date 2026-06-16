from pydantic import BaseModel, EmailStr


class CreateUserCommand(BaseModel):
    email: EmailStr
    password: str
