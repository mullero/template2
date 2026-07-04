# =============================================================================
# Cloud Run (v2) services: backend (FastAPI) and frontend (nginx SPA).
#
# The backend reaches Cloud SQL over the VPC connector via the instance private
# IP; POSTGRES_PASSWORD and other secrets are mounted from Secret Manager. The
# frontend is a static origin — in production the SPA calls the backend's public
# URL directly (VITE_API_URL, baked at build), so nginx's /api proxy is unused.
# =============================================================================

locals {
  deploy_env = var.environment == "prod" ? "production" : (
    var.environment == "staging" ? "staging" : "testing"
  )

  backend_plain_env = merge(
    {
      DEPLOYMENT_ENVIRONMENT = local.deploy_env
      LOG_LEVEL              = "INFO"
      POSTGRES_HOST          = google_sql_database_instance.postgres.private_ip_address
      POSTGRES_PORT          = "5432"
      POSTGRES_DB            = var.db_name
      POSTGRES_USER          = var.db_user
      API_PORT               = "8000"
      AUTH_ENABLED           = "true"
      ENABLE_SWAGGER         = var.environment == "prod" ? "false" : "true"
      ENABLE_DETAILED_ERRORS = var.environment == "prod" ? "false" : "true"
      ENABLE_DEV_ROUTES      = "false"
      CORS_ORIGINS           = var.cors_origins
      GRAPH_ENABLED          = tostring(var.graph_enabled)
      AI_ENABLED             = tostring(var.ai_enabled)
      RATE_LIMIT_ENABLED     = "true"
      DRIFT_CHECK_ENABLED    = "true"
    },
    var.tasks_enabled ? {
      TASKS_ENABLED         = "true"
      CLOUD_TASKS_QUEUE     = google_cloud_tasks_queue.jobs[0].name
      CLOUD_TASKS_LOCATION  = var.region
      TASKS_SERVICE_ACCOUNT = google_service_account.tasks[0].email
      # INTERNAL_BASE_URL + TASKS_OIDC_AUDIENCE must equal the deployed backend
      # URL; set post-deploy (avoids a self-referential resource cycle).
    } : {},
  )
  # name -> secret_id (same project). Values are populated out-of-band.
  backend_secret_env = merge(
    {
      POSTGRES_PASSWORD   = google_secret_manager_secret.db_password.secret_id
      SECRET_KEY          = "${local.name_prefix}-secret-key"
      FIREBASE_PROJECT_ID = "${local.name_prefix}-firebase-project"
    },
    var.graph_enabled ? {
      NEO4J_URI      = "${local.name_prefix}-neo4j-uri"
      NEO4J_PASSWORD = "${local.name_prefix}-neo4j-password"
    } : {},
    var.ai_enabled ? {
      GEMINI_API_KEY = "${local.name_prefix}-gemini-api-key"
    } : {},
  )
}

resource "google_cloud_run_v2_service" "backend" {
  name     = "${local.name_prefix}-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  labels   = local.common_labels

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      dynamic "env" {
        for_each = local.backend_plain_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.backend_secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      startup_probe {
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 6
        http_get {
          path = "/health"
          port = 8000
        }
      }

      liveness_probe {
        period_seconds = 30
        http_get {
          path = "/health"
          port = 8000
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled,
    google_sql_user.app,
    google_secret_manager_secret_version.db_password,
    google_secret_manager_secret_iam_member.backend_db_password,
  ]
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "${local.name_prefix}-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  labels   = local.common_labels

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }

      startup_probe {
        initial_delay_seconds = 3
        period_seconds        = 5
        failure_threshold     = 6
        http_get {
          path = "/healthz"
          port = 8080
        }
      }
    }
  }

  depends_on = [google_project_service.enabled]
}

# --- Public access (optional) -----------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  count    = var.backend_allow_unauthenticated ? 1 : 0
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  count    = var.frontend_allow_unauthenticated ? 1 : 0
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
