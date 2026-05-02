terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "capstone-tanvi-01-447109-tf-state"
    prefix = "personalized-shopping"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
