from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class User:
    id: UUID
    email: str
    password: str

    @classmethod
    def create(cls, email: str, hashed_password: str) -> User:
        return cls(id=uuid4(), email=email, password=hashed_password)
