---
applyTo: "backend/**/*.py"
---
# Backend (FastAPI + SQLAlchemy async)

## Structure & imports
- Package root is `backend/src`; import as `from src.models.project import Project`.
- Layering is strict: **routes → services → repositories → models**. Routes never
  touch the ORM session directly for business logic; put it in a service or
  repository. Repositories never import from `services`/`api`.

## Async everywhere
- Use `async def` for all I/O. The DB session is `AsyncSession` (asyncpg).
- Never call blocking I/O in a request path. Use `httpx.AsyncClient` for HTTP.

## Multi-tenancy (non-negotiable)
- Every table has `tenant_id`. Every read/write filters by `tenant_id`.
- Repository methods take `tenant_id` explicitly; never rely on a global.
- Never expose a route that returns another tenant's data.

## Types & style
- Full type hints; code must pass `mypy` (strict-ish) with no errors.
- `ruff check src/` must be clean. Prefer `ruff format`-compatible formatting.
- Pydantic v2 (`model_config`, `Field`, `field_validator`). Settings via
  `pydantic-settings` in `src/config.py` — read config through the settings
  object, never `os.environ` scattered in modules.

## Errors & responses
- Raise `HTTPException` (or a domain exception mapped to one) from routes.
- Don't leak internals: detailed errors are gated behind `ENABLE_DETAILED_ERRORS`
  (off in prod).

## Don't
- Don't add `from __future__ import annotations` to route modules that use
  slowapi decorators or FastAPI dependency params — it breaks FastAPI's runtime
  type resolution (body/deps get treated as query params). Rate limiting is
  applied globally via `SlowAPIMiddleware`, not per-route decorators.
- Don't create abstractions for a single call site. Don't add error handling for
  impossible states.

## Validate
```bash
cd backend && source .venv/bin/activate && ruff check src/ && mypy src/ && pytest -q
```
