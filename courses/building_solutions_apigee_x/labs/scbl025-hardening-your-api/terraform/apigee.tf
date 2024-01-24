resource "google_apigee_organization" "apigee_org" {
  project_id                           = var.gcp_project_id
  analytics_region                     = var.gcp_region
  description                          = "Terraform-provisioned Apigee Org"
  authorized_network                   = google_compute_network.apigee_network.id
  runtime_database_encryption_key_name = google_kms_crypto_key.apigee_key.id
  billing_type                         = "EVALUATION"
  depends_on = [
    google_service_networking_connection.apigee_vpc_connection,
    google_kms_crypto_key_iam_binding.apigee_sa_keyuser,
  ]
}

resource "google_apigee_instance" "apigee_instance" {
  name                     = "apigee-tf-inst"
  location                 = var.gcp_zone
  description              = "Terraform-provisioned Apigee Runtime Instance"
  org_id                   = google_apigee_organization.apigee_org.id
  disk_encryption_key_name = google_kms_crypto_key.apigee_key.id
}

resource "google_apigee_environment" "apigee_env" {
  org_id = google_apigee_organization.apigee_org.id
  name   = "test-env"
}

resource "google_apigee_instance_attachment" "env_to_instance_attachment" {
  instance_id = google_apigee_instance.apigee_instance.id
  environment = google_apigee_environment.apigee_env.name
}

resource "google_apigee_envgroup" "apigee_envgroup" {
  org_id    = google_apigee_organization.apigee_org.id
  name      = "test-env-group"
  hostnames = [local.apigee_hostname]
}

resource "google_apigee_envgroup_attachment" "env_to_envgroup_attachment" {
  envgroup_id = google_apigee_envgroup.apigee_envgroup.id
  environment = google_apigee_environment.apigee_env.name
}




