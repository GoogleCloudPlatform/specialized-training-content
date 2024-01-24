resource "google_compute_firewall" "mhc-firewall" {
  name    = "mhc-firewall"
  network = google_compute_network.mhc-net.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80"]
  }

  source_ranges = [
    "0.0.0.0/0"
  ]

  target_tags = ["allow-api-http"] 




}