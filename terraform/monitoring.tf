# ================================================================== #
#  OBSERVABILITY & MONITORING
# ================================================================== #

# Uptime checks for all Cloud Run services
resource "google_monitoring_uptime_check_config" "backend_health" {
  display_name = "Shopping Backend Health"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/health"
    port         = 8082
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "cloud_run_revision"
    labels = {
      project_id         = var.project_id
      service_name       = google_cloud_run_v2_service.backend.name
      location           = var.region
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
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
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
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_latencies\""
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
                  filter = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\""
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
                  filter = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_latencies\""
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
                  filter = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/container/instance_count\""
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
                  filter = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/container/memory/utilizations\""
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
