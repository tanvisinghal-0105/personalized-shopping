import random
import time
from typing import Optional, List, Dict, Any
import requests
import json
from ...logger import logger
from ...retry import vertex_ai_retry, imagen_retry, firestore_retry
from datetime import datetime, timedelta

from google.cloud import firestore
from .context import RetailContext
from .session_state import get_state_manager
from config.config import RECOMMENDATION_MODEL, GCS_ASSETS_BASE_URL

_ASSETS = GCS_ASSETS_BASE_URL

# Initialize Firestore client with error handling
db = None
CUSTOMER_CART_INFO = {
    "cart_id": "CART-112233",
    "items": {},
    "subtotal": 0,
    "last_updated": "",
}

try:
    logger.info("Connecting to Firestore...")
    db = firestore.Client()
    logger.info("Connected to Firestore")

    # Carts will be created dynamically per customer when needed
    # No need for hardcoded cart initialization
    logger.info("Firestore ready - carts will be created per customer dynamically")
except Exception as e:
    logger.warning(
        f"Firestore initialization failed: {e}. Running without Firestore support."
    )
    db = None


# Use the product catalog from context.py to ensure consistency
# Convert list of dicts to dict keyed by product_id for easy lookup
PRODUCT_CATALOG = {
    product["product_id"]: {
        "name": product["name"],
        "price": product["price"],
        "sku": product["sku"],
    }
    for product in RetailContext.PRODUCT_CATALOG
}


def send_call_companion_link(phone_number: str) -> str:
    """Sends a link to the user's phone number to connect the call with the companion app."""
    logger.info(f"Sending call companion link to {phone_number}...")
    return {"status": "success", "message": f"Link sent to {phone_number}"}


def approve_discount(
    type: str, value: float, reason: str, product_id: str = ""
) -> dict:
    """Approves a flat rate or percentage discount for a product or service, based on predefined rules."""
    logger.info(
        f"Attempting to approve discount: type={type}, value={value}, reason={reason}, product_id={product_id}"
    )
    logger.info("INSIDE TOOL CALL")
    # Example: Apply price match approval from example.py logic
    if (
        product_id == "GOOGLE-PIXEL9PRO-CASE"
        and type == "price_match"
        and value == 59.99
    ):
        return {
            "status": "approved",
            "message": f"Price match to {value} EUR approved for {product_id}.",
        }
    # Example: Apply bundle discount from example.py
    # if product_id == 'PLUSGARANTIE-PIXEL' and type == 'percentage' and value == 10:
    #      return {"status": "approved", "message": f"Discount of {value}{'%' if type == 'percentage' else 'EUR'} approved for {product_id}."}
    # Fallback generic approval
    return {
        "status": "approved",
        "message": f"Discount of {value}{'%' if type == 'percentage' else 'EUR'} approved.",
    }


def sync_ask_for_approval(
    customer_id: str, type: str, value: float, reason: str, product_id: str = ""
) -> str:
    """Asks a manager for approval synchronously (waits for a response).

    This tool creates an approval request in Firestore and polls until
    the manager approves or denies it via the CRM dashboard.

    Args:
        customer_id: The customer ID requesting the discount.
        type: Type of discount ('percentage', 'flat', 'price_match', 'bundle').
        value: Discount value (e.g. 10 for 10% or 10 EUR).
        reason: Reason for the discount request.
        product_id: Optional product ID the discount applies to.

    Returns:
        A string indicating the manager's decision.
    """
    logger.info(
        f"Requesting manager approval for customer {customer_id}: {type}={value}, reason={reason}, product_id={product_id}"
    )

    # Fetch current cart items to include in the approval request
    cart_items = []
    cart_subtotal = 0
    if db is not None:
        try:
            cart_doc = db.collection("carts").document(customer_id).get()
            if cart_doc.exists:
                cart_data = cart_doc.to_dict()
                items_raw = cart_data.get("items", {})
                if isinstance(items_raw, dict):
                    cart_items = [
                        {"name": v.get("name", k), "price": v.get("price", 0), "quantity": v.get("quantity", 1)}
                        for k, v in items_raw.items()
                    ]
                elif isinstance(items_raw, list):
                    cart_items = [
                        {"name": i.get("name", ""), "price": i.get("price", 0), "quantity": i.get("quantity", 1)}
                        for i in items_raw
                    ]
                cart_subtotal = cart_data.get("subtotal", 0)
        except Exception as e:
            logger.warning(f"Failed to fetch cart for approval: {e}")

    discount_amount = value if type == "flat" else round(cart_subtotal * value / 100, 2)

    payload = {
        "customer_id": customer_id,
        "discount_type": type,
        "discount_value": value,
        "discount_amount_eur": discount_amount,
        "reason": reason,
        "approval_status": "pending",
        "requested_at": datetime.now().isoformat(),
        "cart_items": cart_items,
        "cart_subtotal": cart_subtotal,
        "new_total_after_discount": round(cart_subtotal - discount_amount, 2),
    }

    if db is not None:
        try:
            db.collection("customers").document(customer_id).set(payload)
            logger.info(f"Approval request saved to Firestore for {customer_id}")
        except Exception as e:
            logger.warning(f"Failed to save to Firestore: {e}")
            return "Sorry, I had trouble reaching my manager. Please try again."

    logger.info("Waiting for manager approval...")

    # Poll for approval status -- max 3 minutes with 2 second intervals
    for i in range(90):
        if db is not None:
            try:
                doc = db.collection("customers").document(customer_id).get()
                if doc.exists:
                    status = doc.to_dict().get("approval_status", "pending")
                    if status == "approved":
                        logger.info(f"Manager APPROVED discount for {customer_id}")
                        return (
                            "Great news! My manager has approved the discount for you."
                        )
                    elif status == "denied":
                        logger.info(f"Manager DENIED discount for {customer_id}")
                        return "I'm sorry, my manager was not able to approve that discount at this time."
            except Exception as e:
                logger.warning(f"Failed to check Firestore: {e}")
                break
        else:
            time.sleep(2)
            return "My manager has approved the discount. (simulated)"

        time.sleep(2)

    logger.info(f"Manager approval not received after 3 minutes for {customer_id}")
    return "I haven't heard back from my manager yet. Let me check on that and get back to you."

    logger.info("Sending request to manager...")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response)
    logger.info("Request sent to manager")

    if response.status_code == 200:
        logger.info("Manager approved the discount")
        return response.text  # Return the response text if the status code is 200
    else:
        logger.warning("Simulating sync denial or timeout for unspecified request.")
        # Simulate a denied or timeout scenario for other cases
        return '{"status":"denied", "message":"Manager approval denied or timed out for this request."}'


def identify_phone_from_camera_feed(
    image_data: Optional[str] = None, customer_id: Optional[str] = None
) -> dict:
    """
    Identifies a phone model from a camera feed using Gemini Vision API.

    Args:
        image_data: Optional base64 encoded image data from the camera feed (data URI format or raw base64).
        customer_id: Optional customer ID for context or fetching session-specific data.

    Returns:
        A dictionary containing the identified phone model and a message.
    """
    logger.info(
        f"Attempting to identify phone from camera feed using Gemini Vision. Customer ID: {customer_id}"
    )

    if image_data:
        logger.info(
            f"Image data received (length: {len(image_data)} characters). Processing with Gemini Vision..."
        )

        # Extract base64 data if it's in data URI format
        if image_data.startswith("data:"):
            # Format: "data:image/jpeg;base64,<base64data>"
            image_base64 = image_data.split(",")[1] if "," in image_data else image_data
        else:
            image_base64 = image_data

        # Check for minimal image data
        if len(image_base64) < 1000:
            identified_model = "Unknown Device (low quality image)"
            message = "The image data from the camera feed was minimal, making identification difficult."
            return {
                "status": "failure",
                "identified_phone_model": identified_model,
                "message": message,
                "image_data_processed": True,
            }

        # Use Gemini 3.1 Pro Preview (or Flash) for vision analysis
        try:
            from google import genai
            from google.genai import types
            import base64

            client = genai.Client()

            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_base64)

            # Create the vision prompt
            prompt = """Analyze this image and identify the smartphone model if visible.

Look for distinctive features:
- Brand logos (Apple, Google Pixel, Samsung, etc.)
- Camera module design and layout (number of lenses, arrangement)
- Notch or punch-hole camera style
- Device dimensions and shape
- Any visible text, model numbers, or branding

Respond with ONLY the specific model name in this format:
"[Brand] [Model]"

Examples:
- "Apple iPhone 16 Pro"
- "Google Pixel 9 Pro"
- "Samsung Galaxy S24 Ultra"
- "Apple iPhone 15"

If you cannot clearly identify the phone, respond:
"Unknown Phone Model"

Response (model name only):"""

            # Use Gemini 3.1 Flash Preview or Pro Preview for vision
            # Try Flash first (faster), fall back to Pro if needed
            vision_model = (
                "gemini-3.1-flash-preview"
                if "flash" in RECOMMENDATION_MODEL.lower()
                else "gemini-3.1-pro-preview"
            )

            logger.info(f"Using {vision_model} for phone identification")

            # Call Gemini Vision with image
            response = client.models.generate_content(
                model=vision_model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for precise identification
                    max_output_tokens=100,
                ),
            )

            # Extract the identified model from response
            identified_model = response.text.strip()

            # Clean up the response
            identified_model = identified_model.replace('"', "").replace("'", "")

            logger.info(f"Gemini Vision identified: {identified_model}")

            if "unknown" in identified_model.lower():
                message = "I can see a device in the camera feed, but I'm having trouble identifying the specific model. Could you hold it closer or at a better angle?"
                status = "partial"
            else:
                message = (
                    f"Based on the camera feed, this looks like a {identified_model}."
                )
                status = "success"

            return {
                "status": status,
                "identified_phone_model": identified_model,
                "message": message,
                "image_data_processed": True,
            }

        except Exception as e:
            logger.error(f"Error using Gemini Vision for phone identification: {e}")
            # Fallback to default
            identified_model = "Unknown Device (identification error)"
            message = f"I had trouble analyzing the image. Error: {str(e)[:100]}"
            return {
                "status": "error",
                "identified_phone_model": identified_model,
                "message": message,
                "image_data_processed": False,
            }
    else:
        logger.warning(
            "No image data was provided to the identify_phone_from_camera_feed tool."
        )

        return {
            "status": "error",
            "identified_phone_model": "Unknown - No Image Data",
            "message": "This tool requires image data to identify a phone. However, you have access to the live camera feed in your context - you can see the camera images directly and should analyze them without calling this tool. Look at the visual content you're receiving and identify the phone based on what you actually see (brand logos, camera design, shape, etc.). Do not make assumptions or use defaults.",
            "image_data_processed": False,
        }


