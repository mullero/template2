# machote — Copilot repository instructions

machote is a multi-tenant SaaS **starter skeleton**. It ships one complete
vertical slice (`Project` → `Task`) across a FastAPI backend, a React/Vite
frontend, a Neo4j graph projection, and Terraform for Google Cloud Run. Treat it
as a template: keep the structure, patterns, and guardrails intact when adding
features.

## Golden rules

1. **Secure, fail-closed defaults.** Auth is enabled by default. Never weaken a
   security default to make something "just work". Never commit secrets — use
   `CHANGE_ME` placeholders and Secret Manager / `.env` (gitignored).
2. **Zero-warning bar.** Backend must pass `ruff check` + `mypy` with no errors.
   Frontend must pass `tsc`, `eslint --max-warnings 0`, and `vite build`. Do not
   suppress warnings; fix the cause.
3. **Fix forward.** When you touch code, leave it green. Run the relevant
   validation before declaring done.
4. **Multi-tenancy is mandatory.** Every domain row and every graph node carries
   a `tenant_id`. Never write a query, repository, or Cypher statement that can
   read/write across tenants.
5. **Postgres is the system of record; Neo4j is a derived projection.** Writes
   go to Postgres first, then project to the graph. The graph must never hold
   data that isn't reconstructable from Postgres.

## Architecture at a glance

```
frontend/ (React 19 + Vite + TS strict)     terraform-mvp/ (Cloud Run + Cloud SQL)
   │ axios → /api                                docker-compose.yml (local full stack)
   ▼
backend/ (FastAPI, Python 3.12)
   routes → services → repositories → models (SQLAlchemy async)
                                   └→ graph/ (Neo4j async projection)
```

- Backend package root is `backend/src` (`PYTHONPATH=/app`, imports like
  `from src.models...`).
- Config flows from the root `.env` → `scripts/sync-config.sh` generates
  `backend/.env` and `frontend/.env.*`. **Always run `sync-config.sh` before
  `docker compose up`.**

## Where things live

| Concern | Path |
|---|---|
| API routes | `backend/src/api/routes/` |
| Business logic | `backend/src/services/` |
| Data access (Postgres) | `backend/src/repositories/` |
| ORM models | `backend/src/models/` |
| Graph projection | `backend/src/graph/` |
| Settings | `backend/src/config.py` |
| Migrations | `backend/alembic/` |
| Frontend pages/hooks/api | `frontend/src/{pages,hooks,api}/` |
| Infra | `terraform-mvp/` |

## Adding a new entity (the intended workflow)

1. SQLAlchemy model in `backend/src/models/` (include `tenant_id`).
2. Alembic migration (`alembic revision --autogenerate`).
3. Repository in `backend/src/repositories/` (tenant-scoped queries only).
4. Pydantic schemas + service + routes under `backend/src/api/routes/`.
5. Graph projection in `backend/src/graph/` if the entity participates in the graph.
6. Backend tests (`backend/tests/`).
7. Frontend `api/`, `hooks/`, `pages/`, and tests mirroring the slice.

## Validation commands

```bash
# Backend
cd backend && source .venv/bin/activate && ruff check src/ && mypy src/ && pytest -q
# Frontend
cd frontend && npm run type-check && npm run lint && npm run build && npx vitest run
# Full stack (host ports may need overriding — see docker-compose.yml)
scripts/sync-config.sh && docker compose --profile graph up -d --build
```

More specific rules live in `.github/instructions/*.instructions.md`, scoped by
file globs.
