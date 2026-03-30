from google.cloud import firestore
from core.logger import logger
from datetime import datetime

# Initialize Firestore client
db = firestore.Client()

# Sample customer approval data
SAMPLE_CUSTOMERS = [
    {
        "customer_id": "CY-1234-1234",
        "menuId": 36,
        "menuLang": "en",
        "discount_type": "price_match",
        "discount_value": 59.99,
        "product_id": "GOOGLE-PIXEL9PRO-CASE",
        "crmAccountId": "abc123",
        "approval_status": "pending",
        "messages": {
            "agent": [
                "Customer found the Google Defender Series case at another store for 59.99 EUR and would like a price match."
            ],
            "allow": "My manager says ok",
            "deny": "My manager says no",
            "timeout": "Sorry I did not hear back from my manager",
            "error": "Sorry but I've had some trouble getting hold of my manager",
        },
        "escalationHost": "chat-escalation-243114688021.us-central1.run.app",
        "created_at": datetime.now().isoformat(),
    },
    {
        "customer_id": "CY-5678-5678",
        "menuId": 36,
        "menuLang": "en",
        "discount_type": "percentage",
        "discount_value": 10,
        "product_id": "APPLE-IPHONE-16",
        "crmAccountId": "xyz789",
        "approval_status": "approved",
        "messages": {
            "agent": [
                "Long-time customer requesting 10% loyalty discount on iPhone 16 purchase."
            ],
            "allow": "My manager says ok",
            "deny": "My manager says no",
            "timeout": "Sorry I did not hear back from my manager",
            "error": "Sorry but I've had some trouble getting hold of my manager",
        },
        "escalationHost": "chat-escalation-243114688021.us-central1.run.app",
        "created_at": datetime.now().isoformat(),
    },
    {
        "customer_id": "CY-9999-9999",
        "menuId": 36,
        "menuLang": "en",
        "discount_type": "flat",
        "discount_value": 50,
        "product_id": "SAMSUNG-QLED-65",
        "crmAccountId": "test123",
        "approval_status": "denied",
        "messages": {
            "agent": [
                "Customer requesting 50 EUR discount on Samsung QLED TV for minor packaging damage."
            ],
            "allow": "My manager says ok",
            "deny": "My manager says no",
            "timeout": "Sorry I did not hear back from my manager",
            "error": "Sorry but I've had some trouble getting hold of my manager",
        },
        "escalationHost": "chat-escalation-243114688021.us-central1.run.app",
        "created_at": datetime.now().isoformat(),
    },
]

# Sample cart data
SAMPLE_CART = {
    "cart_id": "CART-112233",
    "items": {
        "GENERIC-PIXEL-CASE": {
            "sku": "1122334",
            "name": "Generic Google Pixel Case",
            "quantity": 1,
            "price": 19,
        }
    },
    "subtotal": 19,
    "last_updated": "2025-04-23 11:05:00",
}


def initialize_sample_data():
    """Initialize Firestore with sample customer and cart data for testing."""
    try:
        logger.info("Initializing sample data in Firestore...")

        # Create sample customer approval requests
        for customer in SAMPLE_CUSTOMERS:
            customer_id = customer["customer_id"]
            db.collection("customers").document(customer_id).set(customer)
            logger.info(f"Created customer document: {customer_id}")

        # Create sample cart
        db.collection("carts").document("CY-1234-1234").set(SAMPLE_CART)
        logger.info("Created sample cart document")

        logger.info("Sample data initialization complete!")
        logger.info("\nTest with these customer IDs:")
        for customer in SAMPLE_CUSTOMERS:
            logger.info(
                f"  - {customer['customer_id']} ({customer['approval_status']})"
            )

    except Exception as e:
        logger.error(f"Failed to initialize sample data: {e}")


if __name__ == "__main__":
    initialize_sample_data()
