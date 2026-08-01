from dataclasses import dataclass


@dataclass(kw_only=True)
class Permission:
    id: int | None = None
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
            id=None,
            key=key,
            resource=resource,
            action=action,
            description=description,
        )
