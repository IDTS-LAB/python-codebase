# Restore Database Foreign Keys Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore all 13 intended foreign keys, align normalized user identifiers with UUID, repair already-migrated databases, and make `make seed` complete without SQLAlchemy mapper errors.

**Architecture:** Treat SQLAlchemy model metadata as the relationship source of truth and load the full model graph in Alembic. Add a forward-only corrective revision after `e73c215d7221` that converts seven normalized user columns to UUID and restores all missing constraints; leave the already-applied normalization revision unchanged.

**Tech Stack:** Python 3.14, SQLAlchemy 2, Alembic, PostgreSQL UUID, pytest, Ruff.

---

## File Structure

- Create `tests/test_database_relationships.py`: mapper, foreign-key target, and UUID metadata regression tests.
- Modify `src/modules/authorization/infrastructure/models/permission_model.py`: restore the permission-to-resource foreign key.
- Modify `src/modules/authorization/infrastructure/models/role_permission_model.py`: restore both role-permission junction foreign keys.
- Modify `src/modules/authorization/infrastructure/models/user_has_role_model.py`: restore both user-role junction foreign keys.
- Modify `src/modules/todo/infrastructure/models/todo_model.py`: restore the todo owner foreign key.
- Modify seven files under `src/modules/user/infrastructure/models/`: use UUID user identifiers and restore user foreign keys.
- Modify `alembic/env.py`: register the complete normalized user model package with Alembic metadata.
- Create `tests/test_restore_database_foreign_keys_migration.py`: verify corrective upgrade and downgrade operations without touching a database.
- Create `alembic/versions/f4a8c2d1e6b9_restore_database_foreign_keys.py`: repair existing schemas after `e73c215d7221`.

### Task 1: Add failing ORM relationship regression tests

**Files:**
- Create: `tests/test_database_relationships.py`

- [ ] **Step 1: Write the mapper and metadata tests**

Create `tests/test_database_relationships.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify RED**

Run: `.venv/bin/pytest tests/test_database_relationships.py -v`

Expected: FAIL with the current `NoForeignKeysError`, missing foreign-key target assertions, and string-type assertions. The test must fail for metadata defects, not import or syntax errors.

- [ ] **Step 3: Commit the failing regression test**

```bash
git add tests/test_database_relationships.py
git commit -m "test: reproduce missing database foreign keys"
```

### Task 2: Restore ORM foreign-key metadata and model discovery

**Files:**
- Modify: `src/modules/authorization/infrastructure/models/permission_model.py`
- Modify: `src/modules/authorization/infrastructure/models/role_permission_model.py`
- Modify: `src/modules/authorization/infrastructure/models/user_has_role_model.py`
- Modify: `src/modules/todo/infrastructure/models/todo_model.py`
- Modify: `src/modules/user/infrastructure/models/user_profile_model.py`
- Modify: `src/modules/user/infrastructure/models/user_security_model.py`
- Modify: `src/modules/user/infrastructure/models/user_settings_model.py`
- Modify: `src/modules/user/infrastructure/models/user_contact_model.py`
- Modify: `src/modules/user/infrastructure/models/user_address_model.py`
- Modify: `src/modules/user/infrastructure/models/user_verification_model.py`
- Modify: `src/modules/user/infrastructure/models/refresh_token_model.py`
- Modify: `alembic/env.py`
- Test: `tests/test_database_relationships.py`

- [ ] **Step 1: Restore authorization and todo foreign keys**

Add `ForeignKey` to each SQLAlchemy import and use these exact column definitions:

```python
# src/modules/authorization/infrastructure/models/permission_model.py
resource_id: Mapped[UUID] = mapped_column(
    ForeignKey("authorization_resources.id"),
    nullable=False,
)

# src/modules/authorization/infrastructure/models/role_permission_model.py
role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
permission_id: Mapped[UUID] = mapped_column(
    ForeignKey("permissions.id"),
    nullable=False,
)

