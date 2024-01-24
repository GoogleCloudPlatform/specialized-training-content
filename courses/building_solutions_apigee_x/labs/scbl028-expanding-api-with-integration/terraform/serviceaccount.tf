resource "google_service_account" "legacyapi" {
  account_id   = "legacyapisa"
  display_name = "Legacy API Service Account"
}

resource "google_service_account" "gateway" {
  account_id   = "gatewaysa"
  display_name = "Gateway Service Account"
}

resource "google_service_account" "sa_apigee_google_services" {
  account_id   = "sa-apigee-google-services"
  display_name = "Service account for Apigee to access Google services"
}

resource "google_project_iam_member" "sa_apigee_role_dlp" {
  project = var.gcp_project_id
  role    = "roles/dlp.user"
  member  = "serviceAccount:${google_service_account.sa_apigee_google_services.email}"
  depends_on = [google_service_account.sa_apigee_google_services]
}

resource "google_project_iam_member" "sa_apigee_role_logs_writer" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.sa_apigee_google_services.email}"
  depends_on = [google_service_account.sa_apigee_google_services]
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
