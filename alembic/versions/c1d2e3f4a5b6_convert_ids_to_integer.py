"""convert all primary and foreign keys from UUID to integer

Revision ID: c1d2e3f4a5b6
Revises: 8efb2c8c7b20
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = '8efb2c8c7b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Parent tables (own a UUID PK), ordered so parents are converted before
# their children are remapped. FK children are converted right after their
# parent in the same step.
TABLES = [
    'tenants',
    'users',
    'user_profiles',
    'user_settings',
    'user_security',
    'user_contacts',
    'user_addresses',
    'user_verifications',
    'user_sessions',
    'todos',
    'authorization_resources',
    'permissions',
    'roles',
    'role_permissions',
    'user_has_roles',
    'casbin_rules',
    'audit_logs',
    'error_traces',
    'login_attempts',
]

# child table -> (fk_column, parent_table)
FK_MAP = {
    'users': [('tenant_id', 'tenants')],
    'user_profiles': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'user_settings': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'user_security': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'user_contacts': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'user_addresses': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'user_verifications': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'user_sessions': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'todos': [('user_id', 'users'), ('tenant_id', 'tenants')],
    'authorization_resources': [('tenant_id', 'tenants')],
    'permissions': [('resource_id', 'authorization_resources'), ('tenant_id', 'tenants')],
    'roles': [('tenant_id', 'tenants')],
    'role_permissions': [('role_id', 'roles'), ('permission_id', 'permissions'), ('tenant_id', 'tenants')],
    'user_has_roles': [('user_id', 'users'), ('role_id', 'roles'), ('tenant_id', 'tenants')],
    'casbin_rules': [('tenant_id', 'tenants')],
    'audit_logs': [('tenant_id', 'tenants')],
    'error_traces': [('tenant_id', 'tenants')],
    'login_attempts': [('tenant_id', 'tenants')],
}

# Shadow table that records the old uuid -> new integer mapping so foreign
# keys can be rewritten and the downgrade can restore the exact original
# uuids (see the "Data-preserving downgrade" note in the task brief).
LEGACY_IDS = '_legacy_ids'

# Shadow table recording indexes and unique constraints on FK columns that
# DROP COLUMN removes, so they can be recreated on the converted columns
# (upgrade) and restored (downgrade) for the earlier migrations' DROP INDEX.
LEGACY_INDEXES = '_legacy_indexes'


def _columns(bind) -> dict[str, list[str]]:
    inspector = sa.inspect(bind)
    return {
        table: [col["name"] for col in inspector.get_columns(table)]
        for table in inspector.get_table_names()
    }


def _fk_constraint_name(bind, table: str, column: str) -> str | None:
    inspector = sa.inspect(bind)
    for fk in inspector.get_foreign_keys(table):
        if column in fk["constrained_columns"]:
            return fk["name"]
    return None


def _fk_name(child: str, column: str) -> str:
    """Constraint names as created by the preceding migrations, so that
    `alembic downgrade` further down the chain can still drop them by
    name: multitenant FKs are named fk_<table>_tenant_id (8efb2c8c7b20),
    the initial schemas' unnamed constraints get PostgreSQL's default
    <table>_<column>_fkey (b0de87aaeb97)."""
    if column == 'tenant_id':
        return f'fk_{child}_tenant_id'
    return f'{child}_{column}_fkey'


def _indexes_on_column(bind, table: str, column: str) -> list[tuple[str, str, bool]]:
    """(name, comma-joined columns, is_unique) of every index or unique
    constraint containing the column (PG implements unique constraints as
    unique indexes)."""
    inspector = sa.inspect(bind)
    out = []
    for idx in inspector.get_indexes(table):
        cols = idx["column_names"] or []
        if column in cols:
            out.append((idx["name"], ",".join(cols), bool(idx.get("unique", False))))
    return out


def _record_indexes(bind, child: str, column: str) -> None:
    """DROP COLUMN removes every index on the column; record them first."""
    indexes = _indexes_on_column(bind, child, column)
    if not indexes:
        return
    op.execute(sa.text(
        f'CREATE TABLE IF NOT EXISTS {LEGACY_INDEXES} '
        f'(table_name TEXT, index_name TEXT, column_names TEXT, is_unique BOOLEAN)'
    ))
    for name, columns, unique in indexes:
        op.execute(sa.text(
            f"INSERT INTO {LEGACY_INDEXES} (table_name, index_name, column_names, is_unique) "
            f"VALUES ('{child}', '{name}', '{columns}', {unique})"
        ))


def _recreate_indexes(bind, child: str) -> None:
    """Recreate the recorded indexes/unique constraints on a table once all
    of their columns have been converted (or restored)."""
    if not sa.inspect(bind).has_table(LEGACY_INDEXES):
        return
    rows = bind.execute(sa.text(
        f'SELECT index_name, column_names, is_unique FROM {LEGACY_INDEXES} '
        f"WHERE table_name = '{child}'"
    )).fetchall()
    for name, columns, unique in dict.fromkeys(rows):
        op.execute(sa.text(
            f"CREATE {'UNIQUE ' if unique else ''}INDEX {name} ON {child} ({columns})"
        ))


def _convert_pk(bind, table: str) -> None:
    """Add _id integer identity column, backfill via row_number over the
    old uuid PK, record the uuid -> int mapping, drop the uuid PK, rename."""
    # skip if already integer
    cols = sa.inspect(bind).get_columns(table)
    id_type = next(c["type"] for c in cols if c["name"] == "id")
    if "UUID" not in str(id_type):
        return

    op.execute(sa.text(f'ALTER TABLE {table} ADD COLUMN _id INTEGER GENERATED BY DEFAULT AS IDENTITY'))
    op.execute(sa.text(
        f'UPDATE {table} SET _id = sub.rn FROM '
        f'(SELECT id, row_number() OVER (ORDER BY id) AS rn FROM {table}) AS sub '
        f'WHERE {table}.id = sub.id'
    ))
    # Record the old uuid -> new integer mapping before the uuid is dropped.
    op.execute(sa.text(
        f'CREATE TABLE IF NOT EXISTS {LEGACY_IDS} '
        f'(table_name TEXT, legacy_uuid UUID, new_id INTEGER)'
    ))
    op.execute(sa.text(
        f'INSERT INTO {LEGACY_IDS} (table_name, legacy_uuid, new_id) '
        f'SELECT \'{table}\', id, _id FROM {table}'
    ))
    # CASCADE: incoming foreign keys from child tables depend on the PK
    # index; they are recreated by _convert_fk once the column is remapped.
    op.execute(sa.text(
        f'ALTER TABLE {table} DROP CONSTRAINT {table}_pkey CASCADE'
    ))
    op.execute(sa.text(f'ALTER TABLE {table} DROP COLUMN id'))
    op.execute(sa.text(f'ALTER TABLE {table} RENAME COLUMN _id TO id'))
    op.execute(sa.text(
        f'ALTER TABLE {table} ADD PRIMARY KEY (id)'
    ))
    op.execute(sa.text(
        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), (SELECT max(id) FROM {table}))"
    ))


def _convert_fk(bind, child: str, column: str, parent: str) -> None:
    """Remap a child FK column to the parent's new integer ids."""
    # The constraint is usually already gone: dropping a parent's PK with
    # CASCADE removed every incoming FK. Drop by name only if it survives.
    fk_name = _fk_constraint_name(bind, child, column)
    if fk_name:
        op.execute(sa.text(f'ALTER TABLE {child} DROP CONSTRAINT {fk_name}'))
    op.execute(sa.text(f'ALTER TABLE {child} ADD COLUMN _fk INTEGER'))
    op.execute(sa.text(
        f'UPDATE {child} SET _fk = l.new_id FROM {LEGACY_IDS} l '
        f'WHERE l.table_name = \'{parent}\' AND {child}.{column} = l.legacy_uuid'
    ))
    _record_indexes(bind, child, column)
    op.execute(sa.text(f'ALTER TABLE {child} DROP COLUMN {column}'))
    op.execute(sa.text(f'ALTER TABLE {child} RENAME COLUMN _fk TO {column}'))
    op.execute(sa.text(
        f'ALTER TABLE {child} ADD CONSTRAINT {_fk_name(child, column)} '
        f'FOREIGN KEY ({column}) REFERENCES {parent} (id)'
    ))
    op.execute(sa.text(f'ALTER TABLE {child} ALTER COLUMN {column} SET NOT NULL'))


