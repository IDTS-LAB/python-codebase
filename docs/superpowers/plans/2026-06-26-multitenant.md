# Multitenant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add optional multitenant support with tenant_id column on all tables and a composite tenant resolution middleware.

**Architecture:** Shared DB with tenant_id FK on every table. TenantMixin on all models. TenantMiddleware resolves via X-Tenant-ID header → subdomain → JWT claim. Repositories receive tenant_id at construction via FastAPI dependency.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL

---

### Task 1: Settings & Env

**Files:**
- Modify: `src/core/config/setting.py:8`
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Add MULTITENANT_ENABLED to Settings**

Edit `src/core/config/setting.py`, add after `LOG_FORMAT` (around line 78):

```python
    # Multitenancy toggle.
    MULTITENANT_ENABLED: bool = Field(
        alias="MULTITENANT_ENABLED", default=False
    )
```

- [ ] **Step 2: Add to .env and .env.example**

Append to `.env`:
```
MULTITENANT_ENABLED=false
```

Append to `.env.example`:
```
# Enable multitenant isolation.
# When false, all data uses a single "Default" tenant.
MULTITENANT_ENABLED=false
```

- [ ] **Step 3: Commit**

```bash
git add src/core/config/setting.py .env .env.example
git commit -m "feat: add MULTITENANT_ENABLED config"
```

---

### Task 2: TenantMixin & Base Model

**Files:**
- Create: `src/shared/database/mixin/tenant.py`
- Modify: `src/shared/database/model.py:7`

- [ ] **Step 1: Create TenantMixin**

Write `src/shared/database/mixin/tenant.py`:

```python
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        sort_order=-60,
    )
```

- [ ] **Step 2: Update shared database model imports**

Edit `src/shared/database/model.py` to re-export `TenantMixin`:

```python
from src.shared.database.mixin.tenant import TenantMixin  # noqa: F401
```

Add after the existing imports (after `from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column`).

- [ ] **Step 3: Commit**

```bash
git add src/shared/database/mixin/tenant.py src/shared/database/model.py
git commit -m "feat: add TenantMixin"
```

---

### Task 3: Tenant Module (Model, Entity, Repository)

**Files:**
- Create: `src/modules/tenants/__init__.py`
- Create: `src/modules/tenants/domain/__init__.py`
- Create: `src/modules/tenants/domain/entities/__init__.py`
- Create: `src/modules/tenants/domain/entities/tenant.py`
- Create: `src/modules/tenants/domain/repositories/__init__.py`
- Create: `src/modules/tenants/domain/repositories/tenant_repository.py`
- Create: `src/modules/tenants/infrastructure/__init__.py`
- Create: `src/modules/tenants/infrastructure/models/__init__.py`
- Create: `src/modules/tenants/infrastructure/models/tenant_model.py`
- Create: `src/modules/tenants/infrastructure/repositories/__init__.py`
- Create: `src/modules/tenants/infrastructure/repositories/tenant_repository.py`
- Create: `src/modules/tenants/presentation/__init__.py`
- Create: `src/modules/tenants/presentation/dependencies.py`
- Create: `src/modules/tenants/presentation/schemas.py`

- [ ] **Step 1: Create all directory __init__.py files**

Create empty `__init__.py` files for all tenant module subdirectories.

- [ ] **Step 2: Write the Tenant domain entity**

`src/modules/tenants/domain/entities/tenant.py`:

```python
from uuid import UUID


class Tenant:
    def __init__(
        self,
        id: UUID,
        name: str,
        slug: str,
        domain: str | None = None,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.domain = domain
```

- [ ] **Step 3: Write the Tenant repository interface**

`src/modules/tenants/domain/repositories/tenant_repository.py`:

```python
from uuid import UUID

from src.modules.tenants.domain.entities.tenant import Tenant


class TenantRepository:
    async def get_by_slug(self, slug: str) -> Tenant | None: ...
    async def get_by_domain(self, domain: str) -> Tenant | None: ...
    async def get_by_id(self, tenant_id: UUID) -> Tenant | None: ...
    async def save(self, tenant: Tenant) -> Tenant: ...
```

- [ ] **Step 4: Write the Tenant SQLAlchemy model**

