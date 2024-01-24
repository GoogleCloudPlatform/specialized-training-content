resource "google_kms_key_ring" "apigee_keyring" {
  provider   = google
  project    = var.gcp_project_id
  name       = "apigee-keyring"
  location   = var.gcp_region
  depends_on = [google_project_service.kms]
  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "apigee_key" {
  provider = google
  name     = "apigee-key"
  key_ring = google_kms_key_ring.apigee_keyring.id
  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_binding" "apigee_sa_keyuser" {
  provider      = google
  crypto_key_id = google_kms_crypto_key.apigee_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:${google_project_service_identity.apigee_sa.email}",
  ]
}

