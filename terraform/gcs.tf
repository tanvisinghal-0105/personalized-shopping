# GCS bucket for product images, eval logs, and generated images
resource "google_storage_bucket" "shopping_assets" {
  name                        = "${var.project_id}-shopping-assets"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  labels = {
    app         = "cymbal-stylesync"
    environment = var.environment
    managed_by  = "terraform"
  }

  # Public read access for product images served to the frontend
  # Eval logs are in a separate prefix and not publicly accessible

  versioning {
    enabled = false
  }

  # Auto-delete evaluation logs after retention period
  lifecycle_rule {
    condition {
      age                = var.eval_log_retention_days
      matches_prefix     = ["evaluation/logs/"]
    }
    action {
      type = "Delete"
    }
  }

  # Auto-delete generated style preview images after 7 days
  lifecycle_rule {
    condition {
      age            = 7
      matches_prefix = ["generated/"]
    }
    action {
      type = "Delete"
    }
  }

  # Move objects older than 90 days to NEARLINE storage for cost savings,
  # except for the assets/ prefix which must stay in STANDARD
  lifecycle_rule {
    condition {
      age                   = 90
      matches_prefix        = ["evaluation/", "generated/", "sessions/"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
}

# Public read access for product images and style previews
resource "google_storage_bucket_iam_member" "assets_public_read" {
  bucket = google_storage_bucket.shopping_assets.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
