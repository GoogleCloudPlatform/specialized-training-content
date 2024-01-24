resource "google_app_engine_application" "app" {
  project     = var.gcp_project_id
  location_id = replace(var.gcp_region, "us-central1", "us-central")
  database_type = "CLOUD_FIRESTORE"
}