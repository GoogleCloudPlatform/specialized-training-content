locals {
  instance_name = "legacy-api"
}

module "gce-container" {
  source = "terraform-google-modules/container-vm/google"

  container = {
    image = var.container_name  
    env = [
      {
        name = "GOOGLE_CLOUD_PROJECT"
        value = var.gcp_project_id
      },
      {
        name = "NODE_ENV"
        value = "production"
      },
      {
        name = "PORT"
        value = "80"
      }
    ],

    volumeMounts = [
      {
        mountPath = "/cache"
        name      = "tempfs-0"
        readOnly  = false
      },
    ]
  }

  volumes = [
    {
      name = "tempfs-0"

      emptyDir = {
        medium = "Memory"
      }
    },
  ]

  restart_policy = "Always"
}


resource "google_compute_instance" "legacy-api" {
  name         = local.instance_name
  machine_type = "e2-small"
  zone         = var.gcp_zone

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-101-17162-40-52"
    }
  }
  
  service_account {
    email  = google_service_account.legacyapi.email
    scopes = ["cloud-platform"]
  }

  network_interface {
    subnetwork = google_compute_subnetwork.mhc-subnet.name
    access_config {
    }
  }

  tags = ["allow-api-http"] 

  metadata = {
    gce-container-declaration = module.gce-container.metadata_value
    google-logging-enabled    = "true"
    google-monitoring-enabled = "true"
  }

  labels = {
    container-vm = module.gce-container.vm_container_label
  }

}
