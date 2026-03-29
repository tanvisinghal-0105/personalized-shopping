import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.cloud import firestore
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = fastapi.FastAPI()

logger.info("Initializing Firestore client")
db = firestore.Client()

# Define the path to the static directory
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route to serve index.html from the root
@app.get("/", include_in_schema=False)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Optional: return a 404 or a simple message if index.html is missing
        return fastapi.Response(content="index.html not found", status_code=404)


@app.put("/api/v1/approvals/{customer_id}")
async def update_approval(customer_id: str):
    logger.info(f"Received PUT request for customer ID: {customer_id}")
    document = db.collection('customers').document(customer_id).get()
    if document.exists:
        try:
            document.reference.update({
                "approval_status": "approved"
            })
            logger.info(f"Successfully updated approval status for customer ID: {customer_id}")
            return {"customer_id": customer_id}
        except Exception as e:
            logger.error(f"Error updating Firestore for customer ID {customer_id}: {e}")
            raise fastapi.HTTPException(status_code=500, detail="Internal server error during update")
    else:
        logger.warning(f"Customer ID not found during PUT request: {customer_id}")
        # Return a proper FastAPI HTTP exception for not found
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")

@app.get("/api/v1/approvals/{customer_id}")
async def get_approval(customer_id: str):
    logger.info(f"Received GET request for customer ID: {customer_id}")
    document = db.collection('customers').document(customer_id).get()
    if document.exists:
        logger.info(f"Found customer ID: {customer_id}")
        return document.to_dict()
    else:
        logger.warning(f"Customer ID not found during GET request: {customer_id}")
        # Return a proper FastAPI HTTP exception for not found
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")


# 
# Add a route to reset the cart info with the DEFAULT CART INFO
@app.post("/api/v1/reset_cart/{customer_id}")
async def reset_cart(customer_id: str):
    CUSTOMER_CART_INFO = {
            'cart_id': 'CART-112233', # Use example ID for consistency
            'items': {
                'GENERIC-PIXEL-CASE': {'sku': '1122334', 'name': 'Generic Google Pixel Case', 'quantity': 1, 'price': 19} },
            'subtotal': 19,
            'last_updated': '2025-04-23 11:05:00' # Use example timestamp
    }

    logger.info(f"Setting up mock cart info for customer ID: {customer_id}...")
    db.collection('carts').document(customer_id).set(CUSTOMER_CART_INFO)
    logger.info(f"Mock cart info set up for customer ID: {customer_id}")
    return {"status": "success", "customer_id": customer_id, "cart_reset": True}


# Add a route to reset approval status back to pending
@app.post("/api/v1/reset_approval/{customer_id}")
async def reset_approval_status(customer_id: str):
    logger.info(f"Received POST request to reset approval status for customer ID: {customer_id}")
    document = db.collection('customers').document(customer_id).get()
    if document.exists:
        try:
            document.reference.update({
                "approval_status": "pending"
            })
            logger.info(f"Successfully reset approval status to pending for customer ID: {customer_id}")
            return {"status": "success", "customer_id": customer_id, "approval_status": "pending"}
        except Exception as e:
            logger.error(f"Error resetting approval status for customer ID {customer_id}: {e}")
            raise fastapi.HTTPException(status_code=500, detail="Internal server error during approval status reset")
    else:
        logger.warning(f"Customer ID not found during reset approval request: {customer_id}")
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")
