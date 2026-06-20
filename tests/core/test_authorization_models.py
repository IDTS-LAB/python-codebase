from src.core.authorization.infrastructure.models.casbin_rule_model import (
    CasbinRuleModel,
)
from src.core.authorization.infrastructure.models.permission_model import (
    PermissionModel,
)
from src.core.authorization.infrastructure.models.resource_model import (
    AuthorizationResourceModel,
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
from src.modules.todo.infrastructure.models.todo_model import TodoModel
from src.modules.user.infrastructure.models.refresh_token_model import RefreshTokenModel
from src.shared.database.model import Base


def test_authorization_tables_are_registered_in_metadata():
    assert AuthorizationResourceModel.__tablename__ == "authorization_resources"
    assert RoleModel.__tablename__ == "roles"
    assert PermissionModel.__tablename__ == "permissions"
    assert RolePermissionModel.__tablename__ == "role_permissions"
    assert UserHasRoleModel.__tablename__ == "user_has_roles"
    assert CasbinRuleModel.__tablename__ == "casbin_rules"


def test_authorization_models_have_expected_columns():
    assert {"key", "name", "description"}.issubset(
        AuthorizationResourceModel.__table__.columns.keys()
    )
    assert {"name", "description"}.issubset(RoleModel.__table__.columns.keys())
    assert "descpription" not in RoleModel.__table__.columns.keys()
    assert {"key", "resource_id", "resource", "action", "description"}.issubset(
        PermissionModel.__table__.columns.keys()
    )
    assert "descpription" not in PermissionModel.__table__.columns.keys()
    assert {"role_id", "permission_id"}.issubset(
        RolePermissionModel.__table__.columns.keys()
    )
    assert {"user_id", "role_id"}.issubset(UserHasRoleModel.__table__.columns.keys())


def test_database_models_do_not_declare_foreign_keys():
    # Import models that live outside authorization so they are registered in metadata.
    assert TodoModel.__tablename__ == "todos"
    assert RefreshTokenModel.__tablename__ == "refresh_tokens"

    foreign_keys = [
        f"{table.name}.{column.name}->{foreign_key.target_fullname}"
        for table in Base.metadata.tables.values()
        for column in table.columns
        for foreign_key in column.foreign_keys
    ]

    assert foreign_keys == []
