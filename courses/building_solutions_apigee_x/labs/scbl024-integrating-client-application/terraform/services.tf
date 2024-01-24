resource "google_project_service" "apigee" {
  provider = google
  project  = var.gcp_project_id
  service  = "apigee.googleapis.com"
}

resource "google_project_service" "compute" {
  provider = google
  project  = var.gcp_project_id
  service  = "compute.googleapis.com"
}

resource "google_project_service" "servicenetworking" {
  provider = google
  project  = var.gcp_project_id
  service  = "servicenetworking.googleapis.com"
}

resource "google_project_service" "kms" {
  provider = google
  project  = var.gcp_project_id
  service  = "cloudkms.googleapis.com"
}