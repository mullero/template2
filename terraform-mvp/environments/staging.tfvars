# Staging environment. CHANGE_ME markers MUST be overridden.
project_id  = "CHANGE_ME-staging"
region      = "us-central1"
environment = "staging"

db_tier                = "db-custom-1-3840"
db_availability_type   = "ZONAL"
db_deletion_protection = true

backend_min_instances  = 0
backend_max_instances  = 4
frontend_min_instances = 0
frontend_max_instances = 4

backend_image  = "CHANGE_ME"
frontend_image = "CHANGE_ME"

cors_origins = "CHANGE_ME"

graph_enabled = true
ai_enabled    = true

github_repository = "CHANGE_ME/CHANGE_ME"
state_bucket      = "CHANGE_ME-tfstate"
