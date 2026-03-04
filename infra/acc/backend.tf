terraform {
  backend "gcs" {
    bucket = "acc_state_bucket_mbink"
    prefix = "acc"
  }
}
