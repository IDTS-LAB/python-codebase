# Multitenant Support Design

## Overview

Add multitenant support to the FastAPI modulith project using a shared-database strategy.
A `tenant_id` column is added to all tenant-scoped tables, and a tenant resolution middleware
identifies the active tenant from the request (header, subdomain, or JWT claim).

Multitenancy is controlled by the `MULTITENANT_ENABLED` environment variable. When disabled,
a single "Default" tenant is used and no filtering occurs.

## Tenant Isolation Strategy

- **Type**: Shared database with `tenant_id` foreign key column on all tenant-scoped tables.
- **Toggle**: `MULTITENANT_ENABLED` env var (default `false`). When disabled, all data
  belongs to a single "Default" tenant created at seed time.
- **Scope**: All modules (user, todo, authorization, api_key) are tenant-scoped.

## Tenant Resolution

Middleware resolves the tenant by trying each method in order:

1. **`X-Tenant-ID` header** — lookup tenant by slug or ID.
2. **Subdomain** — lookup `tenants.domain` matching the request's subdomain.
3. **JWT `tenant_id` claim** — for authenticated requests, read from token payload.

If no tenant can be resolved, the request receives a `400 Bad Request`.

Resolved `tenant_id` is stored in `request.state.tenant_id`.

## Data Model

### New: `tenants` table

| Column      | Type         | Constraints      |
|-------------|--------------|------------------|
| id          | UUID         | PK               |
| name        | String(255)  | NOT NULL          |
| slug        | String(100)  | UNIQUE, NOT NULL  |
| domain      | String(255)  | UNIQUE, NULLABLE  |
| created_at  | DateTime(tz) | server default    |
| updated_at  | DateTime(tz) | server default    |
| deleted_at  | DateTime     | NULLABLE          |

### New: `TenantMixin`

A SQLAlchemy mixin adding:

```python
tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
```

### Modified: All tenant-scoped models

All models in `user`, `todo`, `authorization`, and `api_key` modules inherit `TenantMixin`.

### New: `DefaultTenantEntity`

A singleton entity that represents the fallback tenant when multitenancy is disabled.

## Components

### New Module: `src/modules/tenants/`

- `infrastructure/models/tenant_model.py` — `TenantModel` (SQLAlchemy model)
- `domain/entities/tenant.py` — `Tenant` domain entity
- `domain/repositories/tenant_repository.py` — `TenantRepository` interface
- `infrastructure/repositories/tenant_repository.py` — `SQLAlchemyTenantRepository`

### New: `src/shared/database/mixin/tenant.py`

`TenantMixin` class with `tenant_id` column definition.

### New: `src/core/middleware/tenant.py`

`TenantMiddleware` — resolves tenant from header/subdomain/JWT and sets
`request.state.tenant_id`.

### New: `src/core/dependency/tenant.py`

FastAPI dependency `get_current_tenant_id()` — reads from `request.state.tenant_id`.

### New: `src/core/seed/tenant.py`

Seeds a "Default" tenant when `MULTITENANT_ENABLED=False`.

## Modified Files

| File | Change |
|------|--------|
| `src/core/config/setting.py` | Add `MULTITENANT_ENABLED: bool = False` |
| `src/shared/database/model.py` | Export `TenantMixin` |
| `src/core/bootstrap/middleware.py` | Register `TenantMiddleware` |
| `src/core/lifespan.py` | Seed default tenant on startup |
| `.env` / `.env.example` | Add `MULTITENANT_ENABLED` |
| `alembic/env.py` | Import `TenantModel` |
| All model classes | Add `TenantMixin` as base class |

## Repository Changes

Each repository gets the tenant context through a new parameter or via a dependency.
The tenant ID is applied as a filter in every query:

```python
async def get_by_email(self, email: str, tenant_id: UUID) -> Optional[User]:
    result = await self._db.execute(
        select(UserModel).where(
            UserModel.email == email,
            UserModel.tenant_id == tenant_id,
        )
    )
```

Repositories that create records also set `tenant_id` on the model.

## Migration Plan

1. Create `tenants` table
2. Seed a "Default" tenant row
3. Add `tenant_id` column (non-nullable) to every existing table
4. Update the "Default" tenant's slug in existing rows
5. Add foreign key constraints

All steps are in a single Alembic migration.
