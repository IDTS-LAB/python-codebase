# UUID → int IDs + Module Facade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert all database entity IDs from UUID to auto-increment integers across all modules, and replace the ad-hoc `UserModuleProvider` with a proper Module Facade pattern for cross-module communication.

**Architecture:** All `Base`-derived SQLAlchemy models get an `int` identity PK; `TenantMixin.tenant_id` becomes `int`; domain entities use `id: int | None = None` (DB assigns on insert); JWT subjects / casbin subjects / cursor pagination parse ints instead of UUIDs. Cross-module communication goes through `ModuleFacade` (abstract base in `src/shared/`) — `UserModuleFacade` replaces `UserModuleProvider`; other modules only import the facade.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x (async), PostgreSQL, Alembic (async env), Casbin, import-linter, pytest, ruff, mypy.

## Global Constraints

- All DB PK/FK columns: `Mapped[int]` with autoincrement identity — no `uuid4` defaults anywhere in models/entities.
- Domain entity id fields: `id: int | None = None`; `create()` classmethods must NOT generate ids (DB assigns).
- `tenant_id: int` everywhere (models, repos, deps, middleware, UoW).
- Keep UUID ONLY for: `shared/events/base.py` `event_id`, `core/security/audit.py` event ids, `core/middleware/request_id.py` request ids, JWT `jti`, and the raw api_key secret string (`api_…`).
- JWT `sub` / casbin subjects stay strings: `str(user.id)` / `f"user:{int}"`-style subjects; parse with `int()` not `UUID()`.
- Repository create paths must omit `id=` so the DB identity assigns it; always map entities from the refreshed model.
- Facade: new abstract `ModuleFacade` in `src/shared/facade.py`; `src/modules/user/facade.py` replaces `src/modules/user/providers.py`; consumers import only `src.modules.user.facade` (module root, allowed by `.importlinter`).
- Test/verification commands (from Makefile): `make test`, `make lint`, `make lint-imports`, `make migrate`, `make revision`.

---

### Task 1: Shared int identity PK + int tenant mixin

**Files:**
- Modify: `src/shared/database/model.py`
- Modify: `src/shared/database/mixin/tenant.py`
- Test: `tests/test_database_relationships.py`

**Interfaces:**
- Produces: `Base.id: Mapped[int]` (autoincrement PK), `TenantMixin.tenant_id: Mapped[int]` FK → `tenants.id`. Every later task's models inherit these.

- [ ] **Step 1: Update the relationship test to expect Integer PKs (failing test)**

Replace lines 2 and 53-55 of `tests/test_database_relationships.py`:

```python
from sqlalchemy import Integer
```

```python
@pytest.mark.parametrize("table", NORMALIZED_USER_TABLES)
def test_normalized_user_identifier_uses_int(table):
    assert isinstance(Base.metadata.tables[table].c.user_id.type, Integer)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `make test -k test_normalized_user_identifier_uses_int`
Expected: FAIL (`isinstance(..., Integer)` is False — column is `Uuid`)

- [ ] **Step 3: Convert the shared base model**

`src/shared/database/model.py` — full new content:

```python
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.shared.database.mixin.tenant import TenantMixin  # noqa: F401


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        sort_order=-100,
    )
```

- [ ] **Step 4: Convert the tenant mixin**

`src/shared/database/mixin/tenant.py` — full new content:

```python
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        sort_order=-60,
    )
```

- [ ] **Step 5: Run the tests**

Run: `make test`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/shared/database/model.py src/shared/database/mixin/tenant.py tests/test_database_relationships.py
git commit -m "refactor: use integer primary keys in shared base model"
```

---

### Task 2: Cursor pagination with int ids

**Files:**
- Modify: `src/shared/utils/cursor.py`
- Test: Create `tests/test_cursor.py`

**Interfaces:**
- Produces: `encode_cursor(created_at: datetime, id: int, dir: CursorDirection) -> str`, `decode_cursor(cursor: str) -> tuple[datetime, int, CursorDirection]`. Consumed by todo router and authorization repos.

- [ ] **Step 1: Write the failing test**

Create `tests/test_cursor.py`:

```python
from datetime import datetime

import pytest

from src.shared.utils.cursor import (
    CursorDirection,
    decode_cursor,
    encode_cursor,
)


def test_encode_decode_cursor_roundtrip_with_int_id():
    created_at = datetime(2026, 1, 1, 12, 30, 0)
    cursor = encode_cursor(created_at, 42, CursorDirection.DIRECTION_NEXT)
    decoded_created_at, decoded_id, decoded_dir = decode_cursor(cursor)
    assert decoded_created_at == created_at
    assert decoded_id == 42
    assert decoded_dir == CursorDirection.DIRECTION_NEXT


def test_decode_cursor_rejects_invalid_id():
    cursor = encode_cursor(datetime.now(), 7, CursorDirection.DIRECTION_PREV)
    assert decode_cursor(cursor)[1] == 7


def test_decode_cursor_rejects_garbage():
    with pytest.raises(ValueError, match="Invalid cursor format"):
        decode_cursor("not-a-cursor")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `make test -k cursor`
Expected: FAIL (`id` decoded as `UUID`, so `decoded_id == 42` fails)

- [ ] **Step 3: Convert the cursor utility**

`src/shared/utils/cursor.py` — full new content:

```python
import base64
import json
from datetime import datetime
from enum import Enum


class CursorDirection(Enum):
    DIRECTION_NEXT = "next"
    DIRECTION_PREV = "prev"


