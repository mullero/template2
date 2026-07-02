# Production environment. CHANGE_ME markers MUST be overridden.
project_id  = "CHANGE_ME-prod"
region      = "us-central1"
environment = "prod"

# Regional HA + deletion protection for production data.
db_tier                = "db-custom-2-7680"
db_availability_type   = "REGIONAL"
db_deletion_protection = true
db_disk_size_gb        = 20

# Keep at least one warm backend instance in prod.
backend_min_instances  = 1
backend_max_instances  = 10
frontend_min_instances = 1
frontend_max_instances = 10

backend_image  = "CHANGE_ME"
frontend_image = "CHANGE_ME"

cors_origins = "CHANGE_ME"

graph_enabled = true
ai_enabled    = true

github_repository = "CHANGE_ME/CHANGE_ME"
state_bucket      = "CHANGE_ME-tfstate"
