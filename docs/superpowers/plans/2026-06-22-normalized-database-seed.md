# Normalized Database Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make configured user seeds compatible with the normalized user schema and document exactly which authorization and user records the seed creates.

**Architecture:** Keep orchestration in `src/core/seed/user.py` behind its repository and authorization protocols. Create identity data through the current `User` factory, then persist the legacy full-name setting as `UserProfile.display_name`; the existing SQLAlchemy repository remains responsible for default profile, settings, and security rows and the runner retains transaction ownership.

**Tech Stack:** Python 3.14, dataclasses, async repository protocols, SQLAlchemy async repository adapter, pytest, Ruff, Markdown.

---

## File Structure

- Create `tests/test_user_seed.py`: unit tests for normalized user/profile seeding, environment gating, idempotency, role assignment, and counters.
- Modify `src/core/seed/user.py`: correct the `User.create()` call and persist seed names through `UserProfile`.
- Modify `README.md`: document authorization records, normalized user records, configuration mapping, transaction behavior, and existing-user behavior.

### Task 1: Add normalized user seed contract tests

**Files:**
- Create: `tests/test_user_seed.py`

- [ ] **Step 1: Write test fakes and a failing admin seed test**

Create `tests/test_user_seed.py` with:

```python
import asyncio
from uuid import uuid4

from src.core.seed.user import SeedUserConfig, seed_user
from src.modules.authorization.domain.permissions import (
    ADMIN_ROLE,
    DEFAULT_USER_ROLE,
    MANAGER_ROLE,
    VIEWER_ROLE,
)
from src.modules.user.domain.entities.user import User, UserProfile


class FakeUserRepository:
    def __init__(self, existing_users: tuple[User, ...] = ()) -> None:
        self.users = {user.email: user for user in existing_users}
        self.saved_users: list[User] = []
        self.saved_profiles: list[UserProfile] = []

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def save(self, user: User) -> User:
        self.users[user.email] = user
        self.saved_users.append(user)
        return user

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        self.saved_profiles.append(profile)
        return profile


class FakeAuthorizationService:
    def __init__(self) -> None:
        self.assignments: list[tuple[str, str]] = []

    async def assign_role(self, subject: str, role: str) -> None:
        self.assignments.append((subject, role))


def test_seed_user_creates_admin_with_normalized_profile(monkeypatch):
    monkeypatch.setattr(
        "src.core.seed.user.PasswordSerrvice.hash",
        lambda password: f"hashed:{password}",
    )
    repository = FakeUserRepository()
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="production",
                admin_email="admin@example.com",
                admin_password="secret-password",
                admin_username="admin",
                admin_fullname="System Administrator",
            ),
        )
    )

    assert result.users_created == 1
    assert result.roles_assigned == 1
    assert len(repository.saved_users) == 1
    saved_user = repository.saved_users[0]
    assert saved_user.email == "admin@example.com"
    assert saved_user.username == "admin"
    assert saved_user.password_hash == "hashed:secret-password"
    assert repository.saved_profiles == [
        UserProfile(user_id=saved_user.id, display_name="System Administrator")
    ]
    assert authorization.assignments == [(str(saved_user.id), ADMIN_ROLE)]
```

- [ ] **Step 2: Run the admin test to verify the current factory mismatch fails**

Run: `.venv/bin/pytest tests/test_user_seed.py::test_seed_user_creates_admin_with_normalized_profile -v`

Expected: FAIL with `TypeError` because `User.create()` currently receives unsupported `password` and `fullname` keyword arguments.

- [ ] **Step 3: Add failing development, existing-user, and missing-credentials tests**

Append:

```python
def test_seed_user_creates_development_users_and_profiles(monkeypatch):
    monkeypatch.setattr(
        "src.core.seed.user.PasswordSerrvice.hash",
        lambda password: f"hashed:{password}",
    )
    repository = FakeUserRepository()
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="development",
                admin_email="",
                admin_password="",
                development_users_password="demo-password",
            ),
        )
    )

    assert result.users_created == 3
    assert result.roles_assigned == 3
    assert [user.email for user in repository.saved_users] == [
        "user@example.com",
        "manager@example.com",
        "viewer@example.com",
    ]
    assert [profile.display_name for profile in repository.saved_profiles] == [
        "Default User",
        "Todo Manager",
        "Todo Viewer",
    ]
    assert [role for _, role in authorization.assignments] == [
        DEFAULT_USER_ROLE,
        MANAGER_ROLE,
        VIEWER_ROLE,
    ]


def test_seed_user_does_not_modify_an_existing_user(monkeypatch):
    monkeypatch.setattr(
        "src.core.seed.user.PasswordSerrvice.hash",
        lambda password: f"hashed:{password}",
    )
    existing_user = User(
        id=uuid4(),
        email="admin@example.com",
        password_hash="existing-hash",
        username="existing-admin",
    )
    repository = FakeUserRepository((existing_user,))
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="production",
                admin_email="admin@example.com",
                admin_password="new-password",
                admin_username="admin",
                admin_fullname="System Administrator",
            ),
        )
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert repository.saved_users == []
    assert repository.saved_profiles == []
    assert authorization.assignments == []
    assert repository.users[existing_user.email] == existing_user


def test_seed_user_skips_users_without_credentials():
    repository = FakeUserRepository()
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="production",
                admin_email="",
                admin_password="",
            ),
        )
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert repository.saved_users == []
    assert repository.saved_profiles == []
    assert authorization.assignments == []
```

