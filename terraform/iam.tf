# ================================================================== #
#  SERVICE ACCOUNTS
# ================================================================== #

# Backend service account -- used by the WebSocket server (live-agent-backend).
# This service runs the Gemini Live API integration, handles real-time voice
# shopping sessions, manages shopping carts in Firestore, generates style
# previews via Imagen, and writes evaluation logs to GCS.
resource "google_service_account" "backend" {
  account_id   = "live-agent-backend"
  display_name = "Backend Service Account"
  description  = "Service account for the shopping assistant backend"
}

# Frontend service account -- used by the CRM dashboard and shopping UI
# (cymbal-frontend). This service serves the customer-facing shopping
# interface and the internal CRM dashboard for support agents to review
# discount approvals and monitor sessions.
resource "google_service_account" "frontend" {
  account_id   = "cymbal-frontend"
  display_name = "Frontend Service Account"
  description  = "Service account for the CRM dashboard and shopping UI"
}

# ================================================================== #
#  BACKEND IAM ROLES
# ================================================================== #

# roles/datastore.user -- Allows the backend to read/write Firestore documents.
# Needed for: customer profiles, shopping carts, discount approval records,
# and session history. The backend reads customer data to personalize
# recommendations and writes cart updates during voice shopping sessions.
resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# roles/aiplatform.user -- Allows the backend to call Vertex AI endpoints.
# Needed for: Gemini Live API (real-time voice conversation), Gemini Pro
# (text generation for product descriptions), Imagen (style preview
# generation), and the evaluation framework (model-graded evals).
resource "google_project_iam_member" "backend_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# roles/secretmanager.secretAccessor -- Allows the backend to read secrets.
# Needed for: retrieving GOOGLE_API_KEY (for Custom Search API used in
# product image lookup) and GOOGLE_CSE_ID (Custom Search Engine ID).
# These are stored in Secret Manager rather than environment variables
# for security.
resource "google_project_iam_member" "backend_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# roles/cloudtrace.agent -- Allows the backend to write trace spans.
# Needed for: distributed tracing of WebSocket sessions, Gemini API calls,
# and Firestore operations. Traces help diagnose latency issues in the
# real-time voice shopping pipeline.
resource "google_project_iam_member" "backend_cloudtrace" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# roles/storage.objectViewer -- Allows the backend to read GCS objects.
# Needed for: reading product catalog images from the assets/ prefix
# to serve to the shopping UI and retrieving evaluation reference data.
resource "google_storage_bucket_iam_member" "backend_storage_read" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# roles/storage.objectCreator -- Allows the backend to write GCS objects.
# Needed for: writing evaluation session logs (evaluation/logs/ prefix),
# saving generated style preview images (generated/ prefix), and storing
# session recordings for the eval framework.
resource "google_storage_bucket_iam_member" "backend_storage_write" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# ================================================================== #
#  FRONTEND IAM ROLES
# ================================================================== #

# roles/datastore.user -- Allows the frontend to read/write Firestore documents.
# Needed for: the CRM approval workflow where support agents review and
# approve/deny discount requests submitted by the voice shopping assistant.
# Also reads session metadata for the CRM dashboard.
resource "google_project_iam_member" "frontend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

# roles/storage.objectViewer -- Allows the frontend to read GCS objects.
# Needed for: displaying evaluation logs and session recordings in the
# CRM dashboard so support agents can review past shopping sessions.
resource "google_storage_bucket_iam_member" "frontend_storage_read" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.frontend.email}"
}
