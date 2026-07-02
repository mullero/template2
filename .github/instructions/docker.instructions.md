---
applyTo: "**/{Dockerfile,docker-compose.yml,nginx.conf,.dockerignore}"
---
# Docker & local stack

## Dockerfiles
- Multi-stage builds; run as a **non-root** user. Frontend uses
  `nginxinc/nginx-unprivileged` on port 8080; backend runs uvicorn on 8000.
- Do **not** declare `VITE_*` as `ARG`/`ENV` in the frontend Dockerfile — Docker's
  secret heuristic flags `KEY`/`AUTH` substrings. Vite auto-loads
  `.env.production` at build time (allowed through `.dockerignore`).
- Keep a `HEALTHCHECK`. Keep `.dockerignore` excluding `.env*` except
  `.env.example`/`.env.production` as appropriate.

## nginx (frontend)
- Keep security headers + CSP. `/api/` proxy uses a runtime `resolver` + variable
  `set $api_upstream backend; proxy_pass http://$api_upstream:8000;` so nginx
  boots even when the backend is absent (502 at request time, not startup crash).
- SPA fallback `try_files $uri $uri/ /index.html` with no-cache on index.

## docker-compose
- **Always run `scripts/sync-config.sh` before `docker compose up`** to generate
  `backend/.env` and `frontend/.env.*` from the root `.env`.
- Optional services are behind profiles (`graph`, `auth`, `tools`,
  `observability`). Graph stack: `docker compose --profile graph up -d --build`.
- Host ports are decoupled via `*_HOST_PORT` env vars (internal ports fixed).
  If 5432/8000/8080 are taken, override e.g.
  `POSTGRES_HOST_PORT=5544 BACKEND_HOST_PORT=8100 FRONTEND_HOST_PORT=8181`.
- `backend` depends on `postgres` healthy only (not neo4j) — graph is optional.
- Note: `sync-config.sh` sources the shell env with `set -a`; `unset
  DATABASE_URL DEPLOYMENT_ENVIRONMENT` first if they leaked from a test session.
