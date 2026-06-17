from src.core.authorization.domain.service import AuthorizationService
from src.core.authorization.infrastructure.repositories.casbin_policy_repository import (
    SQLAlchemyCasbinPolicyRepository,
)
from src.core.authorization.permissions import permission_key

CASBIN_MODEL_TEXT = """
[request_definition]
r = sub, perm

[policy_definition]
p = sub, perm

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && (p.perm == "*" || r.perm == p.perm)
"""


class CasbinAuthorizationService(AuthorizationService):
    def __init__(self, policy_repository: SQLAlchemyCasbinPolicyRepository):
        self._policy_repository = policy_repository

    async def can(self, subject: str, resource: str, action: str) -> bool:
        enforcer = await self._build_enforcer()
        return bool(enforcer.enforce(subject, permission_key(resource, action)))

    async def assign_role(self, subject: str, role: str) -> None:
        await self._policy_repository.assign_role(subject, role)

    async def get_roles_for_subject(self, subject: str) -> list[str]:
        return await self._policy_repository.get_roles_for_subject(subject)

    async def _build_enforcer(self):
        try:
            import casbin
            from casbin import persist
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Casbin is not installed. Run `poetry install` to install project dependencies."
            ) from exc

        model = casbin.Model()
        model.load_model_from_text(CASBIN_MODEL_TEXT)
        enforcer = casbin.Enforcer(model)
        for policy_line in await self._policy_repository.load_policy_lines():
            persist.load_policy_line(policy_line, enforcer.model)
        enforcer.build_role_links()
        return enforcer
