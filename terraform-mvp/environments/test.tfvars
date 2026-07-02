# Test environment. Copy real values in; CHANGE_ME markers MUST be overridden.
project_id  = "CHANGE_ME-test"
region      = "us-central1"
environment = "test"

# Cloud SQL — smallest tier, no HA, deletion allowed for ephemeral test.
db_tier                = "db-f1-micro"
db_availability_type   = "ZONAL"
db_deletion_protection = false

# Cloud Run scale-to-zero for cost.
backend_min_instances  = 0
backend_max_instances  = 2
frontend_min_instances = 0
frontend_max_instances = 2

# Images are set by CI at deploy time (terraform apply -var=...).
backend_image  = "CHANGE_ME"
frontend_image = "CHANGE_ME"

cors_origins = "CHANGE_ME"

graph_enabled = false
ai_enabled    = false

github_repository = "CHANGE_ME/CHANGE_ME"
state_bucket      = "CHANGE_ME-tfstate"
