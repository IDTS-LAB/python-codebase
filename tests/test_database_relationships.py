import pytest
from sqlalchemy import Uuid
from sqlalchemy.orm import configure_mappers

import src.modules.authorization.infrastructure.models.permission_model  # noqa: F401
import src.modules.authorization.infrastructure.models.resource_model  # noqa: F401
import src.modules.authorization.infrastructure.models.role_model  # noqa: F401
import src.modules.authorization.infrastructure.models.role_permission_model  # noqa: F401
import src.modules.authorization.infrastructure.models.user_has_role_model  # noqa: F401
import src.modules.todo.infrastructure.models.todo_model  # noqa: F401
import src.modules.user.infrastructure.models  # noqa: F401
from src.shared.database.model import Base


FOREIGN_KEYS = (
    ("permissions", "resource_id", "authorization_resources.id"),
    ("role_permissions", "role_id", "roles.id"),
    ("role_permissions", "permission_id", "permissions.id"),
    ("todos", "user_id", "users.id"),
    ("user_has_roles", "user_id", "users.id"),
    ("user_has_roles", "role_id", "roles.id"),
    ("user_profiles", "user_id", "users.id"),
    ("user_security", "user_id", "users.id"),
    ("user_settings", "user_id", "users.id"),
    ("user_contacts", "user_id", "users.id"),
    ("user_addresses", "user_id", "users.id"),
    ("user_verifications", "user_id", "users.id"),
    ("user_sessions", "user_id", "users.id"),
)

NORMALIZED_USER_TABLES = (
    "user_profiles",
    "user_security",
    "user_settings",
    "user_contacts",
    "user_addresses",
    "user_verifications",
    "user_sessions",
)


def test_all_mappers_configure_with_declared_relationship_joins():
    configure_mappers()


@pytest.mark.parametrize(("table", "column", "target"), FOREIGN_KEYS)
def test_relationship_column_declares_expected_foreign_key(table, column, target):
    foreign_keys = Base.metadata.tables[table].c[column].foreign_keys

    assert {foreign_key.target_fullname for foreign_key in foreign_keys} == {target}


@pytest.mark.parametrize("table", NORMALIZED_USER_TABLES)
def test_normalized_user_identifier_uses_uuid(table):
    assert isinstance(Base.metadata.tables[table].c.user_id.type, Uuid)
