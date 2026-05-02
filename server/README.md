
# Cymbal Shopping Assistant - Backend Server

WebSocket-based backend server for Cymbal's AI shopping assistant, powered by Google Gemini Live API with multimodal capabilities.

## Overview

The server handles:
- WebSocket connections from client applications
- Real-time audio/video/text processing via Gemini Live API
- Tool execution (product lookup, cart management, approvals)
- Session management for customer conversations
- Manager approval workflow integration with Firestore

## Model Configuration

This application supports two Gemini model deployment options:

### Option 1: AI Studio (Recommended for Development)

**Model:** `gemini-3.1-flash-live-preview`

**Setup:**
1. Get your API key from [AI Studio](https://aistudio.google.com/apikey)
2. Configure `.env`:
   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=0
   GOOGLE_API_KEY=your_api_key_here
   MODEL_DEV_API=gemini-3.1-flash-live-preview
   AGENT_MODEL_DEV_API=gemini-3.1-flash-live-preview
   ```

### Option 2: Vertex AI (Recommended for Production)

**Model:** `gemini-live-2.5-flash-native-audio`

**Setup:**
1. Enable Vertex AI in your Google Cloud project
2. Configure `.env`:
   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=1
   GOOGLE_CLOUD_PROJECT=your_project_id
   GOOGLE_CLOUD_LOCATION=us-central1
   MODEL_VERTEX_API=gemini-live-2.5-flash-native-audio
   AGENT_MODEL_VERTEX_API=gemini-live-2.5-flash-native-audio
   ```

## Architecture

```
server/
├── core/
│   ├── agents/
│   │   └── retail/          # Retail agent implementation
│   │       ├── agent.py     # Agent configuration
│   │       ├── prompts.py   # System instructions
│   │       ├── tools.py     # Tool implementations
│   │       ├── context.py   # Customer context
│   │       └── examples.py  # Conversation examples
│   ├── gemini_client.py     # Gemini API client
│   ├── session.py           # Session management
│   ├── tool_handler.py      # Tool routing
│   └── websocket_handler.py # WebSocket handler
├── config/
│   └── config.py            # Configuration management
├── server.py                # Main entry point
├── init_sample_data.py      # Sample data for testing
└── requirements.txt         # Python dependencies
```

## Quick Start

### Local Development

1. **Install dependencies**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Required variables:
   - `GOOGLE_API_KEY` - Your Gemini API key
   - `GOOGLE_CLOUD_PROJECT` - GCP project ID
   - `GOOGLE_CLOUD_LOCATION` - GCP region (e.g., us-central1)

3. **Start server**
   ```bash
   python server.py
   ```
   Server listens on `localhost:8081`

4. **Initialize test data**
   ```bash
   python init_sample_data.py
   ```
   Creates sample customer approval requests in Firestore

### Cloud Run Deployment

```bash
# From project root
gcloud builds submit --config server/cloudbuild.yaml
```

The deployment:
- Builds Docker container
- Deploys to Cloud Run as `live-agent-backend`
- Uses service account with Secret Manager access
- Connects to Firestore for approval workflow

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Gemini API key | Yes (if using Dev API) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes |
| `GOOGLE_CLOUD_LOCATION` | GCP region | Yes |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Vertex AI (1) or Dev API (0) | No (default: 0) |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

### Secret Manager (Production)

For Cloud Run deployment, store secrets in Google Cloud Secret Manager:
- `GOOGLE_API_KEY` - Gemini API key

The service account must have `roles/secretmanager.secretAccessor` role.

## Agent Configuration

The retail agent is configured in `core/agents/retail/`:

- **System Instructions** (`prompts.py`): Defines agent personality and behavior
- **Tools** (`tools.py`): Available functions (product lookup, cart, approvals)
- **Context** (`context.py`): Customer profile information
- **Examples** (`examples.py`): Sample conversations for few-shot learning

## Available Tools

The agent can execute these tools:

| Tool | Description |
|------|-------------|
| `access_cart_information` | Retrieve customer cart contents |
| `modify_cart` | Add/remove items from cart |
| `get_product_recommendations` | Suggest relevant products |
| `check_product_availability` | Check stock at stores |
| `sync_ask_for_approval` | Request manager approval for discounts |
| `lookup_warranty_details` | Get warranty information |
| `get_trade_in_value` | Calculate trade-in value |
| `schedule_service_appointment` | Book service appointments |

## Testing

### WebSocket Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect to local server
wscat -c ws://localhost:8081

# Connect to Cloud Run
wscat -c wss://YOUR-CLOUD-RUN-URL

# Send test message
{"type": "text", "data": "Hello, I need help"}
```

### Testing Manager Approvals

1. Start the server
2. Run `python init_sample_data.py` to create test data
3. Test with customer IDs:
   - `GR-1234-1234` - Pending approval
   - `CY-5678-5678` - Approved request
   - `CY-9999-9999` - Denied request

## Firestore Collections

The server uses these Firestore collections:

- `customers` - Customer approval requests
  - Document ID: customer ID (e.g., "GR-1234-1234")
  - Fields: discount details, approval status, messages

- `carts` - Shopping cart data
  - Document ID: customer ID
  - Fields: cart items, subtotal, timestamp

## Troubleshooting

### Connection Issues

- Check WebSocket URL in client matches server address
- Verify firewall rules allow WebSocket connections on port 8081
- Check server logs for connection errors

### API Errors

- Verify `GOOGLE_API_KEY` is set correctly
- Check API quota limits in Google Cloud Console
- Ensure Gemini API is enabled for your project

### Firestore Errors

- Verify service account has Firestore access
- Check Firestore database exists in your project
- Run `init_sample_data.py` to populate test data

### Tool Execution Failures

- Check tool function signatures match declarations
- Verify Firestore collections exist
- Check logs for specific error messages

## Development

### Adding New Tools

1. Define tool function in `core/agents/retail/tools.py`
2. Add function declaration in `core/agents/retail/agent.py`
3. Update system instructions in `prompts.py` to describe when to use the tool
4. Test the tool with sample conversations

### Modifying Agent Behavior

Edit these files to customize the agent:
- `prompts.py` - System instructions and personality
- `context.py` - Customer profile and context
- `examples.py` - Few-shot learning examples

## Deployed Service

- **Region**: us-central1
- **Service Account**: live-agent-backend@$PROJECT_ID.iam.gserviceaccount.com

The service URL is dynamic and determined at deploy time. No hardcoded project IDs -- all configuration is via environment variables.
