resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.gcp_project_id

  depends_on = [
    google_project_service.firebase
  ]
}

resource "google_firebase_web_app" "default" {
  provider = google-beta
  project      = var.gcp_project_id
  display_name = "Apigee Course Web App"

  depends_on = [
    google_firebase_project.default
  ]
}