def access_cart_information(customer_id: str) -> dict:
    """Retrieves the contents of the user's shopping cart.

    Args:
        customer_id: The ID of the customer.

    Returns:
        A dictionary representing the cart contents.
    """
    logger.info(f"Accessing cart information for customer ID: {customer_id}")

    # Use dynamic customer_id instead of hardcoded value
    if db is not None:
        try:
            mock_cart = db.collection("carts").document(customer_id).get()
            if mock_cart.exists:
                mock_cart = mock_cart.to_dict()
                # Convert items from dict to array if needed
                if (
                    mock_cart
                    and "items" in mock_cart
                    and isinstance(mock_cart["items"], dict)
                ):
                    mock_cart["items"] = [
                        {
                            "product_id": product_id,
                            "name": data["name"],
                            "price": data["price"],
                            "sku": data["sku"],
                            "quantity": data["quantity"],
                        }
                        for product_id, data in mock_cart["items"].items()
                    ]
            else:
                # Cart doesn't exist yet, initialize empty cart
                logger.info(
                    f"No cart found for customer {customer_id}, initializing empty cart"
                )
                mock_cart = {
                    "cart_id": f"CART-{customer_id[-6:]}",
                    "items": [],
                    "subtotal": 0.0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
        except Exception as e:
            logger.warning(f"Failed to access Firestore: {e}. Using empty cart.")
            mock_cart = {
                "cart_id": f"CART-{customer_id[-6:]}",
                "items": [],
                "subtotal": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
    else:
        # No Firestore connection, return empty cart
        logger.info("No Firestore connection, returning empty cart")
        mock_cart = {
            "cart_id": f"CART-{customer_id[-6:]}",
            "items": [],
            "subtotal": 0.0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    return mock_cart


def modify_cart(
    customer_id: str,
    items_to_add: Optional[List[Dict[str, Any]]] = None,
    items_to_remove: Optional[List[str]] = None,
    has_manager_approval: bool = False,
) -> dict:
    """Modifies the user's shopping cart by adding and/or removing items."""
    logger.info(f"Modifying cart for customer ID: {customer_id}")
    items_added_flag = False
    items_removed_flag = False

    # --- MOCK BACKEND CART STATE ---
    # Use dynamic customer_id to fetch cart
    if db is not None:
        try:
            mock_cart = db.collection("carts").document(customer_id).get()
            if mock_cart.exists:
                current_mock_backend_cart = mock_cart.to_dict()
                # Ensure items is a dict for manipulation
                if "items" not in current_mock_backend_cart or not isinstance(
                    current_mock_backend_cart["items"], dict
                ):
                    current_mock_backend_cart["items"] = {}
            else:
                # Cart doesn't exist yet, initialize empty cart for this
                # customer
                logger.info(
                    f"No cart found for customer {customer_id}, initializing empty cart"
                )
                current_mock_backend_cart = {
                    "cart_id": f"CART-{customer_id[-6:]}",
                    "items": {},
                    "subtotal": 0.0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
        except Exception as e:
            logger.warning(f"Failed to access Firestore: {e}. Using empty cart.")
            current_mock_backend_cart = {
                "cart_id": f"CART-{customer_id[-6:]}",
                "items": {},
                "subtotal": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
    else:
        # No Firestore connection, use empty cart
        logger.info("No Firestore connection, using empty cart")
        current_mock_backend_cart = {
            "cart_id": f"CART-{customer_id[-6:]}",
            "items": {},
            "subtotal": 0.0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    if items_to_add:
        logger.info(f"Adding items: {items_to_add}")
        # Validate all product IDs BEFORE adding any items
        invalid_products = []
        for item in items_to_add:
            prod_id = item.get("product_id")
            # Check for None or empty product_id
            if not prod_id or prod_id not in PRODUCT_CATALOG:
                invalid_products.append(prod_id if prod_id else "None")
                logger.warning(f"INVALID PRODUCT ID: {prod_id} not found in catalog")

        # If any invalid products, return error immediately
        if invalid_products:
            # Find similar products to suggest
            suggestions = []
            for invalid_id in invalid_products:
                # Skip None values for suggestions
                if not invalid_id or invalid_id == "None":
                    continue
                # Look for similar product IDs (e.g., same brand/category)
                invalid_lower = invalid_id.lower()
                for valid_id in list(PRODUCT_CATALOG.keys())[:10]:  # Sample first 10
                    if any(
                        word in valid_id.lower()
                        for word in invalid_lower.split("-")[:2]
                    ):
                        suggestions.append(valid_id)
                        if len(suggestions) >= 3:
                            break

            error_msg = f"ERROR: Invalid product ID(s): {', '.join(invalid_products)}. "
            error_msg += "These products do not exist in the catalog. "
            error_msg += "You MUST use EXACT product IDs from the available_products catalog table. "
            error_msg += "NEVER create or modify product IDs. "
            if suggestions:
                error_msg += f"Did you mean one of these valid IDs: {', '.join(suggestions[:3])}? "
            error_msg += "Please check the catalog and try again with the exact Product ID from the table."

            return {
                "status": "error",
                "message": error_msg,
                "invalid_product_ids": invalid_products,
                "items_added": False,
                "items_removed": False,
                "updated_cart": access_cart_information(customer_id),
            }

        # All products valid, proceed with adding
        for item in items_to_add:
            prod_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            if prod_id in current_mock_backend_cart["items"]:
                current_mock_backend_cart["items"][prod_id]["quantity"] += quantity
            else:
                current_mock_backend_cart["items"][prod_id] = {
                    "name": PRODUCT_CATALOG[prod_id]["name"],
                    "price": PRODUCT_CATALOG[prod_id]["price"],
                    "sku": PRODUCT_CATALOG[prod_id]["sku"],
                    "quantity": quantity,
                }
            items_added_flag = True

    if items_to_remove:
        logger.info(f"Removing items: {items_to_remove}")
        # Mock removing items (expects list of product_ids)
        for prod_id in items_to_remove:
            if isinstance(prod_id, dict):
                prod_id = prod_id["product_id"]
            if prod_id in current_mock_backend_cart["items"]:
                del current_mock_backend_cart["items"][prod_id]
                items_removed_flag = True
            else:
                logger.warning(
                    f"Product ID {prod_id} not found in mock cart for removal."
                )

    # MOCK API RESPONSE - Construct based on the simulated backend cart
    if items_added_flag or items_removed_flag or has_manager_approval:
        # Recalculate subtotal for the mock cart
        new_subtotal = sum(
            item["price"] * item["quantity"]
            for item in current_mock_backend_cart["items"].values()
        )
        # Apply price match adjustment specifically for OtterBox if present (as
        # done in example checkout)
        if (
            "GOOGLE-PIXEL9PRO-CASE" in current_mock_backend_cart["items"]
            and has_manager_approval
        ):
            original_price = PRODUCT_CATALOG["GOOGLE-PIXEL9PRO-CASE"]["price"]
            matched_price = 45  # From example
            price_diff = original_price - matched_price
            new_subtotal -= (
                price_diff
                * current_mock_backend_cart["items"]["GOOGLE-PIXEL9PRO-CASE"][
                    "quantity"
                ]
            )
            # Reflect matched price in item data for clarity
            current_mock_backend_cart["items"]["GOOGLE-PIXEL9PRO-CASE"][
                "price"
            ] = matched_price

        # Update the mock backend cart state using dynamic customer_id (save as dict)
        cart_to_save = {
            "cart_id": current_mock_backend_cart["cart_id"],
            "items": current_mock_backend_cart["items"],  # Keep as dict in Firestore
            "subtotal": round(new_subtotal, 2),
            "last_updated": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # Update timestamp
        }

        if db is not None:
            try:
                db.collection("carts").document(customer_id).set(cart_to_save)
                logger.info(f"Cart updated in Firestore for customer {customer_id}")
            except Exception as e:
                logger.warning(f"Failed to update cart in Firestore: {e}")

        # Convert items dict to array for client compatibility (for response only)
        updated_cart_list = [
            {
                "product_id": product_id,
                "name": data["name"],
                "price": data["price"],
                "sku": data["sku"],
                "quantity": data["quantity"],
            }
            for product_id, data in current_mock_backend_cart["items"].items()
        ]

        # Construct the final updated cart structure for response
        final_updated_cart = {
            "cart_id": current_mock_backend_cart["cart_id"],
            "items": updated_cart_list,
            "subtotal": round(new_subtotal, 2),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return {
            "status": "success",
            "message": "Cart updated successfully.",
            "items_added": items_added_flag,
            "items_removed": items_removed_flag,
            "updated_cart": final_updated_cart,  # Return the new state of the cart
        }
    else:
        # If no changes, fetch the current state using
        # access_cart_information's logic
        current_cart_state = access_cart_information(customer_id)
        return {
            "status": "no_change",
            "message": "No changes were requested for the cart.",
            "items_added": False,
            "items_removed": False,
            "updated_cart": current_cart_state,
        }


def get_product_recommendations(
    interest: str = "", customer_id: str = "", current_product_id: str = ""
) -> dict:
    """Provides product recommendations based on interests, purchase history, or related items using Gemini AI."""
    logger.info(
        f"Getting product recommendations for interest: {interest}, customer: {customer_id}, related_to: {current_product_id}"
    )

    if not interest:
        # Return random products if no interest specified
        fallback_recommendations = []
        for product in RetailContext.PRODUCT_CATALOG:
            if product["product_id"] != current_product_id and product.get(
                "in_stock", True
            ):
                fallback_recommendations.append(
                    {
                        "product_id": product["product_id"],
                        "name": product["name"],
                        "description": f"{product['category']} - €{product['price']:.2f}",
                    }
                )
        random.shuffle(fallback_recommendations)
        return {"recommendations": fallback_recommendations[:3]}

    # Use Gemini to intelligently match products
    try:
        from google import genai
        from google.genai import types

        client = genai.Client()

        # Build a concise product catalog for Gemini with home decor metadata
        catalog_text = "Available products:\n"
        for product in RetailContext.PRODUCT_CATALOG:
            if product["product_id"] != current_product_id:
                # Include additional metadata for Home Decor products
                if product.get("category") == "Home Decor":
                    style_info = (
                        f" [Styles: {', '.join(product.get('style_tags', []))}]"
                        if product.get("style_tags")
                        else ""
                    )
                    color_info = (
                        f" [Colors: {', '.join(product.get('color_palette', []))}]"
                        if product.get("color_palette")
                        else ""
                    )
                    room_info = (
                        f" [Rooms: {', '.join(product.get('room_compatibility', []))}]"
                        if product.get("room_compatibility")
                        else ""
                    )
                    catalog_text += f"- {product['product_id']}: {product['name']} ({product.get('subcategory', product['category'])}) - €{product['price']:.2f}{style_info}{color_info}{room_info}\n"
                else:
                    catalog_text += f"- {product['product_id']}: {product['name']} ({product['category']}) - €{product['price']:.2f}\n"

        prompt = f"""You are a product recommendation expert. Based on the customer's interest, recommend the 3 most relevant products from the catalog.

Customer interest: "{interest}"

{catalog_text}

Return ONLY a JSON array with exactly 3 product IDs, nothing else. Format: ["PRODUCT-ID-1", "PRODUCT-ID-2", "PRODUCT-ID-3"]

Choose products that best match the customer's interest. For example:
- "sneakers" or "shoes" → Footwear products (Nike, Adidas, etc.)
- "laptop" or "computer" → Laptop products
- "TV" or "television" → TV products
- "phone" or "smartphone" → Phone products
- "modern living room" → Home Decor products with modern style tags for living room
- "coastal bedroom" → Home Decor products with coastal style tags for bedroom
- "gold accents" → Home Decor products with gold in their color palette"""

        response = client.models.generate_content(
            model=RECOMMENDATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=200),
        )

        # Parse the response to get product IDs
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        product_ids = json.loads(response_text)

        # Build recommendations from the matched product IDs
        recommendations = []
        for pid in product_ids[:3]:
            for product in RetailContext.PRODUCT_CATALOG:
                if product["product_id"] == pid:
                    recommendations.append(
                        {
                            "product_id": product["product_id"],
                            "name": product["name"],
                            "description": f"{product['category']} - €{product['price']:.2f}",
                        }
                    )
                    break

        logger.info(
            f"Gemini recommended {len(recommendations)} products for '{interest}'"
        )

        if recommendations:
            return {"recommendations": recommendations[:3]}

    except Exception as e:
        logger.error(f"Error using Gemini for recommendations: {e}")
        # Fall through to fallback logic

    # Fallback: return random popular products if Gemini fails
    fallback_recommendations = []
    for product in RetailContext.PRODUCT_CATALOG:
        if product["product_id"] != current_product_id and product.get(
            "in_stock", True
        ):
            fallback_recommendations.append(
                {
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "description": f"{product['category']} - €{product['price']:.2f}",
                }
            )

    random.shuffle(fallback_recommendations)
    return {"recommendations": fallback_recommendations[:3]}


def check_product_availability(
    product_id: str, store_id: str = "GR-ONLINE", quantity: int = 1
) -> dict:
    """Checks the availability of a product at a specified store or for online order."""
    logger.info(
        f"Checking availability for product ID: {product_id}, quantity: {quantity} at store/channel: {store_id}"
    )
    # MOCK API RESPONSE - Include products from example.py
    available = False
    stock_quantity = 0
    location = store_id

    # Example Product Availability
    if product_id == "GOOGLE-PIXEL9PRO-CASE" or "otterbox" in product_id.lower():
        available = True
        stock_quantity = random.randint(5, 25)
        location = "GR-ONLINE/ GR-BERLIN"  # Assume online primarily
    elif "zagg" in product_id.lower() or product_id == "ZAGG-IS-PIXEL9PRO":
        available = True
        stock_quantity = random.randint(10, 40)
        location = "GR-ONLINE"
    elif product_id == "PLUSGARANTIE-PIXEL":  # Service/Digital product
        available = True
        stock_quantity = 999  # Essentially unlimited
        location = "GR-ONLINE / In Store"
    elif product_id == "GOOGLE-30W-POWERADAPTER":
        available = True
        stock_quantity = random.randint(15, 60)
        location = "GR-ONLINE / GR-BERLIN"  # Available both
    elif product_id == "PIXEL-6-128GB-BLK":
        # Simulate varying stock
        available = random.choice([True, True, False])
        stock_quantity = random.randint(0, 10) if available else 0
        location = "GR-ONLINE / GR-BERLIN"
    elif product_id == "GENERIC-PIXEL-CASE":
        available = True
        stock_quantity = random.randint(20, 100)
        location = "GR-ONLINE / GR-BERLIN"
    # Keep existing logic for other products
    elif product_id == "APPLE-IPAD-AIR-M1-64GB":
        if store_id == "GR-BERLIN" or store_id == "GR-ONLINE":
            available = True
            stock_quantity = random.randint(5, 20)
        else:
            available = False
            stock_quantity = 0
    elif product_id == "LOGI-MX-MASTER3S":
        available = True
        stock_quantity = random.randint(10, 50)
        location = "GR-ONLINE"
    else:  # Default for unlisted products
        available = random.choice([True, False])
        stock_quantity = random.randint(0, 15) if available else 0
        location = store_id if store_id else "GR-ONLINE"

    final_availability = available and stock_quantity >= quantity
    return {
        "product_id": product_id,
        "requested_quantity": quantity,
        "available": final_availability,
        "available_quantity": stock_quantity,
        "location": location,
    }


def schedule_service_appointment(
    customer_id: str,
    service_type: str,
    date: str,
    time_slot: str,
    store_id: str = "GR-BERLIN",
    product_id: Optional[str] = None,
    issue_description: Optional[str] = None,
) -> dict:
    """Schedules a service appointment (e.g., repair drop-off, consultation)."""
    logger.info(
        f"Scheduling {service_type} for customer {customer_id} at {store_id} on {date} at {time_slot}."
    )
    if product_id:
        logger.info(f"Related Product: {product_id}")
    if issue_description:
        logger.info(f"Details: {issue_description}")

    # MOCK API RESPONSE - Replace with actual scheduling system API call
    appointment_id = f"APP-{random.randint(10000, 99999)}"
    # Extract start time for confirmation string, handle different formats
    try:
        start_time = time_slot.split("-")[0].strip()
        confirmation_datetime_str = f"{date} {start_time}:00"
    except (AttributeError, IndexError):
        # Fallback if format is unexpected
        confirmation_datetime_str = f"{date} {time_slot}"

    return {
        "status": "success",
        "appointment_id": appointment_id,
        "service_type": service_type,
        "date": date,
        "time": time_slot,
        "confirmation_datetime": confirmation_datetime_str,
        "store_id": store_id,
    }


def get_available_service_times(
    date: str,
    service_type: str,
    store_id: str = "GR-BERLIN",
    duration_minutes: int = 60,
) -> list:
    """Retrieves available time slots for a specific service type and date."""
    # Note: duration_minutes parameter added to match prompt, but not used in
    # mock logic yet.
    logger.info(
        f"Retrieving available {service_type} times for {date} at {store_id} (duration: {duration_minutes} mins)"
    )
    # MOCK API RESPONSE - Replace with actual scheduling system API call
    if date >= datetime.now().strftime("%Y-%m-%d"):
        return ["09:00-10:00", "10:00-11:00", "14:00-15:00", "16:00-17:00"]
    else:
        return []


def send_product_information(
    customer_id: str,
    product_id: str,
    info_type: str = "manual",
    delivery_method: str = "email",
) -> dict:
    """Sends product information (e.g., manual, warranty details, order summary) to the customer."""
    logger.info(
        f"Sending {info_type} for product {product_id} to customer: {customer_id} via {delivery_method}"
    )
    # MOCK API RESPONSE - Replace with actual document/email sending logic
    if info_type == "order summary and pickup details":
        message = f"Order summary and pickup details for order related to {product_id} sent via {delivery_method}."
    else:
        message = f"Product information ({info_type}) for {product_id} sent via {delivery_method}."

    return {"status": "success", "message": message}


def generate_qr_code(
    customer_id: str,
    discount_value: float,
    discount_type: str = "percentage",
    expiration_days: int = 30,
    usage_limit: int = 1,
    description: str = "Loyalty Discount",
) -> dict:
    """Generates a QR code for a discount or offer."""
    logger.info(
        f"Generating QR code for customer: {customer_id} - {discount_value}{'%' if discount_type == 'percentage' else 'EUR'} discount. Desc: {description}"
    )
    # MOCK API RESPONSE - Match example.py output format
    expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime(
        "%Y-%m-%d"
    )
    # Construct payload similar to example
    qr_code_payload = f"MOCK_QR_CODE_FOR_CUSTOMER:{customer_id};DISCOUNT:{discount_value};TYPE:{discount_type};EXP:{expiration_date};DESC:{description.replace(' ', '_')};LIMIT:{usage_limit}"

    return {
        "status": "success",
        "qr_code_data": qr_code_payload,
        "description": description,
        "expiration_date": expiration_date,
        "usage_limit": usage_limit,
    }


def process_exchange_request(
    customer_id: str,
    original_order_id: str,
    original_product_id: str,
    reason: str,
    desired_product_id: Optional[str] = None,
) -> dict:
    """Processes an exchange request for a product."""
    # Made desired_product_id Optional to match prompt
    logger.info(
        f"Processing exchange for customer {customer_id}, order {original_order_id}, product {original_product_id}. Reason: {reason}. New Product: {desired_product_id}"
    )
    # Mock exchange processing - Replace with actual order management/RMA
    # system API call
    exchange_id = f"EXCH-{random.randint(1000, 9999)}"
    # More likely to meet policy for mock
    policy_met = random.choice([True, False, True])

    if policy_met:
        price_difference = 0
        if desired_product_id:
            # Simulate getting prices - replace with actual lookup
            original_price = random.uniform(50, 1000)
            new_price = random.uniform(50, 1000)
            price_difference = new_price - original_price

        message = f"Exchange approved (ID: {exchange_id}). Please return the original item '{original_product_id}'. "
        if desired_product_id:
            if price_difference > 0.01:
                message += f"An additional payment of {price_difference:.2f} EUR is required for '{desired_product_id}'."
            elif price_difference < -0.01:
                message += f"A refund of {-price_difference:.2f} EUR will be issued upon return of the original item."
            else:
                message += f"There is no price difference for '{desired_product_id}'."
        else:
            message += "A refund or store credit will be processed upon return."

        return {
            "status": "approved",
            "exchange_id": exchange_id,
            "message": message,
            "return_instructions": "Please bring the original product with packaging and receipt to your nearest store or use the provided shipping label (if applicable).",
            "price_difference": round(price_difference, 2),
        }
    else:
        return {
            "status": "rejected",
            "exchange_id": None,
            "message": "Exchange request could not be approved based on the return policy (e.g., outside return window, condition issues, non-exchangeable item).",
            "price_difference": None,
        }


def get_trade_in_value(
    product_category: str,
    brand: str,
    model: str,
    condition: str,
    storage: Optional[str] = None,
) -> dict:
    """
    Provides an estimated trade-in value for a used device.

    Args:
        product_category: The category of the product (e.g., "phone", "tablet").
        brand: The brand of the device (e.g., "Apple", "Google", "Samsung").
        model: The model of the device (e.g., "iPhone 12", "Pixel 5", "Galaxy Tab S7").
        condition: The condition of the device (e.g., "like new", "good", "fair", "damaged").
        storage: (Optional) The storage capacity of the device (e.g., "128GB", "256GB").

    Returns:
        A dictionary with the estimated trade-in value and related information.
    """
    logger.info(
        f"Calculating trade-in value for: Category='{product_category}', Brand='{brand}', Model='{model}', Condition='{condition}', Storage='{storage}'"
    )

    # --- MOCK TRADE-IN VALUE LOGIC ---
    # In a real application, this would query a database or a third-party API.
    # For this example, we'll use some basic mock logic.

    base_value = 0
    currency = "EUR"
    message = ""

    # Example base values (very simplified)
    if brand.lower() == "apple":
        if "iphone 12" in model.lower():
            base_value = 200
            if "128gb" in str(storage).lower():
                base_value += 20
            elif "256gb" in str(storage).lower():
                base_value += 40
        elif "iphone 11" in model.lower():
            base_value = 150
        elif "ipad air" in model.lower():
            base_value = 250
    elif brand.lower() == "google":
        if "pixel 5" in model.lower():
            base_value = 50
        elif "pixel 6" in model.lower():
            base_value = 60
            if "128gb" in str(storage).lower():
                base_value += 20
            elif "256gb" in str(storage).lower():
                base_value += 40
        elif "pixel 7" in model.lower():
            base_value = 80
        elif "pixel tablet" in model.lower():  # Example for tablet
            base_value = 150
    elif brand.lower() == "samsung":
        if "galaxy s21" in model.lower():
            base_value = 190
        elif "galaxy tab s7" in model.lower():
            base_value = 220

    if not base_value:
        return {
            "status": "error",
            "message": "Could not determine a base trade-in value for the specified device. It might not be eligible or recognized.",
            "estimated_value_min": 0,
            "estimated_value_max": 0,
            "currency": currency,
        }

    # Adjust value based on condition
    condition_multiplier = 1.0
    if condition.lower() == "like new":
        condition_multiplier = 1.0
    elif condition.lower() == "good":
        condition_multiplier = 0.8
    elif condition.lower() == "fair":
        condition_multiplier = 0.6
    elif condition.lower() == "damaged":  # e.g., cracked screen but functional
        condition_multiplier = 0.3
    else:  # unknown condition
        condition_multiplier = 0.5

    estimated_value = base_value * condition_multiplier

    # Provide a range
    estimated_value_min = max(0, estimated_value * 0.85)  # e.g., 85% of estimate
    estimated_value_max = estimated_value * 1.10  # e.g., 110% of estimate

    # Round to sensible values
    estimated_value_min = round(estimated_value_min / 5) * 5  # Round to nearest 5 EUR
    estimated_value_max = round(estimated_value_max / 5) * 5

    if estimated_value_max > 0:
        status = "success"
        message = f"Trade-in value estimated between {estimated_value_min:.2f} and {estimated_value_max:.2f} {currency}. Final value depends on inspection."
    else:
        status = "success"  # Still a success in terms of processing, but value is zero
        message = "The device is eligible for trade-in, but the estimated value is currently 0 EUR based on the provided details."
        estimated_value_min = 0
        estimated_value_max = 0

    return {
        "status": status,
        "estimated_value_min": estimated_value_min,
        "estimated_value_max": estimated_value_max,
        "currency": currency,
        "message": message,
        "details_provided": {
            "category": product_category,
            "brand": brand,
            "model": model,
            "condition": condition,
            "storage": storage,
        },
    }


def lookup_warranty_details(product_id: str) -> dict:
    """
    Looks up warranty details for a given product ID.

    Args:
        product_id: The ID of the product to look up warranty details for (e.g. Pixel 9 Pro, Pixel 9, etc.).

    Returns:
        A dictionary with the estimated trade-in value and related information.
    """

    if "pixel" in product_id.lower() and "plusgarantie" not in product_id.lower():
        logger.info(f"Lookup warranty details for Pixel device: {product_id}")
        return {
            "status": "success",
            "warranty_details": {
                "warranty_type": "standard",
                "warranty_period": "1 year",
                "coverage_summary": "Covers manufacturing defects for one year from purchase date. Does not cover accidental damage like drops or spills.",
            },
            "premium_warranty_details": {
                "warranty_type": "premium",
                "product_id": "PLUSGARANTIE-PIXEL",
                "information": "leverage product id 'PLUSGARANTIE-PIXEL' to retrieve premium warranty details",
            },
        }

    elif "plusgarantie" in product_id.lower() and "pixel" in product_id.lower():
        logger.info(
            f"Lookup warranty details for PlusGarantie Pixel device: {product_id}"
        )
        return {
            "status": "success",
            "warranty_details": {
                "warranty_type": "premium",
                "warranty_period": "1 year",
                "coverage_summary": "Covers accidental damage like drops or spills for one year from purchase date.",
            },
        }
    else:
        logger.info(f"Lookup warranty details for default device: {product_id}")
        return {
            "status": "success",
            "warranty_details": {
                "warranty_type": "standard",
                "warranty_period": "1 year",
                "coverage_summary": "Covers manufacturing defects for one year from purchase date. Does not cover accidental damage like drops or spills.",
            },
        }


def create_style_moodboard(
    customer_id: str,
    style_preferences: List[str],
    room_type: Optional[str] = None,
    color_preferences: Optional[List[str]] = None,
    age_context: Optional[str] = None,
    room_purpose: Optional[str] = None,
    constraints: Optional[Dict[str, List[str]]] = None,
) -> dict:
    """
    Creates a curated style moodboard with product recommendations based on user preferences.

    Args:
        customer_id: The ID of the customer.
        style_preferences: List of preferred decor styles (e.g., ["modern", "minimalist", "bohemian"]).
        room_type: Optional room type (e.g., "living room", "bedroom", "office").
        color_preferences: Optional list of preferred colors (e.g., ["blue", "white", "gold"]).
        age_context: Optional age context (e.g., "toddler", "school-age", "teen", "adult").
        room_purpose: Optional room purpose ("decoration" or "redesign").
        constraints: Optional constraints (items to keep/remove).

    Returns:
        A dictionary with moodboard details and recommended products.
    """
    logger.info(
        f"Creating style moodboard for customer {customer_id} with styles: {style_preferences}, room: {room_type}, colors: {color_preferences}, age: {age_context}, purpose: {room_purpose}"
    )

    # Available style categories with descriptions
    STYLE_CATALOG = {
        "modern": {
            "description": "Clean lines, minimal ornamentation, neutral colors with bold accents",
            "keywords": ["modern", "contemporary", "sleek"],
        },
        "minimalist": {
            "description": "Simplicity, functionality, monochromatic palette, less is more",
            "keywords": ["minimalist", "simple", "clean"],
        },
        "bohemian": {
            "description": "Eclectic mix, rich colors, patterns, global influences, relaxed vibe",
            "keywords": ["bohemian", "boho", "eclectic"],
        },
        "coastal": {
            "description": "Light and airy, nautical themes, blues and whites, natural textures",
            "keywords": ["coastal", "beach", "nautical"],
        },
        "industrial": {
            "description": "Exposed materials, metal accents, reclaimed wood, urban loft aesthetic",
            "keywords": ["industrial", "urban", "loft"],
        },
        "scandinavian": {
            "description": "Functionality, natural materials, light woods, hygge coziness",
            "keywords": ["scandinavian", "nordic", "hygge"],
        },
        "traditional": {
            "description": "Classic elegance, rich woods, ornate details, timeless pieces",
            "keywords": ["traditional", "classic", "elegant"],
        },
        "rustic": {
            "description": "Natural materials, warm tones, handcrafted feel, country charm",
            "keywords": ["rustic", "farmhouse", "country"],
        },
        # Child-themed styles -- mapped to product style_tags for scoring
        "underwater_world": {
            "description": "Soft blues, ocean vibes, dolphins, shells, aqua palette",
            "keywords": ["underwater", "ocean", "dolphins", "coastal", "nautical"],
        },
        "forest_adventure": {
            "description": "Warm greens and browns, woodland creatures, natural wood",
            "keywords": ["forest", "woodland", "rustic", "natural"],
        },
        "northern_lights": {
            "description": "Cool pastels, aurora colours, dreamy ethereal atmosphere",
            "keywords": [
                "northern lights",
                "aurora",
                "pastel",
                "scandinavian",
                "modern",
            ],
        },
        "space_explorer": {
            "description": "Deep navy and silver, planets, rockets, modern clean lines",
            "keywords": ["space", "modern", "industrial"],
        },
        "safari_wild": {
            "description": "Earthy tones, jungle animals, natural materials, adventure",
            "keywords": ["safari", "jungle", "bohemian", "rustic", "natural"],
        },
        "rainbow_bright": {
            "description": "Bold primary colours, playful, cheerful, modern clean design",
            "keywords": ["rainbow", "modern", "bohemian"],
        },
    }

    # Normalize style preferences to match catalog
    matched_styles = []
    for pref in style_preferences:
        pref_lower = pref.lower()
        for style, data in STYLE_CATALOG.items():
            if pref_lower in data["keywords"] or pref_lower in style:
                if style not in matched_styles:
                    matched_styles.append(style)

    # Fallback if no matches
    if not matched_styles:
        matched_styles = ["modern", "minimalist"]
        logger.warning(f"No matching styles found, using default: {matched_styles}")

    # Determine if this is a full room redesign (includes furniture) or just decoration
    include_furniture = room_purpose == "redesign" or (
        room_type and room_type.lower() == "bedroom" and age_context
    )

    # NEW APPROACH: Multi-tier filtering with intelligent expansion
    # Tier 1: Strict matching (style + color + room)
    # Tier 2: Style + color (if not enough products)
    # Tier 3: Color-coordinated with complementary styles (if still not enough)

    # Start with all relevant products (Home Decor + Furniture for redesigns)
    all_relevant_products = []
    for product in RetailContext.PRODUCT_CATALOG:
        if product.get("category") == "Home Decor" or (
            include_furniture and product.get("category") == "Furniture"
        ):
            # Filter by age_appropriate if age_context is provided
            if age_context and product.get("category") == "Furniture":
                age_tags = product.get("age_appropriate", [])
                if age_context in age_tags or not age_tags:
                    all_relevant_products.append(product)
            else:
                all_relevant_products.append(product)

    # Normalize color preferences for matching
    normalized_color_prefs = (
        [c.lower() for c in color_preferences] if color_preferences else []
    )

    # Color family mapping for fuzzy color matching
    _COLOR_FAMILIES = {
        "blue": [
            "blue",
            "navy",
            "sky blue",
            "ocean",
            "cobalt",
            "teal",
            "aqua",
            "cerulean",
            "indigo",
            "azure",
            "sapphire",
            "denim",
            "marine",
        ],
        "white": [
            "white",
            "ivory",
            "cream",
            "off-white",
            "snow",
            "pearl",
            "alabaster",
            "chalk",
            "linen",
        ],
        "green": [
            "green",
            "sage",
            "olive",
            "emerald",
            "forest",
            "mint",
            "lime",
            "moss",
            "jade",
            "fern",
            "eucalyptus",
        ],
        "pink": [
            "pink",
            "blush",
            "rose",
            "coral",
            "salmon",
            "magenta",
            "fuchsia",
            "dusty pink",
            "mauve",
        ],
        "red": [
            "red",
            "crimson",
            "burgundy",
            "maroon",
            "ruby",
            "scarlet",
            "wine",
            "cherry",
        ],
        "yellow": [
            "yellow",
            "gold",
            "mustard",
            "amber",
            "honey",
            "lemon",
            "ochre",
            "saffron",
        ],
        "orange": [
            "orange",
            "terracotta",
            "rust",
            "tangerine",
            "peach",
            "apricot",
            "copper",
        ],
        "brown": [
            "brown",
            "walnut",
            "chocolate",
            "tan",
            "caramel",
            "mocha",
            "chestnut",
            "espresso",
            "wood",
            "timber",
            "oak",
            "birch",
        ],
        "grey": [
            "grey",
            "gray",
            "charcoal",
            "silver",
            "slate",
            "ash",
            "graphite",
            "pewter",
            "stone",
        ],
        "black": ["black", "ebony", "onyx", "jet", "midnight"],
        "beige": [
            "beige",
            "sand",
            "taupe",
            "khaki",
            "camel",
            "nude",
            "natural",
            "wheat",
            "oat",
        ],
        "purple": [
            "purple",
            "violet",
            "lavender",
            "plum",
            "lilac",
            "amethyst",
            "mauve",
            "aubergine",
        ],
    }

    def _color_matches(pref_color, product_color):
        """Check if two colours belong to the same colour family."""
        if pref_color in product_color or product_color in pref_color:
            return True
        for family_members in _COLOR_FAMILIES.values():
            if pref_color in family_members and product_color in family_members:
                return True
        return False

    # Score each product based on how well it matches preferences
    product_scores = {}
    for product in all_relevant_products:
        score = 0
        product_id = product["product_id"]
        product_styles = [s.lower() for s in product.get("style_tags", [])]
        product_colors = [c.lower() for c in product.get("color_palette", [])]
        product_rooms = [r.lower() for r in product.get("room_compatibility", [])]

        # Style match: +10 points per matching style
        style_matches = sum(1 for style in matched_styles if style in product_styles)
        score += style_matches * 10

        # Color match: +15 points per matching color (fuzzy family matching)
        if normalized_color_prefs:
            color_matches = sum(
                1
                for pref in normalized_color_prefs
                for pc in product_colors
                if _color_matches(pref, pc)
            )
            score += color_matches * 15

        # Room match: +5 points if room compatible
        if room_type and room_type.lower() in product_rooms:
            score += 5

        if score > 0:  # Only include products with at least some match
            product_scores[product_id] = score

    # Sort products by score (highest first)
    matching_products = sorted(
        [p for p in all_relevant_products if p["product_id"] in product_scores],
        key=lambda p: product_scores[p["product_id"]],
        reverse=True,
    )

    logger.info(
        f"[MOODBOARD] Scored {len(matching_products)} products. "
        f"Top scores: {[(p['name'], product_scores[p['product_id']]) for p in matching_products[:3]]}"
    )

    # Determine product count based on room purpose
    # For redesigns, show more products (furniture + decor)
    # For decoration only, show fewer products (just decor)
    product_count = 10 if include_furniture else 6

    # Separate furniture and decor products for better curation
    if include_furniture:
        furniture_products = [
            p for p in matching_products if p.get("category") == "Furniture"
        ]
        decor_products = [
            p for p in matching_products if p.get("category") == "Home Decor"
        ]

        # Keep score ordering -- highest scored products first
        # For redesigns: prioritize furniture, then add decor
        # Aim for 40% furniture, 60% decor
        furniture_count = min(4, len(furniture_products))
        decor_count = min(product_count - furniture_count, len(decor_products))

        moodboard_products = (
            furniture_products[:furniture_count] + decor_products[:decor_count]
        )
    else:
        moodboard_products = matching_products[:product_count]

    # Build moodboard response with images directly from catalog
    logger.info(f"Building moodboard with {len(moodboard_products)} products...")
    product_recommendations = []
    for product in moodboard_products:
        product_id = product["product_id"]
        # Use the image_url directly from the product catalog
        image_url = product.get("image_url", f"{_ASSETS}/placeholder_home_decor.jpg")

        logger.info(f"[MOODBOARD] Product {product_id} using image: {image_url}")

        product_recommendations.append(
            {
                "product_id": product_id,
                "name": product["name"],
                "category": product.get("subcategory", product["category"]),
                "price": product["price"],
                "style_tags": product.get("style_tags", []),
                "color_palette": product.get("color_palette", []),
                "image_url": image_url,
            }
        )

    # Create style description for the moodboard
    style_descriptions = [
        STYLE_CATALOG.get(s, {}).get("description", s) for s in matched_styles
    ]

    moodboard_summary = {
        "status": "success",
        "customer_id": customer_id,
        "moodboard_id": f"MOOD-{random.randint(10000, 99999)}",
        "selected_styles": matched_styles,
        "style_descriptions": style_descriptions,
        "room_type": room_type,
        "color_palette": (
            color_preferences if color_preferences else "open to all colors"
        ),
        "product_count": len(product_recommendations),
        "products": product_recommendations,
        "message": f"Created a {', '.join(matched_styles)} style moodboard with {len(product_recommendations)} curated products{f' for your {room_type}' if room_type else ''}.",
    }

    logger.info(f"Moodboard created with {len(product_recommendations)} products")
    return moodboard_summary


def display_product_search_results(
    customer_id: str,
    category: Optional[str] = None,
    search_term: Optional[str] = None,
    max_results: int = 6,
) -> dict:
    """
    Displays product search results as visual cards with images.
    Works for any product category (Laptops, Smartphones, TVs, etc.).

    This tool enables the agent to show products from ANY category (not just Home Decor)
    as visual product cards with images, similar to the moodboard display.

    Args:
        customer_id: The ID of the customer.
        category: Optional category filter (e.g., "Laptops", "Smartphones", "TVs").
        search_term: Optional search term for product name/description.
        max_results: Maximum number of products to return (default 6).

    Returns:
        Dictionary with ui_data for rendering product cards with images.
    """
    logger.info(
        f"[PRODUCT SEARCH] Displaying products for customer {customer_id} - category: {category}, search: {search_term}, max: {max_results}"
    )

    matching_products = []

    # Filter products by category and/or search term
    for product in RetailContext.PRODUCT_CATALOG:
        # Check if product is in stock
        if not product.get("in_stock", True):
            continue

        # Category filter
        if category:
            if product.get("category", "").lower() != category.lower():
                continue

        # Search term filter (matches name or category)
        if search_term:
            search_lower = search_term.lower()
            name_match = search_lower in product.get("name", "").lower()
            category_match = search_lower in product.get("category", "").lower()

            if not (name_match or category_match):
                continue

        matching_products.append(product)

    # If we have too many results, select the most relevant ones
    if len(matching_products) > max_results:
        # Shuffle to provide variety, then limit
        random.shuffle(matching_products)
        selected_products = matching_products[:max_results]
    else:
        selected_products = matching_products

    logger.info(
        f"[PRODUCT SEARCH] Building product list for {len(selected_products)} products..."
    )

    # Build product list with images directly from catalog
    # All products in catalog have image_url field, so we use those directly
    product_list = []
    for product in selected_products:
        product_id = product["product_id"]
        # Use the image_url directly from the product catalog
        image_url = product.get("image_url", f"{_ASSETS}/placeholder_product.jpg")

        logger.info(f"[PRODUCT SEARCH] Product {product_id} using image: {image_url}")

        product_list.append(
            {
                "product_id": product_id,
                "name": product["name"],
                "category": product.get("category"),
                "price": product["price"],
                "image_url": image_url,
            }
        )

    # Create search result ID
    search_id = f"SEARCH-{random.randint(10000, 99999)}"

    # Build response with ui_data for moodboard-style rendering
    search_results = {
        "status": "success",
        "customer_id": customer_id,
        "search_id": search_id,
        "category_filter": category,
        "search_term": search_term,
        "product_count": len(product_list),
        "products": product_list,
        "message": f"Found {len(product_list)} {category if category else 'products'}"
        + (f" matching '{search_term}'" if search_term else ""),
        "ui_data": {
            "display_type": "moodboard",
            "moodboard_id": search_id,
            "products": product_list,
            "product_count": len(product_list),
            "message": f"Here are {len(product_list)} {category if category else 'products'} I found for you"
            + (f" matching '{search_term}'" if search_term else ""),
        },
    }

    logger.info(f"[PRODUCT SEARCH] Returning {len(product_list)} products for display")
    return search_results


_STYLE_PROMPTS = {
    # Adult styles
    "modern": "Transform this room into a stunning modern interior: repaint walls crisp white, replace all furniture with sleek low-profile pieces in black and grey, add geometric pendant lights, a bold abstract canvas on the wall, and a clean monochrome rug.",
    "minimalist": "Transform this room into a serene minimalist space: repaint walls pure white, remove clutter, replace furniture with simple white and pale wood pieces, add one statement floor lamp, bare surfaces, and a single potted plant.",
    "bohemian": "Transform this room into a vibrant bohemian retreat: add a colourful woven tapestry on the wall, layer multiple patterned rugs and kilim cushions, hang macrame plant holders with trailing greenery, drape fairy lights, and fill with jewel-toned textiles in orange, magenta and teal.",
    "coastal": "Transform this room into a breezy coastal retreat: repaint walls soft sky blue, add white-washed wood furniture, hang rope-framed mirrors, place a jute rug, add coral and shell decorations, blue striped cushions, and driftwood accents.",
    "industrial": "Transform this room into an urban industrial loft: add exposed brick accent wall, replace furniture with raw metal and dark wood pieces, hang Edison bulb pendant lights, add a distressed leather chair, metal shelving, and concrete-effect accessories.",
    "scandinavian": "Transform this room into a cosy Scandinavian haven: repaint walls warm white, add light birch wood furniture, layer sheepskin throws and knitted cushions, place a round jute rug, add minimalist wooden shelves, and soft warm lighting.",
    "traditional": "Transform this room into a classic traditional space: add rich dark wood furniture with ornate details, hang elegant curtains with tassels, place a Persian-style rug, add table lamps with fabric shades, framed paintings, and symmetrical arrangement.",
    "rustic": "Transform this room into a warm rustic retreat: add reclaimed wood accent wall, replace furniture with chunky timber pieces, place a cowhide rug, add antler or wrought-iron chandelier, woven baskets, and warm flannel textiles in red and brown.",
    # Child themes
    "underwater_world": "Dramatically transform this children's bedroom into an underwater ocean paradise: repaint walls deep ocean blue with painted coral reefs and seaweed, add dolphin and sea turtle wall decals, replace bedding with ocean-blue duvet covered in fish patterns, hang a jellyfish lamp from the ceiling, add a treasure chest toy box, and scatter shell-shaped cushions.",
    "forest_adventure": "Dramatically transform this children's bedroom into an enchanted forest: repaint walls deep green with painted trees and woodland murals, add a tree-trunk bookshelf, fox and deer wall decals, mushroom-shaped night lights, leaf-patterned green bedding, a woodland animal rug, and hanging bird houses as shelves.",
    "northern_lights": "Dramatically transform this children's bedroom into a magical aurora night sky: repaint ceiling with swirling purple, teal, and green northern lights, add glowing star decals across dark navy walls, replace bedding with galaxy-print purple and teal duvet, hang a crescent moon lamp, add cloud-shaped shelves, and iridescent curtains.",
    "space_explorer": "Dramatically transform this children's bedroom into a space station: repaint walls dark navy blue with painted planets, stars, and constellations, add a rocket ship bookshelf, astronaut wall decals, planet mobile hanging from ceiling, silver metallic bedding with rocket patterns, and a glowing Earth night light.",
    "safari_wild": "Dramatically transform this children's bedroom into a safari jungle camp: repaint walls warm sandy beige with painted savanna landscape and acacia trees, add large giraffe and elephant wall decals, a bamboo canopy over the bed, leopard-print cushions, a jungle green rug, woven grass baskets, and a wooden safari jeep toy shelf.",
    "rainbow_bright": "Dramatically transform this children's bedroom into a bold rainbow wonderland: repaint each wall a different bright primary colour (red, yellow, blue, green), add rainbow arch wall mural, replace bedding with vivid multicoloured rainbow stripes, hang colourful bunting, add a bright yellow bookshelf, and scatter cushions in every colour of the rainbow.",
}


@imagen_retry
def _generate_single_style_preview(
    room_photo_b64: str,
    style_entry: dict,
    room_type: str,
) -> dict:
    """Generate a single style preview image by restyling the uploaded room photo.

    Called from the websocket handler in a background thread.
    Returns the style dict with an updated ``image_url`` (base64 data-URI)
    or the original dict unchanged on failure.
    """
    import base64

    style_id = style_entry["id"]
    prompt = _STYLE_PROMPTS.get(style_id)
    if not prompt:
        logger.warning(
            f"[STYLE PREVIEW] No prompt for style '{style_id}', keeping static image"
        )
        return style_entry

    try:
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client()
        photo_bytes = base64.b64decode(room_photo_b64)
        reference_image = genai_types.RawReferenceImage(
            reference_id=1,
            reference_image=genai_types.Image(image_bytes=photo_bytes),
        )

        edit_prompt = (
            f"{prompt} "
            f"Keep the same room shape, window positions, and camera angle. "
            f"The style transformation must be clearly visible and dramatic. "
            f"Photorealistic interior design photograph, 4K quality, "
            f"natural lighting, editorial magazine style."
        )

        image_response = client.models.edit_image(
            model="imagen-3.0-capability-001",
            prompt=edit_prompt,
            reference_images=[reference_image],
            config=genai_types.EditImageConfig(
                number_of_images=1,
                safety_filter_level="block_some",
                person_generation="dont_allow",
            ),
        )

        if image_response and image_response.generated_images:
            img_bytes = image_response.generated_images[0].image.image_bytes
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            logger.info(
                f"[STYLE PREVIEW] Generated preview for '{style_id}' ({len(img_bytes)} bytes)"
            )
            result = dict(style_entry)
            result["image_url"] = f"data:image/png;base64,{img_b64}"
            return result
        else:
            logger.warning(
                f"[STYLE PREVIEW] No image returned for '{style_id}', keeping static image"
            )
            return style_entry

    except Exception as e:
        logger.error(
            f"[STYLE PREVIEW] Failed to generate preview for '{style_id}': {e}"
        )
        return style_entry


def start_home_decor_consultation(
    customer_id: str,
    initial_request: Optional[str] = None,
) -> dict:
    """
    Starts a structured home decor consultation session. This is the entry point for home decor conversations.

    Args:
        customer_id: The ID of the customer.
        initial_request: Optional initial request from the customer (e.g., "I want to decorate my living room").

    Returns:
        A dictionary with the consultation session details and next steps.
    """
    logger.info(f"[HOME DECOR] Starting consultation for customer {customer_id}")
    logger.info(f"[HOME DECOR] Initial request: {initial_request}")

    state_manager = get_state_manager()

    # If the user is making a fresh request (initial_request provided),
    # always start a new session to avoid resuming stale state.
    existing_session = state_manager.get_customer_session(customer_id)
    if existing_session:
        old_id = existing_session["session_id"]
        logger.info(f"[HOME DECOR] Clearing previous session {old_id} to start fresh")
        state_manager.mark_moodboard_generated(old_id)

    # Create new session
    session_id = f"DECOR-CONSULT-{random.randint(10000, 99999)}"
    state_manager.create_session(customer_id, session_id)
    logger.info(f"[HOME DECOR] Created new session {session_id}")

    # Always show the room selector UI so the customer can confirm their choice
    # Define the consultation stages
    consultation_flow = {
        "stage_1_room_identification": {
            "question": "Which room would you like to decorate?",
            "options": [
                "living room",
                "bedroom",
                "office",
                "dining room",
                "kitchen",
                "bathroom",
                "entryway",
            ],
            "completed": False,
        },
        "stage_2_style_discovery": {
            "question": "What decor style resonates with you?",
            "options": [
                "modern",
                "minimalist",
                "bohemian",
                "coastal",
                "industrial",
                "scandinavian",
                "traditional",
                "rustic",
            ],
            "allow_multiple": True,
            "completed": False,
        },
        "stage_3_color_preferences": {
            "question": "Are there specific colors you'd like to incorporate?",
            "examples": [
                "blue and white",
                "warm earth tones",
                "black and gold",
                "neutral palette",
            ],
            "optional": True,
            "completed": False,
        },
        "stage_4_generate_moodboard": {
            "action": "create_style_moodboard",
            "description": "Generate personalized moodboard with curated products",
            "completed": False,
        },
    }

    # Build UI data for Phase 1 room selection
    room_options_ui = [
        {"id": "living_room", "label": "Living Room", "icon": "🛋️"},
        {"id": "bedroom", "label": "Bedroom", "icon": "🛏️"},
        {"id": "office", "label": "Office", "icon": "💼"},
        {"id": "dining_room", "label": "Dining Room", "icon": "🍽️"},
        {"id": "kitchen", "label": "Kitchen", "icon": "🍳"},
        {"id": "bathroom", "label": "Bathroom", "icon": "🚿"},
        {"id": "entryway", "label": "Entryway", "icon": "🚪"},
    ]

    result = {
        "status": "consultation_started",
        "session_id": session_id,
        "customer_id": customer_id,
        "current_stage": "stage_1_room_identification",
        "consultation_flow": consultation_flow,
        "message": "Home decor consultation started! Let's find the perfect pieces for your space.",
        "next_question": consultation_flow["stage_1_room_identification"]["question"],
        "options": consultation_flow["stage_1_room_identification"]["options"],
        "instructions": "Ask the customer to choose from the provided room options, or let them specify their own.",
        # NEW: UI display data for Phase 1
        "ui_data": {
            "display_type": "room_selector",
            "title": "Which room would you like to decorate?",
            "subtitle": "Select the space you'd like to transform",
            "room_options": room_options_ui,
            "interaction_mode": "single_select",
            "phase": "phase_1_initial_interest",
        },
    }

    logger.info(
        f"[HOME DECOR] Consultation started successfully. Session ID: {session_id}"
    )
    return result


def continue_home_decor_consultation(
    customer_id: str,
    session_id: Optional[str] = None,
    room_type: Optional[str] = None,
    room_purpose: Optional[str] = None,
    age_context: Optional[str] = None,
    constraints: Optional[Dict[str, List[str]]] = None,
    style_preferences: Optional[List[str]] = None,
    color_preferences: Optional[List[str]] = None,
    room_dimensions: Optional[Dict[str, float]] = None,
) -> dict:
    """
    Continues the home decor consultation with customer responses.

    Args:
        customer_id: The ID of the customer.
        session_id: The consultation session ID (optional - will be retrieved if not provided).
        room_type: The room type specified by customer.
        room_purpose: Optional room purpose ("decoration" or "redesign").
        age_context: Optional age context (e.g., "toddler", "school-age", "teen", "adult").
        constraints: Optional constraints (items to keep/remove).
        style_preferences: List of style preferences.
        color_preferences: Optional list of color preferences.
        room_dimensions: Optional room dimensions {"length": float, "width": float} in meters.

    Returns:
        A dictionary with the next step in the consultation or final moodboard.
    """
    logger.info(
        f"[HOME DECOR] Continuing consultation - room: {room_type}, purpose: {room_purpose}, age: {age_context}, styles: {style_preferences}, colors: {color_preferences}, dimensions: {room_dimensions}"
    )

    state_manager = get_state_manager()

    # Get or validate session
    if not session_id:
        session = state_manager.get_customer_session(customer_id)
        if not session:
            logger.warning(
                f"[HOME DECOR] No session found for customer {customer_id}, creating new one"
            )
            return start_home_decor_consultation(customer_id)
        session_id = session["session_id"]
    else:
        session = state_manager.get_session(session_id)
        if not session:
            logger.warning(f"[HOME DECOR] Session {session_id} not found")
            return {
                "status": "error",
                "message": "Session not found. Please start a new consultation.",
            }

    # Guard: do not let the AI agent skip ahead by pre-filling style or
    # color preferences before the user has been shown the UI for them.
    session_before = state_manager.get_session(session_id)
    collected_before = session_before["collected_data"] if session_before else {}
    current_stage = session_before.get("current_stage", "") if session_before else ""

    # If the style selector UI hasn't been shown yet, ignore any styles/colors
    # the AI tries to fill in (e.g. from photo analysis).
    if style_preferences and current_stage not in ("stage_2_style_discovery",):
        if not collected_before.get("style_preferences"):
            logger.info(
                f"[HOME DECOR] Ignoring AI-provided style_preferences {style_preferences} -- style selector not yet shown (stage: {current_stage})"
            )
            style_preferences = None
    if color_preferences and current_stage not in ("stage_3_color_preferences",):
        if not collected_before.get("color_preferences"):
            logger.info(
                f"[HOME DECOR] Ignoring AI-provided color_preferences {color_preferences} -- color selector not yet shown (stage: {current_stage})"
            )
            color_preferences = None

    # Update session state with new information
    state_manager.update_session(
        session_id=session_id,
        room_type=room_type,
        room_purpose=room_purpose,
        age_context=age_context,
        constraints=constraints,
        style_preferences=style_preferences,
        color_preferences=color_preferences,
        room_dimensions=room_dimensions,
    )

    # Get current state
    session = state_manager.get_session(session_id)
    collected = session["collected_data"]

    # Validate style preferences for child rooms -- reject adult styles
    CHILD_THEME_IDS = {
        "underwater_world",
        "forest_adventure",
        "northern_lights",
        "space_explorer",
        "safari_wild",
        "rainbow_bright",
    }
    ADULT_STYLE_IDS = {
        "modern",
        "minimalist",
        "bohemian",
        "coastal",
        "industrial",
        "scandinavian",
        "traditional",
        "rustic",
    }
    age = collected.get("age_context")
    is_child_room = age in ("toddler", "school-age", "teen")

    if is_child_room and collected.get("style_preferences"):
        # If the agent passed adult style names for a child room, clear them
        # so the themed style selector is shown instead
        given_styles = set(s.lower() for s in collected["style_preferences"])
        if given_styles & ADULT_STYLE_IDS and not (given_styles & CHILD_THEME_IDS):
            logger.info(
                f"[HOME DECOR] Rejecting adult styles {given_styles} for child room -- forcing themed style selector"
            )
            collected["style_preferences"] = None
            collected["color_preferences"] = None
            # Use empty list to explicitly clear (None means "don't update")
            state_manager.update_session(
                session_id, style_preferences=[], color_preferences=[]
            )
            # Return with the themed style selector UI so the frontend renders it
            child_style_options = [
                {
                    "id": "underwater_world",
                    "label": "Underwater World",
                    "description": "Soft blues with dolphins, shells & ocean vibes",
                    "image_url": f"{_ASSETS}/theme_underwater_world.jpg",
                },
                {
                    "id": "forest_adventure",
                    "label": "Forest Adventure",
                    "description": "Warm greens & browns, woodland creatures",
                    "image_url": f"{_ASSETS}/theme_forest_adventure.jpg",
                },
                {
                    "id": "northern_lights",
                    "label": "Northern Lights",
                    "description": "Cool pastels, aurora colours & starry skies",
                    "image_url": f"{_ASSETS}/theme_northern_lights.jpg",
                },
                {
                    "id": "space_explorer",
                    "label": "Space Explorer",
                    "description": "Deep navy & silver, planets & rockets",
                    "image_url": f"{_ASSETS}/theme_space_explorer.jpg",
                },
                {
                    "id": "safari_wild",
                    "label": "Safari Wild",
                    "description": "Earthy tones, jungle animals & adventure",
                    "image_url": f"{_ASSETS}/theme_safari_wild.jpg",
                },
                {
                    "id": "rainbow_bright",
                    "label": "Rainbow Bright",
                    "description": "Bold primary colours, playful & cheerful",
                    "image_url": f"{_ASSETS}/theme_rainbow_bright.jpg",
                },
            ]
            room_photo_b64 = collected.get("room_photo_base64")

            return {
                "status": "awaiting_input",
                "session_id": session_id,
                "stage": "stage_2_style_discovery",
                "missing_info": "style_preferences",
                "message": "This is a child's room! Let them choose from the fun themed styles below.",
                "instructions": "STOP: Do NOT call this tool again with style_preferences. The UI is showing child-themed tiles. Wait for the customer to select from the UI and click Continue.",
                "options": [s["id"] for s in child_style_options],
                "ui_data": {
                    "display_type": "style_selector",
                    "title": "Style Finder: Which worlds do you love?",
                    "subtitle": "Everyone pick your favourites! Tap as many as you like.",
                    "style_options": child_style_options,
                    "interaction_mode": "multi_select",
                    "phase": "phase_1_style_discovery",
                    "generate_previews_from_photo": bool(room_photo_b64),
                    "room_photo_base64": room_photo_b64 if room_photo_b64 else None,
                    "room_type": collected["room_type"],
                },
            }

    # If we have all required information, generate the moodboard
    if (
        collected["room_type"]
        and collected["style_preferences"]
        and collected.get("room_dimensions")
    ):
        logger.info(f"[HOME DECOR] All information collected, generating moodboard...")

        # Call the moodboard creation function with all context
        moodboard_result = create_style_moodboard(
            customer_id=customer_id,
            style_preferences=collected["style_preferences"],
            room_type=collected["room_type"],
            color_preferences=collected["color_preferences"],
            age_context=collected.get("age_context"),
            room_purpose=collected.get("room_purpose"),
            constraints=collected.get("constraints"),
        )

        # Mark session as completed
        state_manager.mark_moodboard_generated(session_id)

        logger.info(
            f"[HOME DECOR] Moodboard generated successfully for session {session_id}"
        )

        # Build a slim summary for the live agent (avoid overloading the audio session context)
        product_summary = [
            {"name": p["name"], "price": p["price"], "product_id": p["product_id"]}
            for p in moodboard_result.get("products", [])
        ]

        return {
            "status": "consultation_completed",
            "session_id": session_id,
            "stage": "moodboard_presented",
            "message": f"Based on your {', '.join(collected['style_preferences'])} style preferences for your {collected['room_type']}, I've created a personalized moodboard!",
            "product_summary": product_summary,
            "product_count": len(product_summary),
            "next_action": "Present the moodboard products to the customer. Offer to explain any product choices, make adjustments to the recommendations, or add items to their cart.",
            "ui_data": {
                "display_type": "moodboard",
                "moodboard_id": moodboard_result.get("moodboard_id"),
                "products": moodboard_result.get("products", []),
                "product_count": moodboard_result.get("product_count", 0),
                "room_dimensions": collected.get("room_dimensions"),
                "room_type": collected["room_type"],
                "style_preferences": collected["style_preferences"],
                "message": f"Here are {moodboard_result.get('product_count', 0)} {', '.join(collected['style_preferences'])} products I found for your {collected['room_type']}",
                "show_visualize_button": collected.get("room_photos_analyzed", False),
            },
        }

    # Determine what information we still need
    if not collected["room_type"]:
        state_manager.update_session(session_id, stage="stage_1_room_identification")
        logger.info(f"[HOME DECOR] Awaiting room type from customer")
        room_options_ui = [
            {"id": "living_room", "label": "Living Room", "icon": ""},
            {"id": "bedroom", "label": "Bedroom", "icon": ""},
            {"id": "office", "label": "Office", "icon": ""},
            {"id": "dining_room", "label": "Dining Room", "icon": ""},
            {"id": "kitchen", "label": "Kitchen", "icon": ""},
            {"id": "bathroom", "label": "Bathroom", "icon": ""},
            {"id": "entryway", "label": "Entryway", "icon": ""},
        ]
        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_1_room_identification",
            "missing_info": "room_type",
            "question": "Which room would you like to decorate?",
            "options": [
                "living room",
                "bedroom",
                "office",
                "dining room",
                "kitchen",
                "bathroom",
                "entryway",
            ],
            "message": "Let's start by identifying which room you'd like to transform.",
            "ui_data": {
                "display_type": "room_selector",
                "title": "Which room would you like to decorate?",
                "subtitle": "Select the space you'd like to transform",
                "room_options": room_options_ui,
                "interaction_mode": "single_select",
                "phase": "phase_1_initial_interest",
            },
        }

    # Ask about room purpose (for bedrooms - decoration vs redesign)
    if collected["room_type"].lower() == "bedroom" and not collected.get(
        "room_purpose"
    ):
        state_manager.update_session(session_id, stage="stage_1a_room_purpose")
        logger.info(f"[HOME DECOR] Awaiting room purpose from customer")
        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_1a_room_purpose",
            "missing_info": "room_purpose",
            "question": "Are you looking to redecorate or completely redesign the room?",
            "options": ["decoration", "redesign"],
            "message": f"Great choice! For your {collected['room_type']}, are you looking to add decor to refresh the space, or do you need a full redesign with new furniture?",
            "instructions": "Ask if they want to just add decorative items or if they need furniture too.",
        }

    # Ask about age context (for bedrooms in redesign mode)
    if (
        collected["room_type"].lower() == "bedroom"
        and collected.get("room_purpose") == "redesign"
        and not collected.get("age_context")
    ):
        state_manager.update_session(session_id, stage="stage_1b_age_context")
        logger.info(f"[HOME DECOR] Awaiting age context from customer")
        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_1b_age_context",
            "missing_info": "age_context",
            "question": "Who will be using this bedroom?",
            "options": ["toddler", "school-age", "teen", "adult"],
            "message": "To recommend the right furniture, could you tell me who the room is for?",
            "instructions": "Ask about the age of the person who will use the room so we can recommend age-appropriate furniture.",
        }

    # Ask about constraints (for redesigns - what to keep/remove)
    if collected.get("room_purpose") == "redesign" and not collected.get("constraints"):
        state_manager.update_session(session_id, stage="stage_1c_constraints")
        logger.info(f"[HOME DECOR] Awaiting constraints from customer")
        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_1c_constraints",
            "missing_info": "constraints",
            "question": "Is there any existing furniture you'd like to keep?",
            "message": "Before we create your moodboard, let me know if there's any furniture you want to keep in the room.",
            "instructions": "Ask about existing furniture they want to keep vs remove. This helps us avoid recommending duplicates. The customer can respond conversationally (e.g., 'keep the cube shelf, everything else can go').",
            "examples": [
                "The bookshelf stays, everything else goes",
                "Keep the desk and chair",
                "Start fresh, replace everything",
                "Just the storage unit stays",
            ],
        }

    # Phase 3: Request room photos (for redesigns after constraints)
    if (
        collected.get("room_purpose") == "redesign"
        and collected.get("constraints")
        and not collected.get("room_photos_analyzed")
    ):
        state_manager.update_session(session_id, stage="stage_1d_photo_request")
        logger.info(f"[HOME DECOR] Requesting room photos from customer")
        return {
            "status": "awaiting_photos",
            "session_id": session_id,
            "stage": "stage_1d_photo_request",
            "missing_info": "room_photos",
            "question": "Could you take a few photos of the room?",
            "message": "Perfect! To create the best recommendations, I'd love to see the space. Could you take 2-3 photos showing different angles of the room?",
            "instructions": "Ask the customer to take photos showing: 1) entrance view with bed and window, 2) opposite wall with existing furniture. Use these to analyze the current room state and cross-reference with order history.",
            "ui_data": {
                "display_type": "photo_upload",
                "title": "Let's see your space!",
                "subtitle": "Take 2-3 photos of the room from different angles",
                "photo_guidelines": [
                    "Show the entrance view with the bed and window",
                    "Capture the opposite wall with existing furniture",
                    "Include any furniture you mentioned keeping",
                ],
                "interaction_mode": "camera_upload",
                "phase": "phase_3_photo_analysis",
            },
        }

    if not collected["style_preferences"]:
        state_manager.update_session(session_id, stage="stage_2_style_discovery")
        logger.info(f"[HOME DECOR] Awaiting style preferences from customer")

        age = collected.get("age_context")
        is_child_room = age in ("toddler", "school-age", "teen")

        # Check if we have an uploaded room photo to generate personalised style previews
        room_photo_b64 = collected.get("room_photo_base64")

        if is_child_room:
            # Child-themed style tiles -- fun imaginative worlds
            style_options_ui = [
                {
                    "id": "underwater_world",
                    "label": "Underwater World",
                    "description": "Soft blues with dolphins, shells & ocean vibes",
                    "image_url": f"{_ASSETS}/theme_underwater_world.jpg",
                },
                {
                    "id": "forest_adventure",
                    "label": "Forest Adventure",
                    "description": "Warm greens & browns, woodland creatures",
                    "image_url": f"{_ASSETS}/theme_forest_adventure.jpg",
                },
                {
                    "id": "northern_lights",
                    "label": "Northern Lights",
                    "description": "Cool pastels, aurora colours & starry skies",
                    "image_url": f"{_ASSETS}/theme_northern_lights.jpg",
                },
                {
                    "id": "space_explorer",
                    "label": "Space Explorer",
                    "description": "Deep navy & silver, planets & rockets",
                    "image_url": f"{_ASSETS}/theme_space_explorer.jpg",
                },
                {
                    "id": "safari_wild",
                    "label": "Safari Wild",
                    "description": "Earthy tones, jungle animals & adventure",
                    "image_url": f"{_ASSETS}/theme_safari_wild.jpg",
                },
                {
                    "id": "rainbow_bright",
                    "label": "Rainbow Bright",
                    "description": "Bold primary colours, playful & cheerful",
                    "image_url": f"{_ASSETS}/theme_rainbow_bright.jpg",
                },
            ]
            style_ids = [s["id"] for s in style_options_ui]
            title = "Style Finder: Which worlds do you love?"
            subtitle = "Everyone pick your favourites! Tap as many as you like."
        else:
            # Standard adult style tiles
            room_image_map = {
                "living room": "living_room",
                "bedroom": "bedroom",
                "office": "home_office",
                "home office": "home_office",
                "dining room": "dining_room",
                "kitchen": "kitchen",
                "bathroom": "bathroom",
                "entryway": "living_room",
            }
            room_key = room_image_map.get(collected["room_type"].lower(), "living_room")

            style_options_ui = [
                {
                    "id": "modern",
                    "label": "Modern",
                    "description": "Clean lines, minimal ornamentation",
                    "image_url": f"{_ASSETS}/{room_key}_modern.jpg",
                },
                {
                    "id": "minimalist",
                    "label": "Minimalist",
                    "description": "Less is more, simple & functional",
                    "image_url": f"{_ASSETS}/{room_key}_minimalist.jpg",
                },
                {
                    "id": "bohemian",
                    "label": "Bohemian",
                    "description": "Eclectic mix, rich colors & patterns",
                    "image_url": f"{_ASSETS}/{room_key}_bohemian.jpg",
                },
                {
                    "id": "coastal",
                    "label": "Coastal",
                    "description": "Light & airy, nautical themes",
                    "image_url": f"{_ASSETS}/{room_key}_coastal.jpg",
                },
                {
                    "id": "industrial",
                    "label": "Industrial",
                    "description": "Exposed materials, urban loft",
                    "image_url": f"{_ASSETS}/{room_key}_industrial.jpg",
                },
                {
                    "id": "scandinavian",
                    "label": "Scandinavian",
                    "description": "Natural materials, hygge coziness",
                    "image_url": f"{_ASSETS}/{room_key}_scandinavian.jpg",
                },
                {
                    "id": "traditional",
                    "label": "Traditional",
                    "description": "Classic elegance, timeless pieces",
                    "image_url": f"{_ASSETS}/{room_key}_traditional.jpg",
                },
                {
                    "id": "rustic",
                    "label": "Rustic",
                    "description": "Natural materials, country charm",
                    "image_url": f"{_ASSETS}/{room_key}_rustic.jpg",
                },
            ]
            style_ids = [s["id"] for s in style_options_ui]
            title = f"Perfect! Now, what style speaks to you for your {collected['room_type']}?"
            subtitle = "Choose one or more styles that resonate with you"

        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_2_style_discovery",
            "missing_info": "style_preferences",
            "question": "What decor style resonates with you? You can choose multiple!",
            "options": style_ids,
            "message": f"Great! Now let's explore styles for your {collected['room_type']}.",
            "ui_data": {
                "display_type": "style_selector",
                "title": title,
                "subtitle": subtitle,
                "style_options": style_options_ui,
                "interaction_mode": "multi_select",
                "phase": "phase_1_style_discovery",
                "generate_previews_from_photo": bool(room_photo_b64),
                "room_photo_base64": room_photo_b64 if room_photo_b64 else None,
                "room_type": collected["room_type"],
            },
        }

    # If we're here but don't have colors, ask about them (optional)
    if not collected["color_preferences"]:
        state_manager.update_session(session_id, stage="stage_3_color_preferences")
        logger.info(f"[HOME DECOR] Awaiting color preferences (optional) from customer")

        # Build UI data for Phase 1 color selection
        color_options_ui = [
            {
                "id": "blue",
                "label": "Blue",
                "hex": "#4A90E2",
                "description": "Calming & serene",
            },
            {
                "id": "white",
                "label": "White",
                "hex": "#FFFFFF",
                "description": "Clean & bright",
            },
            {
                "id": "gray",
                "label": "Gray",
                "hex": "#9B9B9B",
                "description": "Neutral & modern",
            },
            {
                "id": "beige",
                "label": "Beige",
                "hex": "#D4C5B9",
                "description": "Warm & inviting",
            },
            {
                "id": "black",
                "label": "Black",
                "hex": "#000000",
                "description": "Bold & dramatic",
            },
            {
                "id": "gold",
                "label": "Gold",
                "hex": "#D4AF37",
                "description": "Luxe & elegant",
            },
            {
                "id": "green",
                "label": "Green",
                "hex": "#7ED321",
                "description": "Fresh & natural",
            },
            {
                "id": "pink",
                "label": "Pink",
                "hex": "#F8B4D8",
                "description": "Soft & playful",
            },
            {
                "id": "brown",
                "label": "Brown",
                "hex": "#8B5A3C",
                "description": "Earthy & grounded",
            },
            {
                "id": "cream",
                "label": "Cream",
                "hex": "#F5E6D3",
                "description": "Soft & cozy",
            },
        ]

        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_3_color_preferences",
            "missing_info": "color_preferences",
            "question": "Are there any specific colors you'd like to incorporate? (optional)",
            "examples": [
                "blue and white",
                "warm earth tones",
                "black and gold",
                "neutral palette",
                "no preference",
            ],
            "message": f"Almost there! Any color preferences for your {', '.join(collected['style_preferences'])} {collected['room_type']}?",
            "optional": True,
            # NEW: UI display data for Phase 1 color selection
            "ui_data": {
                "display_type": "color_selector",
                "title": "Any color palette in mind?",
                "subtitle": "Optional - Select colors you'd like to incorporate, or skip",
                "color_options": color_options_ui,
                "interaction_mode": "multi_select",
                "phase": "phase_1_color_preferences",
                "skip_allowed": True,
            },
        }

    # Phase 2: Collect room dimensions for visualization
    if not collected.get("room_dimensions"):
        state_manager.update_session(session_id, stage="stage_4_room_dimensions")
        logger.info(f"[HOME DECOR] Awaiting room dimensions from customer")

        # Common room size presets based on room type
        room_type_lower = collected["room_type"].lower()
        if "bedroom" in room_type_lower:
            presets = [
                {
                    "id": "small",
                    "label": "Small",
                    "length": 3.0,
                    "width": 2.5,
                    "description": "~7.5 m2",
                },
                {
                    "id": "medium",
                    "label": "Medium",
                    "length": 4.0,
                    "width": 3.5,
                    "description": "~14 m2",
                },
                {
                    "id": "large",
                    "label": "Large",
                    "length": 5.0,
                    "width": 4.0,
                    "description": "~20 m2",
                },
            ]
        elif "living" in room_type_lower:
            presets = [
                {
                    "id": "small",
                    "label": "Small",
                    "length": 4.0,
                    "width": 3.0,
                    "description": "~12 m2",
                },
                {
                    "id": "medium",
                    "label": "Medium",
                    "length": 5.0,
                    "width": 4.0,
                    "description": "~20 m2",
                },
                {
                    "id": "large",
                    "label": "Large",
                    "length": 6.0,
                    "width": 5.0,
                    "description": "~30 m2",
                },
            ]
        else:
            presets = [
                {
                    "id": "small",
                    "label": "Small",
                    "length": 3.0,
                    "width": 2.5,
                    "description": "~7.5 m2",
                },
                {
                    "id": "medium",
                    "label": "Medium",
                    "length": 4.0,
                    "width": 3.5,
                    "description": "~14 m2",
                },
                {
                    "id": "large",
                    "label": "Large",
                    "length": 5.5,
                    "width": 4.5,
                    "description": "~25 m2",
                },
            ]

        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_4_room_dimensions",
            "missing_info": "room_dimensions",
            "question": "What are the approximate dimensions of your room?",
            "message": f"One last thing before I create your moodboard -- how big is the {collected['room_type']}? This helps me ensure the products fit your space perfectly.",
            "ui_data": {
                "display_type": "room_dimensions",
                "title": "How big is your space?",
                "subtitle": "Select a preset or enter custom dimensions",
                "presets": presets,
                "custom_input": {
                    "length_label": "Length (m)",
                    "width_label": "Width (m)",
                    "length_min": 1.5,
                    "length_max": 12.0,
                    "width_min": 1.5,
                    "width_max": 12.0,
                    "step": 0.5,
                },
                "interaction_mode": "single_select_or_custom",
                "phase": "phase_2_room_dimensions",
                "skip_allowed": False,
            },
        }

    return {
        "status": "error",
        "message": "Unable to determine next step in consultation.",
    }


