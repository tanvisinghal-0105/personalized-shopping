# Cymbal StyleSync - Deployment Guide

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated
- Terraform >= 1.5.0
- APIs enabled: Cloud Run, Vertex AI, Firestore, Secret Manager, Cloud Build, VPC Access

## Step 1: Authenticate and Set Project

```bash
gcloud auth login
export PROJECT_ID=$(gcloud config get-value project)

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  vpcaccess.googleapis.com \
  compute.googleapis.com \
  --project=$PROJECT_ID
```

## Step 2: Configure API Keys

The backend uses **Vertex AI** (recommended) or **Google AI Studio** for Gemini and Imagen. Secrets are stored in Secret Manager (provisioned by Terraform).

### Option A: Vertex AI (Recommended -- no API key needed)
Vertex AI uses service account credentials. No API key setup required -- Terraform configures IAM roles automatically.

### Option B: Google AI Studio (Dev/prototyping)
1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Store it in Secret Manager after Terraform creates the secret:

```bash
# After Step 3 (Terraform), store the API key
echo -n "YOUR_API_KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=- --project=$PROJECT_ID
```

## Step 3: Deploy Infrastructure (Terraform)

```bash
# Create state bucket (one-time)
gcloud storage buckets create gs://${PROJECT_ID}-tf-state --location=us-central1

cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tf-state"
terraform plan -var="project_id=${PROJECT_ID}"
terraform apply -var="project_id=${PROJECT_ID}"
```

This creates:
- **cymbal-frontend** -- Cloud Run service (CRM + Shopping UI)
- **live-agent-backend** -- Cloud Run service (WebSocket + Gemini Live)
- **GCS bucket** -- Product images, eval logs, generated images (7d TTL)
- **VPC** -- Private network with connector for backend
- **IAM** -- Service accounts with least-privilege roles (Vertex AI, Firestore, GCS, Secret Manager)
- **Secret Manager** -- `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` secrets
- **Monitoring** -- Cloud Monitoring dashboard (request count, latency, memory)
- **Security** -- Cloud Armor WAF (rate limiting 100/min)

## Step 4: Configure Model Armor (one-time)

Model Armor sanitizes user prompts and model responses for prompt injection, jailbreaks, harmful content, and PII leakage.

```bash
# Enable Model Armor API
gcloud services enable modelarmor.googleapis.com --project=$PROJECT_ID

# Create prompt sanitizer template (input filtering)
gcloud model-armor templates create cymbal-prompt-sanitizer \
  --location=us-central1 \
  --project=$PROJECT_ID \
  --pi-and-jailbreak-filter-settings='{"filterEnforcement":"ENABLED","confidenceLevel":"LOW_AND_ABOVE"}' \
  --malicious-uri-filter-settings='{"filterEnforcement":"ENABLED"}' \
  --rai-settings='{"raiFilters":[{"filterType":"DANGEROUS","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"HARASSMENT","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"HATE_SPEECH","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"SEXUALLY_EXPLICIT","confidenceLevel":"HIGH"}]}' \
  --basic-config-sdp-settings='{"filterEnforcement":"ENABLED"}'

# Create response sanitizer template (output filtering)
gcloud model-armor templates create cymbal-response-sanitizer \
  --location=us-central1 \
  --project=$PROJECT_ID \
  --rai-settings='{"raiFilters":[{"filterType":"DANGEROUS","confidenceLevel":"LOW_AND_ABOVE"},{"filterType":"HARASSMENT","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"HATE_SPEECH","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"SEXUALLY_EXPLICIT","confidenceLevel":"HIGH"}]}' \
  --basic-config-sdp-settings='{"filterEnforcement":"ENABLED"}'
```

## Step 5: Upload Assets (one-time)

```bash
gcloud storage cp -r client/assets/products/* gs://${PROJECT_ID}-shopping-assets/assets/products/
```

## Step 6: Deploy Backend

```bash
cd server
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)
```

Pipeline: pytest (103 tests) + black + mypy + Docker build + Cloud Run deploy

## Step 7: Deploy Frontend

```bash
cd crm
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)
```

Uses `frontend.Dockerfile` at repo root. Builds a single `cymbal-frontend` service (FastAPI) that serves both the CRM dashboard and Shopping UI.

## Step 8: Verify

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
- **Secrets** -- stored in Secret Manager, accessed via `get_secret()` in config.py
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
gcloud storage buckets create gs://${PROJECT_ID}-tf-state --location=us-central1

# Re-initialize
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tf-state" -reconfigure
```

### Import Existing Resources
If resources already exist outside terraform state:
```bash
terraform import -var="project_id=${PROJECT_ID}" google_storage_bucket.shopping_assets ${PROJECT_ID}-shopping-assets
terraform import -var="project_id=${PROJECT_ID}" google_service_account.backend projects/${PROJECT_ID}/serviceAccounts/live-agent-backend@${PROJECT_ID}.iam.gserviceaccount.com
```
