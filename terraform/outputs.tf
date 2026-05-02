output "gcs_bucket_name" {
  description = "GCS bucket for assets and evaluation logs"
  value       = google_storage_bucket.shopping_assets.name
}

output "gcs_assets_url" {
  description = "Public URL base for product images"
  value       = "https://storage.googleapis.com/${google_storage_bucket.shopping_assets.name}/assets/"
}

output "frontend_url" {
  description = "Frontend Cloud Run URL (CRM + Shopping UI)"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "Backend Cloud Run URL (WebSocket + Gemini Live)"
  value       = google_cloud_run_v2_service.backend.uri
}

output "backend_service_account" {
  description = "Backend service account email"
  value       = google_service_account.backend.email
}

output "frontend_service_account" {
  description = "Frontend service account email"
  value       = google_service_account.frontend.email
}
