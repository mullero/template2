# =============================================================================
# Background jobs — Cloud Tasks queue + the queue's push service account.
#
# Cloud Tasks durably stores each job and PUSHes it to the backend's internal
# worker endpoint with an OIDC token minted for the queue service account. That
# SA is granted roles/run.invoker on the backend service ONLY. Retry/backoff and
# per-queue rate/concurrency limits (which also cap paid-API burst cost) are
# configured here. Gated on var.tasks_enabled so a no-async build stays lean.
# =============================================================================

resource "google_service_account" "tasks" {
  count        = var.tasks_enabled ? 1 : 0
  account_id   = "${local.name_prefix}-tasks"
  display_name = "${var.app_name} ${var.environment} Cloud Tasks queue"
}

resource "google_cloud_tasks_queue" "jobs" {
  count    = var.tasks_enabled ? 1 : 0
  name     = "${local.name_prefix}-jobs"
  location = var.region

  rate_limits {
    max_dispatches_per_second = var.tasks_max_dispatches_per_second
    max_concurrent_dispatches = var.tasks_max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = 5
    min_backoff        = "5s"
    max_backoff        = "300s"
    max_doublings      = 4
    max_retry_duration = "3600s"
  }

  depends_on = [google_project_service.enabled]
}

# The queue SA may invoke the backend Cloud Run service (to deliver tasks).
resource "google_cloud_run_v2_service_iam_member" "tasks_invoker" {
  count    = var.tasks_enabled ? 1 : 0
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.tasks[0].email}"
}

# The backend runtime SA may enqueue tasks onto the queue.
resource "google_project_iam_member" "backend_tasks_enqueuer" {
  count   = var.tasks_enabled ? 1 : 0
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}