def get_customer_order_history(
    customer_id: str,
    product_category: Optional[str] = None,
) -> dict:
    """
    Retrieves customer's order history, optionally filtered by category.

    Args:
        customer_id: The ID of the customer.
        product_category: Optional category filter (e.g., "Furniture", "Home Decor").

    Returns:
        A dictionary with order history and identified products.
    """
    logger.info(
        f"[ORDER HISTORY] Retrieving orders for customer {customer_id}, category filter: {product_category}"
    )

    # MOCK ORDER HISTORY - In production, this would query order database
    # For demo, simulate past furniture orders
    mock_orders = []

    # Example: Customer bought furniture 4 years ago
    if customer_id:
        # Simulate order from 4 years ago with children's furniture
        mock_orders.append(
            {
                "order_id": f"ORD-{random.randint(10000, 99999)}",
                "order_date": (datetime.now() - timedelta(days=4 * 365)).strftime(
                    "%Y-%m-%d"
                ),
                "products": [
                    {
                        "product_id": "BED-TODDLER-HOUSE",
                        "name": "Birch House Bed - Toddler",
                        "category": "Furniture",
                        "subcategory": "Children's Beds",
                        "price": 299.00,
                        "quantity": 1,
                        "age_appropriate": ["toddler"],
                        "years_ago": 4,
                    },
                    {
                        "product_id": "BOOKSHELF-CUBE-MODULAR",
                        "name": "Modular Cube Bookshelf System 3x3",
                        "category": "Furniture",
                        "subcategory": "Bookcases",
                        "price": 199.00,
                        "quantity": 1,
                        "years_ago": 4,
                    },
                ],
                "total": 498.00,
            }
        )

    # Filter by category if specified
    filtered_orders = []
    for order in mock_orders:
        if product_category:
            filtered_products = [
                p for p in order["products"] if p.get("category") == product_category
            ]
            if filtered_products:
                filtered_order = order.copy()
                filtered_order["products"] = filtered_products
                filtered_orders.append(filtered_order)
        else:
            filtered_orders.append(order)

    # Identify products from catalog that match order history
    identified_products = []
    for order in filtered_orders:
        for product in order["products"]:
            identified_products.append(
                {
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "category": product["category"],
                    "purchase_date": order["order_date"],
                    "years_since_purchase": product.get("years_ago", 0),
                    "age_appropriate": product.get("age_appropriate", []),
                }
            )

    logger.info(
        f"[ORDER HISTORY] Found {len(filtered_orders)} orders with {len(identified_products)} products"
    )

    return {
        "status": "success",
        "customer_id": customer_id,
        "order_count": len(filtered_orders),
        "orders": filtered_orders,
        "identified_products": identified_products,
        "message": f"Found {len(identified_products)} products from past orders"
        + (f" in category: {product_category}" if product_category else ""),
    }


