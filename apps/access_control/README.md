# Access Control App

Authorization and membership boundaries (roles, permissions, scopes, invitations). This app owns organization membership and RBAC enforcement helpers.

## Current Responsibilities
- User roles per organization.
- Organization invites and acceptance workflow.
- Role-based enforcement helpers used by API views.
- Organization context middleware enforcement.

## Role Types
- `ORG_ADMIN`
- `FINANCE`
- `APPROVER`
- `VIEWER`
- `VENDOR`

## Org Context Enforcement
Requests under `/api/` must include `X-Org-Id` and the user must belong to the org. Enforcement is done in
`apps/organizations/middleware.py` and attaches:
- `request.organization`
- `request.organization_role`

Exempt paths are configured in `sourceright/settings/base.py` via `ORG_CONTEXT_EXEMPT_PATHS`.

## Internal API Guardrails
Internal APIs are prefixed by `/api/internal/` and are blocked for the `VENDOR` role at middleware level.
This prefix list is configured via `INTERNAL_API_PREFIXES`.

## Phase 1 Permission Matrix
Action | Admin | Finance | Approver | Viewer | Vendor
---|---|---|---|---|---
Create vendor | ✅ | ✅ | ❌ | ❌ | ❌
Approve invoice | ❌ | ❌ | ✅ | ❌ | ❌
View invoices | ✅ | ✅ | ✅ | ✅ | ❌
Upload invoice | ❌ | ❌ | ❌ | ❌ | ✅

## Enforcement Points
- Middleware enforces org context, blocks vendor access to internal APIs, and prevents viewer mutations.
- View-layer guards live in `apps/access_control/permissions.py` and return 403 on unauthorized actions.

## Notes
- All membership queries must be org-scoped.
