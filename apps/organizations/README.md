# Organizations App

Multi-tenant organization (company workspace) management. This app defines the tenancy boundary and enforces org-scoped access patterns.

## Responsibilities
- Organization creation with server-generated `org_id`.
- Organization-scoped query helpers to prevent cross-tenant access.

## API
- `POST /api/organizations`
- `POST /api/organizations/invites`
- `POST /api/organizations/invites/accept`

## Data Model
- `organizations` — tenant/workspace records

## Notes
- All org-scoped tables must include `org_id`.
- All queries must enforce org scoping.
- Invite workflows and roles live in the `access_control` app.
