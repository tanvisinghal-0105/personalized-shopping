# Cymbal StyleSync

**AI Hyperpersonalization Platform** -- a voice-first shopping assistant powered by Google Gemini Live API with real-time audio, room visualization, and intelligent product recommendations.

Built by [@tanvisinghal](https://github.com/tanvisinghal-0105)

## What Makes This Different

This project handles the **Gemini Live API for real-time audio** in production -- which is hard to get right. The stability comes from patterns built specifically for live audio sessions:

- **Direct visualization pipeline** -- room rendering bypasses the Gemini agent entirely, preventing context bloat and session timeouts
- **Retry with exponential backoff** -- all Vertex AI, Imagen, and Firestore calls automatically retry on transient failures
- **Lazy tool loading** -- only 17 of 25 tools loaded per session, cutting ~11K tokens from initial context
- **Slim product catalog** -- 130 products summarized as category table (12K tokens -> 200 tokens) with semantic search for retrieval
- **Session auto-save** -- evaluation recordings save after every tool call, not just on disconnect
- **Async style previews** -- room photo restyled into 6 themes in parallel via background tasks, streamed to frontend as they complete

## Quick Start (5 minutes)

```bash
# 1. Clone
git clone git@github.com:tanvisinghal-0105/personalized-shopping.git
cd personalized-shopping

# 2. Auth
gcloud auth application-default login

# 3. Configure
cd server
cp .env.example .env
pip install -r requirements.txt

# Edit .env with your project details:
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GOOGLE_CLOUD_LOCATION=us-central1
#   GOOGLE_GENAI_USE_VERTEXAI=1
#   GCS_BUCKET_NAME=your-project-id-shopping-assets

# 4. Start backend (WebSocket server for Gemini Live)
python server.py &
# Backend runs on :8081 (WebSocket) and :8082 (health endpoint)

# 5. Start CRM dashboard (serves both the shopping UI and CRM)
cd ../crm
pip install fastapi uvicorn google-cloud-firestore python-dotenv
python main.py &
# CRM runs on :8082 -- this is the main entry point

# 6. Open http://localhost:8082
```

That's it. The platform opens with the Shopping Assistant tab. Sign in and start talking.

### Stopping servers
```bash
pkill -f "python server.py"
pkill -f "python main.py"
```

### Restarting everything
```bash
pkill -f "python server.py"; pkill -f "python main.py"
sleep 2
cd server && python server.py &
cd ../crm && python main.py &
```

## Deploy to Google Cloud

```bash
export PROJECT_ID=$(gcloud config get-value project)

# 1. Infrastructure (VPC, IAM, GCS, monitoring, security)
cd terraform
terraform init -backend-config="bucket=${PROJECT_ID}-tf-state"
terraform apply -var="project_id=${PROJECT_ID}"

# 2. Upload product images to GCS (one-time)
cd ../server
python scripts/upload_assets_to_gcs.py

# 3. Deploy backend (pytest + black + mypy + Docker + Cloud Run)
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)

# 4. Deploy frontend (CRM + Shopping UI)
cd ../crm
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)
```

Full guide: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

## Project Structure

```
server/          Backend (WebSocket + Gemini Live + ADK Agent)
crm/             Cymbal StyleSync Dashboard (FastAPI, 5 tabs)
client/          Shopping UI (embedded in CRM)
terraform/       GCP infra (Cloud Run, GCS, VPC, IAM, monitoring)
```

## Demo Personas

**Persona A: Electronics Shopper** -- Show phone via camera, get case recommendation, price match against competitor (manager approval via CRM), add warranty, trade in old device.

**Persona B: Home Decor Consultation** -- 9-stage guided flow: room selection, purpose, photo upload with AI analysis + order history cross-reference, style discovery with AI-generated previews, colour + dimensions, curated moodboard, room visualization (Gemini Pro inpainting / Imagen 4 fallback).

Full script: [docs/DEMO_STORYLINE.md](docs/DEMO_STORYLINE.md)

## Testing

```bash
cd server && python -m pytest tests/ -v    # 103 tests
```
