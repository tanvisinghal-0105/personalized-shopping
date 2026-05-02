# Cymbal Personalized Shopping Assistant

A multimodal AI voice shopping assistant powered by Google Gemini Live API with real-time audio, video, and text interactions. Features an end-to-end home decor consultation flow with AI-generated room visualizations using Imagen 3.

Built with Google ADK (Agents Development Kit), Vertex AI, Firestore, and Cloud Run.

## Architecture

```
                    WebSocket (audio/video/text)
  Client (8000) <------------------------------> Backend (8081)
  HTML/JS/CSS                                     ADK Agent + Gemini Live API
                                                  25+ Tools (cart, decor, viz)
                                                       |
                                          +------------+------------+
                                          |            |            |
                                     Firestore    Vertex AI    Imagen 3
                                     (carts,      (Gemini,     (room viz,
                                      profiles)    eval)       style gen)
                                          |
                                    CRM (8082)
                                    FastAPI + Eval Dashboard
```

## Key Features

- **Voice-first shopping** -- real-time audio conversation with Gemini Live native audio
- **Home decor consultation** -- guided multi-phase flow: room selection, style finder, photo analysis, moodboard generation
- **Child-themed style finder** -- 6 themed room styles (Underwater World, Forest Adventure, etc.) with AI-generated previews from the customer's own room photo
- **Room visualization** -- Imagen 3 inpainting renders selected products into the customer's actual room
- **Order history cross-referencing** -- identifies existing furniture from past purchases using Gemini Vision
- **Evaluation framework** -- 5-layer custom + Vertex AI evaluation for voice agent quality
- **CRM dashboard** -- approval workflow and evaluation results viewer

## Repository Structure

```
personalized_shopping/
  client/                   # Frontend -- static HTML/JS/CSS
    src/api/                #   WebSocket API client
    src/ui/                 #   Home decor renderer, voice orb
    assets/                 #   Product images, style previews (203 files)
  server/                   # Backend -- WebSocket server
    core/agents/retail/     #   ADK agent, 25+ tools, intent detector
    config/                 #   Environment config, GCS settings
    evaluation/             #   Eval framework (recorder, metrics, Vertex AI)
    tests/                  #   Unit tests (40 tests, pytest)
    scripts/                #   Image generation, GCS upload utilities
  crm/                      # CRM Dashboard -- FastAPI
    core/app.py             #   REST API + eval endpoints
    static/                 #   Dashboard UI (dark theme)
  terraform/                # GCP Infrastructure as Code
    cloud_run.tf            #   3 Cloud Run services
    gcs.tf                  #   Storage bucket with lifecycle rules
    iam.tf                  #   Service accounts + IAM bindings
    vpc.tf                  #   VPC connector for Cloud Run
  docs/                     # Documentation
    DEMO_STORYLINE.md       #   Expected demo dialog script
    DEMO_GUIDE.md           #   Full demo walkthrough
    DEPLOYMENT_GUIDE.md     #   Cloud deployment instructions
  TESTS.md                  # Testing guide
  Makefile                  # Dev commands
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud project with Vertex AI enabled
- `gcloud auth application-default login` completed

### Local Development

```bash
# 1. Clone and configure
git clone git@github.com:tanvisinghal-0105/personalized-shopping.git
cd personalized-shopping
cd server && cp .env.example .env
# Edit .env with your project ID and config
pip install -r requirements.txt

# 2. Start all services
make backend    # Backend on :8081
make frontend   # Frontend on :8000
# CRM: cd crm && python main.py  # CRM on :8082

# 3. Open http://localhost:8000
```

### Environment Configuration

```bash
# server/.env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET_NAME=your-project-id-shopping-assets
```

## Testing

Run the full test suite:
```bash
cd server
python -m pytest tests/ -v          # 40 unit tests
python -m evaluation.run_eval       # Eval framework on recorded sessions
```

Or use the Claude Code skill: `/test-suite`

See [TESTS.md](TESTS.md) for the complete testing guide.

## Evaluation Framework

The project includes a custom 5-layer evaluation framework for voice agent quality:

| Layer | Metrics | Engine |
|-------|---------|--------|
| Speech Quality | WER, latency to first byte | Custom |
| Agent Trajectory | Tool call order, argument accuracy | Custom + Vertex AI |
| Conversation Quality | Relevance, naturalness, child-appropriateness | Vertex AI PointwiseMetric |
| Moodboard Quality | Style/color match, furniture balance | Custom |
| End-to-End Session | Task completion, turn efficiency | Custom |

Sessions are auto-recorded during live demos. Run evaluation from the CRM dashboard (Evaluation tab) or CLI:
```bash
cd server
python -m evaluation.run_eval --no-vertex    # Custom metrics only
python -m evaluation.run_eval                # Full eval with Vertex AI
```

## Infrastructure

Terraform manages the full GCP stack:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Resources provisioned:
- 3 Cloud Run services (frontend, backend, CRM)
- GCS bucket with lifecycle rules (eval log retention, generated image cleanup)
- IAM service accounts (Vertex AI, Firestore, Secret Manager, Storage)
- VPC connector for Cloud Run internal networking

## CI/CD Pipelines

Each service has a Cloud Build pipeline that runs **tests before deploy** and tags images with the git commit SHA for traceability.

| Pipeline | Pre-deploy Checks | Image Tag |
|----------|-------------------|-----------|
| `server/cloudbuild.yaml` | pytest (40 tests) + syntax validation | `$SHORT_SHA` + `latest` |
| `client/cloudbuild.yaml` | Asset URL validation (no local refs) | `$SHORT_SHA` + `latest` |
| `crm/cloudbuild.yaml` | Python syntax validation | `$SHORT_SHA` + `latest` |
| `terraform/cloudbuild.yaml` | `terraform validate` + `plan` + `apply` | N/A |

```bash
# Deploy individual services
gcloud builds submit --config server/cloudbuild.yaml      # tests + build + deploy
gcloud builds submit --config client/cloudbuild.yaml      # validate + build + deploy
gcloud builds submit --config crm/cloudbuild.yaml         # syntax + build + deploy
gcloud builds submit --config terraform/cloudbuild.yaml   # validate + plan + apply
```

### Code Quality
```bash
cd server
python -m pytest tests/ -v          # Unit tests
python -m black . --check           # Code formatting
python -m mypy core/ --ignore-missing-imports   # Type checking
```

## Demo Flow

The home decor consultation follows this storyline (see [docs/DEMO_STORYLINE.md](docs/DEMO_STORYLINE.md)):

1. **Initial request** -- "I need help redesigning Mila's bedroom"
2. **Context gathering** -- room purpose, age, constraints (what furniture to keep)
3. **Photo analysis** -- upload room photos or use live camera (1 FPS)
4. **Style finder** -- child-themed tiles with AI-generated previews from the room photo
5. **Color + dimensions** -- preferences and room size
6. **Moodboard** -- 10 curated products matched by style, color, age
7. **Room visualization** -- Imagen 3 renders products into the actual room
8. **Cart + checkout** -- add items, get complementary suggestions
9. **Discount approval** -- customer asks for bundle discount, AI escalates to manager via CRM, manager approves in real-time

## Component Documentation

- [Client README](client/README.md) -- Frontend details
- [Server README](server/README.md) -- Backend configuration
- [CRM README](crm/README.md) -- CRM dashboard
- [Demo Storyline](docs/DEMO_STORYLINE.md) -- Expected dialog script
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) -- Cloud deployment
