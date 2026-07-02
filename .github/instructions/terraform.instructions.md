---
applyTo: "terraform-mvp/**/*.tf"
---
# Terraform (Google Cloud Run MVP)

## Conventions
- Flat root module split into logical files (`network.tf`, `database.tf`,
  `cloudrun.tf`, `iam.tf`, …). Per-env values live in
  `environments/<env>.tfvars`; state config in `environments/<env>.backend.hcl`.
- Name resources `${local.name_prefix}-<thing>` where
  `name_prefix = "${var.app_name}-${var.environment}"`.
- Always attach `local.common_labels`.
- Run `terraform fmt` and keep `terraform validate` green (CI enforces this).

## Secrets
- **Never** put secret values in `.tf` or `.tfvars`. `CHANGE_ME` is a deliberate
  "must override" sentinel for non-secret required inputs only.
- The DB password is generated with `random_password` and written to Secret
  Manager. All other secret *values* are created empty and populated
  out-of-band (`scripts/create-secrets.sh` / CI).
- Cloud Run mounts secrets via `value_source.secret_key_ref`, never plaintext env.

## Security defaults
- Cloud SQL has **no public IP** (`ipv4_enabled = false`) — private IP + VPC
  connector only. Keep it that way.
- Runtime service accounts are least-privilege and per-service. Grant secret
  access with `google_secret_manager_secret_iam_member` on the specific secret,
  not project-wide.
- CI uses **Workload Identity Federation** (keyless), locked to
  `var.github_repository`. Never introduce downloaded SA JSON keys.
- Keep `db_deletion_protection = true` and backups/PITR on for staging/prod.

## Don't
- Don't widen IAM to `roles/editor`/`owner`. Don't disable deletion protection or
  make Cloud SQL public to "simplify" something.
