# Cymbal Shopping Assistant - CRM

Manager interface for approving Cymbal customer discount requests and special offers.

## Overview

The CRM application allows managers to:
- View customer approval requests with details (discount type, value, product, reason)
- Approve or deny discount requests
- Track approval status (pending, approved, denied)

## Architecture

- **Frontend**: Static HTML/CSS/JavaScript served by FastAPI
- **Backend**: FastAPI application that interfaces with Google Cloud Firestore
- **Database**: Firestore collections:
  - `customers` - stores customer approval requests
  - `carts` - stores customer shopping cart data

## Running Locally

1. Navigate to the CRM directory:
   ```bash
   cd crm
   ```

2. Install dependencies using UV:
   ```bash
   uv sync
   ```

3. Start the application:
   ```bash
   uv run main.py
   ```

4. Access the CRM interface at `http://localhost:8082`

## Testing the CRM

### Sample Customer IDs

Use these customer IDs to test the CRM functionality:

- **GR-1234-1234** - Pending approval for price match on Google Pixel case (59.99 EUR)
- **CY-5678-5678** - Approved request for 10% loyalty discount on iPhone 16
- **CY-9999-9999** - Denied request for 50 EUR discount on Samsung TV

### Initializing Sample Data

To populate Firestore with sample customer data for testing:

```bash
cd ../server
python init_sample_data.py
```

This creates 3 sample customer approval requests with different statuses (pending, approved, denied).

### Real-Time Approval Flow

1. Customer interacts with the retail agent (frontend client)
2. Agent requests manager approval using the `sync_ask_for_approval` tool
3. Approval request is created in Firestore with customer ID "GR-1234-1234"
4. Manager views request in CRM interface
5. Manager approves/denies request via CRM
6. Agent receives approval status and continues conversation

## API Endpoints

### GET /api/v1/approvals/{customer_id}
Retrieves approval request details for a specific customer.

**Response:**
```json
{
  "customer_id": "GR-1234-1234",
  "discount_type": "price_match",
  "discount_value": 59.99,
  "product_id": "GOOGLE-PIXEL9PRO-CASE",
  "approval_status": "pending",
  "messages": {
    "agent": ["Customer found the case at another store for 59.99 EUR"]
  }
}
```

### PATCH /api/v1/approvals/{customer_id}
Updates approval status for a customer request.

**Request Body:**
```json
{
  "approval_status": "approved"
}
```

## Deployment

The CRM is deployed to Google Cloud Run at:
https://cymbal-crm-991831686961.us-central1.run.app

### Deploy to Cloud Run

```bash
cd crm
gcloud builds submit --config cloudbuild.yaml .
```

## Environment Variables

- `PROJECT_ID` - Google Cloud project ID (for Firestore)
- `LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - Port to run the application on (default: 8082 for local, 8080 for Cloud Run)

## Troubleshooting

### "Customer not found" Error

This error occurs when:
1. No approval request has been created for that customer ID yet
2. The customer ID doesn't exist in Firestore

**Solutions:**
- Run `python init_sample_data.py` to create sample data
- Use one of the test customer IDs listed above
- Trigger an approval request through the agent interface first

### Firestore Connection Issues

Ensure you have:
- Google Cloud credentials configured (via `GOOGLE_APPLICATION_CREDENTIALS` or Application Default Credentials)
- Firestore API enabled in your Google Cloud project
- Service account with Firestore access permissions
