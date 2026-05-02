# ================================================================== #
#  OBSERVABILITY & MONITORING
# ================================================================== #

# Uptime check for frontend (HTTP health via Cloud Run URL)
resource "google_monitoring_uptime_check_config" "frontend_health" {
  display_name = "Cymbal Frontend Health"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path    = "/"
    port    = 443
    use_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(google_cloud_run_v2_service.frontend.uri, "https://", "")
    }
  }
}

# Alert policy: high error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Shopping Backend High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5%"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = \"live-agent-backend\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = []  # Add Slack/email channels here
  alert_strategy {
    auto_close = "1800s"
  }
}

# Alert policy: high latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Shopping Backend High Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 latency > 5s"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = \"live-agent-backend\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
      }
    }
  }

  notification_channels = []
  alert_strategy {
    auto_close = "1800s"
  }
}

# Dashboard (JSON definition for Cloud Monitoring)
resource "google_monitoring_dashboard" "shopping" {
  dashboard_json = jsonencode({
    displayName = "Shopping Assistant Dashboard"
    gridLayout = {
      columns = 2
      widgets = [
        {
          title   = "Request Count by Status"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = \"live-agent-backend\" AND metric.type = \"run.googleapis.com/request_count\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                    groupByFields    = ["metric.label.response_code_class"]
                  }
                }
              }
            }]
          }
        },
        {
          title   = "Request Latency (P50, P95, P99)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = \"live-agent-backend\" AND metric.type = \"run.googleapis.com/request_latencies\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_PERCENTILE_99"
                  }
                }
              }
            }]
          }
        },
        {
          title   = "Instance Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = \"live-agent-backend\" AND metric.type = \"run.googleapis.com/container/instance_count\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_MAX"
                  }
                }
              }
            }]
          }
        },
        {
          title   = "Memory Utilization"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = \"live-agent-backend\" AND metric.type = \"run.googleapis.com/container/memory/utilizations\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_PERCENTILE_95"
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
}

# ================================================================== #
#  BILLING BUDGET ALERT
# ================================================================== #

resource "google_billing_budget" "monthly_budget" {
  count           = var.billing_account != "" ? 1 : 0
  billing_account = var.billing_account
  display_name    = "Cymbal StyleSync Monthly Budget"

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "500"
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.8
  }
  threshold_rules {
    threshold_percent = 1.0
  }
}

# ================================================================== #
#  CLOUD TRACE
# ================================================================== #

resource "google_project_service" "cloudtrace" {
  project = var.project_id
  service = "cloudtrace.googleapis.com"
}