def analyze_room_with_history(
    customer_id: str,
    session_id: str,
    age_context: Optional[str] = None,
    room_type: Optional[str] = None,
    image_data: Optional[str] = None,
) -> dict:
    """
    Analyzes room photos and cross-references with customer order history.
    This is Phase 3 of the home decor journey: photo analysis + order history.

    IMPORTANT: This tool works with the multimodal agent's context. When the customer shares photos
    via the camera or upload interface, those images are automatically added to your visual context.
    You DO NOT need to pass image_data as a parameter.

    Args:
        customer_id: The ID of the customer.
        session_id: The consultation session ID.
        age_context: Optional age context (e.g., "school-age").
        room_type: Optional room type hint.
        image_data: DEPRECATED - Images come from multimodal context, not as parameters.

    Returns:
        A dictionary with room analysis, order history matches, and next steps.

    Usage:
        - When you see room images in your context, call this tool WITHOUT image_data parameter
        - Example: analyze_room_with_history(customer_id="CY-1234", session_id="DECOR-123", age_context="school-age")
    """
    logger.info(
        f"[PHASE 3] Analyzing room with history for customer {customer_id}, session {session_id}"
    )

    if not image_data:
        logger.info(
            "[PHASE 3] No image_data parameter provided - this is expected for multimodal context"
        )
        return {
            "status": "awaiting_image",
            "message": "I'm ready to analyze your room and match it with your purchase history. Please share photos of the space.",
            "instructions": "This tool works with your multimodal visual context. Wait for the customer to share room photos via WebSocket, then call this tool to analyze them and cross-reference with order history.",
        }

    # First, analyze the room photo
    room_analysis_result = analyze_room_for_decor(
        image_data=image_data, customer_id=customer_id, room_type_hint=room_type
    )

    if room_analysis_result.get("status") != "success":
        return room_analysis_result

    # Get customer's furniture order history
    order_history = get_customer_order_history(
        customer_id=customer_id, product_category="Furniture"
    )

    # Cross-reference identified furniture with order history
    room_analysis = room_analysis_result.get("analysis", {})
    existing_furniture = room_analysis.get("existing_furniture", [])
    identified_products = order_history.get("identified_products", [])

    # Match visible furniture with past purchases
    matched_furniture = []
    for product in identified_products:
        product_name_lower = product["name"].lower()
        # Simple matching: check if product type appears in existing furniture
        for furniture in existing_furniture:
            if any(
                keyword in product_name_lower for keyword in furniture.lower().split()
            ):
                matched_furniture.append(
                    {
                        **product,
                        "identified_in_photo": True,
                        "still_appropriate": (
                            age_context not in product.get("age_appropriate", [])
                            if age_context
                            else False
                        ),
                    }
                )
                break

    # Check if furniture has outgrown its purpose
    outgrown_furniture = [
        f for f in matched_furniture if not f.get("still_appropriate", True)
    ]

    # Update session state to mark photos as analyzed
    state_manager = get_state_manager()
    state_manager.update_session(
        session_id=session_id,
        room_photos_analyzed=True,
        photo_analysis=room_analysis,
        order_history=identified_products,
    )

    logger.info(
        f"[PHASE 3] Matched {len(matched_furniture)} furniture items from order history"
    )
    logger.info(f"[PHASE 3] {len(outgrown_furniture)} items no longer age-appropriate")

    return {
        "status": "success",
        "message": f"I can see your {room_analysis.get('room_type', 'room')}! I've identified furniture from your past orders.",
        "room_analysis": room_analysis,
        "order_history_matches": matched_furniture,
        "outgrown_furniture": outgrown_furniture,
        "next_step": "interact_with_child",
        "instructions": f"The room analysis is complete. I've identified the {', '.join([f['name'] for f in matched_furniture])} from {matched_furniture[0]['years_since_purchase']} years ago. Now, address the child directly: Ask '{age_context if age_context else 'them'}' what they like doing most in their room. Be warm and encouraging - speak directly to the child, not the parent.",
    }


