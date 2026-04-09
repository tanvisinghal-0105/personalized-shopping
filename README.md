# Cymbal Personalized Shopping Assistant

A multimodal AI shopping assistant powered by Google's Gemini 2.0 Flash with real-time voice, video, and text interactions. Built for Cymbal, a retail electronics company.

## Deployed Services

All services are live on Google Cloud Run:

- **Frontend**: https://cymbal-frontend-991831686961.us-central1.run.app
- **Backend**: https://live-agent-backend-lyja7bi4gq-uc.a.run.app
- **CRM**: https://cymbal-crm-991831686961.us-central1.run.app

## Overview

This application enables customers to interact with an AI shopping assistant through:
- Voice conversation with real-time speech recognition
- Video input for product identification
- Text-based chat interface
- Manager approval workflow for discounts and special requests

The system consists of three main components:
1. **Client** - Web-based UI for customer interactions
2. **Server** - WebSocket backend with Gemini 2.0 Flash integration
3. **CRM** - Manager interface for approval requests

## Key Features

- Real-time multimodal interactions (audio, video, text)
- Product recommendations and availability checking
- Shopping cart management
- Price matching and discount approvals
- Manager escalation workflow via CRM
- Low-latency responses with Gemini 2.0 Flash Live API

### Home Decor Consultation
- Multi-phase guided consultation flow (room selection, purpose, age context, constraints, style, colour, dimensions)
- Themed style finder for child bedrooms (Underwater World, Forest Adventure, Northern Lights, Space Explorer, Safari Wild, Rainbow Bright)
- Room photo analysis using Gemini Vision API with order history cross-referencing
- Room size collection with preset sizes and custom dimension input
- Intelligent moodboard generation with age-appropriate, style-matched, colour-coordinated products
- Room visualization powered by Imagen 3 -- renders selected products into the customer's actual room photo via inpainting, or generates a fresh photorealistic rendering
  
## Repository Structure

```
personalized-shopping/
├── client/          # Frontend web application (see client/README.md)
├── server/          # Backend WebSocket server (see server/README.md)
├── crm/             # Manager approval interface (see crm/README.md)
├── assets/          # Project images and logos
└── README.md        # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- **EITHER:**
  - Google AI Studio API key (recommended for development) - [Get API key](https://aistudio.google.com/apikey)
  - OR Google Cloud account with Vertex AI access (recommended for production)

### Model Options

This application supports two Gemini model deployment options:

#### Option 1: AI Studio (Development)
- **Model:** `gemini-3.1-flash-live-preview`
- **Setup:** Get API key from [AI Studio](https://aistudio.google.com/apikey)
- **Best for:** Local development, testing, demos

#### Option 2: Vertex AI (Production)
- **Model:** `gemini-live-2.5-flash-native-audio`
- **Setup:** Enable Vertex AI in Google Cloud project
- **Best for:** Production deployments, enterprise use

See [Server README](server/README.md) for detailed configuration instructions.

### Local Development

1. **Clone the repository**
   ```bash
   git clone git@github.com:tanvisinghal-0105/personalized-shopping.git
   cd personalized-shopping
   ```

2. **Configure backend**
   ```bash
   cd server
   cp .env.example .env
   # Edit .env with your API key or Vertex AI configuration
   pip install -r requirements.txt
   ```

   **For AI Studio (quickest):**
   ```bash
   # In .env file:
   GOOGLE_GENAI_USE_VERTEXAI=0
   GOOGLE_API_KEY=your_api_key_here
   ```

   **For Vertex AI:**
   ```bash
   # In .env file:
   GOOGLE_GENAI_USE_VERTEXAI=1
   GOOGLE_CLOUD_PROJECT=your_project_id
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

3. **Start backend server**
   ```bash
   python server.py
   ```
   Server runs on `localhost:8081`

4. **Start frontend client** (in new terminal)
   ```bash
   cd client
   python -m http.server 8000
   ```
   Access at `http://localhost:8000/index.html`

5. **Initialize test data**
   ```bash
   cd server
   python init_sample_data.py
   ```
   This creates sample customer approval requests for CRM testing

### Cloud Deployment

Deploy individual services to Google Cloud Run:

```bash
# Backend
gcloud builds submit --config server/cloudbuild.yaml

# Frontend
gcloud builds submit --config client/cloudbuild.yaml

# CRM
gcloud builds submit --config crm/cloudbuild.yaml
```

For detailed deployment instructions, see the README in each component directory.

## Testing the Application

1. **Test customer interactions**: Open the frontend and interact via voice or text
2. **Test manager approvals**: Use CRM interface with customer ID `GR-1234-1234`
3. **Check sample data**: Test with customer IDs: `GR-1234-1234`, `CY-5678-5678`, `CY-9999-9999`

## Architecture

The system uses a WebSocket-based architecture:
- Client sends audio/video/text to backend via WebSocket
- Backend processes with Gemini 2.0 Flash Live API
- Agent can call tools (cart management, product lookup, manager approvals)
- Manager approvals are stored in Firestore and accessed via CRM

## Component Documentation

- **[Client README](client/README.md)** - Frontend application details
- **[Server README](server/README.md)** - Backend configuration and deployment
- **[CRM README](crm/README.md)** - Manager approval interface
