# Deployment guide

How to deploy machote to Google Cloud Run using `terraform-mvp/` and the GitHub
Actions workflows. See [terraform-mvp/README.md](../terraform-mvp/README.md) for
module details.

## Topology

```
                         ┌────────────────────────── GCP project (per env) ─────────────┐
GitHub Actions ──WIF──►  │  Cloud Run: frontend (nginx SPA, :8080)                       │
 (keyless deploy)        │  Cloud Run: backend  (FastAPI, :8000) ──VPC connector──┐      │
                         │  Artifact Registry (images)                            ▼      │
                         │  Secret Manager (SECRET_KEY, db pwd, Firebase, ...)  Cloud SQL │
                         │                                                     (private IP)│
                         └───────────────────────────────────────────────────────────────┘
   Neo4j (AuraDB / self-managed, optional)  ◄── NEO4J_URI/PASSWORD via Secret Manager
```

- Frontend SPA calls the backend's **public URL directly** (`VITE_API_URL` baked
  at build). The nginx `/api` proxy is only used in local compose.
- Backend reaches Cloud SQL over the VPC connector via **private IP**; the DB has
  no public IP.

## One-time bootstrap (per environment)

```bash
cd terraform-mvp
./scripts/bootstrap-state.sh <project_id> <state_bucket>   # GCS state bucket
./scripts/enable-apis.sh <project_id>                       # enable APIs
# Edit environments/<env>.tfvars and <env>.backend.hcl (replace CHANGE_ME).
terraform init  -backend-config=environments/<env>.backend.hcl
terraform apply -var-file=environments/<env>.tfvars
# Populate externally-managed secret values (SECRET_KEY, Firebase, Neo4j, Gemini):
PROJECT_ID=<project_id> ENV=<env> ./scripts/create-secrets.sh
```

### Grant CI access

After the first apply, read the outputs and set them as **GitHub Actions
Variables** (per Environment):

```bash
terraform output           # backend_url, frontend_url, wif_provider, deployer_service_account, artifact_registry_repo
```

| GitHub Variable   | Value |
|-------------------|-------|
| `GCP_PROJECT_ID`  | your project id |
| `GCP_REGION`      | e.g. `us-central1` |
| `WIF_PROVIDER`    | `wif_provider` output |
| `DEPLOYER_SA`     | `deployer_service_account` output |
| `TF_STATE_BUCKET` | your state bucket |

The deployer SA is scoped to `var.github_repository` — set that in the tfvars.

## Ongoing deploys

Trigger the **Deploy** workflow (`.github/workflows/deploy.yml`) via
*Actions → Deploy → Run workflow*, choosing the environment. It:

1. Authenticates via WIF (no keys).
2. Builds & pushes `backend` and `frontend` images to Artifact Registry
   (tagged with the commit SHA).
3. Runs `terraform apply` with the new image vars, rolling out Cloud Run.

Database migrations run from the backend container entrypoint
(`backend/entrypoint.sh` → `alembic upgrade head`) on startup.

## CI gates (on every PR)

- `.github/workflows/ci.yml` — backend `ruff`/`mypy`/`pytest`, frontend
  `tsc`/`eslint`/`build`/`vitest`.
- `.github/workflows/terraform.yml` — `terraform fmt -check` + `validate`.

## Environments

| Env | HA DB | Deletion protection | Min instances | Graph/AI |
|-----|-------|---------------------|---------------|----------|
| test    | no  | off | 0 | off |
| staging | no  | on  | 0 | on  |
| prod    | yes (REGIONAL) | on | 1 | on |

## Rollback

- App: re-run Deploy against a previous commit SHA (images are SHA-tagged), or
  `gcloud run services update-traffic` to a prior revision.
- Infra: `terraform` state is versioned in GCS; revert the tfvars/module change
  and re-apply.

## Security checklist before prod

- [ ] All `CHANGE_ME` replaced in tfvars and root `.env`.
- [ ] `AUTH_ENABLED=true`, `VITE_DISABLE_AUTH` unset/false.
- [ ] `CORS_ORIGINS` set to explicit frontend origin(s).
- [ ] Secrets populated in Secret Manager; none in the repo.
- [ ] Cloud SQL private-IP only; `db_deletion_protection = true`.
- [ ] WIF provider locked to the correct `github_repository`.
