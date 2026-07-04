# =============================================================================
# Input variables. Per-environment values live in environments/<env>.tfvars.
# Secrets are NEVER set here — they are created empty in Secret Manager and
# populated out-of-band (scripts/create-secrets or CI). Use CHANGE_ME only as a
# deliberate "must override" sentinel in tfvars.
# =============================================================================

variable "project_id" {
  description = "GCP project ID to deploy into."
  type        = string
}

variable "region" {
  description = "Primary GCP region."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment name (test | staging | prod)."
  type        = string
  validation {
    condition     = contains(["test", "staging", "prod"], var.environment)
    error_message = "environment must be one of: test, staging, prod."
  }
}

variable "app_name" {
  description = "Short application name; used to prefix resource names."
  type        = string
  default     = "app-skeleton"
}

# --- Networking --------------------------------------------------------------
variable "vpc_cidr" {
  description = "Primary subnet CIDR for the app VPC."
  type        = string
  default     = "10.20.0.0/24"
}

variable "connector_cidr" {
  description = "/28 CIDR for the Serverless VPC Access connector."
  type        = string
  default     = "10.20.16.0/28"
}

# --- Cloud SQL ---------------------------------------------------------------
variable "db_tier" {
  description = "Cloud SQL machine tier."
  type        = string
  default     = "db-custom-1-3840"
}

variable "db_version" {
  description = "Cloud SQL Postgres version."
  type        = string
  default     = "POSTGRES_16"
}

variable "db_name" {
  description = "Application database name."
  type        = string
  default     = "app-skeleton"
}

variable "db_user" {
  description = "Application database user."
  type        = string
  default     = "app-skeleton"
}

variable "db_disk_size_gb" {
  description = "Cloud SQL data disk size (GB)."
  type        = number
  default     = 10
}

variable "db_deletion_protection" {
  description = "Protect the Cloud SQL instance from deletion."
  type        = bool
  default     = true
}

variable "db_availability_type" {
  description = "ZONAL or REGIONAL (HA)."
  type        = string
  default     = "ZONAL"
}

# --- Cloud Run ---------------------------------------------------------------
variable "backend_image" {
  description = "Fully-qualified backend container image (Artifact Registry)."
  type        = string
  default     = "CHANGE_ME"
}

variable "frontend_image" {
  description = "Fully-qualified frontend container image (Artifact Registry)."
  type        = string
  default     = "CHANGE_ME"
}

variable "backend_min_instances" {
  description = "Minimum backend Cloud Run instances."
  type        = number
  default     = 0
}

variable "backend_max_instances" {
  description = "Maximum backend Cloud Run instances."
  type        = number
  default     = 4
}

variable "frontend_min_instances" {
  description = "Minimum frontend Cloud Run instances."
  type        = number
  default     = 0
}

variable "frontend_max_instances" {
  description = "Maximum frontend Cloud Run instances."
  type        = number
  default     = 4
}

variable "backend_allow_unauthenticated" {
  description = "Allow public (unauthenticated) access to the backend service."
  type        = bool
  default     = true
}

variable "frontend_allow_unauthenticated" {
  description = "Allow public (unauthenticated) access to the frontend service."
  type        = bool
  default     = true
}

# --- Application config (non-secret) ----------------------------------------
variable "cors_origins" {
  description = "Comma-separated allowed CORS origins for the backend."
  type        = string
  default     = "CHANGE_ME"
}

variable "graph_enabled" {
  description = "Enable the Neo4j graph projection. Neo4j itself is provisioned outside this MVP (e.g. AuraDB); set NEO4J_URI via secret."
  type        = bool
  default     = false
}

variable "ai_enabled" {
  description = "Enable the AI (Vertex/Gemini) integration."
  type        = bool
  default     = false
}

variable "tasks_enabled" {
  description = "Enable durable background jobs on Cloud Tasks (+ the queue service account)."
  type        = bool
  default     = false
}

variable "tasks_max_dispatches_per_second" {
  description = "Cloud Tasks queue dispatch rate cap (also caps paid-API burst cost)."
  type        = number
  default     = 5
}

variable "tasks_max_concurrent_dispatches" {
  description = "Cloud Tasks queue max concurrent dispatches."
  type        = number
  default     = 10
}

# --- CI / Workload Identity Federation --------------------------------------
variable "github_repository" {
  description = "GitHub repo allowed to deploy via WIF, as 'owner/repo'."
  type        = string
  default     = "CHANGE_ME/CHANGE_ME"
}

variable "enable_wif" {
  description = "Create the Workload Identity Federation pool/provider + deployer SA."
  type        = bool
  default     = true
}

# --- State bucket (used by scripts, referenced for docs) --------------------
variable "state_bucket" {
  description = "GCS bucket name holding Terraform state."
  type        = string
  default     = "CHANGE_ME-tfstate"
}

variable "labels" {
  description = "Common resource labels."
  type        = map(string)
  default     = {}
}