# src/modules/authorization/infrastructure/models/user_has_role_model.py
user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)

# src/modules/todo/infrastructure/models/todo_model.py
user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
```

- [ ] **Step 2: Convert every normalized user link to UUID with a foreign key**

In each listed user model, import `UUID` from `uuid`, import `ForeignKey` from SQLAlchemy, remove `String(36)` from `user_id`, and preserve the existing uniqueness/nullability options:

```python
# user_profile_model.py
user_id: Mapped[UUID] = mapped_column(
    ForeignKey("users.id"),
    unique=True,
    nullable=False,
)

# user_security_model.py
user_id: Mapped[UUID] = mapped_column(
    ForeignKey("users.id"),
    unique=True,
    nullable=False,
)

# user_settings_model.py
user_id: Mapped[UUID] = mapped_column(
    ForeignKey("users.id"),
    unique=True,
    nullable=False,
)

# user_contact_model.py
user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

# user_address_model.py
user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

# user_verification_model.py
user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

# refresh_token_model.py (UserSessionModel)
user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
```

Keep `String` imports in files that use it for other columns. Remove it only from `user_settings_model.py`, where it becomes unused.

- [ ] **Step 3: Register the complete user model package in Alembic**

Replace the two direct user-model imports in `alembic/env.py` with:

```python
from src.modules.user.infrastructure import models as user_models  # noqa: F401
```

This imports every class exported by `src/modules/user/infrastructure/models/__init__.py` before `target_metadata = Base.metadata` is evaluated.

- [ ] **Step 4: Run the focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_database_relationships.py -v`

Expected: `21 passed` (one mapper test, 13 foreign-key cases, seven UUID cases).

- [ ] **Step 5: Run focused lint**

Run:

```bash
.venv/bin/ruff check \
  alembic/env.py \
  src/modules/authorization/infrastructure/models \
  src/modules/todo/infrastructure/models/todo_model.py \
  src/modules/user/infrastructure/models \
  tests/test_database_relationships.py
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit ORM metadata repair**

```bash
git add alembic/env.py src/modules/authorization/infrastructure/models src/modules/todo/infrastructure/models/todo_model.py src/modules/user/infrastructure/models tests/test_database_relationships.py
git commit -m "fix: restore ORM foreign key metadata"
```

### Task 3: Add failing corrective-migration contract tests

**Files:**
- Create: `tests/test_restore_database_foreign_keys_migration.py`

- [ ] **Step 1: Write upgrade and downgrade operation tests**

Create `tests/test_restore_database_foreign_keys_migration.py`:

```python
import importlib.util
from pathlib import Path

from sqlalchemy import String, Uuid


MIGRATION_PATH = Path(
    "alembic/versions/f4a8c2d1e6b9_restore_database_foreign_keys.py"
)
USER_TABLES = (
    "user_profiles",
    "user_security",
    "user_settings",
    "user_contacts",
    "user_addresses",
    "user_verifications",
    "user_sessions",
)
FOREIGN_KEYS = {
    ("fk_permissions_resource_id_authorization_resources", "permissions", "authorization_resources", "resource_id"),
    ("role_permissions_role_id_fkey", "role_permissions", "roles", "role_id"),
    ("role_permissions_permission_id_fkey", "role_permissions", "permissions", "permission_id"),
    ("todos_user_id_fkey", "todos", "users", "user_id"),
    ("user_has_roles_user_id_fkey", "user_has_roles", "users", "user_id"),
    ("user_has_roles_role_id_fkey", "user_has_roles", "roles", "role_id"),
    ("fk_user_profiles_user_id_users", "user_profiles", "users", "user_id"),
    ("fk_user_security_user_id_users", "user_security", "users", "user_id"),
    ("fk_user_settings_user_id_users", "user_settings", "users", "user_id"),
    ("fk_user_contacts_user_id_users", "user_contacts", "users", "user_id"),
    ("fk_user_addresses_user_id_users", "user_addresses", "users", "user_id"),
    ("fk_user_verifications_user_id_users", "user_verifications", "users", "user_id"),
    ("fk_user_sessions_user_id_users", "user_sessions", "users", "user_id"),
}


