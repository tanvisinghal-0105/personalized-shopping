# 🚀 Cymbal Shopping AI - Deployment Guide

## Quick Deploy Commands

### Backend Deployment
```bash
cd /Users/tanvisinghal/Documents/personalized_shopping/server
gcloud builds submit --config cloudbuild.yaml
```

### Frontend Deployment
```bash
cd /Users/tanvisinghal/Documents/personalized_shopping/client
gcloud builds submit --config cloudbuild.yaml
```

## Detailed Instructions

### Step 1: Authenticate
```bash
gcloud auth login
gcloud config set project capstone-tanvi-01-447109
```

### Step 2: Deploy Backend
```bash
cd /Users/tanvisinghal/Documents/personalized_shopping/server
gcloud builds submit --config cloudbuild.yaml
```

**Expected Output:**
- Build ID will be displayed
- Container image pushed to GCR
- Service deployed to Cloud Run
- Service URL: `https://live-agent-backend-XXXXX-uc.a.run.app`

### Step 3: Verify Backend Deployment
```bash
gcloud run services describe live-agent-backend --region us-central1 --format 'value(status.url)'
```

### Step 4: Deploy Frontend
```bash
cd /Users/tanvisinghal/Documents/personalized_shopping/client
gcloud builds submit --config cloudbuild.yaml
```

### Step 5: Access Application
Once both are deployed, open the frontend URL in your browser.

## Configuration Notes

✅ **WebSocket endpoint is already updated** to point to the deployed backend:
- File: `/client/src/api/gemini-api.js`
- Endpoint: `wss://live-agent-backend-lyja7bi4gq-uc.a.run.app`

## Troubleshooting

### Permission Denied Error
If you get permission errors, ensure your account has the necessary roles:
```bash
gcloud projects add-iam-policy-binding capstone-tanvi-01-447109 \
  --member="user:tanvisinghal@google.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding capstone-tanvi-01-447109 \
  --member="user:tanvisinghal@google.com" \
  --role="roles/cloudbuild.builds.editor"
```

### View Deployment Logs
```bash
# Backend logs
gcloud run services logs tail live-agent-backend --region us-central1

# Build logs
gcloud builds list --limit 5
gcloud builds log [BUILD_ID]
```


