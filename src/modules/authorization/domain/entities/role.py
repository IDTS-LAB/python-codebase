from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Role:
    id: UUID
    name: str
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def create(cls, name: str, description: str | None = None) -> "Role":
        return cls(
            id=uuid4(),
            name=name,
            description=description,
        )