def load_migration():
    assert MIGRATION_PATH.exists(), "corrective migration does not exist"
    spec = importlib.util.spec_from_file_location("restore_foreign_keys", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_upgrade_converts_user_ids_and_creates_all_foreign_keys(monkeypatch):
    migration = load_migration()
    altered = []
    created = []
    monkeypatch.setattr(
        migration.op,
        "alter_column",
        lambda table, column, **kwargs: altered.append((table, column, kwargs)),
    )
    monkeypatch.setattr(
        migration.op,
        "create_foreign_key",
        lambda name, source, target, local, remote: created.append(
            (name, source, target, local[0], remote[0])
        ),
    )

    migration.upgrade()

    assert [item[:2] for item in altered] == [
        (table, "user_id") for table in USER_TABLES
    ]
    assert all(isinstance(kwargs["type_"], Uuid) for _, _, kwargs in altered)
    assert all(kwargs["postgresql_using"] == "user_id::uuid" for _, _, kwargs in altered)
    assert set(created) == {(*foreign_key, "id") for foreign_key in FOREIGN_KEYS}


def test_downgrade_drops_constraints_and_restores_string_user_ids(monkeypatch):
    migration = load_migration()
    dropped = []
    altered = []
    monkeypatch.setattr(
        migration.op,
        "drop_constraint",
        lambda name, table, **kwargs: dropped.append((name, table, kwargs)),
    )
    monkeypatch.setattr(
        migration.op,
        "alter_column",
        lambda table, column, **kwargs: altered.append((table, column, kwargs)),
    )

    migration.downgrade()

    assert {(name, table) for name, table, _ in dropped} == {
        (name, table) for name, table, _, _ in FOREIGN_KEYS
    }
    assert all(kwargs == {"type_": "foreignkey"} for _, _, kwargs in dropped)
    assert [item[:2] for item in altered] == [
        (table, "user_id") for table in reversed(USER_TABLES)
    ]
    assert all(isinstance(kwargs["type_"], String) for _, _, kwargs in altered)
    assert all(kwargs["postgresql_using"] == "user_id::text" for _, _, kwargs in altered)
```

- [ ] **Step 2: Run the tests to verify RED**

Run: `.venv/bin/pytest tests/test_restore_database_foreign_keys_migration.py -v`

Expected: two assertion failures with `corrective migration does not exist`.

- [ ] **Step 3: Commit the failing migration tests**

```bash
git add tests/test_restore_database_foreign_keys_migration.py
git commit -m "test: specify corrective foreign key migration"
```

### Task 4: Implement the corrective Alembic migration

**Files:**
- Create: `alembic/versions/f4a8c2d1e6b9_restore_database_foreign_keys.py`
- Test: `tests/test_restore_database_foreign_keys_migration.py`

- [ ] **Step 1: Create the corrective revision**

Create `alembic/versions/f4a8c2d1e6b9_restore_database_foreign_keys.py`:

```python
"""restore database foreign keys

Revision ID: f4a8c2d1e6b9
Revises: e73c215d7221
Create Date: 2026-06-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f4a8c2d1e6b9"
down_revision: str | Sequence[str] | None = "e73c215d7221"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_TABLES = (
    "user_profiles",
    "user_security",
    "user_settings",
    "user_contacts",
    "user_addresses",
    "user_verifications",
    "user_sessions",
)

FOREIGN_KEYS = (
    ("fk_permissions_resource_id_authorization_resources", "permissions", "authorization_resources", "resource_id"),
    ("role_permissions_role_id_fkey", "role_permissions", "roles", "role_id"),
    ("role_permissions_permission_id_fkey", "role_permissions", "permissions", "permission_id"),
    ("todos_user_id_fkey", "todos", "users", "user_id"),
    ("user_has_roles_user_id_fkey", "user_has_roles", "users", "user_id"),
    ("user_has_roles_role_id_fkey", "user_has_roles", "roles", "role_id"),
    ("fk_user_profiles_user_id_users", "user_profiles", "users", "user_id"),
    ("fk_user_security_user_id_users", "user_security", "users", "user_id"),
    ("fk_user_settings_user_id_users", "user_settings", "users", "user_id"),
    ("fk_user_contacts_user_id_users", "user_contacts", "users", "user_id"),
    ("fk_user_addresses_user_id_users", "user_addresses", "users", "user_id"),
    ("fk_user_verifications_user_id_users", "user_verifications", "users", "user_id"),
    ("fk_user_sessions_user_id_users", "user_sessions", "users", "user_id"),
)


def upgrade() -> None:
    for table in USER_TABLES:
        op.alter_column(
            table,
            "user_id",
            existing_type=sa.String(length=36),
            type_=sa.Uuid(),
            existing_nullable=False,
            postgresql_using="user_id::uuid",
        )

    for name, source, target, column in FOREIGN_KEYS:
        op.create_foreign_key(name, source, target, [column], ["id"])


def downgrade() -> None:
    for name, source, _, _ in reversed(FOREIGN_KEYS):
        op.drop_constraint(name, source, type_="foreignkey")

    for table in reversed(USER_TABLES):
        op.alter_column(
            table,
            "user_id",
            existing_type=sa.Uuid(),
            type_=sa.String(length=36),
            existing_nullable=False,
            postgresql_using="user_id::text",
        )
```

- [ ] **Step 2: Run migration contract tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_restore_database_foreign_keys_migration.py -v`

Expected: `2 passed`.

- [ ] **Step 3: Verify the Alembic revision graph**

Run: `.venv/bin/alembic heads`

Expected: exactly one head, `f4a8c2d1e6b9 (head)`.

- [ ] **Step 4: Run focused lint**

Run: `.venv/bin/ruff check alembic/versions/f4a8c2d1e6b9_restore_database_foreign_keys.py tests/test_restore_database_foreign_keys_migration.py`

Expected: `All checks passed!`

- [ ] **Step 5: Commit the corrective migration**

```bash
git add alembic/versions/f4a8c2d1e6b9_restore_database_foreign_keys.py tests/test_restore_database_foreign_keys_migration.py
git commit -m "fix: restore database foreign key constraints"
```

### Task 5: Verify migrations, seeding, and the full project

**Files:**
- No code changes expected.

- [ ] **Step 1: Run both focused regression suites**

Run:

```bash
.venv/bin/pytest \
  tests/test_database_relationships.py \
  tests/test_restore_database_foreign_keys_migration.py \
  -v
```

Expected: `23 passed`.

- [ ] **Step 2: Run the full automated checks**

Run: `make check`

Expected: pytest passes, Ruff reports no errors, import-linter contracts pass, and `src.main` prints `import ok`.

- [ ] **Step 3: Inspect the configured database revision before mutation**

Run: `.venv/bin/alembic current`

Expected: a valid current revision. Record it before proceeding. If the command cannot connect, report the database prerequisite instead of claiming database verification.

- [ ] **Step 4: Apply the corrective migration**

Run: `make migrate`

Expected: Alembic upgrades to `f4a8c2d1e6b9` without cast or referential-integrity errors. If PostgreSQL rejects malformed UUIDs or orphaned rows, stop and report the exact rows/constraint category; do not delete or rewrite data automatically.

- [ ] **Step 5: Confirm the new revision**

Run: `.venv/bin/alembic current`

Expected: `f4a8c2d1e6b9 (head)`.

- [ ] **Step 6: Run the original failing workflow**

Run: `make seed`

Expected: seed summary output and exit status 0, with no `NoForeignKeysError`.

- [ ] **Step 7: Confirm the working tree contains no unintended files**

Run: `git status --short`

Expected: only pre-existing unrelated user files, if any. Do not add `.vscode/PythonImportHelper-v2-Completion.json`.
