#!/usr/bin/env bash
# Populate the externally-managed Secret Manager secrets that Terraform created
# empty (SECRET_KEY, FIREBASE_PROJECT_ID, and optionally Neo4j/Gemini). Values
# are read from stdin/env so they never touch the repo or Terraform state.
#
# Usage:
#   PROJECT_ID=machote-prod ENV=prod ./scripts/create-secrets.sh
#
# You will be prompted for each value. Existing versions are left intact unless
# you enter a new value.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
ENV="${ENV:-}"
APP="${APP:-machote}"

if [[ -z "${PROJECT_ID}" || -z "${ENV}" ]]; then
  echo "Set PROJECT_ID and ENV (test|staging|prod). Example:" >&2
  echo "  PROJECT_ID=machote-prod ENV=prod $0" >&2
  exit 1
fi

PREFIX="${APP}-${ENV}"

add_secret() {
  local secret_id="$1" prompt="$2"
  read -r -s -p "${prompt} (blank to skip): " value
  echo
  if [[ -z "${value}" ]]; then
    echo "    skipped ${secret_id}"
    return
  fi
  printf '%s' "${value}" | gcloud secrets versions add "${secret_id}" \
    --project "${PROJECT_ID}" --data-file=- >/dev/null
  echo "    updated ${secret_id}"
}

echo "==> Adding secret versions for ${PREFIX} in ${PROJECT_ID}"
add_secret "${PREFIX}-secret-key"       "Backend SECRET_KEY"
add_secret "${PREFIX}-firebase-project" "Firebase project ID"
add_secret "${PREFIX}-neo4j-uri"        "Neo4j URI (if graph enabled)"
add_secret "${PREFIX}-neo4j-password"   "Neo4j password (if graph enabled)"
add_secret "${PREFIX}-gemini-api-key"   "Gemini API key (if AI enabled)"
echo "==> Done."
