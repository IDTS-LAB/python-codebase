from src.core.authorization.infrastructure.models.casbin_rule_model import (
    CasbinRuleModel,
)
from src.core.authorization.infrastructure.models.permission_model import (
    PermissionModel,
)
from src.core.authorization.infrastructure.models.role_model import (
    RoleModel,
)
from src.core.authorization.infrastructure.models.role_permission_model import (
    RolePermissionModel,
)
from src.core.authorization.infrastructure.models.user_has_role_model import (
    UserHasRoleModel,
)


def test_authorization_tables_are_registered_in_metadata():
    assert RoleModel.__tablename__ == "roles"
    assert PermissionModel.__tablename__ == "permissions"
    assert RolePermissionModel.__tablename__ == "role_permissions"
    assert UserHasRoleModel.__tablename__ == "user_has_roles"
    assert CasbinRuleModel.__tablename__ == "casbin_rules"


def test_authorization_models_have_expected_columns():
    assert {"name"}.issubset(RoleModel.__table__.columns.keys())
    assert {"key", "resource", "action"}.issubset(
        PermissionModel.__table__.columns.keys()
    )
    assert {"role_id", "permission_id"}.issubset(
        RolePermissionModel.__table__.columns.keys()
    )
    assert {"user_id", "role_id"}.issubset(UserHasRoleModel.__table__.columns.keys())
