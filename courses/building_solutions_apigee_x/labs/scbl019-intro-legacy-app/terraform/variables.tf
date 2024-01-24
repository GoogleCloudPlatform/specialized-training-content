variable "gcp_project_id" {
  type        = string
  description = "The GCP Project ID to apply this config to."
}

variable "gcp_region" {
  type        = string
  description = "The GCP region to apply this config to."
}

variable "gcp_zone" {
  type        = string
  description = "The GCP zone to apply this config to."
}

variable "container_name" {
    type = string
    default = "krattan/legacy-api-demo:v5"
}
