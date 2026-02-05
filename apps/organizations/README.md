# Organizations App

Multi-tenant organization (company workspace) management. This app defines the tenancy boundary and enforces org-scoped access patterns.

## Responsibilities
- Organization creation with server-generated `org_id`.
- Automatic `ORG_ADMIN` role assignment for the creator.
- Organization-scoped query helpers to prevent cross-tenant access.
- Internal user invites and membership activation.

## API
- `POST /api/organizations`
- `POST /api/organizations/invites`
- `POST /api/organizations/invites/accept`

## Data Model
- `organizations` — tenant/workspace records
- `user_roles` — user membership + role per org
- `organization_invites` — pending invites and acceptance status

## Notes
- All org-scoped tables must include `org_id`.
- All queries must enforce org scoping.
- `POST /api/organizations/invites` requires `X-Org-Id` and an `ORG_ADMIN` role.
- Set `INVITE_ACCEPT_URL_BASE` to include a clickable acceptance link in invite emails.
