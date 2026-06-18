# Query Optimization Guide

> Best practices for optimizing PostgreSQL queries in a FastAPI + SQLAlchemy application.

---

# Table of Contents

1. General Principles
2. Indexing
3. Query Design
4. SQLAlchemy Best Practices
5. Pagination
6. Avoid N+1 Queries
7. Batch Operations
8. Transactions
9. Query Analysis
10. PostgreSQL Optimization
11. Connection Pool
12. Caching
13. Soft Delete Optimization
14. Full Text Search
15. Monitoring
16. Performance Checklist

---

# General Principles

## Only Select Required Columns

❌ Bad

```python
select(User)
```

✅ Good

```python
select(
    User.id,
    User.email,
)
```

or

```python
select(User.id, User.email)
```

Avoid loading unnecessary columns.

---

## Avoid SELECT *

Never write

```sql
SELECT *
FROM users;
```

Prefer

```sql
SELECT
    id,
    email,
    fullname
FROM users;
```

---

## Filter Early

Good

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

Avoid filtering in Python.

---

# Indexing

## Primary Key

```sql
PRIMARY KEY(id)
```

Already indexed.

---

## Foreign Keys

Always create indexes.

```sql
CREATE INDEX idx_user_role_user
ON user_roles(user_id);
```

---

## Frequently Filtered Columns

Example

```sql
email
username
status
deleted_at
created_at
```

---

## Composite Index

Instead of

```sql
WHERE organization_id = ?
AND deleted_at IS NULL
```

Use

```sql
CREATE INDEX idx_org_deleted
ON users(
    organization_id,
    deleted_at
);
```

---

## Partial Index

Excellent for soft delete.

```sql
CREATE INDEX idx_users_active
ON users(email)
WHERE deleted_at IS NULL;
```

---

# Query Design

## Use EXISTS

Instead of

```sql
SELECT COUNT(*)
```

Use

```sql
SELECT EXISTS(
    SELECT 1
);
```

SQLAlchemy

```python
from sqlalchemy import exists
```

---

## LIMIT

Always limit results.

```sql
LIMIT 50
```

Never fetch millions of rows.

---

## ORDER BY Indexed Columns

Good

```sql
ORDER BY created_at DESC
```

with

```sql
INDEX(created_at)
```

---

# SQLAlchemy Best Practices

## Use select()

Prefer

```python
stmt = select(User)
```

Avoid legacy Query API.

---

## Load Only Needed Fields

```python
stmt = select(
    User.id,
    User.email,
)
```

---

## scalars()

Good

```python
users = await session.scalars(stmt)
```

instead of

```python
await session.execute(stmt)
```

when selecting ORM models.

---

## one_or_none()

Use

```python
result.scalar_one_or_none()
```

instead of

```python
all()
```

when expecting a single record.

---

# Pagination

Avoid

```sql
OFFSET 100000
```

Prefer Cursor Pagination.

Example

```sql
WHERE id > ?
ORDER BY id
LIMIT 50
```

---

# Avoid N+1 Queries

Bad

```python
for user in users:
    print(user.roles)
```

Good

```python
select(User).options(
    selectinload(User.roles)
)
```

or

```python
joinedload()
```

depending on the use case.

---

# Batch Operations

Instead of

```python
for user in users:
    session.add(user)
```

Use

```python
session.add_all(users)
```

---

Bulk Update

```python
update(User)
```

---

Bulk Delete

```python
delete(User)
```

---

# Transactions

Keep transactions short.

Good

```
Begin

Update

Commit
```

Avoid

```
Begin

HTTP Request

Redis

Email

Commit
```

---

# Query Analysis

Use

```sql
EXPLAIN ANALYZE
```

Example

```sql
EXPLAIN ANALYZE
SELECT *
FROM users
WHERE email='john@test.com';
```

Look for

- Seq Scan
- Bitmap Heap Scan
- Index Scan

Prefer

```
Index Scan
```

---

# PostgreSQL Optimization

Vacuum

```sql
VACUUM ANALYZE;
```

Auto Vacuum should be enabled.

---

Update Statistics

```sql
ANALYZE users;
```

---

Avoid Huge JSON Columns

Store large blobs separately.

---

Use UUID

Prefer

```
UUID v7
```

or

```
UUID v4
```

instead of sequential integers when appropriate.

---

# Connection Pool

Recommended

```python
create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=1800,
)
```

Do not create an engine per request.

---

# Caching

Cache

- User Profile
- Roles
- Permissions
- Settings

Use Redis.

Avoid caching mutable transactional data unless invalidation is handled.

---

# Soft Delete

Always filter

```sql
deleted_at IS NULL
```

Create index

```sql
CREATE INDEX idx_deleted
ON users(deleted_at);
```

Better

```sql
CREATE INDEX idx_active_users
ON users(email)
WHERE deleted_at IS NULL;
```

---

# Full Text Search

Instead of

```sql
LIKE '%john%'
```

Use

```sql
GIN Index
```

and

```sql
tsvector
```

Example

```sql
CREATE INDEX idx_users_search
ON users
USING gin(search_vector);
```

---

# Monitoring

Enable

```sql
pg_stat_statements
```

Useful query

```sql
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC;
```

---

Check Slow Queries

```sql
log_min_duration_statement = 500
```

---

# Performance Checklist

## SQL

- [ ] No SELECT *
- [ ] Uses LIMIT
- [ ] Uses indexes
- [ ] No unnecessary ORDER BY
- [ ] No unnecessary DISTINCT
- [ ] Uses EXISTS instead of COUNT where appropriate

---

## SQLAlchemy

- [ ] Uses AsyncSession
- [ ] Uses select()
- [ ] Uses scalars()
- [ ] Uses selectinload()/joinedload()
- [ ] Avoids N+1 queries
- [ ] Loads only required columns

---

## PostgreSQL

- [ ] EXPLAIN ANALYZE checked
- [ ] Indexes created
- [ ] Partial indexes for soft delete
- [ ] Foreign key indexes
- [ ] Composite indexes
- [ ] VACUUM enabled
- [ ] ANALYZE updated

---

## API

- [ ] Cursor pagination
- [ ] Request caching
- [ ] Rate limiting
- [ ] Query timeout
- [ ] Connection pooling

---

## Production

- [ ] pg_stat_statements enabled
- [ ] Slow query logging
- [ ] Metrics (Prometheus/Grafana)
- [ ] Redis cache
- [ ] Read replicas (if needed)