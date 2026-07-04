# AGENTS.md — orientation for AI agents working in this repo

If you are an AI agent starting a session here, read this first. It tells you
what this project is, how it is wired, and the rules you must keep.

## What this is

`app-skeleton` is a **multi-tenant SaaS starter skeleton** — a production-shaped
framework with NO real business features yet. It exists to be copied: keep the
structure, patterns, and guardrails intact when you add features.

It ships **two complete vertical slices** so you can mirror the pattern:

1. **Sync slice** `Project → Task` — model → migration → tenant-scoped repository
   → `/api/projects` router (`require_tenant`) → Neo4j graph projection → typed
   `api/` + `hooks/` + `pages/` + tests on both sides.
2. **Async slice** `Document + Job` — the durable background-job + AI-extraction
   pipeline: upload → quota reserve → enqueue (Cloud Tasks) → OIDC-authed worker
   → confidence gate (auto-commit vs human-review) → tenant-scoped status polling
   → a global frontend progress provider that survives navigation.

Toggles (all default-on here, gated by env): AI (Gemini/Vertex), Neo4j graph,
Cloud Tasks background jobs.

## Source of truth — read before changing architecture

- **`plans/*.md`** = architecture decisions. Consult the relevant plan before
  changing tables, endpoints, or flows, and update it in the SAME change. New
  decisions get a NEW `plans/*.md` file — never bury a decision in a code comment.
  - `plans/graph-database-architecture.md`, `plans/background-jobs.md`,
    `plans/document-processing-flow.md`, `plans/analytics-architecture.md`.
- **`.github/memory/*.md`** = hard-won operational facts (boot-time drift checks,
  test-isolation constraints, KPI placement). Read them before touching models,
  migrations, or the async worker.
- **`.github/instructions/*.instructions.md`** = coding rules scoped by `applyTo`
  globs (secure-coding, tenant-isolation, background-jobs, graph-database, …).
- **`.github/copilot-instructions.md`** = the condensed rulebook + repo cheat sheet.

## Architecture at a glance

```
frontend/ (React 19 + Vite + TS strict)        terraform-mvp/ (Cloud Run + Cloud SQL + Cloud Tasks)
   │ axios → /api                                 docker-compose.yml (local full stack)
   ▼
backend/ (FastAPI, Python 3.12)
   api/routes → services → repositories → models (SQLAlchemy async)
                          ├→ graph/         (Neo4j async projection — derived)
                          ├→ task_queue+worker+internal route (Cloud Tasks jobs)
                          └→ document_extraction + quota + email (AI pipeline)
```

- Backend package root is `backend/src` (`PYTHONPATH=/app`, imports `from src...`).
- **Postgres is the system of record; Neo4j is a derived, disposable projection.**
- Background work is **Cloud Tasks** (durable, retryable), never in-process
  `BackgroundTasks`. Locally `TASKS_ENABLED=false` runs the worker INLINE — no
  emulator needed.

## Where things live

| Concern | Path |
|---|---|
| API routes | `backend/src/api/routes/` (`projects`, `documents`, `jobs`, `internal`, `auth`, `dev`) |
| Services | `backend/src/services/` (`task_queue`, `worker`, `document_extraction`, `quota_service`, `email_service`, `scheduler`, `graph_projection`, `ai_service`, `auth_service`) |
| Repositories (Postgres) | `backend/src/repositories/` |
| ORM models | `backend/src/models/` (every row has NOT NULL `tenant_id`) |
| Graph projection | `backend/src/graph/` |
| Settings | `backend/src/config.py` (`get_settings()` cached singleton) |
| Migrations | `backend/alembic/versions/` (idempotent, `IF [NOT] EXISTS`, one stmt/op) |
| Auth guards | `backend/src/dependencies/auth.py` (+ `internal_auth.py` for OIDC) |
| Frontend api/hooks/pages | `frontend/src/{api,hooks,pages}/` |
| Global job progress | `frontend/src/contexts/JobProgressContext.tsx` |
| UI strings (no hard-coded JSX text) | `frontend/src/constants/uiStrings.ts` |
| Infra | `terraform-mvp/` (Terraform owns env/secrets/probes, not CI) |

## Configuration — single source of truth

All env vars live in the root `.env` (gitignored; template is `.env.example`).
`scripts/sync-config.sh` reads `.env` (+ `.env.${DEPLOYMENT_ENVIRONMENT}` +
`.env.local`) and GENERATES `backend/.env`, `frontend/.env.development`,
`frontend/.env.production`. **Never hand-edit the generated files.** Always run
`scripts/sync-config.sh` before `docker compose up`.

## Non-negotiable guardrails

1. **Secure, fail-closed.** Auth on by default; production refuses to boot with
   `AUTH_ENABLED=false`. Never commit secrets — use `CHANGE_ME` + Secret Manager.
2. **Multi-tenancy is mandatory.** Every repository read takes a required
   `tenant_id` and filters on it; every Cypher `MATCH`/`MERGE` pins `tenant_id`.
   A request scoped to tenant A must NEVER see tenant B's data.
3. **Zero-warning bar / fix forward.** Leave code green: `ruff` + `mypy --strict`
   (backend), `tsc` + `eslint --max-warnings 0` + `vite build` (frontend).
4. **Postgres first, then project to the graph** (best-effort, idempotent MERGE).
5. **Jobs:** enqueue AFTER the Postgres commit; workers are idempotent (skip
   `succeeded`) and authenticate via the Cloud Tasks OIDC token, not Firebase.

## Adding a new entity (intended workflow)

1. SQLAlchemy model in `models/` (include `tenant_id`) → register in
   `models/__init__.py` (see `.github/memory/new-model-checklist.md`).
2. Alembic migration (idempotent) → verify `alembic upgrade head && alembic check`
   → "No new upgrade operations detected."
3. Tenant-scoped repository → Pydantic schemas + service + router under `/api`
   with `require_tenant`.
4. Graph projection in `graph/` if it participates in the graph.
5. Backend tests (`backend/tests/{unit,integration}`), then mirror the slice in
   the frontend (`api/` → `hooks/` → `pages/` → tests).

## Validate before declaring done

```bash
# Backend (needs a Postgres for integration tests; they skip cleanly otherwise)
cd backend && source .venv/bin/activate && ruff check src && mypy src && python -m pytest -q
# Frontend
cd frontend && npm run lint && npm run type-check && npm run build && npx vitest run
# Full stack
scripts/sync-config.sh && docker compose --profile graph up -d --build   # both /health green
```

Local integration DB: `docker run --rm -e POSTGRES_USER=app_skeleton
-e POSTGRES_PASSWORD=app_skeleton -e POSTGRES_DB=app_skeleton_test -p 55432:5432
postgres:15-alpine`, then export
`TEST_DATABASE_URL=postgresql+asyncpg://app_skeleton:app_skeleton@localhost:55432/app_skeleton_test`.
