variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "capstone-tanvi-01-447109"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "eval_log_retention_days" {
  description = "Number of days to retain evaluation logs in GCS"
  type        = number
  default     = 90
}