def upgrade() -> None:
    bind = op.get_bind()
    tables = _columns(bind)

    # tenants is converted first because every table references it
    if 'tenants' in tables:
        _convert_pk(bind, 'tenants')

    for table in TABLES:
        if table == 'tenants' or table not in tables:
            continue
        for fk_column, parent in FK_MAP.get(table, []):
            if parent in tables:
                _convert_fk(bind, table, fk_column, parent)
        _recreate_indexes(bind, table)
        _convert_pk(bind, table)

    # api_keys may exist in dev databases even though it has no migration
    if 'api_keys' in tables:
        _convert_pk(bind, 'api_keys')
        _convert_fk(bind, 'api_keys', 'tenant_id', 'tenants')
        _recreate_indexes(bind, 'api_keys')


def _restore_pk(bind, table: str) -> None:
    """Downgrade: recreate the uuid PK, restoring the exact legacy uuids."""
    op.execute(sa.text(f'ALTER TABLE {table} ADD COLUMN _old_id UUID DEFAULT gen_random_uuid()'))
    op.execute(sa.text(
        f'UPDATE {table} SET _old_id = l.legacy_uuid FROM {LEGACY_IDS} l '
        f'WHERE l.table_name = \'{table}\' AND l.new_id = {table}.id'
    ))
    # CASCADE: incoming foreign keys from child tables depend on the PK
    # index; they are recreated by _restore_fk once the parent is restored.
    op.execute(sa.text(f'ALTER TABLE {table} DROP CONSTRAINT {table}_pkey CASCADE'))
    op.execute(sa.text(f'ALTER TABLE {table} DROP COLUMN id'))
    op.execute(sa.text(f'ALTER TABLE {table} RENAME COLUMN _old_id TO id'))
    op.execute(sa.text(f'ALTER TABLE {table} ADD PRIMARY KEY (id)'))


