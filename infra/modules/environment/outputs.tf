output "mapped_domain" {
  description = "Custom domain mapped to this environment"
  value       = var.domain
}

output "cloud_run_url" {
  description = "Direct Cloud Run service URL"
  value       = google_cloud_run_service.app.status[0].url
}

output "service_account_email" {
  description = "Service account used by Cloud Run"
  value       = google_service_account.cloud_run.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository path for Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}
