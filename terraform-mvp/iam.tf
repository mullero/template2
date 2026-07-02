# =============================================================================
# IAM: least-privilege runtime service accounts for each Cloud Run service, and
# (optionally) Workload Identity Federation so GitHub Actions can deploy without
# long-lived JSON keys.
# =============================================================================

# --- Runtime service accounts -----------------------------------------------
resource "google_service_account" "backend" {
  account_id   = "${local.name_prefix}-backend"
  display_name = "${var.app_name} ${var.environment} backend runtime"
}

resource "google_service_account" "frontend" {
  account_id   = "${local.name_prefix}-frontend"
  display_name = "${var.app_name} ${var.environment} frontend runtime"
}

# Backend needs: Cloud SQL client, secret access, logging/metrics, (opt) Vertex.
resource "google_project_iam_member" "backend_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_vertex_user" {
  count   = var.ai_enabled ? 1 : 0
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Grant the backend SA accessor on exactly the secrets it mounts.
resource "google_secret_manager_secret_iam_member" "backend_db_password" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_external" {
  for_each  = google_secret_manager_secret.external
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# Frontend needs only logging/metrics.
resource "google_project_iam_member" "frontend_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

# =============================================================================
# Workload Identity Federation (keyless GitHub Actions deploys).
# =============================================================================
resource "google_iam_workload_identity_pool" "github" {
  count                     = var.enable_wif ? 1 : 0
  workload_identity_pool_id = "${local.name_prefix}-gh-pool"
  display_name              = "${var.app_name} ${var.environment} GitHub"
  depends_on                = [google_project_service.enabled]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  count                              = var.enable_wif ? 1 : 0
  workload_identity_pool_id          = google_iam_workload_identity_pool.github[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Only tokens from the configured repository may use this provider.
  attribute_condition = "assertion.repository == \"${var.github_repository}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "deployer" {
  count        = var.enable_wif ? 1 : 0
  account_id   = "${local.name_prefix}-deployer"
  display_name = "${var.app_name} ${var.environment} CI deployer"
}

# Allow the GitHub repo (via WIF) to impersonate the deployer SA.
resource "google_service_account_iam_member" "deployer_wif" {
  count              = var.enable_wif ? 1 : 0
  service_account_id = google_service_account.deployer[0].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[0].name}/attribute.repository/${var.github_repository}"
}

# Deployer permissions: deploy Cloud Run, push images, actAs the runtime SAs.
resource "google_project_iam_member" "deployer_run_admin" {
  count   = var.enable_wif ? 1 : 0
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deployer[0].email}"
}

resource "google_project_iam_member" "deployer_ar_writer" {
  count   = var.enable_wif ? 1 : 0
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deployer[0].email}"
}

resource "google_project_iam_member" "deployer_sa_user" {
  count   = var.enable_wif ? 1 : 0
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.deployer[0].email}"
}
