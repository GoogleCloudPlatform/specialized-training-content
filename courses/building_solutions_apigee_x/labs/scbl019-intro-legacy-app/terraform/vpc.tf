
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