# =============================================================================
# Artifact Registry — Docker repository for backend/frontend images.
# =============================================================================

resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "${var.app_name}-docker"
  description   = "Container images for ${var.app_name}."
  format        = "DOCKER"
  labels        = local.common_labels

  depends_on = [google_project_service.enabled]
}
