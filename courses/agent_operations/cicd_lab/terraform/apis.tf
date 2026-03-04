
resource "google_project_service" "services" {
  count              = length(local.services)
  project            = var.project_id
  service            = local.services[count.index]
  disable_on_destroy = false
}
