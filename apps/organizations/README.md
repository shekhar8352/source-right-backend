# Organizations App

Multi-tenant organization (company workspace) management. This app defines the tenancy boundary and enforces org-scoped access patterns.

## Responsibilities
- Organization creation with server-generated `org_id`.
- Automatic `ORG_ADMIN` role assignment for the creator.
- Organization-scoped query helpers to prevent cross-tenant access.

## API
- `POST /api/organizations`

## Data Model
- `organizations` — tenant/workspace records
- `user_roles` — user membership + role per org

## Notes
- All org-scoped tables must include `org_id`.
- All queries must enforce org scoping.
