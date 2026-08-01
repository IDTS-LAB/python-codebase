from datetime import datetime

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.authorization import AuthorizationResource, Permission, Role
from src.modules.authorization.infrastructure.models.casbin_rule_model import (
    CasbinRuleModel,
)
from src.modules.authorization.infrastructure.models.permission_model import (
    PermissionModel,
)
from src.modules.authorization.infrastructure.models.resource_model import (
    AuthorizationResourceModel,
)
from src.modules.authorization.infrastructure.models.role_model import RoleModel
from src.modules.authorization.infrastructure.models.role_permission_model import (
    RolePermissionModel,
)
from src.modules.authorization.infrastructure.models.user_has_role_model import (
    UserHasRoleModel,
)
from src.shared.utils.cursor import CursorDirection


class SQLAlchemyCasbinPolicyRepository:
    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        self._db = db
        self._tenant_id = tenant_id

    async def _filter_by_tenant(self, stmt):
        if self._tenant_id:
            return stmt.where(CasbinRuleModel.tenant_id == self._tenant_id)
        return stmt

    async def _filter_model_by_tenant(self, model, stmt):
        if self._tenant_id:
            return stmt.where(model.tenant_id == self._tenant_id)
        return stmt

    async def load_policy_lines(self) -> list[str]:
        stmt = await self._filter_by_tenant(select(CasbinRuleModel))
        result = await self._db.execute(stmt)
        rules = result.scalars().all()
        return [self._to_policy_line(rule) for rule in rules]

    async def list_policies(self) -> list[tuple[str, ...]]:
        stmt = await self._filter_by_tenant(select(CasbinRuleModel))
        result = await self._db.execute(stmt)
        return [self._to_policy_tuple(rule) for rule in result.scalars().all()]

    async def add_policy(self, ptype: str, *values: str) -> None:
        stmt = select(CasbinRuleModel).where(
            CasbinRuleModel.ptype == ptype,
            CasbinRuleModel.v0 == self._value_at(values, 0),
            CasbinRuleModel.v1 == self._value_at(values, 1),
            CasbinRuleModel.v2 == self._value_at(values, 2),
            CasbinRuleModel.v3 == self._value_at(values, 3),
            CasbinRuleModel.v4 == self._value_at(values, 4),
            CasbinRuleModel.v5 == self._value_at(values, 5),
        )
        stmt = await self._filter_by_tenant(stmt)
        existing = await self._db.execute(stmt)
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
                tenant_id=self._tenant_id,
            )
        )
        await self._db.flush()

    async def remove_policy(self, ptype: str, *values: str) -> None:
        stmt = delete(CasbinRuleModel).where(
            CasbinRuleModel.ptype == ptype,
            CasbinRuleModel.v0 == self._value_at(values, 0),
            CasbinRuleModel.v1 == self._value_at(values, 1),
            CasbinRuleModel.v2 == self._value_at(values, 2),
            CasbinRuleModel.v3 == self._value_at(values, 3),
            CasbinRuleModel.v4 == self._value_at(values, 4),
            CasbinRuleModel.v5 == self._value_at(values, 5),
        )
        stmt = await self._filter_by_tenant(stmt)
        await self._db.execute(stmt)
        await self._db.flush()

    async def assign_role(self, subject: str, role: str) -> None:
        role_model = await self._get_role_by_name(role)
        if role_model is None:
            raise ValueError(f"Role does not exist: {role}")

        user_id = int(subject)
        stmt = select(UserHasRoleModel).where(
            UserHasRoleModel.user_id == user_id,
            UserHasRoleModel.role_id == role_model.id,
        )
        stmt = await self._filter_model_by_tenant(UserHasRoleModel, stmt)
        existing_assignment = await self._db.execute(stmt)
        if existing_assignment.scalar_one_or_none() is None:
            self._db.add(
                UserHasRoleModel(
                    user_id=user_id,
                    role_id=role_model.id,
                    tenant_id=self._tenant_id,
                )
            )
            await self._db.flush()

        await self.add_policy("g", subject, role)

    async def get_roles_for_subject(self, subject: str) -> list[str]:
        user_id = int(subject)
        stmt = (
            select(RoleModel.name)
            .join(UserHasRoleModel, UserHasRoleModel.role_id == RoleModel.id)
            .where(UserHasRoleModel.user_id == user_id)
        )
        if self._tenant_id:
            stmt = stmt.where(UserHasRoleModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def create_resource(
        self,
        resource: AuthorizationResource,
    ) -> AuthorizationResource:
        model = AuthorizationResourceModel(
            key=resource.key,
            name=resource.name,
            description=resource.description,
            tenant_id=self._tenant_id,
        )
        self._db.add(model)
        await self._db.flush()
        return self._resource_from_model(model)

    async def list_resources(self) -> list[AuthorizationResource]:
        stmt = select(AuthorizationResourceModel)
        if self._tenant_id:
            stmt = stmt.where(AuthorizationResourceModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return [self._resource_from_model(model) for model in result.scalars().all()]

    async def create_role(self, role: Role) -> Role:
        model = RoleModel(
            name=role.name,
            description=role.description,
            tenant_id=self._tenant_id,
        )
        self._db.add(model)
        await self._db.flush()
        return self._role_from_model(model)

    async def get_role(self, role_id: int) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.id == role_id)
        if self._tenant_id:
            stmt = stmt.where(RoleModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._role_from_model(model)

    async def list_roles(self) -> list[Role]:
        stmt = select(RoleModel)
        if self._tenant_id:
            stmt = stmt.where(RoleModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return [self._role_from_model(model) for model in result.scalars().all()]

    async def list_roles_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: int | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Role], bool]:
        query = select(RoleModel)
        if self._tenant_id:
            query = query.where(RoleModel.tenant_id == self._tenant_id)
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
        stmt = select(RoleModel).where(RoleModel.id == role.id)
        if self._tenant_id:
            stmt = stmt.where(RoleModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
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

    async def _filter_casbin_stmt(self, stmt):
        if self._tenant_id:
            return stmt.where(CasbinRuleModel.tenant_id == self._tenant_id)
        return stmt

    async def delete_role(self, role_id: int) -> None:
        role = await self.get_role(role_id)
        if role is None:
            return

        rp_stmt = delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
        if self._tenant_id:
            rp_stmt = rp_stmt.where(RolePermissionModel.tenant_id == self._tenant_id)

        uhr_stmt = delete(UserHasRoleModel).where(UserHasRoleModel.role_id == role_id)
        if self._tenant_id:
            uhr_stmt = uhr_stmt.where(UserHasRoleModel.tenant_id == self._tenant_id)

        await self._db.execute(rp_stmt)
        await self._db.execute(uhr_stmt)
        await self._db.execute(delete(RoleModel).where(RoleModel.id == role_id))

        cr_stmt = delete(CasbinRuleModel).where(
            ((CasbinRuleModel.ptype == "p") & (CasbinRuleModel.v0 == role.name))
            | ((CasbinRuleModel.ptype == "g") & (CasbinRuleModel.v1 == role.name))
        )
        cr_stmt = await self._filter_casbin_stmt(cr_stmt)
        await self._db.execute(cr_stmt)
        await self._db.flush()

    async def create_permission(self, permission: Permission) -> Permission:
        resource = await self._get_or_create_resource(permission.resource)
        model = PermissionModel(
            key=permission.key,
            resource_id=resource.id,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
            tenant_id=self._tenant_id,
        )
        self._db.add(model)
        await self._db.flush()
        return self._permission_from_model(model)

    async def get_permission(self, permission_id: int) -> Permission | None:
        stmt = select(PermissionModel).where(PermissionModel.id == permission_id)
        if self._tenant_id:
            stmt = stmt.where(PermissionModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._permission_from_model(model)

    async def list_permissions(self) -> list[Permission]:
        stmt = select(PermissionModel)
        if self._tenant_id:
            stmt = stmt.where(PermissionModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return [self._permission_from_model(model) for model in result.scalars().all()]

    async def list_permissions_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: int | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Permission], bool]:
        query = select(PermissionModel)
        if self._tenant_id:
            query = query.where(PermissionModel.tenant_id == self._tenant_id)
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
        stmt = select(PermissionModel).where(PermissionModel.id == permission.id)
        if self._tenant_id:
            stmt = stmt.where(PermissionModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
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

    async def delete_permission(self, permission_id: int) -> None:
        permission = await self.get_permission(permission_id)
        if permission is None:
            return

        rp_stmt = delete(RolePermissionModel).where(
            RolePermissionModel.permission_id == permission_id
        )
        if self._tenant_id:
            rp_stmt = rp_stmt.where(RolePermissionModel.tenant_id == self._tenant_id)

        await self._db.execute(rp_stmt)
        await self._db.execute(
            delete(PermissionModel).where(PermissionModel.id == permission_id)
        )

        cr_stmt = delete(CasbinRuleModel).where(
            CasbinRuleModel.ptype == "p",
            CasbinRuleModel.v1 == permission.key,
        )
        cr_stmt = await self._filter_casbin_stmt(cr_stmt)
        await self._db.execute(cr_stmt)
        await self._db.flush()

    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:
        role = await self.get_role(role_id)
        permission = await self.get_permission(permission_id)
        if role is None:
            raise ValueError("Role does not exist")
        if permission is None:
            raise ValueError("Permission does not exist")

        stmt = select(RolePermissionModel).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        )
        if self._tenant_id:
            stmt = stmt.where(RolePermissionModel.tenant_id == self._tenant_id)
        existing = await self._db.execute(stmt)
        if existing.scalar_one_or_none() is None:
            self._db.add(
                RolePermissionModel(
                    role_id=role_id,
                    permission_id=permission_id,
                    tenant_id=self._tenant_id,
                )
            )
            await self._db.flush()

        await self.add_policy("p", role.name, permission.key)

    async def list_role_permissions(self) -> list[tuple[str, str]]:
        stmt = (
            select(RoleModel.name, PermissionModel.key)
            .join(RolePermissionModel, RolePermissionModel.role_id == RoleModel.id)
            .join(
                PermissionModel, PermissionModel.id == RolePermissionModel.permission_id
            )
        )
        if self._tenant_id:
            stmt = stmt.where(RolePermissionModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return [
            (role_name, permission_key) for role_name, permission_key in result.all()
        ]

    async def remove_permission_from_role(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:
        role = await self.get_role(role_id)
        permission = await self.get_permission(permission_id)
        if role is None or permission is None:
            return

        rp_stmt = delete(RolePermissionModel).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        )
        if self._tenant_id:
            rp_stmt = rp_stmt.where(RolePermissionModel.tenant_id == self._tenant_id)
        await self._db.execute(rp_stmt)
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
        stmt = select(AuthorizationResourceModel).where(
            AuthorizationResourceModel.key == resource_key,
        )
        if self._tenant_id:
            stmt = stmt.where(AuthorizationResourceModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            return model

        model = AuthorizationResourceModel(
            key=resource_key,
            name=resource_key.replace("_", " ").title(),
            description=f"{resource_key} resources",
            tenant_id=self._tenant_id,
        )
        self._db.add(model)
        await self._db.flush()
        return model

    def _value_at(self, values: tuple[str, ...], index: int) -> str | None:
        if index >= len(values):
            return None
        return values[index]

    async def _get_role_by_name(self, role: str) -> RoleModel | None:
        stmt = select(RoleModel).where(RoleModel.name == role)
        if self._tenant_id:
            stmt = stmt.where(RoleModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _rename_role_policies(self, old_name: str, new_name: str) -> None:
        p_stmt = select(CasbinRuleModel).where(
            CasbinRuleModel.ptype == "p",
            CasbinRuleModel.v0 == old_name,
        )
        p_stmt = await self._filter_casbin_stmt(p_stmt)
        policy_result = await self._db.execute(p_stmt)
        for rule in policy_result.scalars().all():
            rule.v0 = new_name

        g_stmt = select(CasbinRuleModel).where(
            CasbinRuleModel.ptype == "g",
            CasbinRuleModel.v1 == old_name,
        )
        g_stmt = await self._filter_casbin_stmt(g_stmt)
        grouping_result = await self._db.execute(g_stmt)
        for rule in grouping_result.scalars().all():
            rule.v1 = new_name

        await self._db.flush()

    async def _rename_permission_policies(self, old_key: str, new_key: str) -> None:
        stmt = select(CasbinRuleModel).where(
            CasbinRuleModel.ptype == "p",
            CasbinRuleModel.v1 == old_key,
        )
        stmt = await self._filter_casbin_stmt(stmt)
        result = await self._db.execute(stmt)
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
        cursor_id: int | None,
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
