"""Normalized User Domain Schema Design

This module implements a fully normalized user domain following:
- PostgreSQL 17 features
- Third Normal Form (3NF)
- Domain-Driven Design (DDD) principles
- Modular Monolith Architecture
- CQRS compatibility
- Multi-tenancy readiness
- Audit-friendly design

## Domain Analysis: Why Monolithic Users Table is Bad

1. **Single Responsibility Principle Violation**: A monolithic users table mixes identity, 
   profile, security, preferences, and contact information in one place. This makes it 
   difficult to reason about and maintain.

2. **Scalability Bottlenecks**: As the table grows wide with many columns, every query 
   loads unnecessary data. Index efficiency decreases, and vacuum operations become slower.

3. **Security Concerns**: Sensitive data like password hashes and security settings should 
   be isolated from frequently accessed profile data to minimize exposure surface.

4. **Multi-Tenancy Complexity**: Adding tenant isolation to a wide table requires careful 
   consideration of which fields need tenant scoping.

5. **CQRS Incompatibility**: Command and Query Responsibility Segregation becomes difficult 
   when read models need different projections than write models from the same table.

6. **Microservice Extraction**: When extracting services, a monolithic table creates tight 
   coupling. Separated tables allow clean bounded context boundaries.

7. **Audit Trail Gaps**: Tracking changes across many unrelated fields in one table is 
   complex and error-prone.

8. **Performance Contention**: Hot spots form when unrelated operations compete for locks 
   on the same row.

## Recommended Normalized Structure

### Identity Bounded Context
- **users**: Core identity and authentication credentials
- **user_security**: Security state, lockouts, MFA configuration
- **user_verifications**: Verification status per communication channel
- **user_sessions**: Active sessions and refresh tokens

### Profile Bounded Context  
- **user_profiles**: Personal information (names, bio, avatar)
- **user_contacts**: Multiple contact methods with types
- **user_addresses**: Multiple addresses with labels
- **user_settings**: User preferences in flexible JSONB format

### Access Control Bounded Context
- **roles**: Role definitions
- **permissions**: Permission definitions
- **role_permissions**: Role-to-permission assignments
- **user_has_roles**: User-to-role assignments

### Audit Bounded Context
- **audit_logs**: Immutable event log for compliance
- **error_traces**: Error tracking for debugging

## ERD Diagram (Mermaid)

```mermaid
erDiagram
    users ||--o| user_profiles : "has"
    users ||--o| user_security : "has"
    users ||--o| user_contacts : "has multiple"
    users ||--o| user_addresses : "has multiple"
    users ||--o| user_settings : "has"
    users ||--o| user_verifications : "has multiple"
    users ||--o| user_sessions : "has multiple"
    users ||--o| user_has_roles : "assigned"
    
    roles ||--o{ role_permissions : "contains"
    permissions ||--o{ role_permissions : "contained in"
    roles ||--o{ user_has_roles : "assigned to"
    users ||--o{ user_has_roles : "has roles"
    
    authorization_resources ||--o{ permissions : "defines"
    
    users {
        uuid id PK
        varchar email UK
        varchar username UK
        varchar password_hash
        varchar auth_provider
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }
    
    user_profiles {
        uuid id PK
        uuid user_id FK UK
        varchar first_name
        varchar last_name
        varchar display_name
        varchar avatar_url
        text bio
        date birth_date
    }
    
    user_security {
        uuid id PK
        uuid user_id FK UK
        int failed_login_attempts
        timestamptz locked_until
        timestamptz password_changed_at
        boolean two_factor_enabled
        varchar two_factor_secret
    }
    
    user_contacts {
        uuid id PK
        uuid user_id FK
        varchar type
        varchar value
        boolean is_primary
        boolean is_verified
    }
    
    user_addresses {
        uuid id PK
        uuid user_id FK
        varchar label
        varchar line1
        varchar line2
        varchar city
        varchar state
        varchar postal_code
        varchar country
        boolean is_default
    }
    
    user_settings {
        uuid id PK
        uuid user_id FK UK
        jsonb preferences
    }
    
    user_verifications {
        uuid id PK
        uuid user_id FK
        varchar channel
        boolean is_verified
        timestamptz verified_at
        varchar verification_token
    }
    
    user_sessions {
        uuid id PK
        uuid user_id FK
        varchar refresh_token_hash
        timestamptz expires_at
        varchar device_info
        varchar ip_address
        boolean is_revoked
    }
    
    roles {
        uuid id PK
        varchar name UK
        varchar description
    }
    
    permissions {
        uuid id PK
        uuid resource_id FK
        varchar key UK
        varchar resource
        varchar action
        varchar description
    }
    
    authorization_resources {
        uuid id PK
        varchar key UK
        varchar name
        varchar description
    }
    
    role_permissions {
        uuid id PK
        uuid role_id FK
        uuid permission_id FK
    }
    
    user_has_roles {
        uuid id PK
        uuid user_id FK
        uuid role_id FK
    }
    
    audit_logs {
        uuid id PK
        varchar action
        uuid actor_id
        varchar resource_type
        uuid resource_id
        varchar request_id
        jsonb meta
        timestamptz created_at
    }
```

## DDD Mapping

### Aggregates
- **UserAggregate**: Root entity `users` with entities `user_security`, `user_profiles`
- **SessionAggregate**: Root entity `user_sessions`
- **RoleAggregate**: Root entity `roles` with `role_permissions`

### Entities
- `users`: Identity aggregate root
- `user_security`: Security configuration entity
- `user_profiles`: Profile entity
- `user_contacts`: Contact method entity
- `user_addresses`: Address entity
- `user_sessions`: Session entity
- `roles`: Role aggregate root
- `permissions`: Permission entity

### Value Objects
- `Email`: Email address with validation
- `PhoneNumber`: Phone number with formatting
- `Address`: Structured address components
- `Preferences`: JSONB settings object

### Domain Services
- `AuthenticationService`: Login/logout/password management
- `AuthorizationService`: RBAC evaluation
- `VerificationService`: Email/phone verification
- `SessionService`: Session lifecycle management
- `AuditService`: Audit log creation

## Future Scalability Considerations

### Millions of Users
- Partition `audit_logs` and `user_sessions` by date
- Use connection pooling efficiently
- Implement read replicas for query separation
- Cache frequently accessed profiles

### Multi-Tenancy
- Add `tenant_id` column to all tables
- Implement Row Level Security (RLS) policies
- Use schema-per-tenant for high isolation needs

### OAuth/SSO Support
- `auth_provider` field supports external identity providers
- `external_id` can be added for provider-specific IDs
- `user_verifications` tracks OAuth account linking

### Microservice Extraction
- Each bounded context can become a separate service
- Clear foreign key boundaries enable database splitting
- Event sourcing ready via `audit_logs`

### Event-Driven Architecture
- `audit_logs` serves as event store
- Can integrate with message brokers (Kafka, RabbitMQ)
- Supports CQRS read model rebuilding

"""
