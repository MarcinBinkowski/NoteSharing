variable "shared_project_id" {
  description = "GCP project ID that owns the DNS zone"
  type        = string
  default     = "shared-488900"
}

variable "region" {
  description = "Default region for shared resources"
  type        = string
  default     = "europe-west1"
}
