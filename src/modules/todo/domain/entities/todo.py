from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Todo:
    id: UUID
    title: str
    description: str | None
    is_completed: bool
    user_id: UUID

    @classmethod
    def create(cls, title: str, user_id: UUID, description: str | None = None) -> Todo:
        return cls(
            id=uuid4(),
            title=title,
            description=description,
            is_completed=False,
            user_id=user_id,
        )

    def mark_completed(self):
        self.is_completed = True
