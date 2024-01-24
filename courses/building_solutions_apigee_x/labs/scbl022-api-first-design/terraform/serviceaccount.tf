resource "google_service_account" "legacyapi" {
  account_id   = "legacyapisa"
  display_name = "Legacy API Service Account"
}

resource "google_service_account" "gateway" {
  account_id   = "gatewaysa"
  display_name = "Gateway Service Account"
}

resource "google_project_iam_member" "firestore_owner_binding" {
  project = var.gcp_project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.legacyapi.email}"
  depends_on = [google_service_account.legacyapi]
}

resource "google_project_service_identity" "apigee_sa" {
  provider = google-beta
  project  = var.gcp_project_id
  service  = google_project_service.apigee.service
}
