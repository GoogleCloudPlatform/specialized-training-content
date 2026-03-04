
# Create storage bucket to hold logs that are exported from Cloud logging
# These logs will then be injested into BigQuery
resource "google_storage_bucket" "logs_data_bucket" {
  name                        = "${var.project_id}-${var.project_name}-logs"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [resource.google_project_service.services]
}

# Artifact registry repo for the agent container image(s)
# CI/CD pipeline will build a new container and push to this registry
resource "google_artifact_registry_repository" "repo-artifacts-genai" {
  location      = var.region
  repository_id = "${var.project_name}-repo"
  description   = "Repo for Generative AI applications"
  format        = "DOCKER"
  project       = var.project_id
  depends_on    = [resource.google_project_service.services]
}