def encode_cursor(created_at: datetime, id: int, dir: CursorDirection) -> str:
    """
    Encode a cursor from timestamp and ID.
    Format: base64(json({"t": "ISO_TIMESTAMP", "id": "INT"}))
    """
    cursor_data = {"t": created_at.isoformat(), "id": id, "dir": dir.value}
    json_str = json.dumps(cursor_data)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int, CursorDirection]:
    """
    Decode a cursor back to timestamp and ID.
    Returns: (created_at, id)
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        cursor_data = json.loads(json_str)
        created_at = datetime.fromisoformat(cursor_data["t"])
        dir = CursorDirection(cursor_data["dir"])
        id = int(cursor_data["id"])
        return created_at, id, dir
    except Exception as e:
        raise ValueError(f"Invalid cursor format: {e}")
```

- [ ] **Step 4: Run the tests**

Run: `make test -k cursor`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shared/utils/cursor.py tests/test_cursor.py
git commit -m "refactor: cursor pagination uses integer ids"
```

---

### Task 3: Tenants module → int

**Files:**
- Modify: `src/modules/tenants/domain/entities/tenant.py`
- Modify: `src/modules/tenants/domain/repositories/tenant_repository.py`
- Modify: `src/modules/tenants/infrastructure/repositories/tenant_repository.py`
- Modify: `src/modules/tenants/presentation/schemas.py`

**Interfaces:**
- Consumes: `Base.id: int` (Task 1).
- Produces: `Tenant(id: int | None = None, name, slug, domain)`, `SQLAlchemyTenantRepository.get_by_id(tenant_id: int)`, `TenantResponse.id: int`.

- [ ] **Step 1: Convert the entity**

`src/modules/tenants/domain/entities/tenant.py`:

```python
class Tenant:
    def __init__(
        self,
        id: int | None = None,
        name: str = "",
        slug: str = "",
        domain: str | None = None,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.domain = domain
```

(Remove `from uuid import UUID`; `id` defaults to `None` so the DB identity assigns it on insert.)

- [ ] **Step 2: Convert the domain repository interface**

`src/modules/tenants/domain/repositories/tenant_repository.py` — replace the UUID import and `get_by_id(self, tenant_id: UUID)` with `get_by_id(self, tenant_id: int)`.

- [ ] **Step 3: Convert the infra repository**

`src/modules/tenants/infrastructure/repositories/tenant_repository.py`:
- Remove `from uuid import UUID`.
- `get_by_id(self, tenant_id: int)`, `_get_model(self, tenant_id: int)`.
- `save()`: new tenants must not pass `id` (let identity assign) — replace the `TenantModel(id=tenant.id, ...)` branch with:

```python
        else:
            model = TenantModel(
                name=tenant.name,
                slug=tenant.slug,
                domain=tenant.domain,
            )
            self._db.add(model)
```

- [ ] **Step 4: Convert the presentation schema**

`src/modules/tenants/presentation/schemas.py` — remove `from uuid import UUID`, change `id: UUID` to `id: int`.

- [ ] **Step 5: Run the tests and verify no import breakage**

Run: `make test && make lint-imports`
Expected: PASS (no UUID references left in the tenants module)

- [ ] **Step 6: Commit**

```bash
git add src/modules/tenants
git commit -m "refactor: tenants module uses integer ids"
```

---

### Task 4: User module — domain entities, repositories interfaces, commands/queries

**Files:**
- Modify: `src/modules/user/domain/entities/user.py`
- Modify: `src/modules/user/domain/entities/refresh_token.py`
- Modify: `src/modules/user/domain/repositories/user_repository.py`
- Modify: `src/modules/user/domain/repositories/refresh_token_repository.py`
- Modify: `src/modules/user/application/detail_user/query.py`
- Modify: `src/modules/user/application/auth/two_factor/command.py`
- Modify: `src/modules/user/application/auth/logout_user/validation.py`

**Interfaces:**
- Produces: `User.id: int | None = None`, `UserProfile.user_id: int`, `UserSettings.user_id: int`, `UserSecurity.user_id: int`, `User.create(...)` → id=None; `RefreshToken.id: int | None`, `RefreshToken.user_id: int`, `RefreshToken.create(user_id: int, ...)` → id=None; `DetailUserQuery(user_id: int)`; 2FA commands with `user_id: int`; `validate_logout_user_command` validates int.

- [ ] **Step 1: Convert `user.py` entity**

`src/modules/user/domain/entities/user.py`:
- Remove `from uuid import UUID, uuid4`.
- `UserProfile.user_id: UUID` → `int` (line 13); `UserSettings.user_id` → `int` (line 28); `UserSecurity.user_id` → `int` (line 38).
- `User.id: UUID` → `id: int | None = None` (line 53).
- `User.create()` — replace `id=uuid4(),` with `id=None,`.

- [ ] **Step 2: Convert `refresh_token.py` entity**

`src/modules/user/domain/entities/refresh_token.py`:
- Remove `from uuid import UUID, uuid4`.
- `id: UUID` → `id: int | None = None`; `user_id: UUID` → `int`.
- `create(cls, user_id: int, ...)` — replace `id=uuid4(),` with `id=None,`.

- [ ] **Step 3: Convert domain repository interfaces**

`src/modules/user/domain/repositories/user_repository.py` — remove `from uuid import UUID`; change every `UUID` type hint to `int` (`get_by_id`, `get_by_id_with_relations`, `_get_user_model` signatures).

`src/modules/user/domain/repositories/refresh_token_repository.py` — same: `user_id: int`.

- [ ] **Step 4: Convert commands/queries/validation**

`src/modules/user/application/detail_user/query.py`: remove UUID import, `user_id: UUID` → `int`.

`src/modules/user/application/auth/two_factor/command.py`: remove `from uuid import UUID`; replace all 7 `user_id: UUID` with `user_id: int`.

`src/modules/user/application/auth/logout_user/validation.py`:

```python
def validate_logout_user_command(command: LogoutUserCommand) -> None:
    try:
        int(command.user_id)
    except ValueError as exc:
        raise ValueError("User id must be a valid integer") from exc

    if not command.access_token.strip():
        raise ValueError("Access token is required")
```

- [ ] **Step 5: Update the validation test (failing test)**

`tests/test_application_validation.py`:
- Remove `from uuid import uuid4`.
- `test_logout_validation_rejects_invalid_user_id`: change regex `"User id must be a valid UUID"` → `"User id must be a valid integer"` and input `"not-a-uuid"` → `"not-an-int"`.
- `test_logout_validation_rejects_blank_access_token`: `LogoutUserCommand(user_id=str(uuid4()), ...)` → `LogoutUserCommand(user_id="1", ...)`.
- `test_query_validation_accepts_valid_queries`: `user_id = uuid4()` → `user_id = 1`.

Run: `make test -k validation`
Expected: FAIL until step 4 applied (then PASS)

- [ ] **Step 6: Run tests**

Run: `make test`
Expected: PASS (remaining failures in other modules are expected and resolved in later tasks)

- [ ] **Step 7: Commit**

```bash
git add src/modules/user/domain src/modules/user/application/detail_user src/modules/user/application/auth/logout_user src/modules/user/application/auth/two_factor tests/test_application_validation.py
git commit -m "refactor: user domain entities and commands use integer ids"
```

---

### Task 5: User module — infrastructure models → int

**Files (all modify):**
- `src/modules/user/infrastructure/models/user_model.py`
- `src/modules/user/infrastructure/models/user_profile_model.py`
- `src/modules/user/infrastructure/models/user_settings_model.py`
- `src/modules/user/infrastructure/models/user_security_model.py`
- `src/modules/user/infrastructure/models/user_contact_model.py`
- `src/modules/user/infrastructure/models/user_address_model.py`
- `src/modules/user/infrastructure/models/user_verification_model.py`
- `src/modules/user/infrastructure/models/refresh_token_model.py`

**Interfaces:**
- Consumes: `Base.id: int` (Task 1), `TenantMixin.tenant_id: int` (Task 1).
- Produces: all models' `id` from `Base` (int) and `user_id: Mapped[int]` FK columns.

- [ ] **Step 1: Apply the canonical model transformation**

For every file above, apply these exact changes:

1. Remove the imports:
```python
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
```
2. Replace every FK/PK column typed `Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ...)` with the int form.

Canonical example — `user_profile_model.py` becomes:

```python
from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserProfileModel(Base, TimeStampMixin, SoftDeleteMixin, TenantMixin):
    """User profile containing personal information."""

    __tablename__ = "user_profiles"
    __table_args__ = (Index("ix_user_profiles_user_id", "user_id", unique=True),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # Personal Information
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Avatar and Bio
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Birth Date
    birth_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="profile",
        foreign_keys=[user_id],
    )
```

Apply the identical pattern to the remaining files: `user_settings_model.py`, `user_security_model.py`, `user_contact_model.py`, `user_address_model.py`, `user_verification_model.py` (each has one `user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), ...)` → `user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), ...)` keeping their existing `unique`/`index` args).

`refresh_token_model.py` (`UserSessionModel`): `id` comes from `Base`; convert `user_id` exactly as above (keep `Index("ix_user_sessions_user_id", "user_id")`).

`user_model.py`: only remove the `UUID`/`PG_UUID` imports if present; `id` comes from `Base`; ensure `tenant_id` comes from `TenantMixin` (already does).

- [ ] **Step 2: Verify**

Run: `rg -n "UUID|uuid" src/modules/user/infrastructure/models/`
Expected: no matches.

Run: `make test -k relationships`
Expected: PASS (`test_normalized_user_identifier_uses_int` asserts Integer on all 7 user tables)

- [ ] **Step 3: Commit**

```bash
git add src/modules/user/infrastructure/models
git commit -m "refactor: user infrastructure models use integer foreign keys"
```

---

### Task 6: User module — infrastructure repositories → int

**Files:**
- Modify: `src/modules/user/infrastructure/repositories/user_repository.py`
- Modify: `src/modules/user/infrastructure/repositories/refresh_token_repository.py`

**Interfaces:**
- Consumes: int-typed entities (Task 4) and models (Task 5).
- Produces: `SQLAlchemyUserRepository(db, tenant_id: int | None)`, `save()` returning entity with DB-assigned int id; `SQLAlchemyRefreshTokenRepository` same.

- [ ] **Step 1: Convert `user_repository.py`**

- Remove `from uuid import UUID`.
- `__init__(self, db, tenant_id: int | None = None)`.
- `get_by_id(self, user_id: int)`, `get_by_id_with_relations(self, user_id: int)`, `_get_user_model(self, user_id: int)`, `_create_default_related_records(self, user_id: int)`.
- In `save()` create branch, do not pass `id` when it is `None` (DB identity assigns) AND flush before creating the default related records so `user_model.id` is populated (otherwise `user_id` is NULL → IntegrityError). Replace lines 80-91 with:

```python
        else:
            # Create new user
            model_kwargs = {
                "email": user.email,
                "username": user.username,
                "password_hash": user.password_hash,
                "auth_provider": user.auth_provider,
                "status": user.status,
                "external_id": user.external_id,
                "tenant_id": self._tenant_id or user.tenant_id,
            }
            if user.id is not None:
                model_kwargs["id"] = user.id
            user_model = UserModel(**model_kwargs)
            self._db.add(user_model)
            await self._db.flush()

            # Create default related records
            await self._create_default_related_records(user_model.id)
```

(`user.tenant_id` — add a `tenant_id: int | None = None` field to the `User` dataclass in `user.py` (Task 4) if it does not exist; check first: `user.py` has no `tenant_id` field — add `tenant_id: int | None = None` after `updated_at`. The `User` dataclass is `kw_only` (Task 4), so field order is flexible.)

- [ ] **Step 2: Convert `refresh_token_repository.py`**

- Remove `from uuid import UUID`; `__init__(self, db, tenant_id: int | None = None)`.
- `save()` — do not pass `id` when `None` (DB identity assigns) AND keep update semantics for existing tokens (the caller `refresh_token/handler.py` revokes an existing token then saves it — insert-only would duplicate the row and never revoke the original). Use merge + conditional id:

```python
    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        model_kwargs = {
            "user_id": refresh_token.user_id,
            "tenant_id": self._tenant_id,
            "refresh_token_hash": refresh_token.token_hash,
            "expires_at": refresh_token.expires_at,
            "is_revoked": refresh_token.is_revoked,
        }
        if refresh_token.id is not None:
            model_kwargs["id"] = refresh_token.id
        model = RefreshTokenModel(**model_kwargs)
        model = await self.db.merge(model)
        await self.db.flush()
        await self.db.refresh(model)
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.refresh_token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
        )
```

- `revoke_by_user_id(self, user_id: int)`.
- `get_by_token_hash` already maps `id=model.id` — works unchanged.

- [ ] **Step 3: Run tests**

Run: `make test`
Expected: PASS (no user-module-specific test failures; cross-module failures resolved in later tasks)

- [ ] **Step 4: Commit**

```bash
git add src/modules/user/infrastructure/repositories src/modules/user/domain/entities/user.py
git commit -m "refactor: user repositories persist integer ids"
```

---

### Task 7: User module — application handlers, presentation, 2FA → int

**Files:**
- Modify: `src/modules/user/application/detail_user/handler.py`
- Modify: `src/modules/user/application/auth/register_user/handler.py`
- Modify: `src/modules/user/application/auth/login_user/handler.py`
- Modify: `src/modules/user/application/auth/refresh_token/handler.py`
- Modify: `src/modules/user/application/auth/two_factor/handler.py`
- Modify: `src/modules/user/presentation/routers/user_router.py`
- Modify: `src/modules/user/presentation/routers/two_factor_router.py`
- Modify: `src/modules/user/presentation/dependency.py`
- Modify: `src/core/security/two_factor_auth.py`

**Interfaces:**
- Consumes: int-typed domain layer (Task 4).
- Produces: handlers taking/returning int ids; routers parsing `int(user_id)` from JWT claims; `TwoFactorAuthService` methods typed `user_id: int`.

- [ ] **Step 1: Convert application handlers**

For each handler file, remove `from uuid import UUID` (where present) and change `UUID` type hints to `int`:
- `detail_user/handler.py`: `user_id: int` param and any `str(...)` casts of ids remain fine.
- `register_user/handler.py`: `subject=str(saved_user.id)` — unchanged (works for int); `UserRegisteredEvent(user_id=str(saved_user.id), ...)` — unchanged.
- `login_user/handler.py`: `str(user.id)` JWT subs unchanged; `actor_id=str(user.id)` unchanged; `RefreshToken.create(user_id=user.id, ...)` — works (user.id now int).
- `refresh_token/handler.py`: verify `user_id` parsing — replace `UUID(...)`-style parsing with `int(...)` if present (grep for `UUID` first; this file had none per audit).
- `two_factor/handler.py`: any `UUID` type hints → `int`.

- [ ] **Step 2: Convert presentation layer**

`src/modules/user/presentation/dependency.py`: remove `from uuid import UUID`; 4× `tenant_id: UUID = Depends(get_current_tenant_id)` → `tenant_id: int`.

`src/modules/user/presentation/routers/user_router.py`: `id=str(user.id)` — unchanged (works for int).

`src/modules/user/presentation/routers/two_factor_router.py`: replace each of the 5 occurrences of the pattern

```python
    from uuid import UUID
    ...
    command = ...Command(user_id=UUID(current_user_id))
```

with `user_id=int(current_user_id)` — the file has `UUID(current_user_id)` on lines 65, 94, 124, 157, 185, 221, 252; remove those `from uuid import UUID` local imports and cast with `int()`.

- [ ] **Step 3: Convert the 2FA service**

`src/core/security/two_factor_auth.py`: remove `from uuid import UUID`; all `user_id: UUID` signatures (lines 37, 69, 103, 150, 202, 293) → `user_id: int`.

- [ ] **Step 4: Run tests**

Run: `make test`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modules/user/application src/modules/user/presentation src/core/security/two_factor_auth.py
git commit -m "refactor: user application and presentation use integer ids"
```

---

### Task 8: Todo module → int

**Files:**
- Modify: `src/modules/todo/domain/entities/todo.py`
- Modify: `src/modules/todo/domain/repositories/todo_repository.py`
- Modify: `src/modules/todo/infrastructure/models/todo_model.py`
- Modify: `src/modules/todo/infrastructure/repositories/todo_repository.py`
- Modify: `src/modules/todo/application/create_todo/handler.py`
- Modify: `src/modules/todo/application/list_todo/handler.py`
- Modify: `src/modules/todo/application/list_todo/query.py`
- Modify: `src/modules/todo/application/detail_todo/handler.py`
- Modify: `src/modules/todo/application/update_todo/handler.py`
- Modify: `src/modules/todo/application/delete_todo/handler.py`
- Modify: `src/modules/todo/presentation/routers/todo_router.py`
- Modify: `src/modules/todo/presentation/dependency.py`
- Modify: `src/modules/todo/presentation/schemas/response.py`

**Interfaces:**
- Consumes: `encode_cursor/decode_cursor` with int (Task 2), `UserModuleFacade.get_user_profile(user_id: int)` (Task 13 — type hints reference it; ordering is safe because python resolves at runtime).
- Produces: `Todo(id: int | None = None, ..., user_id: int)`, `Todo.create(title, user_id: int)` → id=None; repositories with `tenant_id: int | None`, `todo_id: int`, `user_id: int`, `cursor_id: int | None`; router path params `todo_id: int`.

- [ ] **Step 1: Convert the entity**

`src/modules/todo/domain/entities/todo.py` — full new content:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Todo:
    id: int | None = None
    title: str = ""
    description: str | None = None
    is_completed: bool = False
    user_id: int = 0

    @classmethod
    def create(cls, title: str, user_id: int, description: str | None = None) -> Todo:
        return cls(
            id=None,
            title=title,
            description=description,
            is_completed=False,
            user_id=user_id,
        )

    def mark_completed(self):
        self.is_completed = True
```

- [ ] **Step 2: Convert the model**

`src/modules/todo/infrastructure/models/todo_model.py`:

```python
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.model import Base
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin


class TodoModel(Base, TimeStampMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = "todos"

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

- [ ] **Step 3: Convert the domain repository interface**

`src/modules/todo/domain/repositories/todo_repository.py`: remove UUID import; `get_by_id(todo_id: int)`, `get_all_by_user(user_id: int)`, `get_by_user_cursor(user_id: int, ..., cursor_id: int | None = None)`, `delete(todo_id: int)`.

- [ ] **Step 4: Convert the infra repository**

`src/modules/todo/infrastructure/repositories/todo_repository.py`:
- Remove `from uuid import UUID`.
- `__init__(self, db, tenant_id: int | None = None)`.
- `get_by_id(todo_id: int)`, `get_by_user_cursor(user_id: int, cursor_created_at, cursor_id: int | None, ...)`, `get_all_by_user(user_id: int)`, `delete(todo_id: int)`.
- `save()` — do not pass `id` when `None`:

```python
    async def save(self, todo: Todo) -> Todo:
        model_kwargs = {
            "title": todo.title,
            "description": todo.description,
            "is_completed": todo.is_completed,
            "user_id": todo.user_id,
            "tenant_id": self._tenant_id,
        }
        if todo.id is not None:
            model_kwargs["id"] = todo.id
        model = TodoModel(**model_kwargs)
        model = await self.db.merge(model)
        await self.db.flush()
        await self.db.refresh(model)
        return Todo(
            id=model.id,
            title=model.title,
            description=model.description,
            is_completed=model.is_completed,
            user_id=model.user_id,
        )
```

- `_to_entity`: replace `id=str(model.id)` with `id=model.id`.

- [ ] **Step 5: Convert application layer**

Remove `from uuid import UUID` from: `create_todo/handler.py`, `list_todo/handler.py`, `list_todo/query.py`, `detail_todo/handler.py`, `update_todo/handler.py`, `delete_todo/handler.py`.
Change `UUID` → `int` in the same files:
- `create_todo/handler.py`: `execute(self, command, user_id: int)`.
- `list_todo/handler.py`: `user_id: int`, `cursor_id: int | None`.
- `list_todo/query.py`: `user_id: int`.
- `detail_todo/handler.py`: `execute(self, todo_id: int, user_id: int)`; `id=str(todo.id)` stays (str cast fine).
- `update_todo/handler.py`: `execute(self, todo_id: int, command, user_id: int)`.
- `delete_todo/handler.py`: `execute(self, todo_id: int, user_id: int)`.

`src/modules/todo/presentation/schemas/response.py` — no UUID fields (`TodoResponse.id: str` and `TodoWithOwnerResponse.owner: UserProfile` both work as-is; `UserProfile` now carries `id: int` after Task 13). No change needed in this file.

- [ ] **Step 6: Convert presentation layer**

`src/modules/todo/presentation/routers/todo_router.py`:
- Remove `from uuid import UUID`.
- Path params `todo_id: UUID` → `todo_id: int` (lines 140, 163, 187).
- `id=str(todo.id)` → `id=todo.id` (lines 67, 99, 174) — ints serialize fine in JSON.
- `GetTodosQuery(user_id=current_user.get("id"))` — unchanged (dict value is now int from JWT).

`src/modules/todo/presentation/dependency.py`:
- Remove `from uuid import UUID`; `tenant_id: UUID = Depends(get_current_tenant_id)` → `tenant_id: int`.
- Line 22 `from src.modules.user.providers import UserModuleProvider` and line 56 `user_provider: UserModuleProvider` will be updated in Task 13 (facade). For now keep them — the file still imports the old module which still exists.

- [ ] **Step 7: Run tests**

Run: `make test`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/modules/todo
git commit -m "refactor: todo module uses integer ids"
```

---

### Task 9: Authorization module → int

**Files:**
- Modify: `src/modules/authorization/domain/entities/role.py`, `permission.py`, `resource.py`
- Modify: `src/modules/authorization/domain/services/authorization_service.py`
- Modify: `src/modules/authorization/infrastructure/models/role_model.py`, `permission_model.py`, `resource_model.py`, `role_permission_model.py`, `user_has_role_model.py`
- Modify: `src/modules/authorization/infrastructure/services/casbin_authorization_service.py`
- Modify: `src/modules/authorization/infrastructure/repositories/casbin_policy_repository.py`
- Modify: `src/modules/authorization/application/create_role/handler.py`, `update_role/handler.py`, `delete_role/handler.py`, `get_role/handler.py`, `list_roles/handler.py`, `create_permission/handler.py`, `update_permission/handler.py`, `delete_permission/handler.py`, `get_permission/handler.py`, `list_permissions/handler.py`
- Modify: `src/modules/authorization/application/create_role/command.py`, `update_role/command.py`, `delete_role/command.py`, `get_role/query.py`, `update_permission/command.py`, `delete_permission/command.py`, `get_permission/query.py`
- Modify: `src/modules/authorization/presentation/routers/role_router.py`, `permission_router.py`
- Modify: `src/modules/authorization/presentation/schema/*` (response schemas)
- Modify: `src/modules/authorization/presentation/dependency.py`

**Interfaces:**
- Consumes: int `Base.id`, int `TenantMixin.tenant_id`.
- Produces: `Role(id: int | None = None, ...)`, `Role.create(name, description)` → id=None; same for `Permission` and `AuthorizationResource`; casbin subjects `"user:<int>"` parsed via `int(subject)`.

- [ ] **Step 1: Convert domain entities**

`role.py`:

```python
from dataclasses import dataclass


@dataclass
class Role:
    id: int | None = None
    name: str = ""
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def create(cls, name: str, description: str | None = None) -> "Role":
        return cls(
            id=None,
            name=name,
            description=description,
        )
```

`permission.py`: same transformation — `id: int | None = None`, `create(...)` returns `id=None`.

`resource.py`: same transformation — `id: int | None = None`, `create(...)` returns `id=None`.

- [ ] **Step 2: Convert models**

- `role_model.py`: no UUID (id from Base) — no change needed.
- `resource_model.py`: no UUID — no change needed.
- `permission_model.py`: remove UUID/PG_UUID imports; `resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("authorization_resources.id"), ...)` → `resource_id: Mapped[int] = mapped_column(ForeignKey("authorization_resources.id"), nullable=False)`.
- `role_permission_model.py`: remove UUID/PG_UUID imports; `role_id: Mapped[UUID]` → `Mapped[int]` (keep `ForeignKey("roles.id")`, `nullable=False`); `permission_id` same.
- `user_has_role_model.py`: remove UUID/PG_UUID imports; `user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)` → `user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)`; `role_id: Mapped[UUID]` → `Mapped[int]`.

- [ ] **Step 3: Convert services**

`domain/services/authorization_service.py`: remove `from uuid import UUID`; all `role_id: UUID`, `permission_id: UUID`, `user_id: UUID`, `cursor_id: UUID | None` → `int`.

`infrastructure/services/casbin_authorization_service.py`: same transformation (all `UUID` → `int`).

- [ ] **Step 4: Convert the casbin policy repository**

`infrastructure/repositories/casbin_policy_repository.py`:
- Remove `from uuid import UUID`.
- `__init__(self, db, tenant_id: int | None = None)`.
- `assign_role`: `user_id = UUID(subject)` → `user_id = int(subject)` (line 101).
- `get_roles_for_subject`: `user_id = UUID(subject)` → `user_id = int(subject)` (line 121).
- All signatures: `role_id: UUID` → `int` (get_role, delete_role, list_roles_cursor cursor_id), `permission_id: UUID` → `int`, `cursor_id: UUID | None` → `int | None` (line 544).
- `create_resource`/`create_role`/`create_permission`: remove `id=resource.id` / `id=role.id` / `id=permission.id` kwargs from the model constructors (models now get identity-assigned ids; the `_*_from_model` helpers already read `model.id`).

- [ ] **Step 5: Convert application layer**

For each handler/command/query file in the list: remove `from uuid import UUID` and change `UUID` → `int` in signatures (commands/queries: `role_id: int`, `permission_id: int`; handlers pass through). The `id=str(role.id)`/`id=str(permission.id)` casts in handlers stay (harmless).

- [ ] **Step 6: Convert presentation layer**

- `presentation/dependency.py`: `tenant_id: UUID` → `int`.
- `presentation/routers/role_router.py` and `permission_router.py`: remove UUID imports; path params `role_id: UUID` → `int`, `permission_id: UUID` → `int`.
- `presentation/schema/*` response models: `id: UUID` → `int` (grep for `UUID` in the schema dir and replace).

- [ ] **Step 7: Run tests**

Run: `make test && make lint-imports`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/modules/authorization
git commit -m "refactor: authorization module uses integer ids"
```

---

### Task 10: api_key module → int

**Files:**
- Modify: `src/modules/api_key/domain/entities.py`
- Modify: `src/modules/api_key/domain/repository.py`
- Modify: `src/modules/api_key/infrastructure/models.py`
- Modify: `src/modules/api_key/infrastructure/repository.py`
- Modify: `src/modules/api_key/presentation/routers.py`
- Modify: `src/modules/api_key/presentation/dependencies.py`

**Interfaces:**
- Consumes: `Base.id: int` (Task 1), `TenantMixin.tenant_id: int`.
- Produces: `ApiKey(id: int | None = None, ...)` — the `api_…` raw key string stays a random secret; `SQLAlchemyApiKeyRepository.create()` returns the entity with DB-assigned int id; `ApiKeyModel` id from Base (int).

- [ ] **Step 1: Convert the entity**

`src/modules/api_key/domain/entities.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ApiKey:
    id: int | None = None
    key_prefix: str = ""
    key_hash: str = ""
    name: str = ""
    permissions: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    last_used_at: datetime | None = None
```

- [ ] **Step 2: Convert the domain repository**

`src/modules/api_key/domain/repository.py`: remove UUID import; `get_by_id(self, id: int)`, `revoke(self, id: int)`, `update_last_used(self, id: int)`.

- [ ] **Step 3: Convert the model**

`src/modules/api_key/infrastructure/models.py`: delete the explicit `id: Mapped[str] = mapped_column(String(36), primary_key=True)` override (line 13) — the int `Base.id` applies. Keep `String` import only if still used (it is — `key_prefix`, `key_hash`, `name`).

- [ ] **Step 4: Convert the repository**

`src/modules/api_key/infrastructure/repository.py`:
- Remove `from uuid import UUID`.
- `__init__(self, session, tenant_id: int | None = None)`.
- `create()` — drop `id=str(api_key.id)` and refresh the entity:

```python
    async def create(self, api_key: ApiKey) -> ApiKey:
        model = ApiKeyModel(
            key_prefix=api_key.key_prefix,
            key_hash=api_key.key_hash,
            name=api_key.name,
            permissions=json.dumps(api_key.permissions),
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
            tenant_id=self._tenant_id,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        api_key.id = model.id
        return api_key
```

- `get_by_id(self, id: int)`: `ApiKeyModel.id == id` (drop `str()` cast).
- `revoke(self, id: int)` / `update_last_used(self, id: int)`: `await self._session.get(ApiKeyModel, id)` (drop `str()` cast).
- `_to_entity`: `id=UUID(model.id)` → `id=model.id`.

- [ ] **Step 5: Convert presentation**

`src/modules/api_key/presentation/routers.py`: remove `from uuid import UUID`; path param `api_key_id: UUID` → `int`; `id=str(api_key.id)` → `id=api_key.id` (lines 36, 56); route responses unchanged otherwise.

`src/modules/api_key/presentation/dependencies.py`: `tenant_id: UUID` → `int`.

- [ ] **Step 6: Run tests**

Run: `make test`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/modules/api_key
git commit -m "refactor: api_key module uses integer ids"
```

---

### Task 11: Core layer → int

**Files:**
- Modify: `src/core/dependency/auth.py`
- Modify: `src/core/dependency/tenant.py`
- Modify: `src/core/middleware/tenant.py`
- Modify: `src/core/database/unit_of_work.py`
- Modify: `src/core/database/postgres/session.py`
- Modify: `src/core/security/infrastructure/repositories/login_attempt_repository.py`

**Interfaces:**
- Consumes: int-typed repos/models.
- Produces: `get_current_tenant_id(request) -> int`, `get_optional_tenant_id(request) -> int | None`, `get_current_user` returns `{"id": int, ...}` (JWT subject parsed as int), `UnitOfWork(session, tenant_id: int | None)`.

- [ ] **Step 1: Convert tenant dependencies**

`src/core/dependency/tenant.py` — full new content:

```python
from fastapi import HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST


def get_current_tenant_id(request: Request) -> int:
    tenant_id: int | None = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Tenant not identified",
        )
    return tenant_id


def get_optional_tenant_id(request: Request) -> int | None:
    return getattr(request.state, "tenant_id", None)
```

- [ ] **Step 2: Convert the tenant middleware**

`src/core/middleware/tenant.py`:
- Remove `from uuid import UUID`.
- `_default_tenant_id: int | None = None`; `set_default_tenant_id(tenant_id: int) -> None`.
- Line 74: `request.state.tenant_id = UUID(tid) if isinstance(tid, str) else tid` → `request.state.tenant_id = int(tid) if isinstance(tid, str) else tid`.

- [ ] **Step 3: Convert the auth dependency**

`src/core/dependency/auth.py`:
- Remove `from uuid import UUID`.
- `tenant_id: UUID | None = Depends(get_optional_tenant_id)` → `tenant_id: int | None = Depends(get_optional_tenant_id)`.
- Line 40: `user = await repo.get_by_id(UUID(user_id))` → `user = await repo.get_by_id(int(user_id))`.

- [ ] **Step 4: Convert UoW and session**

`src/core/database/unit_of_work.py`: remove UUID import; `__init__(self, session, tenant_id: int | None = None)`.

`src/core/database/postgres/session.py`: remove UUID import; `tenant_id: int | None = Depends(get_optional_tenant_id)`.

`src/core/security/infrastructure/repositories/login_attempt_repository.py`: remove UUID import; `__init__(self, db, tenant_id: int | None = None)`.

- [ ] **Step 5: Run tests**

Run: `make test`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/core/dependency/auth.py src/core/dependency/tenant.py src/core/middleware/tenant.py src/core/database src/core/security/infrastructure/repositories
git commit -m "refactor: core dependencies parse integer ids"
```

---

### Task 12: Seeds → int

**Files:**
- Modify: `src/core/seed/tenant.py`

**Interfaces:**
- Consumes: int `TenantModel.id` (identity).
- Produces: default tenant created without explicit id; `set_default_tenant_id(tenant.id)` with int.

- [ ] **Step 1: Convert the tenant seed**

`src/core/seed/tenant.py` — full new content:

```python
from sqlalchemy import select

from src.core.config.setting import get_settings
from src.core.database.postgres.session import AsyncSessionLocal
from src.core.middleware.tenant import set_default_tenant_id
from src.modules.tenants.infrastructure.models.tenant_model import TenantModel

DEFAULT_TENANT_SLUG = "default"


async def seed_default_tenant() -> None:
    settings = get_settings()
    if settings.MULTITENANT_ENABLED:
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TenantModel).where(TenantModel.slug == DEFAULT_TENANT_SLUG)
        )
        existing = result.scalar_one_or_none()
        if existing:
            set_default_tenant_id(existing.id)
            return

        tenant = TenantModel(
            name="Default Tenant",
            slug=DEFAULT_TENANT_SLUG,
            domain=None,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        set_default_tenant_id(tenant.id)
```

(`seed/user.py` and `seed/authorization.py` need no changes — they use entity factories and `str(saved_user.id)` subjects which work with ints.)

- [ ] **Step 2: Run tests**

Run: `make test`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/core/seed/tenant.py
git commit -m "refactor: tenant seed relies on database-assigned integer id"
```

---

### Task 13: Module facade pattern

**Files:**
- Create: `src/shared/facade.py`
- Create: `src/modules/user/facade.py`
- Delete: `src/modules/user/providers.py`
- Modify: `src/modules/user/__init__.py`
- Rename: `src/core/dependency/providers.py` → `src/core/dependency/facades.py`
- Modify: `src/modules/todo/presentation/dependency.py`
- Modify: `src/modules/todo/application/detail_todo/handler.py`
- Modify: `.importlinter`

**Interfaces:**
- Produces: `ModuleFacade` (abstract base, `src/shared/facade.py`); `UserModuleFacade(ModuleFacade)` with `get_user_profile(user_id: int) -> UserProfile | None`, `UserProfile(id: int, email: str, username: str | None)`; `get_user_module_facade` DI factory in `src/core/dependency/facades.py`; consumers type against `UserModuleFacade`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_user_facade.py`:

```python
import asyncio

from src.modules.user.domain.entities.user import User
from src.modules.user.facade import UserModuleFacade


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def get_by_id(self, user_id: int) -> User | None:
        if self._user is None or self._user.id != user_id:
            return None
        return self._user


def test_facade_returns_profile_with_int_id():
    facade = UserModuleFacade(FakeUserRepository(
        User(id=7, email="a@example.com", password_hash="x", username="alice")
    ))
    profile = asyncio.run(facade.get_user_profile(7))
    assert profile is not None
    assert profile.id == 7
    assert profile.email == "a@example.com"
    assert profile.username == "alice"


def test_facade_returns_none_for_unknown_user():
    facade = UserModuleFacade(FakeUserRepository(None))
    assert asyncio.run(facade.get_user_profile(99)) is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `make test -k user_facade`
Expected: FAIL (`ModuleNotFoundError: src.modules.user.facade`)

- [ ] **Step 3: Create the shared facade base**

Create `src/shared/facade.py`:

```python
from abc import ABC


class ModuleFacade(ABC):
    """Public contract a module exposes for cross-module communication.

    Other modules depend only on a module's facade — never on its
    application, domain, or infrastructure internals.
    """
```

- [ ] **Step 4: Create the user module facade**

Create `src/modules/user/facade.py`:

```python
from pydantic import BaseModel

from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.facade import ModuleFacade


class UserProfile(BaseModel):
    id: int
    email: str
    username: str | None = None


class UserModuleFacade(ModuleFacade):
    def __init__(self, user_repository: UserRepository):
        self._user_detail_query = DetailUserQueryHandler(
            user_repository=user_repository
        )

    async def get_user_profile(self, user_id: int) -> UserProfile | None:
        user = await self._user_detail_query.execute(
            DetailUserQuery(user_id=user_id)
        )
        if user is None:
            return None

        return UserProfile(
            id=user.id,
            email=user.email,
            username=user.username,
        )
```

- [ ] **Step 5: Update `src/modules/user/__init__.py`**

```python
from src.modules.user.domain.exceptions.user_exception import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.modules.user.facade import UserProfile

__all__ = [
    "UserProfile",
    "UserAlreadyExistsError",
    "UserNotFoundError",
]
```

- [ ] **Step 6: Delete the old provider and rename the DI module**

```bash
git rm src/modules/user/providers.py
git mv src/core/dependency/providers.py src/core/dependency/facades.py
```

`src/core/dependency/facades.py` — full new content:

```python
from fastapi import Depends

from src.core.database.postgres.session import get_unit_of_work
from src.modules.user.facade import UserModuleFacade
from src.shared.unit_of_work import UnitOfWork


def get_user_module_facade(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserModuleFacade:
    return UserModuleFacade(user_repository=uow.users)
```

- [ ] **Step 7: Update todo consumers**

`src/modules/todo/presentation/dependency.py`:
- Line 8: `from src.core.dependency.providers import get_user_module_provider` → `from src.core.dependency.facades import get_user_module_facade`
- Line 22: `from src.modules.user.providers import UserModuleProvider` → `from src.modules.user.facade import UserModuleFacade`
- Line 56: `user_provider: UserModuleProvider = Depends(get_user_module_provider)` → `user_facade: UserModuleFacade = Depends(get_user_module_facade)`
- Line 58: `return GetTodoDetailWithOwnerHandler(todo_repo, user_provider=user_facade)`

`src/modules/todo/application/detail_todo/handler.py`:
- Line 10: `from src.modules.user.providers import UserModuleProvider` → `from src.modules.user.facade import UserModuleFacade`
- Line 17: `user_provider: UserModuleProvider` → `user_facade: UserModuleFacade`
- Line 20: `self._user_provider = user_provider` → `self._user_facade = user_facade`
- Line 31: `owner = await self._user_provider.get_user_profile(todo.user_id)` → `owner = await self._user_facade.get_user_profile(todo.user_id)`

- [ ] **Step 8: Update `.importlinter`**

Keep all existing contracts (they forbid todo/user/authorization from importing each other's `application`/`domain`/`infrastructure`/`presentation`, which still holds — the facade lives at the module root). Add `src.modules.user.providers` to the `forbidden_modules` of the `todo-cross-module-boundary` contract so the removed provider path is explicitly banned:

```toml
forbidden_modules =
    src.modules.user.providers
    src.modules.user.application
    src.modules.user.domain
    src.modules.user.infrastructure
    src.modules.user.presentation
```

- [ ] **Step 9: Run tests + import linter**

Run: `make test && make lint-imports`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add -A src/shared/facade.py src/modules/user/facade.py src/modules/user/__init__.py src/core/dependency/facades.py src/modules/todo tests/test_user_facade.py .importlinter
git commit -m "refactor: replace user provider with module facade pattern"
```

---

### Task 14: Alembic migration — in-place UUID → int conversion

**Files:**
- Create: `alembic/versions/c1d2e3f4a5b6_convert_ids_to_integer.py`

**Interfaces:**
- Consumes: `down_revision = '8efb2c8c7b20'` (head before this change).
- Produces: revision `c1d2e3f4a5b6` converting every table PK/FK from UUID to INTEGER identity, preserving data and FK relationships; downgrade re-creates UUID columns with freshly generated uuids and remaps FKs.

- [ ] **Step 1: Write the failing migration test (smoke check)**

No automated migration test exists; verification is manual against PostgreSQL. Start docker DB:

```bash
make db-up
sleep 5
make migrate
```

Expected before writing the migration: migration applies cleanly (no-op — no new revision yet). This step confirms the toolchain works before the change.

- [ ] **Step 2: Create the migration**

Create `alembic/versions/c1d2e3f4a5b6_convert_ids_to_integer.py` with this content:

```python
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


def _convert_pk(bind, table: str) -> None:
    """Add _id integer identity column, backfill via row_number over the
    old uuid PK, drop the uuid PK, rename."""
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
    op.execute(sa.text(
        f'ALTER TABLE {table} DROP CONSTRAINT {table}_pkey'
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
    op.execute(sa.text(f'ALTER TABLE {child} ADD COLUMN _fk INTEGER'))
    op.execute(sa.text(
        f'UPDATE {child} SET _fk = sub.rn FROM '
        f'(SELECT id, row_number() OVER (ORDER BY id) AS rn FROM {parent}) AS sub '
        f'WHERE {child}.{column} = sub.id'
    ))
    fk_name = _fk_constraint_name(bind, child, column)
    if fk_name:
        op.execute(sa.text(f'ALTER TABLE {child} DROP CONSTRAINT {fk_name}'))
    op.execute(sa.text(f'ALTER TABLE {child} DROP COLUMN {column}'))
    op.execute(sa.text(f'ALTER TABLE {child} RENAME COLUMN _fk TO {column}'))
    op.execute(sa.text(
        f'ALTER TABLE {child} ADD CONSTRAINT {child}_{column}_fkey '
        f'FOREIGN KEY ({column}) REFERENCES {parent} (id)'
    ))


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
        _convert_pk(bind, table)

    # api_keys may exist in dev databases even though it has no migration
    if 'api_keys' in tables:
        _convert_pk(bind, 'api_keys')
        _convert_fk(bind, 'api_keys', 'tenant_id', 'tenants')


def _restore_pk(bind, table: str) -> None:
    """Downgrade: recreate the uuid PK, remap children back."""
    op.execute(sa.text(f'ALTER TABLE {table} ADD COLUMN _old_id UUID DEFAULT gen_random_uuid()'))
    op.execute(sa.text(
        f'UPDATE {table} SET _old_id = sub.u FROM '
        f'(SELECT id, gen_random_uuid() AS u FROM {table}) AS sub '
        f'WHERE {table}.id = sub.id'
    ))
    op.execute(sa.text(f'ALTER TABLE {table} DROP CONSTRAINT {table}_pkey'))
    op.execute(sa.text(f'ALTER TABLE {table} DROP COLUMN id'))
    op.execute(sa.text(f'ALTER TABLE {table} RENAME COLUMN _old_id TO id'))
    op.execute(sa.text(f'ALTER TABLE {table} ADD PRIMARY KEY (id)'))


def _restore_fk(bind, child: str, column: str, parent: str) -> None:
    op.execute(sa.text(f'ALTER TABLE {child} ADD COLUMN _fk UUID DEFAULT gen_random_uuid()'))
    op.execute(sa.text(
        f'UPDATE {child} SET _fk = sub.id FROM '
        f'(SELECT id FROM {parent}) AS sub'
    ))
    op.execute(sa.text(f'ALTER TABLE {child} DROP COLUMN {column}'))
    op.execute(sa.text(f'ALTER TABLE {child} RENAME COLUMN _fk TO {column}'))
    op.execute(sa.text(
        f'ALTER TABLE {child} ADD CONSTRAINT {child}_{column}_fkey '
        f'FOREIGN KEY ({column}) REFERENCES {parent} (id)'
    ))


def downgrade() -> None:
    bind = op.get_bind()
    tables = _columns(bind)

    for table in reversed(TABLES):
        if table == 'tenants' or table not in tables:
            continue
        _restore_pk(bind, table)
        for fk_column, parent in FK_MAP.get(table, []):
            if parent in tables:
                _restore_fk(bind, table, fk_column, parent)

    if 'tenants' in tables:
        _restore_pk(bind, 'tenants')

    if 'api_keys' in tables:
        _restore_pk(bind, 'api_keys')
        _restore_fk(bind, 'api_keys', 'tenant_id', 'tenants')
```

> Note: the downgrade remaps FKs by a 1:1 cross-join in `_restore_fk` — this is only valid for single-row or already-aligned test data. For realistic downgrades with production data, restore the exact UUID→int mapping (see "Data-preserving downgrade" note below) before relying on it.

**Data-preserving downgrade (recommended for real data):** to restore the original UUIDs, store them during upgrade instead of generating new ones. In `_convert_pk`, before dropping the uuid column, create a shadow table:

```python
    op.execute(sa.text(
        f'CREATE TABLE IF NOT EXISTS _legacy_ids (table_name TEXT, legacy_uuid UUID, new_id INTEGER)'
    ))
    op.execute(sa.text(
        f'INSERT INTO _legacy_ids (table_name, legacy_uuid, new_id) '
        f'SELECT \'{table}\', id, _id FROM {table}'
    ))
```

and in `_restore_pk` backfill `_old_id` from `_legacy_ids`:

```sql
UPDATE {table} SET _old_id = l.legacy_uuid
FROM _legacy_ids l WHERE l.table_name = '{table}' AND l.new_id = {table}.id;
```

- [ ] **Step 3: Apply the migration**

```bash
make migrate
```

Expected: applies cleanly; `alembic current` shows `c1d2e3f4a5b6 (head)`.

- [ ] **Step 4: Verify schema**

```bash
.venv/bin/alembic upgrade head
.venv/bin/python - <<'EOF'
import asyncio
from sqlalchemy import inspect, text
from src.core.database.postgres.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        rows = (await s.execute(text(
            "SELECT table_name, data_type FROM information_schema.columns "
            "WHERE column_name = 'id' ORDER BY table_name"
        ))).all()
        for table, dtype in rows:
            print(f"{table}: {dtype}")

asyncio.run(main())
EOF
```

Expected: every table's `id` column reports `integer`.

- [ ] **Step 5: Test the in-place conversion with existing data**

With the DB still running, seed data using the pre-conversion branch behavior is not possible on a fresh DB — instead insert a realistic UUID FK graph manually before running the migration, by reverting to `8efb2c8c7b20` first:

```bash
.venv/bin/alembic downgrade 8efb2c8c7b20
.venv/bin/python - <<'EOF'
import asyncio
from sqlalchemy import text
from src.core.database.postgres.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, name, slug) VALUES "
            "('11111111-1111-1111-1111-111111111111', 't1', 't1')"
        ))
        await s.execute(text(
            "INSERT INTO users (id, email, password_hash, tenant_id) VALUES "
            "('22222222-2222-2222-2222-222222222222', 'a@b.c', 'h', '11111111-1111-1111-1111-111111111111')"
        ))
        await s.execute(text(
            "INSERT INTO todos (id, title, user_id, tenant_id) VALUES "
            "('33333333-3333-3333-3333-333333333333', 't', '22222222-2222-2222-2222-222222222222', "
            "'11111111-1111-1111-1111-111111111111')"
        ))
        await s.commit()

asyncio.run(main())
EOF
.venv/bin/alembic upgrade head
.venv/bin/python - <<'EOF'
import asyncio
from sqlalchemy import text
from src.core.database.postgres.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        result = await s.execute(text(
            "SELECT u.id, t.id, t.user_id FROM users u "
            "JOIN todos t ON t.user_id = u.id "
            "JOIN tenants ten ON u.tenant_id = ten.id "
            "WHERE u.email = 'a@b.c'"
        ))
        row = result.one()
        assert isinstance(row[0], int) and isinstance(row[1], int) and isinstance(row[2], int), row
        assert row[2] == row[0]  # FK still points at the user's new id
        print("FK integrity preserved:", row)

asyncio.run(main())
EOF
```

Expected: all ids are ints and the todo→user FK still resolves.

- [ ] **Step 6: Verify downgrade**

```bash
.venv/bin/alembic downgrade 8efb2c8c7b20 && .venv/bin/alembic upgrade head
```

Expected: both run cleanly (downgrade generates fresh UUIDs; re-upgrade converts again).

- [ ] **Step 7: Commit**

```bash
git add alembic/versions/c1d2e3f4a5b6_convert_ids_to_integer.py
git commit -m "feat: alembic migration converting uuid ids to integer"
```

---

### Task 15: Test sweep and full verification

**Files:**
- Modify: `tests/test_user_seed.py` (if needed — verify)
- Run full verification

- [ ] **Step 1: Verify `tests/test_user_seed.py`**

`test_seed_user_does_not_modify_an_existing_user` constructs `User(id=uuid4(), ...)` (line 122) — replace `from uuid import uuid4` and `id=uuid4()` with `id=1`:

```python
    existing_user = User(
        id=1,
        email="admin@example.com",
        password_hash="existing-hash",
        username="existing-admin",
    )
```

- [ ] **Step 2: Sweep for leftover UUID id usages**

Run: `rg -n "UUID\(|uuid4\(\)" src --type py`
Expected: only remaining matches are `shared/events/base.py` (`event_id`, `uuid4`), `core/security/audit.py` (`id: UUID`, `uuid4`), `core/middleware/request_id.py` (`uuid4`), `core/security/jwt.py` (`jti`). All are intentional (correlation ids).

- [ ] **Step 3: Full verification**

```bash
make check
make lint-imports
.venv/bin/mypy src
```

Expected: tests pass, ruff clean, import-linter contracts pass, mypy clean.

- [ ] **Step 4: Commit any remaining test changes**

```bash
git add tests
git commit -m "test: update tests for integer ids"
```

- [ ] **Step 5: Final smoke test**

```bash
make db-up && make migrate && make seed
```

Expected: migrations apply, seeders run (admin + dev users created with int ids, roles assigned via `user:<int>` subjects).

---

## Self-Review Notes

- **Spec coverage:** every spec item maps to a task — int convention (Tasks 1-12), migration (14), event UUID keeps (Task 15 step 2), facade (13), import-linter (13 step 8), tests (Tasks 1, 2, 4, 15).
- **Type consistency:** `ModuleFacade`/`UserModuleFacade`/`UserProfile(id: int)` consistent across Task 13 steps; `DetailUserQuery(user_id: int)` matches facade usage; `User.tenant_id` added in Task 6 (needed by `save()`); `Todo` dataclass defaults reordered to keep `id` first.
- **Casbin subjects:** `int(subject)` in Task 9 step 4 matches `str(user.id)` subjects produced in Tasks 7 and 12.
