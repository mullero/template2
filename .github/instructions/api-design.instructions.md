---
applyTo: "backend/src/api/**/*.py"
---
# API design

- One router module per resource under `src/api/routes/`. Register on the app in
  `src/main.py` with a versioned prefix (`/api`).
- Request/response models are explicit Pydantic v2 schemas — never return ORM
  objects directly. Separate `Create`, `Update`, and `Read` schemas.
- Dependencies (auth principal, DB session, tenant) come via FastAPI `Depends`.
  Derive `tenant_id` from the authenticated principal, not the request body.
- Status codes: 201 on create, 204 on delete, 404 for not-found (scoped to
  tenant so you never confirm existence across tenants), 422 handled by FastAPI.
- **Do not** use `from __future__ import annotations` in route modules — it
  breaks FastAPI's runtime resolution of body/dependency params. Do not add
  per-route slowapi decorators; global rate limiting is applied via
  `SlowAPIMiddleware`.
- Keep routes thin: validation + delegate to a service/repository. No business
  logic or raw SQL in the route body.
- Pagination and filtering are tenant-scoped by construction.
