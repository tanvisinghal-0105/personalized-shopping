# Cymbal Shopping Assistant - Frontend Client

Web-based customer interface for Cymbal's AI shopping assistant with multimodal interactions.

## Overview

The client application provides:
- Voice input via microphone with WebAudio API
- Video capture from webcam and screen sharing
- Text-based chat interface
- Real-time audio playback of AI responses
- WebSocket connection to backend server

## Architecture

```
client/
├── index.html           # Development UI with debugging features
├── mobile.html          # Mobile-optimized production UI
├── src/
│   ├── api/
│   │   └── gemini-api.js        # WebSocket communication
│   ├── audio/
│   │   ├── audio-recorder.js    # Microphone recording
│   │   ├── audio-streamer.js    # Audio playback
│   │   └── audio-recording-worklet.js  # Audio processing
│   ├── media/
│   │   └── media-handler.js     # Webcam/screen sharing
│   └── utils/
│       └── utils.js             # Helper functions
├── styles/
│   ├── style.css                # Development UI styles
│   └── mobile-style.css         # Mobile UI styles
├── assets/                      # Images and icons
├── nginx.conf                   # nginx configuration
└── Dockerfile                   # Container build config
```

## Quick Start

### Local Development

1. **Start backend server first**
   ```bash
   cd server
   python server.py
   ```
   Backend runs on `localhost:8081`

2. **Start frontend server**
   ```bash
   cd client
   python -m http.server 8000
   ```

3. **Access the application**
   - Development UI: http://localhost:8000/index.html
   - Mobile UI: http://localhost:8000/mobile.html

### Configure Backend URL

Edit `index.html` and `mobile.html` to set the WebSocket endpoint:

```javascript
// For local development
const api = new GeminiAPI();  // Uses ws://localhost:8081

// For deployed backend
const api = new GeminiAPI('wss://live-agent-backend-xxxx.run.app');
```

### Cloud Run Deployment

```bash
# From project root
gcloud builds submit --config client/cloudbuild.yaml
```

The deployment:
- Builds nginx-based container
- Serves static files
- Runs on port 8080
- Deployed as `cymbal-frontend`

## Features

### Development UI (index.html)

- Detailed WebSocket connection status
- Function call logging in chat
- Text input for testing
- Verbose error messages
- Debug console output

### Mobile UI (mobile.html)

- Clean, minimal interface
- Voice-first interaction
- Touch-optimized controls
- Mobile-friendly layout
- Streamlined error handling

## Browser Permissions

The application requires:
- **Microphone access**: For voice input
- **Camera access**: For product identification via video
- **Screen sharing** (optional): For visual assistance

Grant permissions when prompted by the browser.

## WebSocket Communication

The client sends these message types to the backend:

```javascript
// Audio data
{ type: 'audio', data: '<base64-encoded-audio>' }

// Text message
{ type: 'text', data: 'User message' }

// Image/video frame
{ type: 'image', data: '<base64-encoded-image>' }

// End of turn signal
{ type: 'end' }
```

## Troubleshooting

### WebSocket Connection Errors

- **"Connection failed"**: Check backend is running on correct port
- **"Missing Connection header"**: Don't access WebSocket URL directly in browser
- **CORS errors**: Verify backend allows requests from client origin

### Audio/Video Issues

- **No audio playback**: Check browser permissions and AudioContext state
- **Microphone not working**: Grant microphone permissions in browser settings
- **Video not capturing**: Verify camera access and device availability

### localStorage Errors

- **Data not persisting**: Don't use `file://` protocol, use HTTP server
- **Sign-in not working**: Serve via HTTP (port 8000) not file system

## Development

### Testing Locally

1. Start backend: `cd server && python server.py`
2. Start frontend: `cd client && python -m http.server 8000`
3. Open browser: http://localhost:8000/index.html
4. Check console for errors
5. Test voice/text interactions

### Modifying UI

- **Development UI**: Edit `index.html` and `styles/style.css`
- **Mobile UI**: Edit `mobile.html` and `styles/mobile-style.css`
- **WebSocket logic**: Edit `src/api/gemini-api.js`
- **Audio handling**: Edit files in `src/audio/`

## Deployed Service

- **URL**: https://cymbal-frontend-991831686961.us-central1.run.app
- **Region**: us-central1
- **Backend**: https://live-agent-backend-lyja7bi4gq-uc.a.run.app
