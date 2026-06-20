from pydantic import BaseModel


class RefreshTokenCommand(BaseModel):
    token: str
