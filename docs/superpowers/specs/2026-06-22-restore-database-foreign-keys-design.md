# Restore Database Foreign Keys Design

## Goal

Restore every foreign-key relationship removed or omitted by the normalized user-schema change so SQLAlchemy can configure all mappers, PostgreSQL enforces referential integrity, migrations remain safe for databases that already applied `e73c215d7221`, and `make seed` completes successfully.

## Root Cause

The current ORM models declare relationship properties but no `ForeignKey` metadata. SQLAlchemy therefore cannot infer joins such as `permissions.id` to `role_permissions.permission_id`, causing mapper configuration to fail before the seed query executes.

The latest normalization migration was generated from that incomplete metadata. It drops six established constraints:

- `permissions.resource_id` to `authorization_resources.id`
- `role_permissions.role_id` to `roles.id`
- `role_permissions.permission_id` to `permissions.id`
- `todos.user_id` to `users.id`
- `user_has_roles.user_id` to `users.id`
- `user_has_roles.role_id` to `roles.id`

It also creates seven normalized user tables whose `user_id` columns are `VARCHAR(36)` even though `users.id` is UUID, and omits their intended constraints.

## Design

### ORM metadata

Each affected model column will declare a SQLAlchemy `ForeignKey` targeting the parent table. Existing relationship names, `back_populates` pairs, collection shapes, and ORM cascade settings remain unchanged.

The seven normalized user tables will use `Mapped[UUID]` and UUID-backed columns for `user_id`:

- `user_profiles`
- `user_security`
- `user_settings`
- `user_contacts`
- `user_addresses`
- `user_verifications`
- `user_sessions`

The authorization junction tables, permission resource link, todo owner link, and user-role junction table will retain their existing UUID Python types while gaining their missing `ForeignKey` declarations.

No database-level delete cascade will be introduced. This restores the relationships that existed before normalization without adding new deletion behavior.

### Model discovery

Alembic must load every normalized user model before reading `Base.metadata`. Its environment will import the user model package, which already exports all eight user-domain models, instead of importing only `UserModel` and `UserSessionModel`. This keeps migration comparison aligned with runtime metadata.

### Corrective migration

A new Alembic revision after `e73c215d7221` will repair databases where the normalization migration has already run. The existing revision will not be rewritten.

The corrective upgrade will:

1. Convert the seven normalized `user_id` columns from `VARCHAR(36)` to UUID using an explicit PostgreSQL cast.
2. Recreate the six constraints dropped by `e73c215d7221`.
3. Add the seven missing normalized-user constraints.

The migration will use deterministic constraint names. If an existing normalized `user_id` contains a malformed UUID or references a missing user, PostgreSQL will reject the migration. The migration must fail visibly rather than discard, rewrite, or detach invalid data.

The downgrade will drop the 13 constraints added by the corrective revision and convert the seven normalized `user_id` columns back to `VARCHAR(36)`, returning the schema to the exact state represented by `e73c215d7221`.

### Runtime data flow

After mapper configuration succeeds, seeding keeps its current transaction flow: seed authorization resources, roles, permissions, and junction records; then seed users, normalized profile data, and role assignments. The fix changes schema metadata and integrity enforcement only. Seed definitions and idempotency behavior remain unchanged.

## Testing and Verification

Regression tests will import the complete model graph and assert that:

- `configure_mappers()` completes without `NoForeignKeysError`.
- All 13 child columns expose the expected foreign-key target in `Base.metadata`.
- The seven normalized `user_id` columns use UUID rather than string types.

The implementation will then run focused tests, the full test suite, Ruff, and Alembic migration checks. Against the configured local PostgreSQL service, verification will upgrade through the corrective revision and run `make seed`. A disposable database or reversible upgrade/downgrade cycle will be used for migration verification so application data is not destroyed.

## Scope

This change restores all affected foreign keys and corrects the normalized user identifier types. It does not change domain entities, repository APIs, seed contents, authorization policy definitions, indexes, uniqueness rules, or delete semantics.
