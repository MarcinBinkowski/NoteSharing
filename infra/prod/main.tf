terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
  }
}

variable "project_id" {
  description = "GCP project ID for prod"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

variable "container_image" {
  description = "Container image for deployment"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "notes"
}

variable "firestore_database_id" {
  description = "Firestore database ID"
  type        = string
  default     = "(default)"
}

variable "firestore_location" {
  description = "Firestore location"
  type        = string
  default     = "eur3"
}

variable "secret_prefix" {
  description = "Secret Manager prefix"
  type        = string
  default     = "notes"
}

variable "google_oauth_client_id" {
  description = "Google OAuth client id"
  type        = string
  sensitive   = true
}

variable "google_oauth_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

variable "session_secret_key" {
  description = "Session signing secret"
  type        = string
  sensitive   = true
}

variable "min_instance_count" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 1
}

variable "max_instance_count" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 5
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

module "environment" {
  source = "../modules/environment"

  providers = {
    google      = google
    google-beta = google-beta
  }

  project_id                 = var.project_id
  region                     = var.region
  environment                = "prod"
  domain                     = "mbinkowski.tech"
  container_image            = var.container_image
  service_name               = var.service_name
  firestore_database_id      = var.firestore_database_id
  firestore_location         = var.firestore_location
  secret_prefix              = var.secret_prefix
  google_oauth_client_id     = var.google_oauth_client_id
  google_oauth_client_secret = var.google_oauth_client_secret
  jwt_secret_key             = var.jwt_secret_key
  session_secret_key         = var.session_secret_key
  min_instance_count         = var.min_instance_count
  max_instance_count         = var.max_instance_count
  memory_limit               = var.memory_limit
  cpu_limit                  = var.cpu_limit
}

output "cloud_run_url" {
  description = "Production Cloud Run URL"
  value       = module.environment.cloud_run_url
}

output "service_account_email" {
  description = "Production Cloud Run service account"
  value       = module.environment.service_account_email
}

output "mapped_domain" {
  description = "Production mapped custom domain"
  value       = module.environment.mapped_domain
}