def analyze_room_photos_batch(
    customer_id: str,
    session_id: str,
    age_context: Optional[str] = None,
    room_type: Optional[str] = None,
    image_data_list: Optional[List[str]] = None,
) -> dict:
    """
    Analyzes multiple room photos at once and cross-references with order history.
    This handles batch photo uploads from the UI.

    IMPORTANT: This tool works with the multimodal agent's context. When the customer shares
    multiple photos via the camera or upload interface, those images are automatically added
    to your visual context. You DO NOT need to pass image_data_list as a parameter.

    Args:
        customer_id: The ID of the customer.
        session_id: The consultation session ID.
        age_context: Optional age context.
        room_type: Optional room type hint.
        image_data_list: DEPRECATED - Images come from multimodal context, not as parameters.

    Returns:
        Combined analysis from all photos.

    Usage:
        - When you see multiple room images in your context, call this tool WITHOUT image_data_list parameter
        - Example: analyze_room_photos_batch(customer_id="CY-1234", session_id="DECOR-123", room_type="bedroom")
    """
    logger.info(
        f"[BATCH PHOTOS] Called for customer {customer_id}, session {session_id}"
    )

    if not image_data_list or len(image_data_list) == 0:
        logger.info(
            "[BATCH PHOTOS] No image_data_list parameter provided - this is expected for multimodal context"
        )
        return {
            "status": "awaiting_images",
            "message": "I'm ready to analyze multiple photos of your room. Please share 2-3 photos from different angles.",
            "instructions": "This tool works with your multimodal visual context. Wait for the customer to share multiple room photos via WebSocket, then call this tool to perform batch analysis.",
        }

    # Analyze the first photo in detail (main view)
    main_photo_result = analyze_room_with_history(
        image_data=image_data_list[0],
        customer_id=customer_id,
        session_id=session_id,
        age_context=age_context,
        room_type=room_type,
    )

    # For additional photos, do quick analysis to supplement the main view
    additional_insights = []
    if len(image_data_list) > 1:
        logger.info(
            f"[BATCH PHOTOS] Analyzing {len(image_data_list) - 1} additional photos"
        )
        for i, image_data in enumerate(image_data_list[1:], start=2):
            try:
                additional_result = analyze_room_for_decor(
                    image_data=image_data,
                    customer_id=customer_id,
                    room_type_hint=room_type,
                )
                if additional_result.get("status") == "success":
                    additional_insights.append(
                        {
                            "photo_number": i,
                            "analysis": additional_result.get("analysis", {}),
                        }
                    )
            except Exception as e:
                logger.warning(f"[BATCH PHOTOS] Error analyzing photo {i}: {e}")
                continue

    # Combine insights
    combined_message = main_photo_result.get("message", "")
    if additional_insights:
        combined_message += f" I also analyzed {len(additional_insights)} additional views of your space."

    return {
        **main_photo_result,
        "photo_count": len(image_data_list),
        "additional_photos_analyzed": len(additional_insights),
        "message": combined_message,
    }


