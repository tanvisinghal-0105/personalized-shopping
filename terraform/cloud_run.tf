# Frontend - CRM dashboard + Shopping UI (FastAPI)
resource "google_cloud_run_v2_service" "frontend" {
  name     = "cymbal-frontend"
  location = var.region

  labels = {
    app         = "cymbal-stylesync"
    environment = var.environment
    managed_by  = "terraform"
  }

  template {
    service_account = google_service_account.frontend.email

    containers {
      image = "gcr.io/${var.project_id}/cymbal-frontend:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.shopping_assets.name
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Backend - WebSocket server with Gemini Live API
resource "google_cloud_run_v2_service" "backend" {
  name     = "live-agent-backend"
  location = var.region

  labels = {
    app         = "cymbal-stylesync"
    environment = var.environment
    managed_by  = "terraform"
  }

  template {
    service_account = google_service_account.backend.email

    containers {
      image = "gcr.io/${var.project_id}/live-agent-backend:latest"

      ports {
        container_port = 8081
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "1"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.shopping_assets.name
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    }

    # 15 minute timeout for long-running WebSocket sessions
    timeout = "900s"

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    # Session affinity to keep WebSocket connections on the same instance
    session_affinity = true

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Public access to Cloud Run -- app-level auth validates @google.com on WebSocket connect
# App-level auth (AUTH_ENABLED=true) validates @google.com on WebSocket connect
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
