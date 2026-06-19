"""add authorization resources

Revision ID: d9a7c3f2b6e1
Revises: c7a1b9e5d4f2
Create Date: 2026-06-19 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "d9a7c3f2b6e1"
down_revision: Union[str, Sequence[str], None] = "c7a1b9e5d4f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "authorization_resources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_authorization_resources_key"),
        "authorization_resources",
        ["key"],
        unique=True,
    )

    with op.batch_alter_table("permissions") as batch_op:
        batch_op.add_column(sa.Column("resource_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            op.f("ix_permissions_resource_id"),
            ["resource_id"],
            unique=False,
        )

    bind = op.get_bind()
    resources = [
        row[0]
        for row in bind.execute(
            sa.text("select distinct resource from permissions where resource is not null")
        )
    ]

    resource_ids = {}
    for resource in resources:
        resource_id = uuid4()
        resource_ids[resource] = resource_id
        bind.execute(
            sa.text(
                """
                insert into authorization_resources
                    (id, key, name, description)
                values
                    (:id, :key, :name, :description)
                """
            ),
            {
                "id": resource_id,
                "key": resource,
                "name": resource.replace("_", " ").title(),
                "description": f"{resource} resources",
            },
        )

    for resource, resource_id in resource_ids.items():
        bind.execute(
            sa.text(
                """
                update permissions
                set resource_id = :resource_id
                where resource = :resource
                """
            ),
            {"resource_id": resource_id, "resource": resource},
        )

    with op.batch_alter_table("permissions") as batch_op:
        batch_op.create_foreign_key(
            "fk_permissions_resource_id_authorization_resources",
            "authorization_resources",
            ["resource_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("permissions") as batch_op:
        batch_op.drop_constraint(
            "fk_permissions_resource_id_authorization_resources",
            type_="foreignkey",
        )
        batch_op.drop_index(op.f("ix_permissions_resource_id"))
        batch_op.drop_column("resource_id")

    op.drop_index(
        op.f("ix_authorization_resources_key"),
        table_name="authorization_resources",
    )
    op.drop_table("authorization_resources")
