
resource "google_compute_network" "mhc-net" {
  name                    = "mhc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "mhc-subnet" {
  name          = "mhc-subnetwork"
  ip_cidr_range = "10.2.0.0/16"
  region        = var.gcp_region
  network       = google_compute_network.mhc-net.id
  private_ip_google_access = true
}

resource "google_compute_network" "apigee_network" {
  provider                = google
  project                 = var.gcp_project_id
  name                    = "apigee-network"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.compute]
}

resource "google_compute_subnetwork" "apigee_subnetwork" {
  project                  = var.gcp_project_id
  name                     = "apigee-subnetwork"
  region                   = var.gcp_region
  network                  = google_compute_network.apigee_network.id
  ip_cidr_range            = "10.2.0.0/20"
  private_ip_google_access = true
  depends_on               = [google_project_service.compute,
                              google_compute_network.apigee_network]
}

resource "google_compute_global_address" "external_ip" {
  project      = var.gcp_project_id
  name         = "global-external-ip"
  address_type = "EXTERNAL"
}

locals {
  apigee_hostname = "${replace(google_compute_global_address.external_ip.address, ".", "-")}.nip.io"
}


resource "google_compute_global_address" "apigee_range" {
  project       = var.gcp_project_id
  name          = "apigee-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 22
  network       = google_compute_network.apigee_network.id
}


resource "google_service_networking_connection" "apigee_vpc_connection" {
  provider                = google
  network                 = google_compute_network.apigee_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.apigee_range.name]
  depends_on              = [google_project_service.servicenetworking]
}

