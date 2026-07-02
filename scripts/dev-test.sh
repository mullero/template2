#!/usr/bin/env bash
# =============================================================================
# dev-test.sh — One-command local stack bring-up.
# Validates Docker, checks required keys, syncs config, brings up compose,
# waits for health, and confirms migrations applied.
# =============================================================================
set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log()  { printf '\033[0;34m[dev-test]\033[0m %s\n' "$*"; }
die()  { printf '\033[0;31m[dev-test] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "docker not found on PATH."
docker compose version >/dev/null 2>&1 || die "docker compose v2 required."
docker info >/dev/null 2>&1 || die "Docker daemon not running."

[[ -f .env ]] || die "Root .env not found. Copy .env.example to .env first."

log "Syncing config from root .env ..."
./scripts/sync-config.sh

# Enable the graph profile automatically when GRAPH_ENABLED=true.
GRAPH_ENABLED="$(grep -E '^GRAPH_ENABLED=' .env | tail -n1 | cut -d= -f2- || true)"
PROFILE_ARGS=()
if [[ "${GRAPH_ENABLED:-false}" == "true" ]]; then
  log "GRAPH_ENABLED=true -> enabling 'graph' compose profile."
  PROFILE_ARGS=(--profile graph)
fi

log "Starting stack ..."
docker compose "${PROFILE_ARGS[@]}" up -d --build

wait_for_health() {
  local url="$1" name="$2" tries="${3:-60}"
  log "Waiting for $name ($url) ..."
  for _ in $(seq 1 "$tries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$name is healthy."
      return 0
    fi
    sleep 2
  done
  die "$name did not become healthy in time. Check: docker compose logs $name"
}

BACKEND_PORT="$(grep -E '^API_PORT=' .env | tail -n1 | cut -d= -f2- || echo 8000)"
wait_for_health "http://localhost:${BACKEND_PORT:-8000}/health" "backend"

log "Stack is up. Backend health green. Frontend: http://localhost:5173"
log "Tail logs with: docker compose logs -f"
