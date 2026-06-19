from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class AuthorizationResource:
    id: UUID
    key: str
    name: str
    description: str | None = None

    @classmethod
    def create(
        cls,
        key: str,
        name: str,
        description: str | None = None,
    ) -> "AuthorizationResource":
        return cls(
            id=uuid4(),
            key=key,
            name=name,
            description=description,
        )