`src/modules/tenants/infrastructure/models/tenant_model.py`:

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class TenantModel(Base, TimeStampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
```

- [ ] **Step 5: Write the SQLAlchemy repository**

`src/modules/tenants/infrastructure/repositories/tenant_repository.py`:

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tenants.domain.entities.tenant import Tenant
from src.modules.tenants.domain.repositories.tenant_repository import TenantRepository
from src.modules.tenants.infrastructure.models.tenant_model import TenantModel


class SQLAlchemyTenantRepository(TenantRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_domain(self, domain: str) -> Tenant | None:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.domain == domain)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, tenant: Tenant) -> Tenant:
        existing = None
        if tenant.id:
            existing = await self.get_by_id(tenant.id)

        if existing:
            model = await self._get_model(tenant.id)
            model.name = tenant.name
            model.slug = tenant.slug
            model.domain = tenant.domain
        else:
            model = TenantModel(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                domain=tenant.domain,
            )
            self._db.add(model)

        await self._db.flush()
        await self._db.refresh(model)
        return self._to_entity(model)

    async def _get_model(self, tenant_id: UUID) -> TenantModel:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        return result.scalar_one()

    def _to_entity(self, model: TenantModel) -> Tenant:
        return Tenant(
            id=model.id,
            name=model.name,
            slug=model.slug,
            domain=model.domain,
        )
```

- [ ] **Step 6: Write tenant dependencies**

`src/modules/tenants/presentation/dependencies.py`:

```python
from fastpi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgres.session import get_db
from src.modules.tenants.domain.repositories.tenant_repository import TenantRepository
from src.modules.tenants.infrastructure.repositories.tenant_repository import (
    SQLAlchemyTenantRepository,
)


def get_tenant_repository(
    db: AsyncSession = Depends(get_db),
) -> TenantRepository:
    return SQLAlchemyTenantRepository(db)
```

- [ ] **Step 7: Write tenant schemas**

`src/modules/tenants/presentation/schemas.py`:

```python
from uuid import UUID

from pydantic import BaseModel


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 8: Commit**

```bash
git add src/modules/tenants/
git commit -m "feat: add tenants module with model, entity, repository"
```

---

### Task 4: Tenant Middleware

**Files:**
- Create: `src/core/middleware/tenant.py`

- [ ] **Step 1: Write TenantMiddleware**

`src/core/middleware/tenant.py`:

```python
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.config.setting import get_settings

settings = get_settings()
_default_tenant_id: UUID | None = None


def set_default_tenant_id(tenant_id: UUID) -> None:
    global _default_tenant_id
    _default_tenant_id = tenant_id


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not settings.MULTITENANT_ENABLED:
            request.state.tenant_id = _default_tenant_id
            return await call_next(request)

        tenant_id: UUID | None = None

        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            from src.core.database.postgres.session import AsyncSessionLocal
            from src.modules.tenants.infrastructure.models.tenant_model import TenantModel
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TenantModel.id).where(TenantModel.slug == tenant_header)
                )
                tenant_id = result.scalar_one_or_none()
            if tenant_id:
                request.state.tenant_id = tenant_id
                return await call_next(request)

        host = request.headers.get("host", "")
        if "." in host and host.count(".") >= 2:
            subdomain = host.split(".")[0]
            from src.core.database.postgres.session import AsyncSessionLocal
            from src.modules.tenants.infrastructure.models.tenant_model import TenantModel
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TenantModel.id).where(TenantModel.domain == host)
                )
                tenant_id = result.scalar_one_or_none()
            if tenant_id:
                request.state.tenant_id = tenant_id
                return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            from jose import jwt as jose_jwt

            try:
                payload = jose_jwt.decode(
                    auth_header.split(" ", 1)[1],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                    options={"verify_aud": False, "verify_sub": False},
                )
                tid = payload.get("tenant_id")
                if tid:
                    request.state.tenant_id = UUID(tid)
                    return await call_next(request)
            except Exception:
                pass

        return JSONResponse(
            status_code=400,
            content={"detail": "Tenant not identified. Provide X-Tenant-ID header."},
        )
