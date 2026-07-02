#!/usr/bin/env bash
# Enable the GCP APIs Terraform needs. Terraform also enables them via
# google_project_service, but enabling up-front avoids first-apply race errors.
set -euo pipefail

PROJECT_ID="${1:-}"
if [[ -z "${PROJECT_ID}" ]]; then
  echo "Usage: $0 <project_id>" >&2
  exit 1
fi

APIS=(
  run.googleapis.com
  sqladmin.googleapis.com
  compute.googleapis.com
  servicenetworking.googleapis.com
  vpcaccess.googleapis.com
  artifactregistry.googleapis.com
  secretmanager.googleapis.com
  iam.googleapis.com
  iamcredentials.googleapis.com
  sts.googleapis.com
  cloudresourcemanager.googleapis.com
  aiplatform.googleapis.com
)

echo "==> Enabling ${#APIS[@]} APIs on ${PROJECT_ID}"
gcloud services enable "${APIS[@]}" --project "${PROJECT_ID}"
echo "==> Done."
