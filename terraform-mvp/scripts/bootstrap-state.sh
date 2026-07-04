#!/usr/bin/env bash
# Create the GCS bucket that holds Terraform remote state. Run ONCE per project
# before the first `terraform init`. Requires the gcloud CLI and owner/editor on
# the target project.
set -euo pipefail

PROJECT_ID="${1:-}"
BUCKET="${2:-}"
LOCATION="${3:-US}"

if [[ -z "${PROJECT_ID}" || -z "${BUCKET}" ]]; then
  echo "Usage: $0 <project_id> <bucket_name> [location]" >&2
  echo "Example: $0 app-skeleton-prod app-skeleton-prod-tfstate US" >&2
  exit 1
fi

echo "==> Ensuring bucket gs://${BUCKET} exists in project ${PROJECT_ID}"
if ! gcloud storage buckets describe "gs://${BUCKET}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET}" \
    --project "${PROJECT_ID}" \
    --location "${LOCATION}" \
    --uniform-bucket-level-access \
    --public-access-prevention
else
  echo "    bucket already exists"
fi

echo "==> Enabling object versioning (state history / recovery)"
gcloud storage buckets update "gs://${BUCKET}" --versioning

echo "==> Done. Set 'bucket = \"${BUCKET}\"' in environments/<env>.backend.hcl"
