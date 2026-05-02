variable "project_id" {
  description = "GCP project ID"
  type        = string
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

variable "enable_vpc_service_controls" {
  description = "Enable VPC Service Controls perimeter (requires org-level access)"
  type        = bool
  default     = false
}

variable "access_policy_id" {
  description = "Access Context Manager policy ID (required if enable_vpc_service_controls=true)"
  type        = string
  default     = ""
}

variable "billing_account" {
  description = "GCP billing account ID for budget alerts"
  type        = string
  default     = ""
}
