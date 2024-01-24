resource "google_compute_instance_template" "mig_bridge_template" {
  project      = var.gcp_project_id
  name_prefix  = "mig-bridge-${var.gcp_region}-"
  machine_type = "e2-small"
  tags = ["https-server", "mig-bridge"]
  // boot disk
  disk {
    source_image = "centos-cloud/centos-7"
    boot         = true
    disk_size_gb = 20
  }
  // networking
  network_interface {
    network    = google_compute_network.apigee_network.id
    subnetwork = google_compute_subnetwork.apigee_subnetwork.id
  }
  metadata = {
    ENDPOINT           = google_apigee_instance.apigee_instance.host
    startup-script-url = "gs://apigee-5g-saas/apigee-envoy-proxy-release/latest/conf/startup-script.sh"
  }
 service_account {
    scopes = ["storage-ro"]
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_region_instance_group_manager" "mig_bridge_manager" {
  name               = "mig-bridge-manager-${var.gcp_region}"
  project            = var.gcp_project_id
  base_instance_name = "mig-bridge-${var.gcp_region}"
  region             = var.gcp_region
  version {
    instance_template  = google_compute_instance_template.mig_bridge_template.id
  }
  named_port {
    name = "apigee-https"
    port = 443
  }
}

resource "google_compute_region_autoscaler" "mig_bridge_autoscaler" {
  name    = "mig-autoscaler-${var.gcp_region}"
  project = var.gcp_project_id
  region  = var.gcp_region
  target  = google_compute_region_instance_group_manager.mig_bridge_manager.id
  autoscaling_policy {
    max_replicas    = 2
    min_replicas    = 1
    cooldown_period = 90
    cpu_utilization {
      target = 0.80
    }
  }
}

##########################################################
### Configure the firewall between the GCLB and MIG
### uses "130.211.0.0/22" and "35.191.0.0/16" GCLB ranges 
##########################################################
resource "google_compute_firewall" "allow_glb_to_mig_bridge" {
  name          = "allow-glb-to-mig-bridge"
  project       = var.gcp_project_id
  network       = google_compute_network.apigee_network.id
  source_ranges = ["130.211.0.0/22","35.191.0.0/16"]
  target_tags   = ["mig-bridge"]
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

##########################################################
### Create the SSL certificate
##########################################################
resource "google_compute_managed_ssl_certificate" "apigee_cert" {
  project = var.gcp_project_id
  name    = "apigee-cert"
  managed {
    domains = [local.apigee_hostname]
  }
}

##########################################################
### Create the L7 GCLB
##########################################################
resource "google_compute_backend_service" "default" {
  project         = var.gcp_project_id
  name            = "backend-service"
  port_name       = "apigee-https"
  protocol        = "HTTPS"
  timeout_sec     = 10
  health_checks   = [google_compute_health_check.default.id]
  backend {
    group = google_compute_region_instance_group_manager.mig_bridge_manager.instance_group
  }
}

resource "google_compute_url_map" "default" {
  project         = var.gcp_project_id
  name            = "url-map"
  default_service = google_compute_backend_service.default.id
}

resource "google_compute_target_https_proxy" "default" {
  project          = var.gcp_project_id
  name             = "lb-target-proxy"
  url_map          = google_compute_url_map.default.id
  ssl_certificates = [google_compute_managed_ssl_certificate.apigee_cert.id]
}

resource "google_compute_health_check" "default" {
  project            = var.gcp_project_id
  name               = "https-health-check"
  https_health_check {
    port         = "443"
    request_path = "/healthz/ingress"
  }
}

resource "google_compute_global_forwarding_rule" "external" {
  project    = var.gcp_project_id
  name       = "external-global-rule"
  target     = google_compute_target_https_proxy.default.id
  ip_address = google_compute_global_address.external_ip.address
  port_range = "443"
}