def _restore_fk(bind, child: str, column: str, parent: str) -> None:
    op.execute(sa.text(f'ALTER TABLE {child} ADD COLUMN _fk UUID DEFAULT gen_random_uuid()'))
    op.execute(sa.text(
        f'UPDATE {child} SET _fk = l.legacy_uuid FROM {LEGACY_IDS} l '
        f'WHERE l.table_name = \'{parent}\' AND l.new_id = {child}.{column}'
    ))
    op.execute(sa.text(f'ALTER TABLE {child} DROP COLUMN {column}'))
    op.execute(sa.text(f'ALTER TABLE {child} RENAME COLUMN _fk TO {column}'))
    op.execute(sa.text(
        f'ALTER TABLE {child} ADD CONSTRAINT {_fk_name(child, column)} '
        f'FOREIGN KEY ({column}) REFERENCES {parent} (id)'
    ))
    op.execute(sa.text(f'ALTER TABLE {child} ALTER COLUMN {column} SET NOT NULL'))


def downgrade() -> None:
    bind = op.get_bind()
    tables = _columns(bind)

    # Pass 1: restore every PK to uuid. All PKs must be restored before any
    # FK is re-added, because a foreign key cannot reference an integer id
    # with a uuid column (or vice versa).
    for table in reversed(TABLES):
        if table == 'tenants' or table not in tables:
            continue
        _restore_pk(bind, table)

    if 'tenants' in tables:
        _restore_pk(bind, 'tenants')

    if 'api_keys' in tables:
        _restore_pk(bind, 'api_keys')

    # Pass 2: remap every FK back to the restored uuid ids.
    for table in reversed(TABLES):
        if table == 'tenants' or table not in tables:
            continue
        for fk_column, parent in FK_MAP.get(table, []):
            if parent in tables:
                _restore_fk(bind, table, fk_column, parent)
        _recreate_indexes(bind, table)

    if 'api_keys' in tables:
        _restore_fk(bind, 'api_keys', 'tenant_id', 'tenants')
        _recreate_indexes(bind, 'api_keys')

    op.execute(sa.text(f'DROP TABLE IF EXISTS {LEGACY_INDEXES}'))
    op.execute(sa.text(f'DROP TABLE IF EXISTS {LEGACY_IDS}'))
