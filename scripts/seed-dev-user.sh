#!/usr/bin/env bash
# =============================================================================
# seed-dev-user.sh — Create a dev superadmin in the Firebase Auth emulator and
# promote it via the backend /auth/bootstrap endpoint. Run by the
# `firebase-seed` one-shot container. Safe to re-run.
# =============================================================================
set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

log() { printf '\033[0;34m[seed]\033[0m %s\n' "$*"; }
die() { printf '\033[0;31m[seed] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

EMULATOR_HOST="${FIREBASE_AUTH_EMULATOR_HOST:-firebase-emulator:9099}"
PROJECT_ID="${FIREBASE_PROJECT_ID:-machote-local}"
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
ADMIN_EMAIL="${BOOTSTRAP_ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-devpassword}"
TENANT_ID="${BOOTSTRAP_TENANT_ID:-dev-tenant}"

log "Waiting for Firebase Auth emulator at ${EMULATOR_HOST} ..."
for _ in $(seq 1 30); do
  if curl -fsS "http://${EMULATOR_HOST}/" >/dev/null 2>&1; then break; fi
  sleep 2
done

log "Creating dev user ${ADMIN_EMAIL} ..."
SIGNUP_RESP="$(curl -fsS -X POST \
  "http://${EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=fake-api-key" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\",\"returnSecureToken\":true}" \
  || echo '')"

if [[ -z "$SIGNUP_RESP" ]]; then
  log "User may already exist; signing in instead."
  SIGNUP_RESP="$(curl -fsS -X POST \
    "http://${EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\",\"returnSecureToken\":true}")"
fi

ID_TOKEN="$(printf '%s' "$SIGNUP_RESP" | sed -n 's/.*"idToken":"\([^"]*\)".*/\1/p')"
[[ -n "$ID_TOKEN" ]] || die "Could not obtain an ID token from the emulator."

log "Waiting for backend at ${BACKEND_URL}/health ..."
for _ in $(seq 1 60); do
  if curl -fsS "${BACKEND_URL}/health" >/dev/null 2>&1; then break; fi
  sleep 2
done

log "Bootstrapping first superadmin via ${BACKEND_URL}/api/auth/bootstrap ..."
curl -fsS -X POST "${BACKEND_URL}/api/auth/bootstrap" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"tenant_id\":\"${TENANT_ID}\"}" || die "Bootstrap request failed."

log "Dev superadmin ready: ${ADMIN_EMAIL} (tenant ${TENANT_ID})."