- [ ] **Step 4: Run the test file**

Run: `.venv/bin/pytest tests/test_user_seed.py -v`

Expected: missing-credentials and existing-user tests PASS; admin and development creation tests FAIL at the outdated `User.create()` call.

- [ ] **Step 5: Commit the failing tests**

```bash
git add tests/test_user_seed.py
git commit -m "test: cover normalized user seeding"
```

### Task 2: Persist seeded names through normalized profiles

**Files:**
- Modify: `src/core/seed/user.py:1-161`
- Test: `tests/test_user_seed.py`

- [ ] **Step 1: Import `UserProfile` and extend the seed repository contract**

```python
from src.modules.user.domain.entities.user import User, UserProfile


class SeedUserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    async def save(self, user: User) -> User:
        raise NotImplementedError

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        raise NotImplementedError
```

- [ ] **Step 2: Correct user creation and save the normalized profile before role assignment**

Replace the creation block in `_seed_one_user()` with:

```python
    user = User.create(
        email=email,
        password_hash=PasswordSerrvice.hash(password),
        username=username,
    )
    saved_user = await user_repository.save(user)
    await user_repository.save_profile(
        UserProfile(
            user_id=saved_user.id,
            display_name=fullname,
        )
    )
    await authorization_service.assign_role(str(saved_user.id), role)
```

This preserves ordering inside the runner transaction: identity and defaults, profile value, then role assignment.

- [ ] **Step 3: Run seed tests**

Run: `.venv/bin/pytest tests/test_user_seed.py -v`

Expected: 4 tests PASS.

- [ ] **Step 4: Run all tests**

Run: `.venv/bin/pytest -q`

Expected: all tests PASS.

- [ ] **Step 5: Run focused lint**

Run: `.venv/bin/ruff check src/core/seed/user.py tests/test_user_seed.py`

Expected: `All checks passed!`

- [ ] **Step 6: Commit the implementation**

```bash
git add src/core/seed/user.py
git commit -m "fix: align user seed with normalized schema"
```

### Task 3: Document normalized seed behavior

**Files:**
- Modify: `README.md:431-462`

- [ ] **Step 1: Replace the database-seeding section with schema-accurate text**

The revised section must state:

````markdown
Seed baseline records after applying migrations:

```bash
make seed
```

The seeder runs all changes in one transaction and is idempotent. It creates the default authorization resources, roles (`admin`, `user`, `manager`, and `viewer`), permissions, role-permission links, and matching Casbin policies without duplicating existing records.

For each new seeded user, the repository creates records that follow the normalized user schema:

- `users` stores email, username, password hash, authentication provider, and status.
- `user_profiles` stores `SEED_ADMIN_FULLNAME` (or the demo name) as `display_name`.
- `user_settings` stores default preferences.
- `user_security` stores default security state.
- `user_has_roles` associates the user with its seeded role.

`SEED_ADMIN_FULLNAME` is retained for configuration compatibility; there is no `users.fullname` column. Existing users are not modified.
````

Keep the existing environment examples, add display names to the demo-account list, and explicitly describe transaction rollback and production/development gating.

- [ ] **Step 2: Search for obsolete seed claims**

Run: `rg -n "SEED_ADMIN_FULLNAME|fullname|default .*roles|user_profiles|user_settings|user_security" README.md src/core/seed`

Expected: README maps `SEED_ADMIN_FULLNAME` to `user_profiles.display_name`; source uses `fullname` only as seed input; README lists all four roles.

- [ ] **Step 3: Check whitespace**

Run: `git diff --check`

Expected: no output and exit status 0.

- [ ] **Step 4: Commit README changes**

```bash
git add README.md
git commit -m "docs: explain normalized database seeding"
```

### Task 4: Verify the complete change

**Files:**
- Verify: `src/core/seed/user.py`
- Verify: `tests/test_user_seed.py`
- Verify: `README.md`

- [ ] **Step 1: Run the full test suite**

Run: `.venv/bin/pytest -q`

Expected: all tests PASS.

- [ ] **Step 2: Run project lint**

Run: `.venv/bin/ruff check src tests scripts`

Expected: `All checks passed!`

- [ ] **Step 3: Run import-boundary checks**

Run: `.venv/bin/lint-imports`

Expected: all configured contracts are kept.

- [ ] **Step 4: Verify application imports**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c "import src.main; print('import ok')"`

Expected: `import ok`.

- [ ] **Step 5: Inspect the final scoped diff and worktree**

Run:

```bash
git diff HEAD~3 -- src/core/seed/user.py tests/test_user_seed.py README.md
git status --short
```

Expected: only the planned seed, tests, and README changes appear; the pre-existing untracked `.vscode/PythonImportHelper-v2-Completion.json` remains untouched.
