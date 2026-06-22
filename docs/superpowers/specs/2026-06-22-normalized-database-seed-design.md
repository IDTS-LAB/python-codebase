# Normalized Database Seed Design

## Goal

Update user seeding to work with the normalized user database schema while preserving the existing seed configuration and idempotent behavior. Update the README so operators can understand which records are created and how `SEED_ADMIN_FULLNAME` maps to the current schema.

## Current Problem

The user seeder passes `fullname` to `User.create()`. The normalized `users` table and current domain factory no longer accept that field. Personal names now belong in `user_profiles`, specifically `display_name` for the existing seed value. As a result, configured user seeding fails before a user can be persisted.

## Design

### User creation

The seeder will create each user with the current identity fields only: email, password hash, and username. It will continue using `SQLAlchemyUserRepository.save()`, which creates the required default `user_profiles`, `user_settings`, and `user_security` records alongside a new user.

### Profile population

The seed repository contract will expose profile persistence. After saving a new user, the seeder will save a `UserProfile` whose `display_name` contains the configured full name. `SEED_ADMIN_FULLNAME` remains unchanged for backward compatibility. Development-user full names follow the same mapping.

The profile is saved before assigning the role. All operations remain within the seed runner's existing transaction, so a failure rolls back the user, normalized related records, profile update, and role assignment together.

### Idempotency

Email remains the identity used to detect existing seed users. If a user already exists, the seeder will not update identity data, profile data, password hashes, settings, security state, or role assignments. Authorization resource, role, permission, role-permission, and Casbin policy seeding retains its existing idempotency checks.

### Configuration

No environment-variable names change. The relevant variables remain:

- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`
- `SEED_ADMIN_USERNAME`
- `SEED_ADMIN_FULLNAME`
- `SEED_DEVELOPMENT_USERS_PASSWORD`

`SEED_ADMIN_FULLNAME` is documented as the value stored in `user_profiles.display_name`, not a column in `users`.

## Testing

Focused unit tests will cover:

- Creating an admin user with current `User.create()` arguments.
- Saving the admin display name to a normalized profile.
- Creating development users and their profiles only in development mode.
- Skipping user and profile writes when seed credentials are missing or the email exists.
- Assigning the configured role only after a new user and profile are saved.
- Returning accurate user and role counters.

Existing project tests and Ruff checks will be run after implementation. Database-backed execution will be used only if the configured local services are available; otherwise unit tests will verify the seeder's behavior through its repository and authorization contracts.

## README Changes

The database-seeding section will explain:

- The authorization records created by the baseline seed.
- The normalized user records created for each new seeded user: `users`, `user_profiles`, `user_settings`, and `user_security`.
- The mapping from `SEED_ADMIN_FULLNAME` to `user_profiles.display_name`.
- Development-only demo accounts and their roles.
- Existing-user behavior and transactional/idempotent guarantees.

## Scope

This change does not alter migrations, database models, seed account credentials, authorization definitions, or existing-user reconciliation. It fixes user seed compatibility with the current schema and documents actual behavior.
