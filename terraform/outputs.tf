output "gcs_bucket_name" {
  description = "GCS bucket for assets and evaluation logs"
  value       = google_storage_bucket.shopping_assets.name
}

output "gcs_assets_url" {
  description = "Public URL base for product images"
  value       = "https://storage.googleapis.com/${google_storage_bucket.shopping_assets.name}/assets/"
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "Backend Cloud Run URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "crm_url" {
  description = "CRM Cloud Run URL"
  value       = google_cloud_run_v2_service.crm.uri
}

output "backend_service_account" {
  description = "Backend service account email"
  value       = google_service_account.backend.email
}

output "crm_service_account" {
  description = "CRM service account email"
  value       = google_service_account.crm.email
}
