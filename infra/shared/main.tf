terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.shared_project_id
  region  = var.region
}

resource "google_dns_managed_zone" "mbinkowski_tech" {
  name        = "mbinkowski-tech-zone"
  dns_name    = "mbinkowski.tech."
  description = "Public DNS zone for mbinkowski.tech"
}

resource "google_dns_record_set" "prod_root" {
  name         = "mbinkowski.tech."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.mbinkowski_tech.name

  rrdatas = [
    "216.239.32.21",
    "216.239.34.21",
    "216.239.36.21",
    "216.239.38.21",
  ]
}

resource "google_dns_record_set" "acc" {
  name         = "acc.mbinkowski.tech."
  type         = "CNAME"
  ttl          = 300
  managed_zone = google_dns_managed_zone.mbinkowski_tech.name

  rrdatas = ["ghs.googlehosted.com."]
}

resource "google_dns_record_set" "domain_verification" {
  name         = "mbinkowski.tech."
  type         = "TXT"
  ttl          = 300
  managed_zone = google_dns_managed_zone.mbinkowski_tech.name

  rrdatas = [
    "\"google-site-verification=6Sg95fUt4B8oToZTMwt6RzNXbie0N8f-u5BpNdKWT1Q\"",
  ]
}
