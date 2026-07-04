terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.40.0, < 7.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.40.0, < 7.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
  }

  # Remote state in GCS. Bootstrap the bucket first with scripts/bootstrap-state.sh,
  # then `terraform init -backend-config=environments/<env>.backend.hcl`.
  backend "gcs" {
    prefix = "app-skeleton/state"
  }
}
