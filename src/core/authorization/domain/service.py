from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.core.utils.cursor import CursorDirection
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.entities.role import Role


class AuthorizationService(ABC):
    @abstractmethod
    async def can(self, subject: str, resource: str, action: str) -> bool:
        pass

    @abstractmethod
    async def assign_role(self, subject: str, role: str) -> None:
        pass

    @abstractmethod
    async def get_roles_for_subject(self, subject: str) -> list[str]:
        pass

    @abstractmethod
    async def create_role(self, role: Role) -> Role:
        pass

    @abstractmethod
    async def update_role(self, role: Role) -> Role | None:
        pass

    @abstractmethod
    async def delete_role(self, role_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_role(self, role_id: UUID) -> Role | None:
        pass

    @abstractmethod
    async def list_roles(self) -> list[Role]:
        pass

    @abstractmethod
    async def list_roles_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Role], bool]:
        pass

    @abstractmethod
    async def create_permission(self, permission: Permission) -> Permission:
        pass

    @abstractmethod
    async def update_permission(self, permission: Permission) -> Permission | None:
        pass

    @abstractmethod
    async def delete_permission(self, permission_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_permission(self, permission_id: UUID) -> Permission | None:
        pass

    @abstractmethod
    async def list_permissions(self) -> list[Permission]:
        pass

    @abstractmethod
    async def list_permissions_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Permission], bool]:
        pass

    @abstractmethod
    async def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        pass

    @abstractmethod
    async def remove_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        pass
