resource "google_service_account" "legacyapi" {
  account_id   = "legacyapisa"
  display_name = "Legacy API Service Account"
}

resource "google_project_iam_member" "firestore_owner_binding" {
  project = var.gcp_project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.legacyapi.email}"
  depends_on = [google_service_account.legacyapi]
}