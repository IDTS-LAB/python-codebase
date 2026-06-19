from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Permission:
    id: UUID
    key: str
    resource: str
    action: str
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def create(
        cls,
        key: str,
        resource: str,
        action: str,
        description: str | None,
    ) -> "Permission":
        return cls(
            id=uuid4(),
            key=key,
            resource=resource,
            action=action,
            description=description,
        )
