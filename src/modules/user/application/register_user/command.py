from pydantic import BaseModel, EmailStr


class RegisterUserCommand(BaseModel):
    email: EmailStr
    password: str
