#!/usr/bin/env bash
# =============================================================================
# entrypoint.sh — Container entrypoint. NEVER destructive by contract.
#
#   1. Refuse to boot if RESET_DB_ON_STARTUP is set (destructive).
#   2. Sync pre-check: core tables exist but alembic_version missing -> stamp head.
#   3. alembic upgrade head.
#   4. Verify required core tables exist; fatal exit(1) if missing.
#   5. Drift check: alembic check (read-only); hard-stop unless DRIFT_CHECK_ENABLED=false.
#   6. exec "$@" if given, else uvicorn.
# =============================================================================
set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

log()   { printf '\033[0;34m[entrypoint]\033[0m %s\n' "$*"; }
fatal() { printf '\033[0;31m[entrypoint] FATAL:\033[0m %s\n' "$*" >&2; exit 1; }

REQUIRED_TABLES=(projects tasks)

# --- 1. Destructive-reset guard ---------------------------------------------
if [[ "${RESET_DB_ON_STARTUP:-false}" == "true" ]]; then
  fatal "RESET_DB_ON_STARTUP=true is refused. This entrypoint never drops data."
fi

# Helper: run a scalar SQL query via Python (asyncpg-free, uses sync psycopg?).
# We use Python + SQLAlchemy which is already installed.
table_exists() {
  local table="$1"
  python - "$table" <<'PY'
import asyncio
import sys

from sqlalchemy import text
from src.database import get_engine, dispose_engine


async def main(table: str) -> None:
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT to_regclass(:name)"),
            {"name": f"public.{table}"},
        )
        exists = result.scalar() is not None
    await dispose_engine()
    sys.exit(0 if exists else 1)


asyncio.run(main(sys.argv[1]))
PY
}

alembic_version_exists() {
  table_exists alembic_version
}

# --- 2. Sync pre-check ------------------------------------------------------
log "Checking migration state ..."
core_present=true
for t in "${REQUIRED_TABLES[@]}"; do
  if ! table_exists "$t"; then core_present=false; fi
done

if [[ "$core_present" == "true" ]] && ! alembic_version_exists; then
  log "Core tables present but alembic_version missing -> stamping head."
  alembic stamp head
fi

# --- 3. Apply migrations ----------------------------------------------------
log "Applying migrations (alembic upgrade head) ..."
alembic upgrade head

# --- 4. Verify required tables ----------------------------------------------
for t in "${REQUIRED_TABLES[@]}"; do
  if ! table_exists "$t"; then
    fatal "Required table '$t' missing after migration."
  fi
done
log "Required core tables verified."

# --- 5. Drift check ---------------------------------------------------------
if [[ "${DRIFT_CHECK_ENABLED:-true}" == "true" ]]; then
  log "Running drift check (alembic check) ..."
  if ! alembic check; then
    fatal "Model<->migration drift detected. Fix-forward with a new migration (or set DRIFT_CHECK_ENABLED=false to override)."
  fi
  log "No drift detected."
else
  log "Drift check disabled (DRIFT_CHECK_ENABLED=false)."
fi

# --- 6. Exec ----------------------------------------------------------------
if [[ "$#" -gt 0 ]]; then
  log "Executing: $*"
  exec "$@"
fi

log "Starting uvicorn on port ${PORT:-8000} ..."
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
