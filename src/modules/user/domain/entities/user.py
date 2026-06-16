from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4


@dataclass
class User:
    id: UUID
    email: str
    password: str

    username: str | None = None
    fullname: str | None = None
    birthday: date | None = None

    @classmethod
    def create(
        cls,
        email: str,
        password: str,
        username: str | None = None,
        fullname: str | None = None,
        birthday: date | None = None,
    ) -> User:
        return cls(
            id=uuid4(),
            email=email,
            password=password,
            username=username,
            fullname=fullname,
            birthday=birthday,
        )
