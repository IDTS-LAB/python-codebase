from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization.infrastructure.models.casbin_rule_model import (
    CasbinRuleModel,
)
from src.core.authorization.infrastructure.models.permission_model import (
    PermissionModel,
)
from src.core.authorization.infrastructure.models.resource_model import (
    AuthorizationResourceModel,
)
from src.core.authorization.infrastructure.models.role_model import RoleModel
from src.core.authorization.infrastructure.models.role_permission_model import (
    RolePermissionModel,
)
from src.core.authorization.infrastructure.models.user_has_role_model import (
    UserHasRoleModel,
)
from src.modules.authorization import AuthorizationResource, Permission, Role
from src.shared.utils.cursor import CursorDirection


class SQLAlchemyCasbinPolicyRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def load_policy_lines(self) -> list[str]:
        result = await self._db.execute(select(CasbinRuleModel))
        rules = result.scalars().all()
        return [self._to_policy_line(rule) for rule in rules]

    async def list_policies(self) -> list[tuple[str, ...]]:
        result = await self._db.execute(select(CasbinRuleModel))
        return [self._to_policy_tuple(rule) for rule in result.scalars().all()]

    async def add_policy(self, ptype: str, *values: str) -> None:
        existing = await self._db.execute(
            select(CasbinRuleModel).where(
                CasbinRuleModel.ptype == ptype,
                CasbinRuleModel.v0 == self._value_at(values, 0),
                CasbinRuleModel.v1 == self._value_at(values, 1),
                CasbinRuleModel.v2 == self._value_at(values, 2),
                CasbinRuleModel.v3 == self._value_at(values, 3),
                CasbinRuleModel.v4 == self._value_at(values, 4),
                CasbinRuleModel.v5 == self._value_at(values, 5),
            )
        )
        if existing.scalar_one_or_none():
            return

        self._db.add(
            CasbinRuleModel(
                ptype=ptype,
                v0=self._value_at(values, 0),
                v1=self._value_at(values, 1),
                v2=self._value_at(values, 2),
                v3=self._value_at(values, 3),
                v4=self._value_at(values, 4),
                v5=self._value_at(values, 5),
            )
        )
        await self._db.flush()

    async def remove_policy(self, ptype: str, *values: str) -> None:
        await self._db.execute(
            delete(CasbinRuleModel).where(
                CasbinRuleModel.ptype == ptype,
                CasbinRuleModel.v0 == self._value_at(values, 0),
                CasbinRuleModel.v1 == self._value_at(values, 1),
                CasbinRuleModel.v2 == self._value_at(values, 2),
                CasbinRuleModel.v3 == self._value_at(values, 3),
                CasbinRuleModel.v4 == self._value_at(values, 4),
                CasbinRuleModel.v5 == self._value_at(values, 5),
            )
        )
        await self._db.flush()

    async def assign_role(self, subject: str, role: str) -> None:
        role_model = await self._get_role_by_name(role)
        if role_model is None:
            raise ValueError(f"Role does not exist: {role}")

        user_id = UUID(subject)
        existing_assignment = await self._db.execute(
            select(UserHasRoleModel).where(
                UserHasRoleModel.user_id == user_id,
                UserHasRoleModel.role_id == role_model.id,
            )
        )
        if existing_assignment.scalar_one_or_none() is None:
            self._db.add(UserHasRoleModel(user_id=user_id, role_id=role_model.id))
            await self._db.flush()

        await self.add_policy("g", subject, role)

    async def get_roles_for_subject(self, subject: str) -> list[str]:
        user_id = UUID(subject)
        result = await self._db.execute(
            select(RoleModel.name)
            .join(UserHasRoleModel, UserHasRoleModel.role_id == RoleModel.id)
            .where(UserHasRoleModel.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create_resource(
        self,
        resource: AuthorizationResource,
    ) -> AuthorizationResource:
        model = AuthorizationResourceModel(
            id=resource.id,
            key=resource.key,
            name=resource.name,
            description=resource.description,
        )
        self._db.add(model)
        await self._db.flush()
        return self._resource_from_model(model)

    async def list_resources(self) -> list[AuthorizationResource]:
        result = await self._db.execute(select(AuthorizationResourceModel))
        return [self._resource_from_model(model) for model in result.scalars().all()]

    async def create_role(self, role: Role) -> Role:
        model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
        )
        self._db.add(model)
        await self._db.flush()
        return self._role_from_model(model)

    async def get_role(self, role_id: UUID) -> Role | None:
        result = await self._db.execute(
            select(RoleModel).where(RoleModel.id == role_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._role_from_model(model)

    async def list_roles(self) -> list[Role]:
        result = await self._db.execute(select(RoleModel))
        return [self._role_from_model(model) for model in result.scalars().all()]

    async def list_roles_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Role], bool]:
        query = select(RoleModel)
        query = self._apply_cursor_pagination(
            query,
            RoleModel,
            cursor_created_at,
            cursor_id,
            direction,
        ).limit(limit + 1)

        result = await self._db.execute(query)
        models = list(result.scalars().all())
        has_more = len(models) > limit
        models = models[:limit]

        if direction == CursorDirection.DIRECTION_PREV:
            models = list(reversed(models))

        return [self._role_from_model(model) for model in models], has_more

    async def update_role(self, role: Role) -> Role | None:
        result = await self._db.execute(
            select(RoleModel).where(RoleModel.id == role.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        old_name = model.name
        model.name = role.name
        model.description = role.description
        await self._db.flush()

        if old_name != role.name:
            await self._rename_role_policies(old_name, role.name)

        return self._role_from_model(model)

    async def delete_role(self, role_id: UUID) -> None:
        role = await self.get_role(role_id)
        if role is None:
            return

        await self._db.execute(
            delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
        )
        await self._db.execute(
            delete(UserHasRoleModel).where(UserHasRoleModel.role_id == role_id)
        )
        await self._db.execute(delete(RoleModel).where(RoleModel.id == role_id))
        await self._db.execute(
            delete(CasbinRuleModel).where(
                ((CasbinRuleModel.ptype == "p") & (CasbinRuleModel.v0 == role.name))
                | ((CasbinRuleModel.ptype == "g") & (CasbinRuleModel.v1 == role.name))
            )
        )
        await self._db.flush()

    async def create_permission(self, permission: Permission) -> Permission:
        resource = await self._get_or_create_resource(permission.resource)
        model = PermissionModel(
            id=permission.id,
            key=permission.key,
            resource_id=resource.id,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
        )
        self._db.add(model)
        await self._db.flush()
        return self._permission_from_model(model)

    async def get_permission(self, permission_id: UUID) -> Permission | None:
        result = await self._db.execute(
            select(PermissionModel).where(PermissionModel.id == permission_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._permission_from_model(model)

    async def list_permissions(self) -> list[Permission]:
        result = await self._db.execute(select(PermissionModel))
        return [self._permission_from_model(model) for model in result.scalars().all()]

    async def list_permissions_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Permission], bool]:
        query = select(PermissionModel)
        query = self._apply_cursor_pagination(
            query,
            PermissionModel,
            cursor_created_at,
            cursor_id,
            direction,
        ).limit(limit + 1)

        result = await self._db.execute(query)
        models = list(result.scalars().all())
        has_more = len(models) > limit
        models = models[:limit]

        if direction == CursorDirection.DIRECTION_PREV:
            models = list(reversed(models))

        return [self._permission_from_model(model) for model in models], has_more

    async def update_permission(self, permission: Permission) -> Permission | None:
        result = await self._db.execute(
            select(PermissionModel).where(PermissionModel.id == permission.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        old_key = model.key
        resource = await self._get_or_create_resource(permission.resource)
        model.key = permission.key
        model.resource_id = resource.id
        model.resource = permission.resource
        model.action = permission.action
        model.description = permission.description
        await self._db.flush()

        if old_key != permission.key:
            await self._rename_permission_policies(old_key, permission.key)

        return self._permission_from_model(model)

    async def delete_permission(self, permission_id: UUID) -> None:
        permission = await self.get_permission(permission_id)
        if permission is None:
            return

        await self._db.execute(
            delete(RolePermissionModel).where(
                RolePermissionModel.permission_id == permission_id
            )
        )
        await self._db.execute(
            delete(PermissionModel).where(PermissionModel.id == permission_id)
        )
        await self._db.execute(
            delete(CasbinRuleModel).where(
                CasbinRuleModel.ptype == "p",
                CasbinRuleModel.v1 == permission.key,
            )
        )
        await self._db.flush()

    async def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        role = await self.get_role(role_id)
        permission = await self.get_permission(permission_id)
        if role is None:
            raise ValueError("Role does not exist")
        if permission is None:
            raise ValueError("Permission does not exist")

        existing = await self._db.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self._db.add(
                RolePermissionModel(role_id=role_id, permission_id=permission_id)
            )
            await self._db.flush()

        await self.add_policy("p", role.name, permission.key)

    async def list_role_permissions(self) -> list[tuple[str, str]]:
        result = await self._db.execute(
            select(RoleModel.name, PermissionModel.key)
            .join(RolePermissionModel, RolePermissionModel.role_id == RoleModel.id)
            .join(
                PermissionModel, PermissionModel.id == RolePermissionModel.permission_id
            )
        )
        return [
            (role_name, permission_key) for role_name, permission_key in result.all()
        ]

    async def remove_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        role = await self.get_role(role_id)
        permission = await self.get_permission(permission_id)
        if role is None or permission is None:
            return

        await self._db.execute(
            delete(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission_id,
            )
        )
        await self.remove_policy("p", role.name, permission.key)

    def _to_policy_line(self, rule: CasbinRuleModel) -> str:
        values = [rule.v0, rule.v1, rule.v2, rule.v3, rule.v4, rule.v5]
        populated = [value for value in values if value is not None]
        return ", ".join([rule.ptype, *populated])

    def _to_policy_tuple(self, rule: CasbinRuleModel) -> tuple[str, ...]:
        values = [rule.v0, rule.v1, rule.v2, rule.v3, rule.v4, rule.v5]
        populated = [value for value in values if value is not None]
        return (rule.ptype, *populated)

    async def _get_or_create_resource(
        self, resource_key: str
    ) -> AuthorizationResourceModel:
        result = await self._db.execute(
            select(AuthorizationResourceModel).where(
                AuthorizationResourceModel.key == resource_key,
            )
        )
        model = result.scalar_one_or_none()
        if model is not None:
            return model

        model = AuthorizationResourceModel(
            key=resource_key,
            name=resource_key.replace("_", " ").title(),
            description=f"{resource_key} resources",
        )
        self._db.add(model)
        await self._db.flush()
        return model

    def _value_at(self, values: tuple[str, ...], index: int) -> str | None:
        if index >= len(values):
            return None
        return values[index]

    async def _get_role_by_name(self, role: str) -> RoleModel | None:
        result = await self._db.execute(select(RoleModel).where(RoleModel.name == role))
        return result.scalar_one_or_none()

    async def _rename_role_policies(self, old_name: str, new_name: str) -> None:
        policy_result = await self._db.execute(
            select(CasbinRuleModel).where(
                CasbinRuleModel.ptype == "p",
                CasbinRuleModel.v0 == old_name,
            )
        )
        for rule in policy_result.scalars().all():
            rule.v0 = new_name

        grouping_result = await self._db.execute(
            select(CasbinRuleModel).where(
                CasbinRuleModel.ptype == "g",
                CasbinRuleModel.v1 == old_name,
            )
        )
        for rule in grouping_result.scalars().all():
            rule.v1 = new_name

        await self._db.flush()

    async def _rename_permission_policies(self, old_key: str, new_key: str) -> None:
        result = await self._db.execute(
            select(CasbinRuleModel).where(
                CasbinRuleModel.ptype == "p",
                CasbinRuleModel.v1 == old_key,
            )
        )
        for rule in result.scalars().all():
            rule.v1 = new_key
        await self._db.flush()

    def _role_from_model(self, model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

    def _resource_from_model(
        self,
        model: AuthorizationResourceModel,
    ) -> AuthorizationResource:
        return AuthorizationResource(
            id=model.id,
            key=model.key,
            name=model.name,
            description=model.description,
        )

    def _permission_from_model(self, model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            key=model.key,
            resource=model.resource,
            action=model.action,
            description=model.description,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

    def _apply_cursor_pagination(
        self,
        query,
        model,
        cursor_created_at: datetime | None,
        cursor_id: UUID | None,
        direction: CursorDirection,
    ):
        if cursor_created_at and cursor_id:
            if direction == CursorDirection.DIRECTION_NEXT:
                query = query.where(
                    or_(
                        model.created_at < cursor_created_at,
                        and_(
                            model.created_at == cursor_created_at,
                            model.id < cursor_id,
                        ),
                    )
                )
                return query.order_by(model.created_at.desc(), model.id.desc())

            query = query.where(
                or_(
                    model.created_at > cursor_created_at,
                    and_(
                        model.created_at == cursor_created_at,
                        model.id > cursor_id,
                    ),
                )
            )
            return query.order_by(model.created_at.asc(), model.id.asc())

        return query.order_by(model.created_at.desc(), model.id.desc())
