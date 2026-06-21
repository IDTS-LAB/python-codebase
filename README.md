# FastAPI Modulith Todo API

A modular FastAPI backend for user authentication and todo management. The project is structured as a modulith and follows the main ideas of Domain-Driven Design, Clean Architecture, and CQRS:

- Each business module owns its presentation, application, domain, and infrastructure code.
- FastAPI routers stay at the delivery edge.
- Application handlers coordinate use cases.
- Domain entities and repository contracts define business concepts.
- Infrastructure repositories adapt SQLAlchemy models to domain entities.

The API is currently versioned under `/api/v1`.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Request Flow](#request-flow)
- [API Routes](#api-routes)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Running the Application](#running-the-application)
- [Database and Migrations](#database-and-migrations)
- [Testing and Quality Checks](#testing-and-quality-checks)
- [Makefile Commands](#makefile-commands)
- [Additional Documentation](#additional-documentation)
- [Docker Notes](#docker-notes)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [Security TODO](#security-todo)
- [Known Notes](#known-notes)

## Features

- User registration.
- User login with JWT access and refresh tokens.
- Refresh token rotation and logout/token revocation.
- Authentication middleware that validates bearer tokens.
- RBAC authorization with Casbin-backed roles and permissions.
- Current-user lookup from authenticated request state.
- Todo creation.
- Cursor-paginated todo listing by authenticated user.
- Todo update with ownership checks.
- Todo delete with ownership checks.
- Role and permission management APIs.
- Redis-backed rate limiting.
- Request ID, structured logging, audit logging, and security headers.
- Request size limiting and idempotency support.
- Health, liveness, and readiness endpoints.
- API route grouping under `/api/v1`.
- Async SQLAlchemy persistence.
- Alembic database migrations.
- Database seeders for authorization data and optional users.
- Pytest application-validation tests.
- Ruff linting.

## Tech Stack

- Python `>=3.14`
- FastAPI
- Uvicorn
- SQLAlchemy async ORM
- Asyncpg PostgreSQL driver
- PostgreSQL
- Alembic
- Pydantic and Pydantic Settings
- Python JOSE for JWT handling
- Passlib for password hashing
- Casbin for authorization policies
- Redis and fastapi-limiter for rate limiting and token revocation
- Pytest
- Ruff
- Poetry

## Project Structure

```text
.
├── alembic/                         # Alembic migration environment and versions
├── scripts/                         # Helper shell scripts
├── src/
│   ├── main.py                      # FastAPI application entrypoint
│   ├── core/
│   │   ├── bootstrap/               # Application bootstrap helpers
│   │   ├── authorization/           # Shared authorization persistence and services
│   │   ├── config/                  # Runtime settings
│   │   ├── database/                # PostgreSQL and Redis connection setup
│   │   ├── dependency/              # Shared FastAPI dependencies
│   │   ├── exceptions/              # Exception registration and handlers
│   │   ├── middleware/              # Auth, audit, security, logging, request middleware
│   │   ├── routers/                 # API router composition
│   │   ├── schemas/                 # Shared response schemas
│   │   ├── security/                # JWT, password, revocation, audit helpers
│   │   ├── seed/                    # Database seeding orchestration
│   │   └── lifespan.py              # FastAPI lifespan hook
│   ├── modules/
│   │   ├── authorization/
│   │   │   ├── application/         # Role and permission use cases
│   │   │   ├── domain/              # Role, resource, and permission entities
│   │   │   ├── infrastructure/      # Casbin and SQLAlchemy adapters
│   │   │   └── presentation/        # Role and permission routers/schemas
│   │   ├── user/
│   │   │   ├── application/         # User commands, queries, handlers
│   │   │   ├── domain/              # User entity, exceptions, repository port
│   │   │   ├── infrastructure/      # SQLAlchemy model/repository/services
│   │   │   └── presentation/        # FastAPI router, dependencies, schemas
│   │   └── todo/
│   │       ├── application/         # Todo commands, queries, handlers
│   │       ├── domain/              # Todo entity, exceptions, repository port
│   │       ├── infrastructure/      # SQLAlchemy model/repository
│   │       └── presentation/        # FastAPI router and dependencies
│   └── shared/
│       ├── database/                # Shared SQLAlchemy base and mixins
│       ├── email/                   # Shared email contracts
│       ├── events/                  # Shared event contracts
│       ├── exceptions/              # Cross-cutting exceptions
│       └── utils/                   # Cursor pagination helpers
├── templates/emails/                # Transactional email templates
├── tests/                           # Pytest tests
├── pyproject.toml                   # Project metadata and dependencies
├── poetry.lock                      # Poetry lock file
├── alembic.ini                      # Alembic configuration
├── Dockerfile                       # Docker image definition
└── docker-compose.yml               # Local API, PostgreSQL, and Redis services
```

## Architecture

### Modulith

This is a single deployable application with module boundaries inside the codebase. The `user`, `todo`, and `authorization` modules are independent feature areas under `src/modules`.

### Clean Architecture Direction

The intended dependency direction is:

```text
presentation -> application -> domain
infrastructure -> domain
```

The domain layer should not depend on FastAPI, SQLAlchemy, or external infrastructure. Infrastructure implements domain repository contracts.

### DDD Layers

Each module follows this shape:

- `domain`: entities, domain exceptions, repository interfaces.
- `application`: commands, queries, and handlers that coordinate use cases.
- `infrastructure`: SQLAlchemy models and repository implementations.
- `presentation`: FastAPI routers, request/response schemas, and dependency wiring.

### CQRS

The code separates commands and queries at the application naming level:

- Commands mutate state, for example register user, login user, create todo, update todo.
- Queries read state, for example user detail and todo listing.

Some flows are still pragmatic and can be made stricter over time by introducing dedicated read repositories or read DTOs.

## Request Flow

### Register User

```text
POST /api/v1/auth/register
  -> user_router.register
  -> RegisterUserCommand
  -> RegisterUserCommandHandler
  -> UserRepository port
  -> SQLAlchemyUserRepository
  -> users table
```

### Login User

```text
POST /api/v1/auth/login
  -> user_router.login
  -> LoginUserCommand
  -> LoginUserCommandHandler
  -> SQLAlchemyUserRepository
  -> JWT access token
```

### Authenticated Todo Request

```text
Request with Authorization: Bearer <token>
  -> AuthenticationMiddleware validates JWT
  -> request.state.user_id is set
  -> route dependency checks role permission
  -> todo handler executes use case
  -> TodoRepository port
  -> SQLAlchemyTodoRepository
  -> todos table
```

## API Routes

Base API prefix:

```text
/api/v1
```

Current routes:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/logout
POST   /api/v1/todos/
GET    /api/v1/todos/?cursor=<cursor>&limit=10
GET    /api/v1/todos/{todo_id}
PATCH  /api/v1/todos/{todo_id}
DELETE /api/v1/todos/{todo_id}
POST   /api/v1/roles/
GET    /api/v1/roles/?cursor=<cursor>&limit=10
GET    /api/v1/roles/{role_id}
PATCH  /api/v1/roles/{role_id}
DELETE /api/v1/roles/{role_id}
POST   /api/v1/roles/{role_id}/permissions/{permission_id}
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
POST   /api/v1/permissions/
GET    /api/v1/permissions/?cursor=<cursor>&limit=10
GET    /api/v1/permissions/{permission_id}
PATCH  /api/v1/permissions/{permission_id}
DELETE /api/v1/permissions/{permission_id}
GET    /health
GET    /live
GET    /ready
```

Public routes:

- `/health`
- `/live`
- `/ready`
- `/docs`
- `/redoc`
- `/openapi.json`
- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/auth/refresh`

Protected routes require:

```text
Authorization: Bearer <access_token>
```

Swagger UI, ReDoc, and OpenAPI JSON are disabled when `APP_ENV=production`.

## Prerequisites

- Python `3.14` or compatible with the project constraint.
- Poetry.
- PostgreSQL, either local or via Docker.
- Redis, either local or via Docker.
- Docker with the Compose plugin, if using the containerized stack.
- Make, if using the generated `Makefile`.

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Expected values:

```env
APP_NAME=Todo Modulith API
APP_ENV=production
FRONTEND_URL=http://localhost:3000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DB=todo_db
REDIS_PASSWORD=
DATABASE_URL=
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
REDIS_URL=
SECRET_KEY=
MAX_REQUEST_SIZE_MB=5242880
ALGORITHM=HS256
JWT_ISSUER=todo-modulith-api
JWT_AUDIENCE=todo-modulith-client
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
RATE_LIMIT=100/minute
CORS_ALLOW_ORIGINS=http://localhost:3000
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
SECURITY_CONTENT_SECURITY_POLICY=default-src 'self'; frame-ancestors 'none'
IDEMPOTENCY_TTL_SECONDS=86400
ACCOUNT_LOCKOUT_MAX_ATTEMPTS=5
ACCOUNT_LOCKOUT_WINDOW_MINUTES=15
ACCOUNT_LOCKOUT_DURATION_MINUTES=15
LOG_FORMAT=json
EMAIL_PROVIDER=ses
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
SES_FROM_EMAIL=noreply@example.com
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=noreply@example.com
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@example.com
SMTP_USE_TLS=true
SEED_ADMIN_EMAIL=
SEED_ADMIN_PASSWORD=
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_FULLNAME=System Administrator
SEED_DEVELOPMENT_USERS_PASSWORD=
```

`MAX_REQUEST_SIZE_MB` is currently interpreted as a byte count despite its name. Keep it at `5242880` for a 5 MiB limit.

For local development without Docker, use development mode and point the service URLs at local PostgreSQL and Redis instances, for example:

```env
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/todo_db
REDIS_URL=redis://127.0.0.1:6379/0
```

Production mode requires a non-default `SECRET_KEY`, non-empty database and Redis URLs, JWT issuer and audience values, positive token lifetimes, and explicit CORS origins.

## Local Setup

The Makefile expects Poetry to create `.venv` inside the repository. Configure that once, then install dependencies:

```bash
poetry config virtualenvs.in-project true --local
poetry install
```

Run commands through Poetry directly:

```bash
poetry run pytest -q
```

This repository also has a local `.venv`, so the Makefile uses `.venv/bin/...` where practical.

## Running the Application

Run the API locally:

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or with Make:

```bash
make run
```

Open:

```text
http://localhost:8000/docs
```

This documentation endpoint is available only when `APP_ENV` is not `production`.

Health check:

```text
http://localhost:8000/health
```

Operational checks:

```text
http://localhost:8000/live
http://localhost:8000/ready
```

## Database and Migrations

Alembic is configured in:

- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/`

Apply migrations:

```bash
poetry run alembic upgrade head
```

Create a new migration with autogenerate:

```bash
poetry run alembic revision --autogenerate -m "describe change"
```

Rollback one migration:

```bash
poetry run alembic downgrade -1
```

With Make:

```bash
make migrate
make seed
make revision name="add todo due date"
make downgrade
```

Important: migration autogeneration depends on importing all SQLAlchemy models in `alembic/env.py`, so new module models must be imported there or through a central model registry.

Seed baseline authorization data after applying migrations:

```bash
make seed
```

The seeder is idempotent. It creates default authorization resources, the default `admin` and `user` roles, default permissions, role-permission links, and matching Casbin policies without duplicating existing records.

To seed an initial admin user, set these environment variables before running `make seed`:

```env
SEED_ADMIN_EMAIL=admin@example.com
SEED_ADMIN_PASSWORD=
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_FULLNAME=System Administrator
```

If `SEED_ADMIN_EMAIL` or `SEED_ADMIN_PASSWORD` is empty, user seeding is skipped. Existing users are not modified.

When `APP_ENV=development`, the seeder can also create demo users with different roles. Set a shared development password before running `make seed`:

```env
SEED_DEVELOPMENT_USERS_PASSWORD=
```

Development demo accounts:

- `user@example.com` with the `user` role
- `manager@example.com` with the `manager` role
- `viewer@example.com` with the `viewer` role

These users are skipped outside development and are not updated if they already exist.

## Testing and Quality Checks

Run tests:

```bash
make test
```

Run lint:

```bash
make lint
```

Run the full local check:

```bash
make check
```

Current check set:

- `pytest -q`
- `ruff check src tests scripts`
- import boundary checks through `lint-imports`
- import check for `src.main`

The current pytest suite focuses on application-layer command and query validation. Broader middleware, API integration, and infrastructure regression coverage still needs to be added.

Dependency scanning is available separately:

```bash
make security-scan
```

## Makefile Commands

```bash
make help
make install
make run
make test
make lint
make lint-imports
make import-check
make security-scan
make check
make migrate
make seed
make downgrade
make revision name="migration message"
make db-up
make db-down
make db-logs
make clean
```

## Additional Documentation

- [Query Optimization Guide](docs/QUERY_OPTIMIZATION.md)

## Docker Notes

Before starting Docker Compose, set non-empty `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and `SECRET_KEY` in `.env`. Compose intentionally fails fast when database or Redis passwords are missing.

Run API, PostgreSQL, and Redis services:

```bash
make db-up
```

The API container applies Alembic migrations before starting Uvicorn. Database seeding remains an explicit `make seed` step.

Stop services:

```bash
make db-down
```

Follow service logs:

```bash
make db-logs
```

## Development Guide

### Adding a New Use Case

1. Add a command or query in the module application layer.
2. Add a handler in the application layer.
3. Keep business rules in the domain entity when they are true invariants.
4. Depend on domain repository interfaces, not SQLAlchemy directly.
5. Add or extend infrastructure repositories only in the infrastructure layer.
6. Wire the handler in presentation dependencies.
7. Expose the use case from the FastAPI router.
8. Add focused tests.

### Adding a New Module

Use the same structure:

```text
src/modules/<module_name>/
├── application/
├── domain/
├── infrastructure/
└── presentation/
```

Then register its router in:

```text
src/core/routers/api/v1.py
```

### Adding a New Table

1. Create the SQLAlchemy model in the module infrastructure layer.
2. Ensure the model imports into Alembic metadata discovery.
3. Generate a migration:

   ```bash
   make revision name="add new table"
   ```

4. Review the generated migration before applying it.
5. Apply:

   ```bash
   make migrate
   ```

## Troubleshooting

### Import errors in tests

The tests add both the repository root and `src` to `sys.path` through `tests/conftest.py`. If new tests import modules inconsistently, prefer absolute `src...` imports.

### Database connection errors

Check `DATABASE_URL`.

For Docker Compose, the database hostname is usually:

```text
db
```

For local execution against a host PostgreSQL instance, it is usually:

```text
localhost
```

### Alembic does not detect model changes

Make sure the model is imported by `alembic/env.py` or by something that is imported there before `target_metadata = Base.metadata`.

### Authentication failures

Protected routes require:

```text
Authorization: Bearer <token>
```

The token must contain a `sub` claim with a valid user id.

## Security TODO

Legend: `Implemented` means code exists in the repository. `Partial` means code exists but still needs a fix, test, or production hardening.

| Category | Recommended | Current Status | Notes |
| --- | --- | --- | --- |
| JWT Authentication | Required | Implemented | `AuthenticationMiddleware` validates bearer tokens for non-public routes. |
| Refresh Token Rotation | Required | Implemented | Refresh flow revokes the old refresh token and persists a new token. |
| RBAC + Permissions | Required | Implemented | Casbin-backed role and permission checks are wired through route dependencies. |
| Rate Limiting (Redis-backed) | Required | Implemented | Redis-backed limiter reads the configured `RATE_LIMIT` value. |
| Security Headers Middleware | Required | Implemented | Adds `X-Content-Type-Options`, `X-Frame-Options`, CSP `frame-ancestors`, `Referrer-Policy`, and `Permissions-Policy`. |
| CORS Configuration | Required | Implemented | CORS origins, methods, and headers are environment-driven through settings. |
| Request ID Middleware | Required | Implemented | Generates or propagates `X-Request-ID` and stores it on request state. |
| Audit Logging | Required | Implemented | Adds global endpoint audit logging, domain audit events, and separate persisted error traces. |
| Structured Logging | Required | Implemented | Logs request ID, method, path, status, latency, and user context when available. |
| Global Exception Handling | Required | Implemented | Domain exceptions are registered explicitly and `Exception` is used only as the fallback handler. |
| Input Validation | Required | Implemented | Pydantic schemas and application validation functions are used across user and todo flows. |
| Password Hashing (Argon2 or bcrypt) | Required | Implemented | User auth service uses bcrypt hashing. |
| Account Lockout | Required | Implemented | Tracks failed logins and temporarily locks accounts after configured thresholds. |
| Token Revocation | Required | Implemented | Refresh tokens are revoked on rotation/logout, and access tokens are denylisted in Redis until expiry. |
| OpenAPI Authentication | Required | Implemented | Swagger OAuth2 auth is configured, and docs/OpenAPI endpoints are disabled when `APP_ENV=production`. |
| Health Check Endpoint | Required | Implemented | `/health` endpoint returns service health. |
| Readiness/Liveness Endpoints | Required | Implemented | Adds `/live` and `/ready` operational endpoints. |
| Request Size Limiting | Required | Implemented | `LimitRequestSizeMiddleware` rejects oversized write requests. |
| Idempotency Support (for applicable POST endpoints) | Optional but valuable | Implemented | Supports `Idempotency-Key` replay caching for POST responses. |
| Database Migrations | Required | Implemented | Alembic is configured with migration commands in the README and Makefile. |
| Dependency Injection | Required | Implemented | FastAPI dependencies wire repositories, handlers, auth, authorization, and database sessions. |
| Configuration via Environment Variables | Required | Implemented | Pydantic settings read `.env` and reject the default secret key in production. |

### Next Implementation Checklist

- [x] Fix and verify rate limit configuration wiring.
- [x] Add security headers middleware.
- [x] Add request ID middleware.
- [x] Add structured request logging.
- [x] Add audit logging for sensitive actions.
- [x] Add account lockout or equivalent failed-login protection.
- [x] Disable or authenticate `/docs`, `/redoc`, and `/openapi.json` in production.
- [x] Add readiness and liveness endpoints.
- [x] Add production config validation for secrets and unsafe defaults.
- [x] Harden CORS through environment-driven allowed origins, methods, and headers.
- [x] Review exception responses to avoid leaking token parsing details or internal exception messages.
- [ ] Add automated tests for request size limits, rate limiting, auth failures, authorization failures, CORS, security headers, and request IDs.
- [x] Add dependency vulnerability scanning to local or CI checks, for example `pip-audit` or an equivalent Poetry-compatible scanner.

## Known Notes

- The automated test suite currently covers application validation only; middleware, router, database, Redis, and authorization integration paths are not covered.
- Authorization persistence currently exists under both `src/core/authorization/infrastructure` and `src/modules/authorization/infrastructure`; new work should avoid increasing that duplication.
- Some authorization routes call the domain service directly while other modules use dedicated application handlers, so CQRS boundaries are not yet applied consistently.
