---
applyTo: "backend/alembic/**/*.py"
---
# Database migrations (Alembic)

- Generate with `alembic revision --autogenerate -m "<desc>"` after changing a
  model, then **review** the generated migration — autogenerate misses things
  (server defaults, enum changes, index renames). Edit as needed.
- Every domain table must include a non-nullable `tenant_id` column and an index
  that leads with `tenant_id` for tenant-scoped queries.
- Migrations must be **reversible**: implement `downgrade()` unless truly
  impossible (document why).
- Never edit an already-applied/committed migration — add a new one.
- Keep migrations deterministic and data-safe: no destructive column drops
  without a considered data-migration step. Batch large backfills.
- Apply locally with `alembic upgrade head`; CI/entrypoint runs it on deploy.
