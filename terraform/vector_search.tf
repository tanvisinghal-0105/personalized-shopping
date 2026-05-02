# ================================================================== #
#  VERTEX AI VECTOR SEARCH -- product catalog semantic search
# ================================================================== #
# Requires: embedding index created from product catalog (130 products)
# Index is created programmatically via server/core/agents/retail/product_search.py
#
# resource "google_vertex_ai_index" "product_catalog" {
#   display_name = "cymbal-product-catalog-index"
#   region       = var.region
#   project      = var.project_id
#
#   metadata {
#     contents_delta_uri = "gs://${var.project_id}-product-embeddings/"
#     config {
#       dimensions                  = 768
#       approximate_neighbors_count = 10
#       algorithm_config {
#         tree_ah_config {
#           leaf_node_embedding_count    = 500
#           leaf_nodes_to_search_percent = 10
#         }
#       }
#     }
#   }
#
#   index_update_method = "STREAM_UPDATE"
# }
#
# resource "google_vertex_ai_index_endpoint" "product_search" {
#   display_name = "cymbal-product-search-endpoint"
#   region       = var.region
#   project      = var.project_id
#   network      = google_compute_network.vpc.id
# }
