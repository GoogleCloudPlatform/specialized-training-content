
variable "project_name" {
  type        = string
  description = "Project name used as a base for resource naming"
  default     = "lab-agent"
}

variable "project_id" {
  type        = string
  description = "Google Cloud Project ID for resource deployment."
}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us-east1"
}

variable "host_connection_name" {
  description = "Name of the host connection to create in Cloud Build"
  type        = string
}

variable "repository_name" {
  description = "Name of the GitHub repository you'd like to connect to Cloud Build"
  type        = string
}

variable "app_sa_roles" {
  description = "List of roles to assign to the application service account"
  type        = list(string)
  default = [

    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/storage.admin",
    "roles/serviceusage.serviceUsageConsumer",
  ]
}

variable "cicd_roles" {
  description = "List of roles to assign to the CICD runner service account"
  type        = list(string)
  default = [
    "roles/run.developer",
    "roles/run.invoker",
    "roles/storage.admin",
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.builder",
    "roles/iam.serviceAccountUser"
  ]
}


variable "repository_owner" {
  description = "Owner of the GitHub repository - username or organization"
  type        = string
}


variable "feedback_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing feedback data. Captures logs where the `log_type` field is `feedback`."
  default     = "jsonPayload.log_type=\"feedback\" jsonPayload.service_name=\"lab-agent\""
}

