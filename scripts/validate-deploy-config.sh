#!/usr/bin/env bash
# =============================================================================
# validate-deploy-config.sh — Fail CI if non-secret deploy env vars in
# .env.production drift from what the app/terraform expects. Secrets are NEVER
# checked here (they live only in Secret Manager / GitHub Environment secrets).
# =============================================================================
set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

die() { printf '\033[0;31m[validate-deploy] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }
log() { printf '\033[0;34m[validate-deploy]\033[0m %s\n' "$*"; }

PROD_ENV_FILE=".env.production"
[[ -f "$PROD_ENV_FILE" ]] || { log "No $PROD_ENV_FILE present; nothing to validate."; exit 0; }

# Non-secret vars that MUST be present and non-placeholder in production.
REQUIRED_NON_SECRET=(
  DEPLOYMENT_ENVIRONMENT PROJECT_NAME API_VERSION
  ENABLE_SWAGGER ENABLE_DETAILED_ERRORS AUTH_ENABLED
  CORS_ORIGINS VITE_API_URL GRAPH_ENABLED
)

# Secrets that MUST NOT be committed to .env.production (must come from SM).
FORBIDDEN_SECRETS=(
  POSTGRES_PASSWORD SECRET_KEY GEMINI_API_KEY NEO4J_PASSWORD
  BOOTSTRAP_ADMIN_PASSWORD SENTRY_DSN
)

errors=0
get() { grep -E "^$1=" "$PROD_ENV_FILE" | tail -n1 | cut -d= -f2- || true; }

for var in "${REQUIRED_NON_SECRET[@]}"; do
  val="$(get "$var")"
  if [[ -z "$val" ]]; then
    echo "Missing required non-secret var: $var" >&2; errors=$((errors + 1))
  elif [[ "$val" == *CHANGE_ME* ]]; then
    echo "Placeholder value for $var in $PROD_ENV_FILE" >&2; errors=$((errors + 1))
  fi
done

for var in "${FORBIDDEN_SECRETS[@]}"; do
  val="$(get "$var")"
  if [[ -n "$val" ]]; then
    echo "Secret '$var' must NOT be set in $PROD_ENV_FILE (use Secret Manager)." >&2
    errors=$((errors + 1))
  fi
done

# Production hard rules.
[[ "$(get DEPLOYMENT_ENVIRONMENT)" == "production" ]] || { echo "DEPLOYMENT_ENVIRONMENT must be 'production'." >&2; errors=$((errors + 1)); }
[[ "$(get AUTH_ENABLED)" == "true" ]] || { echo "AUTH_ENABLED must be 'true' in production." >&2; errors=$((errors + 1)); }
[[ "$(get ENABLE_DETAILED_ERRORS)" == "false" ]] || { echo "ENABLE_DETAILED_ERRORS must be 'false' in production." >&2; errors=$((errors + 1)); }

[[ "$errors" -eq 0 ]] || die "$errors deploy-config validation error(s)."
log "Deploy config OK."
