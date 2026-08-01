from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Todo:
    id: int | None = None
    title: str = ""
    description: str | None = None
    is_completed: bool = False
    user_id: int = 0

    @classmethod
    def create(cls, title: str, user_id: int, description: str | None = None) -> Todo:
        return cls(
            id=None,
            title=title,
            description=description,
            is_completed=False,
            user_id=user_id,
        )

    def mark_completed(self):
        self.is_completed = True
