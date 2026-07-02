#!/usr/bin/env bash
# =============================================================================
# run-tests.sh — Run backend + frontend test suites the same way CI does.
# =============================================================================
set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() { printf '\033[0;34m[run-tests]\033[0m %s\n' "$*"; }

TARGET="${1:-all}"

run_backend() {
  log "Backend: ruff + mypy + pytest"
  cd "$ROOT_DIR/backend"
  ruff check src
  mypy src
  python -m pytest -q
  cd "$ROOT_DIR"
}

run_frontend() {
  log "Frontend: eslint + tsc + build + vitest"
  cd "$ROOT_DIR/frontend"
  npm run lint
  npm run type-check
  npm run build
  npx vitest run
  cd "$ROOT_DIR"
}

case "$TARGET" in
  backend)  run_backend ;;
  frontend) run_frontend ;;
  all)      run_backend; run_frontend ;;
  *) echo "Usage: $0 [backend|frontend|all]" >&2; exit 2 ;;
esac

log "All requested tests passed."
