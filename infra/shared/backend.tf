terraform {
  backend "gcs" {
    bucket = "state_bucket_mbink"
    prefix = "shared"
  }
}