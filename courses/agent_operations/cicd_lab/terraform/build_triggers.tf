# Create staging deployment trigger
resource "google_cloudbuild_trigger" "deployment_trigger" {
  name            = "deploy-${var.project_name}"
  project         = var.project_id
  location        = var.region
  service_account = resource.google_service_account.cicd_runner_sa.id
  description     = "Trigger for deployment on push to repository"

  repository_event_config {
    repository = "projects/${var.project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
    push {
      branch = ".*"
    }
  }

  filename = "./cloudbuild.yaml"
  included_files = [
    "app/**",
    "data_ingestion/**",
    "tests/**",
    "deployment/**",
    "uv.lock"
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _PROJECT_ID                  = var.project_id
    _LOGS_BUCKET_NAME            = resource.google_storage_bucket.logs_data_bucket.name
    _APP_SERVICE_ACCOUNT         = google_service_account.app_sa.email
    _REGION                      = var.region
    _CONTAINER_NAME              = var.project_name
    _ARTIFACT_REGISTRY_REPO_NAME = resource.google_artifact_registry_repository.repo-artifacts-genai.repository_id
  }
  depends_on = [
    resource.google_project_service.services,
    google_cloudbuildv2_repository.repo
  ]
}