```

- [ ] **Step 2: Commit**

```bash
git add src/core/middleware/tenant.py
git commit -m "feat: add TenantMiddleware for header/subdomain/JWT resolution"
```

---

### Task 5: Tenant Dependency & Middleware Registration

**Files:**
- Create: `src/core/dependency/tenant.py`
- Modify: `src/core/bootstrap/middleware.py:46`

- [ ] **Step 1: Create tenant dependency**

`src/core/dependency/tenant.py`:

```python
from uuid import UUID

from fastapi import HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST


def get_current_tenant_id(request: Request) -> UUID:
    tenant_id: UUID | None = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Tenant not identified",
        )
    return tenant_id


def get_optional_tenant_id(request: Request) -> UUID | None:
    return getattr(request.state, "tenant_id", None)
```

- [ ] **Step 2: Register middleware**

Edit `src/core/bootstrap/middleware.py`, import TenantMiddleware and register it.
Add import: `from src.core.database.postgres.session import engine`
and `from src.core.middleware.tenant import TenantMiddleware`.

Register after `RequestIDMiddleware` (last middleware):

```python
    app.add_middleware(TenantMiddleware)
```

- [ ] **Step 3: Commit**

```bash
git add src/core/dependency/tenant.py src/core/bootstrap/middleware.py
git commit -m "feat: add tenant dependency and register TenantMiddleware"
```

---

### Task 6: Seed Default Tenant

**Files:**
- Create: `src/core/seed/tenant.py`
- Modify: `src/core/lifespan.py`

- [ ] **Step 1: Create seed module**

`src/core/seed/tenant.py`:

```python
from uuid import uuid4

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
            id=uuid4(),
            name="Default Tenant",
            slug=DEFAULT_TENANT_SLUG,
            domain=None,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        set_default_tenant_id(tenant.id)
```

- [ ] **Step 2: Call from lifespan**

Edit `src/core/lifespan.py`, add import and call in lifespan:

```python
from src.core.seed.tenant import seed_default_tenant
```

Add `await seed_default_tenant()` after `register_event_handlers()`.

- [ ] **Step 3: Commit**

```bash
git add src/core/seed/tenant.py src/core/lifespan.py
git commit -m "feat: seed default tenant on startup and set as fallback"
```

---

### Task 7: Add TenantMixin to All Models

**Files:**
- Modify: All model files to inherit `TenantMixin`
- Modify: `alembic/env.py` to import TenantModel

Models to update:
- `src/modules/user/infrastructure/models/user_model.py`
- `src/modules/user/infrastructure/models/user_profile_model.py`
- `src/modules/user/infrastructure/models/user_security_model.py`
- `src/modules/user/infrastructure/models/user_settings_model.py`
- `src/modules/user/infrastructure/models/user_contact_model.py`
- `src/modules/user/infrastructure/models/user_address_model.py`
- `src/modules/user/infrastructure/models/user_verification_model.py`
- `src/modules/user/infrastructure/models/user_session_model.py` (check if exists)
- `src/modules/user/infrastructure/models/refresh_token_model.py`
- `src/modules/todo/infrastructure/models/todo_model.py`
- `src/modules/authorization/infrastructure/models/permission_model.py`
- `src/modules/authorization/infrastructure/models/role_model.py`
- `src/modules/authorization/infrastructure/models/resource_model.py`
- `src/modules/authorization/infrastructure/models/user_has_role_model.py`
- `src/modules/authorization/infrastructure/models/role_permission_model.py`
- `src/modules/authorization/infrastructure/models/casbin_rule_model.py`
- `src/modules/api_key/infrastructure/models/__init__.py` (ApiKeyModel)
- `src/core/security/infrastructure/models/audit_log_model.py`
- `src/core/security/infrastructure/models/error_trace_model.py`
- `src/core/security/infrastructure/models/login_attempt_model.py`

For each model, add `TenantMixin` as a base class and import it.

Example for UserModel (after `SoftDeleteMixin`):

```python
from src.shared.database.mixin.tenant import TenantMixin


