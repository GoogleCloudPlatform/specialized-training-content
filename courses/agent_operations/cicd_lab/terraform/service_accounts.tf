
# Service account for Cloud Build
# This is used to run the CI/CD pipeline
resource "google_service_account" "cicd_runner_sa" {
  account_id   = "${var.project_name}-cb"
  display_name = "CICD Runner SA"
  project      = var.project_id
  depends_on   = [resource.google_project_service.services]
}

# Agent service account 
# The agent will be deployed to Cloud Run and the Cloud Run service will be assigned this Service Account
resource "google_service_account" "app_sa" {
  account_id   = "${var.project_name}-app"
  display_name = "${var.project_name} Agent Service Account"
  project      = var.project_id
  depends_on   = [resource.google_project_service.services]
}


