# VPC network for Cloud Run services
resource "google_compute_network" "vpc" {
  name                    = "shopping-vpc"
  auto_create_subnetworks = false
}

# Subnet for the VPC connector
resource "google_compute_subnetwork" "subnet" {
  name          = "shopping-subnet"
  ip_cidr_range = "10.8.0.0/28"
  region        = var.region
  network       = google_compute_network.vpc.id

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Serverless VPC Access connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name   = "shopping-vpc-connector"
  region = var.region

  subnet {
    name = google_compute_subnetwork.subnet.name
  }

  min_instances = 2
  max_instances = 3

  machine_type = "e2-micro"
}
