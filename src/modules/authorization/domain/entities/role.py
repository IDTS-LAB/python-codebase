from dataclasses import dataclass


@dataclass(kw_only=True)
class Role:
    id: int | None = None
    name: str
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def create(cls, name: str, description: str | None = None) -> "Role":
        return cls(
            id=None,
            name=name,
            description=description,
        )
