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

resource "google_project_service" "cloud_run" {
  project            = var.project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore" {
  project            = var.project_id
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secret_manager" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  project            = var.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = "notes"
  description   = "Docker images for notes (${var.environment})"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

resource "google_firestore_database" "main" {
  name        = var.firestore_database_id
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
}

resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-${var.environment}-sa"
  display_name = "Cloud Run SA for ${var.service_name} (${var.environment})"
}

resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "${var.secret_prefix}-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "jwt_secret_key" {
  secret      = google_secret_manager_secret.jwt_secret_key.id
  secret_data = var.jwt_secret_key
}

resource "google_secret_manager_secret" "session_secret_key" {
  secret_id = "${var.secret_prefix}-session-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "session_secret_key" {
  secret      = google_secret_manager_secret.session_secret_key.id
  secret_data = var.session_secret_key
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "${var.secret_prefix}-google-client-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "google_client_id" {
  secret      = google_secret_manager_secret.google_client_id.id
  secret_data = var.google_oauth_client_id
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "${var.secret_prefix}-google-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "google_client_secret" {
  secret      = google_secret_manager_secret.google_client_secret.id
  secret_data = var.google_oauth_client_secret
}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_cloud_run_service" "app" {
  name     = "${var.service_name}-${var.environment}"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = tostring(var.min_instance_count)
        "autoscaling.knative.dev/maxScale" = tostring(var.max_instance_count)
      }
    }

    spec {
      container_concurrency = 80
      service_account_name  = google_service_account.cloud_run.email

      containers {
        image = var.container_image

        resources {
          limits = {
            memory = var.memory_limit
            cpu    = var.cpu_limit
          }
        }

        ports {
          container_port = 8080
        }

        env {
          name  = "NOTES_GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "NOTES_FIRESTORE_DATABASE"
          value = var.firestore_database_id
        }

        env {
          name = "NOTES_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "NOTES_SESSION_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.session_secret_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "NOTES_GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_id.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "NOTES_GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "NOTES_CORS_ORIGINS"
          value = jsonencode(["https://${var.domain}"])
        }

        env {
          name  = "NOTES_FRONTEND_URL"
          value = "https://${var.domain}"
        }

        env {
          name  = "NOTES_BACKEND_URL"
          value = "https://${var.domain}"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.cloud_run,
    google_firestore_database.main,
    google_secret_manager_secret_version.jwt_secret_key,
    google_secret_manager_secret_version.session_secret_key,
    google_secret_manager_secret_version.google_client_id,
    google_secret_manager_secret_version.google_client_secret,
  ]
}

resource "google_cloud_run_service_iam_member" "public_invoker" {
  service  = google_cloud_run_service.app.name
  location = google_cloud_run_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_domain_mapping" "default" {
  location = var.region
  name     = var.domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.app.name
  }

  depends_on = [google_cloud_run_service_iam_member.public_invoker]
}

resource "google_firestore_index" "notes_by_owner" {
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = "notes"

  fields {
    field_path = "owner_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "expires_at"
    order      = "DESCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_firestore_database.main]
}
