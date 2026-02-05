# Core App

Foundation utilities and shared application concerns that don't belong to a specific domain. Keep this app lightweight and avoid placing domain-specific logic here.

## Current Responsibilities
- Example endpoint for basic wiring tests.
- Celery task placeholders and shared service patterns.

## Notes
- Domain logic should live in dedicated apps (e.g., `organizations`).
- If you add shared primitives here, keep them framework-agnostic where possible.
