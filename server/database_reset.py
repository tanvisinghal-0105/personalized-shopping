from core.agents.retail.tools import db
from core.logger import logger

CUSTOMER_CART_INFO = {
    "cart_id": "CART-112233",  # Use example ID for consistency
    "items": {
        "GENERIC-PIXEL-CASE": {
            "sku": "1122334",
            "name": "Generic Google Pixel Case",
            "quantity": 1,
            "price": 19,
        }
    },
    "subtotal": 19,
    "last_updated": "2025-04-23 11:05:00",  # Use example timestamp
}

logger.info("Setting up mock cart info...")
db.collection("carts").document("CY-1234-1234").set(CUSTOMER_CART_INFO)
logger.info("Mock cart info set up")
