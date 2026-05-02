# ================================================================== #
#  API GATEWAY -- fronts the Cloud Run backend
# ================================================================== #
# API Gateway resources require google provider >= 6.x or google-beta.
# Provision via gcloud if not available in your provider version:
#
#   gcloud api-gateway apis create cymbal-stylesync-api --project=$PROJECT_ID
#   gcloud api-gateway api-configs create cymbal-stylesync-config \
#     --api=cymbal-stylesync-api --openapi-spec=terraform/openapi.yaml \
#     --project=$PROJECT_ID --backend-auth-service-account=$SA_EMAIL
#   gcloud api-gateway gateways create cymbal-stylesync-gateway \
#     --api=cymbal-stylesync-api --api-config=cymbal-stylesync-config \
#     --location=us-central1 --project=$PROJECT_ID
#
# OpenAPI spec: terraform/openapi.yaml
#
# resource "google_api_gateway_api" "shopping" {
#   api_id  = "cymbal-stylesync-api"
#   project = var.project_id
# }
#
# resource "google_api_gateway_api_config" "shopping" {
#   api           = google_api_gateway_api.shopping.api_id
#   api_config_id = "cymbal-stylesync-config"
#   project       = var.project_id
#
#   openapi_documents {
#     document {
#       path     = "openapi.yaml"
#       contents = base64encode(templatefile("${path.module}/openapi.yaml", {
#         backend_url = google_cloud_run_v2_service.backend.uri
#       }))
#     }
#   }
# }
#
# resource "google_api_gateway_gateway" "shopping" {
#   gateway_id = "cymbal-stylesync-gateway"
#   api_config = google_api_gateway_api_config.shopping.id
#   project    = var.project_id
#   region     = var.region
# }
