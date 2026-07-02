# QUICKSTART

Get `machote` running locally in a few minutes.

## Prerequisites

- Docker + Docker Compose v2
- (For non-Docker dev) Python >=3.12, Node.js >=20, `bash`

## 1. Configure

All configuration flows from the **root `.env`**. Copy the template and fill in
secrets (anything set to `CHANGE_ME`):

```bash
cp .env.example .env
$EDITOR .env
```

Optional per-environment / personal overrides (later wins):

- `.env.${DEPLOYMENT_ENVIRONMENT}` — e.g. `.env.production` (committed, non-secret)
- `.env.local` — personal overrides (gitignored)

## 2. Sync config

`sync-config.sh` reads `.env` (+ overrides) and **generates**:

- `backend/.env`
- `frontend/.env.development`
- `frontend/.env.production`

```bash
./scripts/sync-config.sh
```

It **validates** for `CHANGE_ME` placeholders and missing required vars and
refuses silent misconfiguration. **Never hand-edit the generated files** — they
carry a `DO NOT EDIT — auto-generated` header and are overwritten on every run.

## 3. Run the full stack

```bash
# --profile graph enables the Neo4j service (GRAPH_ENABLED=true)
docker compose --profile graph up --build
```

Or use the one-command helper (validates Docker, checks required keys, waits for
health, runs migrations):

```bash
./scripts/dev-test.sh
```

Services:

| Service          | URL                              |
| ---------------- | -------------------------------- |
| Backend API      | http://localhost:8000/api        |
| Backend health   | http://localhost:8000/health     |
| Swagger UI       | http://localhost:8000/docs       |
| Frontend         | http://localhost:5173            |
| Neo4j browser    | http://localhost:7474            |
| Firebase emu UI  | http://localhost:4000            |
| pgAdmin (opt.)   | http://localhost:5050            |
| Jaeger (opt.)    | http://localhost:16686           |

## 4. Local auth

Two options for local development:

1. **Firebase emulator (default).** `FIREBASE_AUTH_EMULATOR_HOST` is set; the
   `firebase-seed` one-shot creates a dev superadmin and promotes it via
   `/auth/bootstrap`.
2. **Auth disabled (fastest).** Set `AUTH_ENABLED=false` and
   `VITE_DISABLE_AUTH=true` in `.env`, re-run `sync-config.sh`. A stub superadmin
   with tenant `dev-tenant` is injected. **This is refused in production.**

## 5. Run tests

```bash
# Backend  (ruff + mypy strict + pytest)
cd backend
ruff check src && mypy src && python -m pytest -q

# Frontend (eslint + tsc + build + vitest)
cd frontend
npm install
npm run lint && npm run type-check && npm run build && npx vitest run
```

## 6. Database migrations

Migrations run automatically at container start (`entrypoint.sh`). Manually:

```bash
cd backend
alembic upgrade head       # apply
alembic check              # verify no model<->migration drift
alembic revision -m "add X" --autogenerate
```

See [.github/memory/new-model-checklist.md](.github/memory/new-model-checklist.md)
before adding a model or column.

## 7. Copy the vertical slice

The `Project` entity is implemented end-to-end. To add your own entity, copy:

- `backend/src/models/project.py` → model (NOT NULL `tenant_id`)
- `backend/alembic/versions/*_add_projects.py` → idempotent migration
- `backend/src/repositories/project_repository.py` → tenant-scoped reads
- `backend/src/graph/repositories/project_graph_repository.py` → graph projection
- `backend/src/api/routes/projects.py` → router under `/api` with `require_tenant`
- `frontend/src/api/projects.ts` + `frontend/src/hooks/useProjects.ts` +
  `frontend/src/pages/ProjectsPage.tsx` + `uiStrings` entries
- Tests on both sides.
