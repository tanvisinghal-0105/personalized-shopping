# Cymbal StyleSync - Deployment Guide

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated
- Terraform >= 1.5.0

## Step 1: Authenticate

```bash
gcloud auth login
export PROJECT_ID=$(gcloud config get-value project)
```

## Step 2: Deploy Infrastructure (Terraform)

Terraform provisions all GCP resources: Cloud Run services, VPC, IAM, GCS bucket, monitoring, and security.

```bash
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tf-state"
terraform plan -var="project_id=${PROJECT_ID}"
terraform apply -var="project_id=${PROJECT_ID}"
```

This creates:
- **cymbal-frontend** -- Cloud Run service (CRM + Shopping UI)
- **live-agent-backend** -- Cloud Run service (WebSocket + Gemini Live)
- **GCS bucket** -- Product images, eval logs, generated images
- **VPC** -- Private network for backend services
- **IAM** -- Service accounts with least-privilege roles
- **Monitoring** -- Dashboards and alert policies
- **Security** -- Cloud Armor WAF, Secret Manager

## Step 3: Upload Assets (one-time)

```bash
gcloud storage cp -r client/assets/products/* gs://${PROJECT_ID}-shopping-assets/assets/products/
```

## Step 4: Deploy Backend

```bash
cd server
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)
```

Pipeline: pytest (103 tests) + black + mypy + Docker build + Cloud Run deploy

## Step 5: Deploy Frontend

```bash
cd crm
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)
```

Uses `frontend.Dockerfile` at repo root. Builds a single `cymbal-frontend` service (FastAPI) that serves both the CRM dashboard and Shopping UI.

## Step 6: Verify

```bash
# Get service URLs
gcloud run services describe cymbal-frontend --region us-central1 --format 'value(status.url)'
gcloud run services describe live-agent-backend --region us-central1 --format 'value(status.url)'

# Check terraform outputs
cd terraform && terraform output
```

## Architecture

| Service | Image | Port | Resources |
|---------|-------|------|-----------|
| cymbal-frontend | `gcr.io/$PROJECT_ID/cymbal-frontend` | 8080 | 1 CPU, 512Mi |
| live-agent-backend | `gcr.io/$PROJECT_ID/live-agent-backend` | 8081 | 2 CPU, 2Gi |

## Configuration

- **No hardcoded project IDs** -- all dynamic via environment variables
- **WebSocket endpoint** -- auto-detected from frontend hostname
- **GCS assets** -- served from `${PROJECT_ID}-shopping-assets/assets/products/`
- **Service accounts** -- `live-agent-backend@${PROJECT_ID}.iam.gserviceaccount.com`

## Troubleshooting

### Permission Denied
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/cloudbuild.builds.editor"
```

### View Logs
```bash
gcloud run services logs tail live-agent-backend --region us-central1
gcloud run services logs tail cymbal-frontend --region us-central1
gcloud builds list --limit 5
```

### Terraform State
```bash
# Create state bucket if it doesn't exist
gsutil mb gs://${PROJECT_ID}-tf-state

# Re-initialize
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tf-state" -reconfigure
```
