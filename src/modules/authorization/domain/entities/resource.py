from dataclasses import dataclass


@dataclass(kw_only=True)
class AuthorizationResource:
    id: int | None = None
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
            id=None,
            key=key,
            name=name,
            description=description,
        )
