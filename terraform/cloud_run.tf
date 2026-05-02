# Frontend - Static client served via nginx
resource "google_cloud_run_v2_service" "frontend" {
  name     = "shopping-frontend"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/live-agent-frontend:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Backend - WebSocket server with Gemini Live API
resource "google_cloud_run_v2_service" "backend" {
  name     = "shopping-backend"
  location = var.region

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

# CRM - FastAPI dashboard
resource "google_cloud_run_v2_service" "crm" {
  name     = "shopping-crm"
  location = var.region

  template {
    service_account = google_service_account.crm.email

    containers {
      image = "gcr.io/${var.project_id}/live-agent-crm:latest"

      ports {
        container_port = 8082
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.shopping_assets.name
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access to frontend and CRM
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "crm_public" {
  name     = google_cloud_run_v2_service.crm.name
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
