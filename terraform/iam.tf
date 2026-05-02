# Service account for the backend (WebSocket server)
resource "google_service_account" "backend" {
  account_id   = "shopping-backend-sa"
  display_name = "Shopping Backend Service Account"
  description  = "Service account for the shopping assistant backend"
}

# Service account for the CRM dashboard
resource "google_service_account" "crm" {
  account_id   = "shopping-crm-sa"
  display_name = "Shopping CRM Service Account"
  description  = "Service account for the CRM dashboard"
}

# Backend IAM roles
# Firestore access for customer data and carts
resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Vertex AI access for Gemini, Imagen, and evaluation
resource "google_project_iam_member" "backend_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Secret Manager access for API keys
resource "google_project_iam_member" "backend_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# GCS access for reading product images and writing eval logs
resource "google_storage_bucket_iam_member" "backend_storage_read" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "backend_storage_write" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# CRM IAM roles
# Firestore access for approval workflow
resource "google_project_iam_member" "crm_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.crm.email}"
}

# GCS read access for eval logs
resource "google_storage_bucket_iam_member" "crm_storage_read" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.crm.email}"
}
