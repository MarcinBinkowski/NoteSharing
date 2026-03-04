variable "project_id" {
  description = "GCP project ID for this environment"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment name (prod or acc)"
  type        = string

  validation {
    condition     = contains(["acc", "prod"], var.environment)
    error_message = "environment must be 'acc' or 'prod'"
  }
}

variable "domain" {
  description = "Domain name for the managed SSL certificate (e.g. mbinkowski.tech)"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "notes"
}

variable "firestore_database_id" {
  description = "Firestore database ID"
  type        = string
  default     = "(default)"
}

variable "firestore_location" {
  description = "Firestore location. Use a multi-region ID (e.g. eur3) for resilience."
  type        = string
  default     = "eur3"
}

variable "min_instance_count" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instance_count" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 3
}

variable "memory_limit" {
  description = "Cloud Run memory limit"
  type        = string
  default     = "512Mi"
}

variable "cpu_limit" {
  description = "Cloud Run CPU limit"
  type        = string
  default     = "1"
}

variable "container_image" {
  description = "Container image for the Cloud Run service"
  type        = string
}

variable "secret_prefix" {
  description = "Prefix for Secret Manager secret names"
  type        = string
  default     = "notes"
}
