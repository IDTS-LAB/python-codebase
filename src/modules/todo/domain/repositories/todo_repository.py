from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.todo.domain.entities.todo import Todo


class TodoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, todo_id: UUID) -> Todo | None:
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: UUID) -> list[Todo]:
        pass

    @abstractmethod
    async def save(self, todo: Todo) -> Todo:
        pass

    @abstractmethod
    async def delete(self, todo_id: UUID) -> None:
        pass
