# machote

> Multi-tenant SaaS starter — a production-grade, fail-closed, zero-warning
> full-stack skeleton (FastAPI + React 19 + Postgres + Neo4j on GCP Cloud Run).

This repository is a **framework/skeleton**. It ships one complete end-to-end
vertical slice (`Project`) so you can copy the pattern and start building
features immediately on solid foundations.

## Architecture at a glance

| Layer        | Stack                                                                 |
| ------------ | --------------------------------------------------------------------- |
| Backend      | FastAPI, SQLAlchemy 2.x async + asyncpg, Alembic, Pydantic v2         |
| Graph        | Neo4j 5.x (async driver) — derived projection, Postgres = system of record |
| Frontend     | React 19, TypeScript (strict), Vite 6, react-router-dom 7, Vitest     |
| AI           | Gemini / Vertex AI                                                     |
| Auth         | Firebase / Identity Platform (multi-tenant), fail-closed guards       |
| Infra        | GCP Cloud Run + Cloud SQL + VPC, Terraform, keyless WIF CI/CD          |

```
/
├── backend/        # FastAPI + SQLAlchemy async + Alembic (+ Neo4j graph)
├── frontend/       # React 19 + TypeScript + Vite + Vitest
├── scripts/        # bash automation (config sync, tests, db init, seeds)
├── terraform-mvp/  # IaC: VPC + Cloud SQL + Cloud Run + Workload Identity
├── plans/          # architecture decision docs = source of truth
├── docs/           # operational / user-facing docs
├── .github/        # instructions, workflows, copilot-instructions, memory
├── .env.example    # documented template (committed)
├── docker-compose.yml
└── README.md / QUICKSTART.md
```

## Core principles

- **Centralized config.** Every env var lives in the root `.env`.
  `scripts/sync-config.sh` generates `backend/.env`, `frontend/.env.development`
  and `frontend/.env.production`. Never hand-edit the generated files.
- **Tenant isolation.** Every table has a NOT NULL `tenant_id`; every repository
  read requires a `tenant_id` and filters by it. Every Neo4j node/relationship
  carries `tenant_id` and every Cypher query is parameterized and tenant-scoped.
- **Fail-closed.** Production refuses to boot with `AUTH_ENABLED=false` or
  `CHANGE_ME` secrets. The entrypoint refuses destructive resets.
- **Zero-warning.** ruff + mypy strict (backend), ESLint `--max-warnings 0` +
  strict tsc (frontend). CI enforces model↔migration drift checks.
- **Fix-forward.** Migrations are idempotent and never destructive.

## Quick start

See [QUICKSTART.md](QUICKSTART.md). TL;DR:

```bash
cp .env.example .env          # fill in secrets (CHANGE_ME values)
./scripts/sync-config.sh      # generate per-app env files
docker compose --profile graph up --build
# backend  -> http://localhost:8000/health
# frontend -> http://localhost:5173
```

## Running tests

```bash
# Backend
cd backend && ruff check src && mypy src && python -m pytest -q

# Frontend
cd frontend && npm run lint && npm run type-check && npm run build && npx vitest run
```

## Deploying

Infrastructure is owned by Terraform (`terraform-mvp/`), not CI. CI/CD builds an
image once and rolls it via `gcloud run services update --image`. Auth to GCP is
keyless via Workload Identity Federation. See
[docs/deployment.md](docs/deployment.md) and
[plans/deployment-architecture.md](plans/deployment-architecture.md).

## The `plans/` directory is the source of truth

Consult `plans/*.md` before changing architecture, tables, or endpoints, and
update the relevant plan in the same PR. New decisions get a new `plans/*.md`
file — never bury architectural decisions in code comments.
