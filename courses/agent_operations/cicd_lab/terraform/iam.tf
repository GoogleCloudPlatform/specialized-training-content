
# Data source to get project number
data "google_project" "project" {
  project_id = var.project_id
}

# Assign roles to CI/CD runner service account
# These roles are given to the service account used by Cloud Build to run the CI/CD pipeline
resource "google_project_iam_member" "cicd_project_roles" {
  for_each = toset(var.cicd_roles)

  project    = var.project_id
  role       = each.value
  member     = "serviceAccount:${resource.google_service_account.cicd_runner_sa.email}"
  depends_on = [resource.google_project_service.services]
}

# Grant application service account the required permissions to run the application
# The agent will be deployed to Cloud Run and the service account will be assigned these roles
resource "google_project_iam_member" "app_sa_roles" {
  for_each = toset(var.app_sa_roles)

  project    = var.project_id
  role       = each.value
  member     = "serviceAccount:${google_service_account.app_sa.email}"
  depends_on = [resource.google_project_service.services]
}

# Allow Cloud Run service SA to pull containers from Artifact Registry
resource "google_project_iam_member" "run_artifact_registry_reader" {
  project = var.project_id

  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:service-${data.google_project.project.number}@serverless-robot-prod.iam.gserviceaccount.com"
  depends_on = [resource.google_project_service.services]
}

# Allow the CI/CD SA to create tokens
resource "google_service_account_iam_member" "cicd_token_creator" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${resource.google_service_account.cicd_runner_sa.email}"
  depends_on         = [resource.google_project_service.services]
}

# Allow the CI/CD SA to impersonate itself for trigger creation
resource "google_service_account_iam_member" "cicd_account_user" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${resource.google_service_account.cicd_runner_sa.email}"
  depends_on         = [resource.google_project_service.services]
}
