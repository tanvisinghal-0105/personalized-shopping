# ================================================================== #
#  1. AUTHENTICATION & AUTHORIZATION
# ================================================================== #

# Identity-Aware Proxy (IAP) -- restricts access to @google.com
resource "google_iap_web_iam_member" "google_employees" {
  project = var.project_id
  role    = "roles/iap.httpsResourceAccessor"
  member  = "domain:google.com"
}

# ================================================================== #
#  2. INFRASTRUCTURE & NETWORK SECURITY
# ================================================================== #

# Cloud Armor WAF policy for DDoS protection and rate limiting
resource "google_compute_security_policy" "waf" {
  name = "shopping-waf-policy"

  # Default rule: allow
  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }

  # Rate limiting: max 100 requests per minute per IP
  rule {
    action   = "rate_based_ban"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    description = "Rate limiting: 100 req/min per IP"
  }

  # Block known bad IPs / Tor exit nodes
  rule {
    action   = "deny(403)"
    priority = 500
    match {
      expr {
        expression = "evaluateThreatIntelligence('iplist-known-malicious-ips')"
      }
    }
    description = "Block known malicious IPs"
  }
}

# Firewall rules for VPC
resource "google_compute_firewall" "allow_internal" {
  name    = "shopping-allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["8081", "8082"]
  }

  source_ranges = ["10.8.0.0/28"]  # VPC connector subnet only
  description   = "Allow internal traffic from VPC connector"
}

resource "google_compute_firewall" "deny_all_ingress" {
  name    = "shopping-deny-all-ingress"
  network = google_compute_network.vpc.name

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]
  priority      = 65534
  description   = "Deny all external ingress (Cloud Run handles external traffic)"
}

# ================================================================== #
#  3. DATA PROTECTION & PRIVACY
# ================================================================== #

# Encryption: GCS bucket uses Google-managed encryption by default (GMEK)
# For CMEK, uncomment and configure:
# resource "google_kms_key_ring" "shopping" {
#   name     = "shopping-keyring"
#   location = var.region
# }
#
# resource "google_kms_crypto_key" "shopping_data" {
#   name     = "shopping-data-key"
#   key_ring = google_kms_key_ring.shopping.id
#   purpose  = "ENCRYPT_DECRYPT"
#   rotation_period = "7776000s"  # 90 days
# }

# VPC Service Controls perimeter (protects Firestore + Vertex AI)
# Prevents data exfiltration from within the project
resource "google_access_context_manager_service_perimeter" "shopping" {
  count  = var.enable_vpc_service_controls ? 1 : 0
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/shopping_perimeter"
  title  = "Shopping Assistant Perimeter"

  status {
    restricted_services = [
      "firestore.googleapis.com",
      "aiplatform.googleapis.com",
      "storage.googleapis.com",
      "secretmanager.googleapis.com",
    ]

    resources = ["projects/${var.project_id}"]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED-SERVICES"]
    }
  }
}

# ================================================================== #
#  4. AI-SPECIFIC SECURITY
# ================================================================== #

# Vertex AI model access -- restrict to specific service accounts only
resource "google_project_iam_member" "vertex_ai_restricted" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"

  condition {
    title       = "vertex_ai_models_only"
    description = "Restrict to Gemini and Imagen model access"
    expression  = "resource.type == \"aiplatform.googleapis.com/Model\""
  }
}

# Secret Manager -- store API keys securely, not in env vars
resource "google_secret_manager_secret" "api_keys" {
  for_each = toset(["GOOGLE_API_KEY", "GOOGLE_CSE_ID"])

  secret_id = each.value
  replication {
    auto {}
  }
}

# ================================================================== #
#  5. COMPLIANCE & GOVERNANCE
# ================================================================== #

# Cloud Audit Logs -- enabled by default for GCP services
# Explicit data access logging for sensitive services
resource "google_project_iam_audit_config" "firestore_audit" {
  project = var.project_id
  service = "firestore.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_project_iam_audit_config" "aiplatform_audit" {
  project = var.project_id
  service = "aiplatform.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_project_iam_audit_config" "secretmanager_audit" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
}

# Data retention via GCS lifecycle (already in gcs.tf)
# Audit logs in Firestore have separate TTL (managed in application code)

# Organization policy constraints (if org-level access)
# Prevents public GCS buckets except our assets bucket
# resource "google_org_policy_policy" "no_public_buckets" {
#   name   = "projects/${var.project_id}/policies/storage.publicAccessPrevention"
#   parent = "projects/${var.project_id}"
#   spec {
#     rules {
#       enforce = "TRUE"
#     }
#   }
# }
