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

variable "analytics_region" {
  description = "Analytics Region for the Apigee Organization (immutable). See https://cloud.google.com/apigee/docs/api-platform/get-started/install-cli."
  type = string
  default = "us-central1"
}

variable "apigee_environments" {
  description = "Apigee Environment Names."
  type        = list(string)
  default     = ["eval"]
}

variable "network" {
  description = "Name of the VPC network to be created."
  type        = string
  default     = "apigee-vpc"
}

variable "peering_range" {
  description = "RFC CIDR range for service network peering."
  type        = string
  default     = "10.0.0.0/21"
}

variable "runtime_region" {
  description = "Apigee Runtime Instance Region."
  type        = string
  default     = "us-central1"
}

variable "instance_cidr" {
  description = "CIDR Block to be used by the Apigee instance."
  type        = string
  default     = "10.0.0.0/22"
}

variable "address_name" {
  description = "Name for the external IP address"
  type        = string
  default     = "apigee-x-ip"
}

variable "subdomain_prefixes" {
  description = "Subdomain prefixes for the nip hostname (Optional)."
  type        = list(string)
  default     = []
}