class UserModel(
    Base,
    TimeStampMixin,
    SoftDeleteMixin,
    TenantMixin,
):
```

This pattern applies to all models.

- [ ] **Step 1: Find all model files and verify list**

Run: `find src -name "*model*.py" | sort`

- [ ] **Step 2-20: Update each model file to add TenantMixin**

For every model file, add `from src.shared.database.mixin.tenant import TenantMixin` and add `TenantMixin` to the class bases.

- [ ] **Step 21: Update alembic/env.py**

Add import:
```python
from src.modules.tenants.infrastructure.models.tenant_model import TenantModel  # noqa: F401
```

- [ ] **Step 22: Commit**

```bash
git add src/modules/user/infrastructure/models/ src/modules/todo/infrastructure/models/ src/modules/authorization/infrastructure/models/ src/modules/api_key/infrastructure/models/ src/core/security/infrastructure/models/ alembic/env.py
git commit -m "feat: add TenantMixin to all models"
```

---

### Task 8: Add tenant_id Filtering to Repositories

**Files:**
- Modify: `src/modules/user/infrastructure/repositories/user_repository.py`
- Modify: `src/modules/user/infrastructure/repositories/refresh_token_repository.py`
- Modify: `src/modules/todo/infrastructure/repositories/todo_repository.py`
- Modify: `src/modules/api_key/infrastructure/repositories/...` (check)
- Modify: `src/core/security/infrastructure/repositories/audit_log_repository.py`
- Modify: `src/core/security/infrastructure/repositories/login_attempt_repository.py`

For each repository:
1. Add `tenant_id: UUID` parameter to `__init__`
2. Store as `self._tenant_id`
3. Add `.where(Model.tenant_id == self._tenant_id)` to every query
4. Set `tenant_id` on new model instances

Example for TodoRepository:

```python
from uuid import UUID

class SQLAlchemyTodoRepository(TodoRepository):
    def __init__(self, db: AsyncSession, tenant_id: UUID | None = None):
        self._db = db
        self._tenant_id = tenant_id

    async def get_by_id(self, todo_id: UUID) -> Optional[Todo]:
        stmt = select(TodoModel).where(TodoModel.id == todo_id)
        if self._tenant_id:
            stmt = stmt.where(TodoModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        ...
```

- [ ] **Step 1-7: Update each repository with tenant_id parameter and filtering**

- [ ] **Step 8: Commit**

```bash
git add src/modules/user/infrastructure/repositories/ src/modules/todo/infrastructure/repositories/ src/modules/api_key/infrastructure/repositories/ src/core/security/infrastructure/repositories/
git commit -m "feat: add tenant_id filtering to repositories"
```

---

### Task 9: Update Dependency Factory Functions

**Files:**
- Modify: `src/modules/user/presentation/dependency.py`
- Modify: `src/modules/todo/presentation/dependency.py`
- Modify: `src/modules/authorization/presentation/dependency.py`
- Modify: `src/modules/api_key/presentation/dependencies.py`

Each factory function that creates a repository needs to pass tenant_id. Add:

```python
from src.core.dependency.tenant import get_current_tenant_id

def get_user_repository(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> UserRepository:
    return SQLAlchemyUserRepository(db, tenant_id)
```

- [ ] **Step 1-4: Update each dependency file**

- [ ] **Step 5: Commit**

```bash
git add src/modules/user/presentation/dependency.py src/modules/todo/presentation/dependency.py src/modules/authorization/presentation/dependency.py src/modules/api_key/presentation/dependencies.py
git commit -m "feat: pass tenant_id to repository factories"
```

---

### Task 10: Alembic Migration

**Files:**
- Create: `alembic/versions/xxxx_add_multitenant.py`

- [ ] **Step 1: Generate migration**

Run: `alembic revision --autogenerate -m "add multitenant support"`

If autogenerate doesn't work well, write manually.

- [ ] **Step 2: Verify migration content**

Check that the migration creates `tenants` table and adds `tenant_id` to all existing tables.

- [ ] **Step 3: Commit**

```bash
git add alembic/versions/
git commit -m "feat: add alembic migration for multitenant schema"
```

---

### Task 11: Verify

- [ ] **Step 1: Run lint**

Run: `ruff check src/`

- [ ] **Step 2: Run type check**

Run: `mypy src/`

- [ ] **Step 3: Run existing tests**

Run: `pytest tests/ -v`

- [ ] **Step 4: Fix any issues**