def analyze_room_for_decor(
    customer_id: Optional[str] = None,
    room_type_hint: Optional[str] = None,
    image_data: Optional[str] = None,
) -> dict:
    """
    Analyzes a room photo using Gemini Vision API to provide home decor recommendations.

    IMPORTANT: This tool is called automatically by the websocket handler when images are received
    during an active home decor consultation. The image_data parameter contains base64-encoded image data.

    Args:
        customer_id: Optional customer ID for context.
        room_type_hint: Optional hint about the room type (e.g., "living room", "bedroom").
        image_data: Base64-encoded image data (with or without data URI prefix).

    Returns:
        A dictionary containing room analysis and decor recommendations.

    Usage:
        - Websocket handler calls this automatically when images arrive during consultations
        - Agent can also call it if needed for manual analysis
        - Example: analyze_room_for_decor(customer_id="CY-1234", room_type_hint="bedroom", image_data="base64...")
    """
    logger.info(
        f"[ROOM ANALYSIS] Called for customer {customer_id}. Room hint: {room_type_hint}"
    )

    if not image_data:
        logger.warning(
            "[ROOM ANALYSIS] No image_data parameter provided - tool called without image"
        )
        return {
            "status": "awaiting_image",
            "message": "No image data was provided. Please ask the customer to share a photo of their space using the camera or upload feature.",
            "instructions": "This tool requires image_data parameter. The websocket handler should call this automatically when images arrive during consultations. If you're seeing this, the image may not have been intercepted properly.",
            "analysis": None,
            "recommendations": [],
        }

    # Extract base64 data if in data URI format
    if image_data.startswith("data:"):
        image_base64 = image_data.split(",")[1] if "," in image_data else image_data
    else:
        image_base64 = image_data

    # Check for minimal image data - use a very low threshold (100 chars)
    # This allows most legitimate photos through while blocking truly empty data
    if len(image_base64) < 100:
        return {
            "status": "failure",
            "message": "The image quality is too low for accurate analysis. Please provide a clearer photo.",
            "analysis": None,
            "recommendations": [],
        }

    # Use Gemini Vision API for room analysis
    response_text = ""
    try:
        from google import genai
        from google.genai import types
        import base64

        client = genai.Client()

        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)

        # Create the vision prompt for room analysis
        prompt = """Analyze this room image and provide detailed insights for home decor recommendations.

Please identify and describe:

1. Room Type: What type of room is this (living room, bedroom, office, kitchen, etc.)?

2. Current Style: What is the existing decor style (modern, traditional, minimalist, bohemian, etc.)?

3. Color Palette: What are the dominant colors in the room (walls, furniture, accents)?

4. Lighting: Describe the natural and artificial lighting situation.

5. Furniture & Layout: What furniture is present? How is the space laid out?

6. Opportunities: What decor elements are missing or could be improved (wall art, lighting, plants, textiles, etc.)?

7. Recommendations: Based on the analysis, what specific types of home decor would enhance this space?

Respond in this JSON format:
{
  "room_type": "living room",
  "current_style": "modern minimalist",
  "dominant_colors": ["white", "gray", "beige"],
  "lighting_assessment": "Good natural light from windows, needs ambient lighting",
  "existing_furniture": ["sofa", "coffee table", "TV stand"],
  "improvement_opportunities": ["Add wall art above sofa", "Include floor lamp for reading", "Add plants for warmth", "Layer with textiles (throw blankets, cushions)"],
  "recommended_decor_categories": ["Wall Art", "Lighting", "Plants & Planters", "Textiles"]
}

Response (JSON only):"""

        # Use Gemini for vision analysis
        vision_model = "gemini-2.5-flash"

        logger.info(f"Using {vision_model} for room analysis")

        import concurrent.futures

        def _call_gemini():
            return client.models.generate_content(
                model=vision_model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                ),
            )

        # Run the Gemini API call with a 60-second timeout to prevent hanging
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_gemini)
            try:
                response = future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                logger.error("Gemini Vision API call timed out after 60 seconds")
                return {
                    "status": "error",
                    "message": "The image analysis took too long. Please try again with a smaller or clearer photo.",
                    "analysis": None,
                    "recommendations": [],
                }

        # Parse the JSON response
        if not response.text:
            logger.error("Gemini Vision API returned empty response")
            return {
                "status": "error",
                "message": "I couldn't analyze the image. Please try again with a different photo.",
                "analysis": None,
                "recommendations": [],
            }

        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

        room_analysis = json.loads(response_text)

        logger.info(
            f"Room analysis completed: {room_analysis.get('room_type', 'Unknown')} - {room_analysis.get('current_style', 'Unknown')}"
        )

        # Find matching products based on analysis
        recommended_categories = room_analysis.get("recommended_decor_categories", [])
        dominant_colors = room_analysis.get("dominant_colors", [])
        room_type = room_analysis.get("room_type", room_type_hint)

        matching_products = []
        for product in RetailContext.PRODUCT_CATALOG:
            if product.get("category") == "Home Decor":
                # Match by subcategory
                if product.get("subcategory") in recommended_categories:
                    # Further filter by room compatibility
                    compatible_rooms = product.get("room_compatibility", [])
                    if room_type and any(
                        room_type.lower() in r.lower() for r in compatible_rooms
                    ):
                        matching_products.append(
                            {
                                "product_id": product["product_id"],
                                "name": product["name"],
                                "category": product.get("subcategory", "Home Decor"),
                                "price": product["price"],
                                "why_recommended": f"Complements your {room_analysis.get('current_style', 'existing')} style",
                            }
                        )

        # Limit to top 5 recommendations
        random.shuffle(matching_products)
        product_recommendations = matching_products[:5]

        return {
            "status": "success",
            "message": f"Successfully analyzed your {room_analysis.get('room_type', 'room')}. Found {len(product_recommendations)} product recommendations.",
            "analysis": room_analysis,
            "product_recommendations": product_recommendations,
            "analysis_id": f"ROOM-{random.randint(10000, 99999)}",
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini Vision response as JSON: {e}")
        logger.error(f"Raw response: {response_text[:200]}")
        return {
            "status": "error",
            "message": "I had trouble analyzing the room image. Please try again with a different photo.",
            "analysis": None,
            "recommendations": [],
        }
    except Exception as e:
        logger.error(f"Error using Gemini Vision for room analysis: {e}")
        return {
            "status": "error",
            "message": f"An error occurred while analyzing the room: {str(e)[:100]}",
            "analysis": None,
            "recommendations": [],
        }


def visualize_room_with_products(
    customer_id: str,
    session_id: str,
    product_ids: Optional[List[str]] = None,
    style_preferences: Optional[List[str]] = None,
    room_type: Optional[str] = None,
    room_dimensions: Optional[Dict[str, float]] = None,
    image_data: Optional[str] = None,
) -> dict:
    """
    Generates a photorealistic room visualization showing how selected products
    would look in the customer's room.

    When product_ids is provided, ONLY those products are visualized.
    When product_ids is not provided, all moodboard products from the session are used.

    Args:
        customer_id: The ID of the customer.
        session_id: The consultation session ID.
        product_ids: List of product IDs to visualize. Pass the exact IDs the customer selected.
        style_preferences: Optional. Auto-resolved from session if not provided.
        room_type: Optional. Auto-resolved from session if not provided.
        room_dimensions: Optional. Auto-resolved from session if not provided.
        image_data: Base64-encoded room photo to use as base. If not provided,
                    falls back to generating a fresh room rendering.

    Returns:
        A dictionary with the visualization result and UI data.
    """
    logger.info(
        f"[ROOM VIZ] Generating visualization for customer {customer_id}, session {session_id}"
    )

    state_manager = get_state_manager()

    # Retrieve session data for context
    session = state_manager.get_session(session_id) if session_id else None
    collected = {}
    if session:
        collected = session.get("collected_data", {})
        if not style_preferences:
            style_preferences = collected.get("style_preferences", [])
        if not room_type:
            room_type = collected.get("room_type", "bedroom")
        if not room_dimensions:
            room_dimensions = collected.get("room_dimensions")
        # Use the uploaded room photo as base for inpainting
        if not image_data and collected.get("room_photo_base64"):
            image_data = collected["room_photo_base64"]
            logger.info(
                "[ROOM VIZ] Using stored room photo from session for inpainting"
            )

    # --- Resolve products to show ---
    # Priority 1: explicit product_ids passed in
    # Priority 2: re-run the moodboard scoring logic using session data (gets ALL moodboard products)
    products_to_show = []
    if product_ids:
        for product in RetailContext.PRODUCT_CATALOG:
            if product["product_id"] in product_ids:
                products_to_show.append(product)

    if not products_to_show:
        # Re-run the same scoring logic as create_style_moodboard to get the exact
        # same products the customer saw.  This avoids the mismatch from loose keyword search.
        age_context = collected.get("age_context")
        room_purpose = collected.get("room_purpose")
        include_furniture = room_purpose == "redesign" or (
            room_type and room_type.lower() == "bedroom" and age_context
        )

        STYLE_KEYWORDS = {
            "underwater_world": [
                "underwater",
                "ocean",
                "dolphins",
                "coastal",
                "nautical",
            ],
            "forest_adventure": ["forest", "woodland", "rustic", "natural"],
            "northern_lights": [
                "northern lights",
                "aurora",
                "pastel",
                "scandinavian",
                "modern",
            ],
            "space_explorer": ["space", "modern", "industrial"],
            "safari_wild": ["safari", "jungle", "bohemian", "rustic", "natural"],
            "rainbow_bright": ["rainbow", "modern", "bohemian"],
            "modern": ["modern", "contemporary", "sleek"],
            "minimalist": ["minimalist", "simple", "clean"],
            "bohemian": ["bohemian", "boho", "eclectic"],
            "coastal": ["coastal", "beach", "nautical"],
            "industrial": ["industrial", "urban", "loft"],
            "scandinavian": ["scandinavian", "nordic", "hygge"],
            "traditional": ["traditional", "classic", "elegant"],
            "rustic": ["rustic", "farmhouse", "country"],
        }

        matched_styles = []
        for pref in style_preferences or []:
            pref_lower = pref.lower()
            for style, kws in STYLE_KEYWORDS.items():
                if pref_lower in kws or pref_lower in style:
                    if style not in matched_styles:
                        matched_styles.append(style)
        if not matched_styles:
            matched_styles = style_preferences or ["modern"]

        color_prefs = collected.get("color_preferences")
        normalized_colors = [c.lower() for c in color_prefs] if color_prefs else []

        all_relevant = []
        for product in RetailContext.PRODUCT_CATALOG:
            cat = product.get("category", "")
            if cat == "Home Decor" or (include_furniture and cat == "Furniture"):
                if age_context and cat == "Furniture":
                    age_tags = product.get("age_appropriate", [])
                    if age_context in age_tags or not age_tags:
                        all_relevant.append(product)
                else:
                    all_relevant.append(product)

        scored = {}
        for product in all_relevant:
            score = 0
            p_styles = [s.lower() for s in product.get("style_tags", [])]
            p_colors = [c.lower() for c in product.get("color_palette", [])]
            p_rooms = [r.lower() for r in product.get("room_compatibility", [])]
            score += sum(1 for s in matched_styles if s in p_styles) * 10
            if normalized_colors:
                score += sum(1 for c in normalized_colors if c in p_colors) * 15
            if room_type and room_type.lower() in p_rooms:
                score += 5
            if score > 0:
                scored[product["product_id"]] = score

        sorted_products = sorted(
            [p for p in all_relevant if p["product_id"] in scored],
            key=lambda p: scored[p["product_id"]],
            reverse=True,
        )

        if include_furniture:
            furn = [p for p in sorted_products if p.get("category") == "Furniture"]
            decor = [p for p in sorted_products if p.get("category") == "Home Decor"]
            products_to_show = furn[:4] + decor[:6]
        else:
            products_to_show = sorted_products[:6]

    logger.info(
        f"[ROOM VIZ] Products to visualize: {[p['name'] for p in products_to_show]}"
    )

    # --- Build prompt ---
    product_descriptions = [
        f"{p['name']} ({p.get('subcategory', p.get('category', ''))})"
        for p in products_to_show[:8]
    ]

    style_desc_map = {
        "underwater_world": "underwater ocean theme with soft blues, dolphins, shells, and coral accents",
        "forest_adventure": "woodland forest theme with warm greens, browns, and nature elements",
        "northern_lights": "aurora northern lights theme with cool pastels, lavender, and mint tones",
        "space_explorer": "space exploration theme with deep navy, silver accents, and constellation elements",
        "safari_wild": "safari jungle theme with earthy khaki, olive tones, and animal motifs",
        "rainbow_bright": "cheerful rainbow theme with bold primary colours against clean white",
        "modern": "modern style with clean lines and minimal ornamentation",
        "minimalist": "minimalist design with simple functional furniture",
        "bohemian": "bohemian style with eclectic mix and rich patterns",
        "coastal": "coastal style with light blues, whites, and nautical textures",
        "industrial": "industrial style with exposed materials and metal accents",
        "scandinavian": "Scandinavian style with light woods and cozy textiles",
        "traditional": "traditional style with classic elegance",
        "rustic": "rustic style with natural wood and warm earth tones",
    }

    style_descriptions = [
        style_desc_map.get(s.lower(), s) for s in (style_preferences or [])
    ]
    style_text = (
        " combined with ".join(style_descriptions)
        if style_descriptions
        else "modern clean"
    )

    dim_text = ""
    if room_dimensions:
        area = room_dimensions.get("length", 4) * room_dimensions.get("width", 3)
        dim_text = f" The room is approximately {room_dimensions.get('length', 4)}m x {room_dimensions.get('width', 3)}m ({area:.0f} m2)."

    room_label = room_type or "bedroom"

    # Build product placement descriptions with realistic positioning hints
    product_placement = []
    for i, p in enumerate(products_to_show[:8]):
        name = p["name"]
        name_lower = name.lower()
        subcat = p.get("subcategory", p.get("category", "")).lower()
        if "bed" in subcat or "bed" in name_lower:
            product_placement.append(
                f"a {name} positioned against the main wall as the centrepiece"
            )
        elif "desk" in subcat or "desk" in name_lower:
            product_placement.append(
                f"a {name} placed near the window for natural light"
            )
        elif "chair" in subcat or "chair" in name_lower:
            product_placement.append(
                f"a {name} tucked under the desk or beside the bed"
            )
        elif "wardrobe" in subcat or "wardrobe" in name_lower or "closet" in name_lower:
            product_placement.append(f"a {name} standing against a side wall")
        elif "lamp" in subcat or "light" in subcat or "lamp" in name_lower:
            product_placement.append(
                f"a {name} on the bedside table or desk providing warm light"
            )
        elif "rug" in subcat or "rug" in name_lower or "carpet" in name_lower:
            product_placement.append(
                f"a {name} laid flat on the floor in the centre of the room"
            )
        elif (
            "art" in subcat
            or "print" in subcat
            or "canvas" in name_lower
            or "poster" in name_lower
        ):
            product_placement.append(
                f"a {name} hanging centred on the wall above the bed or desk, NOT on a window"
            )
        elif "clock" in subcat or "clock" in name_lower:
            product_placement.append(
                f"a {name} mounted on the wall above the window or on a side wall, NOT on the window glass"
            )
        elif "mirror" in subcat or "mirror" in name_lower:
            product_placement.append(
                f"a {name} mounted on the wall at eye height, NOT on a window"
            )
        elif "plant" in subcat or "planter" in name_lower or "plant" in name_lower:
            product_placement.append(
                f"a {name} standing on the floor in a corner or placed on a shelf"
            )
        elif "cushion" in subcat or "cushion" in name_lower or "pillow" in name_lower:
            product_placement.append(f"a {name} arranged on the bed or a chair")
        elif "shelf" in subcat or "bookshelf" in name_lower or "shelf" in name_lower:
            product_placement.append(
                f"a {name} mounted on the wall or standing against a wall"
            )
        elif "curtain" in subcat or "curtain" in name_lower or "blind" in name_lower:
            product_placement.append(f"a {name} hanging from a rod above the window")
        elif "basket" in subcat or "basket" in name_lower or "storage" in name_lower:
            product_placement.append(
                f"a {name} placed on the floor near a shelf or under a desk"
            )
        elif "throw" in subcat or "blanket" in name_lower or "throw" in name_lower:
            product_placement.append(
                f"a {name} draped casually over the bed or a chair"
            )
        elif "vase" in subcat or "vase" in name_lower:
            product_placement.append(f"a {name} placed on a shelf or desk surface")
        else:
            product_placement.append(
                f"a {name} placed naturally in the room at an appropriate location"
            )

    # Randomize camera angle and time of day for variety on regeneration
    camera_angles = [
        "Shot with a wide-angle lens from the doorway perspective",
        "Viewed from the corner of the room looking diagonally across the space",
        "Photographed from a low angle near floor level for a dramatic perspective",
        "Captured from the window side looking back into the room",
        "Shot from a slightly elevated angle as if standing in the doorway",
    ]
    time_moods = [
        "Natural morning daylight streaming through windows with warm golden tones",
        "Soft afternoon light filtering through sheer curtains creating gentle shadows",
        "Bright midday natural light filling the room evenly",
        "Warm evening light with cosy interior lamps switched on",
        "Overcast day providing soft diffused light throughout the space",
    ]
    angle = random.choice(camera_angles)
    mood = random.choice(time_moods)

    # Build room layout description from photo analysis if available
    room_layout_hint = ""
    if collected.get("photo_analysis"):
        room_layout_hint = (
            f"The room has a window on one wall, "
            f"with the bed against the main wall. "
            f"The room layout is compact and cosy. "
        )

    # Include constraint about existing furniture to keep
    keep_constraint = ""
    raw_constraints = collected.get("constraints", {})
    if raw_constraints:
        if isinstance(raw_constraints, dict) and raw_constraints.get("keep"):
            keep_constraint = f"The room must include a {', '.join(raw_constraints['keep'])} as existing furniture. "
        elif isinstance(raw_constraints, str) and ("shelf" in raw_constraints.lower() or "keep" in raw_constraints.lower()):
            keep_constraint = f"The room must include a cube shelf / modular bookshelf as existing furniture. "
        elif isinstance(raw_constraints, list):
            keep_constraint = f"The room must include: {', '.join(str(c) for c in raw_constraints)} as existing furniture. "

    prompt = (
        f"Beautiful aspirational interior design photograph of a child's {room_label} "
        f"designed in {style_text} style.{dim_text} "
        f"{room_layout_hint}"
        f"The room features a single window with natural light, wooden flooring, and light-coloured walls. "
        f"{keep_constraint}"
        f"The room is furnished with these specific items, all clearly visible: "
        f"{'; '.join(product_placement)}. "
        f"{angle}. "
        f"{mood}, complemented by interior lighting. "
        f"The room feels warm, inviting, and inspirational -- a dream bedroom that a child would love. "
        f"Realistic textures on all surfaces -- visible wood grain, fabric weave, soft textiles. "
        f"Styled like a real cosy home, not a catalogue or showroom. "
        f"Professional architectural photography for an interior design magazine, "
        f"4K resolution, depth of field, soft shadows, colour-accurate."
    )

    logger.info(f"[ROOM VIZ] Prompt: {prompt[:300]}...")

    # --- Attempt image generation via google-genai SDK (Vertex AI) ---
    generated_image_b64 = None

    try:
        from google import genai
        from google.genai import types as genai_types
        import base64

        client = genai.Client()

        # Try Imagen 3 inpainting first if room photo is available.
        # This preserves the actual room layout. Falls back to Imagen 4 Ultra.
        if image_data and not generated_image_b64:
            logger.info("[ROOM VIZ] Using Imagen 3 inpainting on customer's room photo")

            # Focus the prompt on adding furniture rather than redesigning
            item_names = [p["name"] for p in products_to_show[:6]]
            constraints = collected.get("constraints", {})
            keep_items = ""
            if constraints:
                if isinstance(constraints, dict):
                    keep_list = constraints.get("keep", [])
                    if keep_list:
                        keep_items = f"CRITICAL: The existing {', '.join(keep_list)} MUST remain in the room -- do not remove, replace, or hide it. It should be clearly visible. "
                elif isinstance(constraints, str):
                    if "shelf" in constraints.lower() or "keep" in constraints.lower():
                        keep_items = f"CRITICAL: The customer wants to keep existing furniture: {constraints}. Do NOT remove it. "
                elif isinstance(constraints, list):
                    keep_items = f"CRITICAL: Keep these existing items in the room: {', '.join(str(c) for c in constraints)}. Do NOT remove them. "

            edit_prompt = (
                f"Add the following new furniture and decor items into this room: "
                f"{'; '.join(item_names)}. "
                f"Place each item naturally in the room: "
                f"{'; '.join(product_placement[:6])}. "
                f"Style the room in a {style_text} theme. "
                f"Keep the existing room structure, walls, window, and flooring exactly as they are. "
                f"{keep_items}"
                f"The new furniture must look photorealistic with correct perspective and shadows. "
                f"Interior design magazine quality photograph."
            )

            photo_bytes = base64.b64decode(image_data)

            try:
                from PIL import Image as PILImage
                from io import BytesIO

                # Use Gemini 3 Pro Image (Nano Banana Pro) for intelligent editing
                # It uses Gemini's reasoning to understand the room and place items naturally
                pil_image = PILImage.open(BytesIO(photo_bytes))

                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
                    contents=[pil_image, edit_prompt],
                    config=genai_types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                    ),
                )

                # Extract the generated image from the response
                if response and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, "inline_data") and part.inline_data:
                            img_bytes = part.inline_data.data
                            generated_image_b64 = base64.b64encode(img_bytes).decode("utf-8")
                            logger.info(f"[ROOM VIZ] Gemini 3 Pro Image edit successful ({len(img_bytes)} bytes)")
                            break

                if not generated_image_b64:
                    logger.warning("[ROOM VIZ] Gemini 3 Pro Image returned no image, falling back to Imagen 4 Ultra")

            except Exception as edit_err:
                logger.warning(f"[ROOM VIZ] Gemini 3 Pro Image edit failed: {edit_err}, falling back to Imagen 4 Ultra")

        # Fallback: Imagen 4 Ultra fresh generation
        if not generated_image_b64:
            # --- Fresh generation: no base photo ---
            logger.info(
                "[ROOM VIZ] Generating fresh room rendering with Imagen 4 Ultra"
            )

            image_response = client.models.generate_images(
                model="imagen-4.0-ultra-generate-001",
                prompt=prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="4:3",
                    safety_filter_level="block_some",
                    person_generation="dont_allow",
                ),
            )

            if image_response and image_response.generated_images:
                img_bytes = image_response.generated_images[0].image.image_bytes
                generated_image_b64 = base64.b64encode(img_bytes).decode("utf-8")
                logger.info(
                    f"[ROOM VIZ] Imagen 4 Ultra image generated successfully ({len(img_bytes)} bytes)"
                )
            else:
                logger.warning("[ROOM VIZ] Imagen 4 Ultra returned no images")

    except Exception as e:
        logger.warning(f"[ROOM VIZ] Image generation failed: {e}")

    # --- Build response ---
    viz_id = f"VIZ-{random.randint(10000, 99999)}"
    product_info = [
        {"product_id": p["product_id"], "name": p["name"], "price": p["price"]}
        for p in products_to_show[:8]
    ]

    if generated_image_b64:
        return {
            "status": "success",
            "visualization_id": viz_id,
            "session_id": session_id,
            "message": f"Here is how your {room_label} could look with the {style_text} design!",
            "products_shown": [p["name"] for p in products_to_show[:8]],
            "room_dimensions": room_dimensions,
            "ui_data": {
                "display_type": "room_visualization",
                "visualization_id": viz_id,
                "image_base64": generated_image_b64,
                "room_type": room_label,
                "style_preferences": style_preferences,
                "products_shown": product_info,
                "room_dimensions": room_dimensions,
                "message": f"Your {room_label} reimagined with {', '.join(style_preferences or ['your chosen'])} style",
            },
        }
    else:
        return {
            "status": "partial",
            "visualization_id": viz_id,
            "session_id": session_id,
            "message": (
                f"I've designed a concept for your {room_label} with {style_text}. "
                f"Products included: {', '.join(p['name'] for p in products_to_show[:8])}."
                f"{dim_text}"
            ),
            "visualization_prompt": prompt,
            "products_shown": [p["name"] for p in products_to_show[:8]],
            "room_dimensions": room_dimensions,
            "ui_data": {
                "display_type": "room_visualization",
                "visualization_id": viz_id,
                "image_base64": None,
                "room_type": room_label,
                "style_preferences": style_preferences,
                "products_shown": product_info,
                "room_dimensions": room_dimensions,
                "message": f"Your {room_label} concept with {', '.join(style_preferences or ['your chosen'])} style",
                "fallback_description": prompt,
            },
        }
