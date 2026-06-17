"""add casbin policy table

Revision ID: d4bb4d2b3f0a
Revises: ab661f0b6986
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision: str = "d4bb4d2b3f0a"
down_revision: Union[str, Sequence[str], None] = "ab661f0b6986"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )
    op.create_index(op.f("ix_permissions_action"), "permissions", ["action"])
    op.create_index(op.f("ix_permissions_key"), "permissions", ["key"], unique=True)
    op.create_index(op.f("ix_permissions_resource"), "permissions", ["resource"])

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_id_permission_id",
        ),
    )
    op.create_index(
        op.f("ix_role_permissions_permission_id"),
        "role_permissions",
        ["permission_id"],
    )
    op.create_index(
        op.f("ix_role_permissions_role_id"),
        "role_permissions",
        ["role_id"],
    )

    op.create_table(
        "user_has_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_has_roles_user_id_role_id"),
    )
    op.create_index(op.f("ix_user_has_roles_role_id"), "user_has_roles", ["role_id"])
    op.create_index(op.f("ix_user_has_roles_user_id"), "user_has_roles", ["user_id"])

    op.create_table(
        "casbin_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ptype", sa.String(length=16), nullable=False),
        sa.Column("v0", sa.String(length=255), nullable=True),
        sa.Column("v1", sa.String(length=255), nullable=True),
        sa.Column("v2", sa.String(length=255), nullable=True),
        sa.Column("v3", sa.String(length=255), nullable=True),
        sa.Column("v4", sa.String(length=255), nullable=True),
        sa.Column("v5", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_casbin_rules_ptype"), "casbin_rules", ["ptype"])
    op.create_index(op.f("ix_casbin_rules_v0"), "casbin_rules", ["v0"])
    op.create_index(op.f("ix_casbin_rules_v1"), "casbin_rules", ["v1"])
    op.create_index(op.f("ix_casbin_rules_v2"), "casbin_rules", ["v2"])

    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid),
        sa.column("key", sa.String),
        sa.column("resource", sa.String),
        sa.column("action", sa.String),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("id", sa.Uuid),
        sa.column("role_id", sa.Uuid),
        sa.column("permission_id", sa.Uuid),
    )
    casbin_rules = sa.table(
        "casbin_rules",
        sa.column("id", sa.Uuid),
        sa.column("ptype", sa.String),
        sa.column("v0", sa.String),
        sa.column("v1", sa.String),
        sa.column("v2", sa.String),
    )

    admin_role_id = UUID("10000000-0000-0000-0000-000000000001")
    user_role_id = UUID("10000000-0000-0000-0000-000000000002")
    admin_permission_id = UUID("20000000-0000-0000-0000-000000000001")
    todo_create_permission_id = UUID("20000000-0000-0000-0000-000000000002")
    todo_read_permission_id = UUID("20000000-0000-0000-0000-000000000003")
    todo_update_permission_id = UUID("20000000-0000-0000-0000-000000000004")
    todo_delete_permission_id = UUID("20000000-0000-0000-0000-000000000005")
    user_me_permission_id = UUID("20000000-0000-0000-0000-000000000006")

    op.bulk_insert(
        roles,
        [
            {"id": admin_role_id, "name": "admin"},
            {"id": user_role_id, "name": "user"},
        ],
    )
    op.bulk_insert(
        permissions,
        [
            {
                "id": admin_permission_id,
                "key": "*",
                "resource": "*",
                "action": "*",
            },
            {
                "id": todo_create_permission_id,
                "key": "todo:create",
                "resource": "todo",
                "action": "create",
            },
            {
                "id": todo_read_permission_id,
                "key": "todo:read",
                "resource": "todo",
                "action": "read",
            },
            {
                "id": todo_update_permission_id,
                "key": "todo:update",
                "resource": "todo",
                "action": "update",
            },
            {
                "id": todo_delete_permission_id,
                "key": "todo:delete",
                "resource": "todo",
                "action": "delete",
            },
            {
                "id": user_me_permission_id,
                "key": "user:me",
                "resource": "user",
                "action": "me",
            },
        ],
    )
    op.bulk_insert(
        role_permissions,
        [
            {
                "id": UUID("30000000-0000-0000-0000-000000000001"),
                "role_id": admin_role_id,
                "permission_id": admin_permission_id,
            },
            {
                "id": UUID("30000000-0000-0000-0000-000000000002"),
                "role_id": user_role_id,
                "permission_id": todo_create_permission_id,
            },
            {
                "id": UUID("30000000-0000-0000-0000-000000000003"),
                "role_id": user_role_id,
                "permission_id": todo_read_permission_id,
            },
            {
                "id": UUID("30000000-0000-0000-0000-000000000004"),
                "role_id": user_role_id,
                "permission_id": todo_update_permission_id,
            },
            {
                "id": UUID("30000000-0000-0000-0000-000000000005"),
                "role_id": user_role_id,
                "permission_id": todo_delete_permission_id,
            },
            {
                "id": UUID("30000000-0000-0000-0000-000000000006"),
                "role_id": user_role_id,
                "permission_id": user_me_permission_id,
            },
        ],
    )
    op.bulk_insert(
        casbin_rules,
        [
            {
                "id": UUID("00000000-0000-0000-0000-000000000001"),
                "ptype": "p",
                "v0": "admin",
                "v1": "*",
            },
            {
                "id": UUID("00000000-0000-0000-0000-000000000002"),
                "ptype": "p",
                "v0": "user",
                "v1": "todo:create",
            },
            {
                "id": UUID("00000000-0000-0000-0000-000000000003"),
                "ptype": "p",
                "v0": "user",
                "v1": "todo:read",
            },
            {
                "id": UUID("00000000-0000-0000-0000-000000000004"),
                "ptype": "p",
                "v0": "user",
                "v1": "todo:update",
            },
            {
                "id": UUID("00000000-0000-0000-0000-000000000005"),
                "ptype": "p",
                "v0": "user",
                "v1": "todo:delete",
            },
            {
                "id": UUID("00000000-0000-0000-0000-000000000006"),
                "ptype": "p",
                "v0": "user",
                "v1": "user:me",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_casbin_rules_v2"), table_name="casbin_rules")
    op.drop_index(op.f("ix_casbin_rules_v1"), table_name="casbin_rules")
    op.drop_index(op.f("ix_casbin_rules_v0"), table_name="casbin_rules")
    op.drop_index(op.f("ix_casbin_rules_ptype"), table_name="casbin_rules")
    op.drop_table("casbin_rules")
    op.drop_index(op.f("ix_user_has_roles_user_id"), table_name="user_has_roles")
    op.drop_index(op.f("ix_user_has_roles_role_id"), table_name="user_has_roles")
    op.drop_table("user_has_roles")
    op.drop_index(op.f("ix_role_permissions_role_id"), table_name="role_permissions")
    op.drop_index(
        op.f("ix_role_permissions_permission_id"),
        table_name="role_permissions",
    )
    op.drop_table("role_permissions")
    op.drop_index(op.f("ix_permissions_resource"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_key"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_action"), table_name="permissions")
    op.drop_table("permissions")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
