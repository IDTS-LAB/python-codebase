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
- [Docker Notes](#docker-notes)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [Security TODO](#security-todo)
- [Known Notes](#known-notes)

## Features

- User registration.
- User login with JWT access tokens.
- Authentication middleware that validates bearer tokens.
- Current-user lookup from authenticated request state.
- Todo creation.
- Todo listing by authenticated user.
- Todo update with ownership checks.
- Todo delete with ownership checks.
- API route grouping under `/api/v1`.
- Async SQLAlchemy persistence.
- Alembic database migrations.
- Pytest regression tests.
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
│   │   ├── config/                  # Runtime settings
│   │   ├── database/                # SQLAlchemy async session setup
│   │   ├── middleware/              # Authentication middleware
│   │   ├── routers/                 # API router composition
│   │   ├── security/                # JWT and password helpers
│   │   ├── di.py                    # Shared dependency helpers
│   │   └── lifespan.py              # FastAPI lifespan hook
│   ├── modules/
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
│       └── exceptions/              # Cross-cutting exceptions
├── tests/                           # Pytest tests
├── pyproject.toml                   # Project metadata and dependencies
├── poetry.lock                      # Poetry lock file
├── alembic.ini                      # Alembic configuration
├── Dockerfile                       # Docker image definition
└── docker-compose.yml               # Local API and PostgreSQL services
```

## Architecture

### Modulith

This is a single deployable application with module boundaries inside the codebase. The `user` and `todo` modules are independent feature areas under `src/modules`.

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
  -> route dependency resolves current user
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
GET    /api/v1/auth/me
POST   /api/v1/todos/
GET    /api/v1/todos/
PATCH  /api/v1/todos/{todo_id}
DELETE /api/v1/todos/{todo_id}
GET    /health
```

Public routes:

- `/health`
- `/docs`
- `/redoc`
- `/openapi.json`
- `/api/v1/auth/login`
- `/api/v1/auth/register`

Protected routes require:

```text
Authorization: Bearer <access_token>
```

## Prerequisites

- Python `3.14` or compatible with the project constraint.
- Poetry.
- PostgreSQL, either local or via Docker.
- Make, if using the generated `Makefile`.

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Expected values:

```env
APP_NAME=Todo Modulith API
DATABASE_URL=
SECRET_KEY=
ALGORITHM=HS256
JWT_ISSUER=todo-modulith-api
JWT_AUDIENCE=todo-modulith-client
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

For local development without Docker, point `DATABASE_URL` at your local PostgreSQL host, for example:

```env
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/todo_db
```

## Local Setup

Install dependencies:

```bash
poetry install
```

Activate the virtual environment if desired:

```bash
poetry shell
```

Or run commands through Poetry:

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

Health check:

```text
http://localhost:8000/health
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
make revision name="add todo due date"
make downgrade
```

Important: migration autogeneration depends on importing all SQLAlchemy models in `alembic/env.py`, so new module models must be imported there or through a central model registry.

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
- `ruff check src tests`
- import check for `src.main`

## Makefile Commands

```bash
make help
make install
make run
make test
make lint
make import-check
make check
make migrate
make downgrade
make revision name="migration message"
make db-up
make db-down
make db-logs
make clean
```

## Docker Notes

Run database and API services:

```bash
make db-up
```

Stop services:

```bash
make db-down
```

Follow service logs:

```bash
make db-logs
```

Known Dockerfile note: `Dockerfile` currently references `start.sh`, while the actual script is under `scripts/start.sh`. If you plan to rely on Docker builds, align those paths first.

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
| Rate Limiting (Redis-backed) | Required | Partial | Redis-backed limiter exists, but `apply_global_rate_limit` reads `GLOBAL_RATE_LIMIT` while settings expose `RATE_LIMIT`. |
| Security Headers Middleware | Required | Not Implemented | Add headers such as `X-Content-Type-Options`, `X-Frame-Options` or CSP `frame-ancestors`, `Referrer-Policy`, and production CSP. |
| CORS Configuration | Required | Partial | CORS middleware exists, but production origins, methods, and headers should be environment-driven. |
| Request ID Middleware | Required | Not Implemented | Add request/correlation ID generation and response header propagation. |
| Audit Logging | Required | Not Implemented | Add audit events for sensitive auth, user, role, permission, and todo mutations. |
| Structured Logging | Required | Not Implemented | Add structured application logs with request ID, method, path, status, latency, and user context when available. |
| Global Exception Handling | Required | Partial | Exception handlers exist, but `Exception` is registered twice; verify domain and fallback handling behavior. |
| Input Validation | Required | Implemented | Pydantic schemas and application validation functions are used across user and todo flows. |
| Password Hashing (Argon2 or bcrypt) | Required | Implemented | User auth service uses bcrypt hashing. |
| Account Lockout | Required | Not Implemented | Add failed-login tracking and temporary lockout or throttling by account. |
| Token Revocation | Required | Implemented | Refresh tokens are revoked on rotation/logout, and access tokens are denylisted in Redis until expiry. |
| OpenAPI Authentication | Required | Partial | Swagger OAuth2 auth is configured, but `/docs`, `/redoc`, and `/openapi.json` are public; disable them in production or protect them with authentication. |
| Health Check Endpoint | Required | Implemented | `/health` endpoint returns service health. |
| Readiness/Liveness Endpoints | Required | Not Implemented | Add separate readiness and liveness endpoints for deployment orchestration. |
| Request Size Limiting | Required | Implemented | `LimitRequestSizeMiddleware` rejects oversized write requests. |
| Idempotency Support (for applicable POST endpoints) | Optional but valuable | Not Implemented | Consider idempotency keys for retry-safe create/payment-like workflows. |
| Database Migrations | Required | Implemented | Alembic is configured with migration commands in the README and Makefile. |
| Dependency Injection | Required | Implemented | FastAPI dependencies wire repositories, handlers, auth, authorization, and database sessions. |
| Configuration via Environment Variables | Required | Partial | Pydantic settings read `.env`, but production validation should reject unsafe defaults. |

### Next Implementation Checklist

- [ ] Fix and verify rate limit configuration wiring.
- [ ] Add security headers middleware.
- [ ] Add request ID middleware.
- [ ] Add structured request logging.
- [ ] Add audit logging for sensitive actions.
- [ ] Add account lockout or equivalent failed-login protection.
- [ ] Disable or authenticate `/docs`, `/redoc`, and `/openapi.json` in production.
- [ ] Add readiness and liveness endpoints.
- [ ] Add production config validation for secrets and unsafe defaults.
- [ ] Harden CORS through environment-driven allowed origins, methods, and headers.
- [ ] Review exception responses to avoid leaking token parsing details or internal exception messages.
- [ ] Add automated tests for request size limits, rate limiting, auth failures, authorization failures, CORS, security headers, and request IDs.
- [ ] Add dependency vulnerability scanning to local or CI checks, for example `pip-audit` or an equivalent Poetry-compatible scanner.

## Known Notes

- `alembic/env.py` currently prints metadata debug output during migrations.
- `src/core/lifespan.py` still calls `Base.metadata.create_all`; with Alembic in place, production environments normally rely on migrations instead.
- The project has a Pydantic v2 deprecation warning for class-based settings config.
- The Dockerfile start script path needs alignment before relying on Docker builds.
- The current architecture is clean enough for a learning modulith, but some flows can be made stricter by moving remaining business orchestration out of routers and into application handlers.
