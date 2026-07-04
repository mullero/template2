# new-model-checklist

Adding a SQLAlchemy model/table OR a column without breaking Cloud Run boot
(entrypoint runs `alembic check` and FATALs on drift):

1. Wire the model so `env.py` sees it — via `import_all_models()`.
2. Add it to `models/__init__.py`: the `TYPE_CHECKING` import, the
   `import_all_models()` body, AND `__all__` (or ruff F401 fires).
3. Column metadata must match the migration — `alembic check` compares type,
   `server_default`, AND column comments. A model `comment=` needs a matching
   `COMMENT ON COLUMN` (one stmt per `op.execute`) or omit both.
4. A model `id` with `index=True` needs an explicit
   `CREATE INDEX IF NOT EXISTS ix_<table>_id` (the PK's implicit index does NOT
   satisfy it) or `alembic check` reports phantom drift.
5. `Float` columns render as `FLOAT` in the migration (Postgres float8); keep the
   migration DDL as `FLOAT` to match the model.

Verify locally: `alembic upgrade head && alembic check` →
"No new upgrade operations detected." Escape hatch: `DRIFT_CHECK_ENABLED=false`.
Already-applied migrations don't re-run — heal deployed drift by changing the
MODEL or adding a NEW migration (fix-forward only).
