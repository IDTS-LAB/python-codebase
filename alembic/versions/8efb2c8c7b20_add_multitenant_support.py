"""add multitenant support

Revision ID: 8efb2c8c7b20
Revises: b0de87aaeb97
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8efb2c8c7b20'
down_revision: Union[str, Sequence[str], None] = 'b0de87aaeb97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('domain'),
    )
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)

    # Insert default tenant
    op.execute(
        sa.text(
            "INSERT INTO tenants (id, name, slug) VALUES ("
            "'00000000-0000-0000-0000-000000000001', "
            "'Default Tenant', 'default')"
        )
    )
    default_tenant_id = '00000000-0000-0000-0000-000000000001'

    # Add tenant_id column helper
    def add_tenant_id_column(table: str) -> None:
        op.add_column(table, sa.Column('tenant_id', sa.UUID(), nullable=True))
        op.execute(
            sa.text(
                f"UPDATE {table} SET tenant_id = '{default_tenant_id}'"
            )
        )
        op.alter_column(table, 'tenant_id', nullable=False)
        op.create_foreign_key(
            f'fk_{table}_tenant_id',
            table, 'tenants',
            ['tenant_id'], ['id'],
        )

    # Add tenant_id to all existing tables
    tables = [
        'users', 'user_profiles', 'user_security', 'user_settings',
        'user_contacts', 'user_addresses', 'user_verifications',
        'user_sessions', 'todos',
        'authorization_resources', 'permissions', 'roles',
        'user_has_roles', 'role_permissions', 'casbin_rules',
        'audit_logs', 'error_traces', 'login_attempts',
    ]

    for table in tables:
        add_tenant_id_column(table)


def downgrade() -> None:
    # Remove tenant_id from all tables
    tables = [
        'users', 'user_profiles', 'user_security', 'user_settings',
        'user_contacts', 'user_addresses', 'user_verifications',
        'user_sessions', 'todos',
        'authorization_resources', 'permissions', 'roles',
        'user_has_roles', 'role_permissions', 'casbin_rules',
        'audit_logs', 'error_traces', 'login_attempts',
    ]

    for table in tables:
        op.drop_constraint(
            f'fk_{table}_tenant_id', table, type_='foreignkey'
        )
        op.drop_column(table, 'tenant_id')

    # Drop tenants table
    op.drop_index(op.f('ix_tenants_slug'), table_name='tenants')
    op.drop_table('tenants')
