from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization.infrastructure.models.casbin_rule_model import (
    CasbinRuleModel,
)
from src.core.authorization.infrastructure.models.role_model import RoleModel
from src.core.authorization.infrastructure.models.user_has_role_model import (
    UserHasRoleModel,
)


class SQLAlchemyCasbinPolicyRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def load_policy_lines(self) -> list[str]:
        result = await self._db.execute(select(CasbinRuleModel))
        rules = result.scalars().all()
        return [self._to_policy_line(rule) for rule in rules]

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

    def _to_policy_line(self, rule: CasbinRuleModel) -> str:
        values = [rule.v0, rule.v1, rule.v2, rule.v3, rule.v4, rule.v5]
        populated = [value for value in values if value is not None]
        return ", ".join([rule.ptype, *populated])

    def _value_at(self, values: tuple[str, ...], index: int) -> str | None:
        if index >= len(values):
            return None
        return values[index]

    async def _get_role_by_name(self, role: str) -> RoleModel | None:
        result = await self._db.execute(select(RoleModel).where(RoleModel.name == role))
        return result.scalar_one_or_none()
