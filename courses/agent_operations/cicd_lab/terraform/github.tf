provider "github" {
  owner = var.repository_owner
}

# Get existing GitHUb repo 
data "github_repository" "repo" {
  full_name = "${var.repository_owner}/${var.repository_name}"
}

# Attach existing GitHub repo to Cloud Build connection 
resource "google_cloudbuildv2_repository" "repo" {
  project  = var.project_id
  location = var.region
  name     = var.repository_name

  # Use existing connection ID
  parent_connection = "projects/${var.project_id}/locations/${var.region}/connections/${var.host_connection_name}"
  remote_uri        = "https://github.com/${var.repository_owner}/${var.repository_name}.git"
  depends_on = [
    resource.google_project_service.services,
    data.github_repository.repo,
  ]
}