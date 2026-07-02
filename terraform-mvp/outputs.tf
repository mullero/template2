# =============================================================================
# Outputs.
# =============================================================================

output "backend_url" {
  description = "Public URL of the backend Cloud Run service."
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Public URL of the frontend Cloud Run service."
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_service_account" {
  description = "Backend runtime service account email."
  value       = google_service_account.backend.email
}

output "frontend_service_account" {
  description = "Frontend runtime service account email."
  value       = google_service_account.frontend.email
}

output "artifact_registry_repo" {
  description = "Artifact Registry Docker repository path."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "cloudsql_instance" {
  description = "Cloud SQL instance connection name."
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloudsql_private_ip" {
  description = "Cloud SQL instance private IP."
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "wif_provider" {
  description = "Workload Identity provider resource name for GitHub Actions."
  value       = var.enable_wif ? google_iam_workload_identity_pool_provider.github[0].name : null
}

output "deployer_service_account" {
  description = "CI deployer service account email (impersonated via WIF)."
  value       = var.enable_wif ? google_service_account.deployer[0].email : null
}
