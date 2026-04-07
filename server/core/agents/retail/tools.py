import random
import time
from typing import Optional, List, Dict, Any
import requests
from ...logger import logger
from datetime import datetime, timedelta

from google.cloud import firestore
from .context import RetailContext
from .session_state import get_state_manager
from config.config import RECOMMENDATION_MODEL

# Initialize Firestore client with error handling
db = None
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

try:
    logger.info("Connecting to Firestore...")
    db = firestore.Client()
    logger.info("Connected to Firestore")

    # Carts will be created dynamically per customer when needed
    # No need for hardcoded cart initialization
    logger.info(
        "Firestore ready - carts will be created per customer dynamically"
    )
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
    return {"status": "approved", "message": f"Discount of {value}{
            '%' if type == 'percentage' else 'EUR'} approved."}


def sync_ask_for_approval(
    type: str, value: float, reason: str, product_id: str = ""
) -> str:
    """Asks a manager for approval synchronously (waits for a response)."""
    logger.info(
        f"Requesting sync manager approval for discount: type={type}, value={value}, reason={reason}, product_id={product_id}"
    )
    url = "https://escalation-handler-243114688021.us-central1.run.app/request"
    payload = {
        "menuId": 36,
        "menuLang": "en",
        "customer_id": "CY-1234-1234",
        "discount_type": type,
        "discount_value": value,
        "product_id": product_id,
        "crmAccountId": "abc123",
        "approval_status": "pending",
        "messages": {
            "agent": [reason],
            "allow": "My manager says ok",
            "deny": "My manager says no",
            "timeout": "Sorry I did not hear back from my manager",
            "error": "Sorry but I've had some trouble getting hold of my manager",
        },
        "escalationHost": "chat-escalation-243114688021.us-central1.run.app",
    }

    if db is not None:
        try:
            db.collection("customers").document("CY-1234-1234").set(payload)
        except Exception as e:
            logger.warning(f"Failed to save to Firestore: {e}")

    logger.info("Waiting for manager approval...")

    # poll for approval status. max of 5 minutes with 1 second intervals
    for i in range(300):
        if db is not None:
            try:
                doc = db.collection("customers").document("CY-1234-1234").get()
                if doc.exists:
                    if doc.to_dict()["approval_status"] == "approved":
                        return "Manager approved the discount"
            except Exception as e:
                logger.warning(f"Failed to check Firestore: {e}")
                break
        else:
            # Without Firestore, simulate approval for demo purposes
            time.sleep(2)
            return "Manager approved the discount (simulated)"

        time.sleep(1)

    logger.info("Manager approval not received after 5 minutes")

    logger.info("Sending request to manager...")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response)
    logger.info("Request sent to manager")

    if response.status_code == 200:
        logger.info("Manager approved the discount")
        return (
            response.text
        )  # Return the response text if the status code is 200
    else:
        logger.warning(
            "Simulating sync denial or timeout for unspecified request."
        )
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
            f"Image data received (length: {
                len(image_data)} characters). Processing with Gemini Vision..."
        )

        # Extract base64 data if it's in data URI format
        if image_data.startswith("data:"):
            # Format: "data:image/jpeg;base64,<base64data>"
            image_base64 = (
                image_data.split(",")[1] if "," in image_data else image_data
            )
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
                    types.Part.from_bytes(
                        data=image_bytes, mime_type="image/jpeg"
                    ),
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
            identified_model = identified_model.replace('"', "").replace(
                "'", ""
            )

            logger.info(f"Gemini Vision identified: {identified_model}")

            if "unknown" in identified_model.lower():
                message = "I can see a device in the camera feed, but I'm having trouble identifying the specific model. Could you hold it closer or at a better angle?"
                status = "partial"
            else:
                message = f"Based on the camera feed, this looks like a {identified_model}."
                status = "success"

            return {
                "status": status,
                "identified_phone_model": identified_model,
                "message": message,
                "image_data_processed": True,
            }

        except Exception as e:
            logger.error(
                f"Error using Gemini Vision for phone identification: {e}"
            )
            # Fallback to default
            identified_model = "Unknown Device (identification error)"
            message = f"I had trouble analyzing the image. Error: {
                str(e)[
                    :100]}"
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
                    "last_updated": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
        except Exception as e:
            logger.warning(
                f"Failed to access Firestore: {e}. Using empty cart."
            )
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
                    "last_updated": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
        except Exception as e:
            logger.warning(
                f"Failed to access Firestore: {e}. Using empty cart."
            )
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
                logger.warning(
                    f"INVALID PRODUCT ID: {prod_id} not found in catalog"
                )

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
                for valid_id in list(PRODUCT_CATALOG.keys())[
                    :10
                ]:  # Sample first 10
                    if any(
                        word in valid_id.lower()
                        for word in invalid_lower.split("-")[:2]
                    ):
                        suggestions.append(valid_id)
                        if len(suggestions) >= 3:
                            break

            error_msg = f"ERROR: Invalid product ID(s): {
                ', '.join(invalid_products)}. "
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
                current_mock_backend_cart["items"][prod_id][
                    "quantity"
                ] += quantity
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
                db.collection("carts").document(customer_id).set(
                    cart_to_save
                )
                logger.info(
                    f"Cart updated in Firestore for customer {customer_id}"
                )
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
            "last_updated": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
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
                    style_info = f" [Styles: {', '.join(product.get('style_tags', []))}]" if product.get('style_tags') else ""
                    color_info = f" [Colors: {', '.join(product.get('color_palette', []))}]" if product.get('color_palette') else ""
                    room_info = f" [Rooms: {', '.join(product.get('room_compatibility', []))}]" if product.get('room_compatibility') else ""
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
            config=types.GenerateContentConfig(
                temperature=0.3, max_output_tokens=200
            ),
        )

        # Parse the response to get product IDs
        import json

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

        logger.info(f"Gemini recommended {
                len(recommendations)} products for '{interest}'")

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
    if (
        product_id == "GOOGLE-PIXEL9PRO-CASE"
        or "otterbox" in product_id.lower()
    ):
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
        f"Generating QR code for customer: {customer_id} - {discount_value}{
            '%' if discount_type == 'percentage' else 'EUR'} discount. Desc: {description}"
    )
    # MOCK API RESPONSE - Match example.py output format
    expiration_date = (
        datetime.now() + timedelta(days=expiration_days)
    ).strftime("%Y-%m-%d")
    # Construct payload similar to example
    qr_code_payload = f"MOCK_QR_CODE_FOR_CUSTOMER:{customer_id};DISCOUNT:{discount_value};TYPE:{discount_type};EXP:{expiration_date};DESC:{
        description.replace(
            ' ', '_')};LIMIT:{usage_limit}"

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
                message += f"An additional payment of {
                    price_difference:.2f} EUR is required for '{desired_product_id}'."
            elif price_difference < -0.01:
                message += f"A refund of {
                    -price_difference:.2f} EUR will be issued upon return of the original item."
            else:
                message += (
                    f"There is no price difference for '{desired_product_id}'."
                )
        else:
            message += (
                "A refund or store credit will be processed upon return."
            )

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
    estimated_value_min = max(
        0, estimated_value * 0.85
    )  # e.g., 85% of estimate
    estimated_value_max = estimated_value * 1.10  # e.g., 110% of estimate

    # Round to sensible values
    estimated_value_min = (
        round(estimated_value_min / 5) * 5
    )  # Round to nearest 5 EUR
    estimated_value_max = round(estimated_value_max / 5) * 5

    if estimated_value_max > 0:
        status = "success"
        message = f"Trade-in value estimated between {
            estimated_value_min:.2f} and {
            estimated_value_max:.2f} {currency}. Final value depends on inspection."
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

    if (
        "pixel" in product_id.lower()
        and "plusgarantie" not in product_id.lower()
    ):
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

    elif (
        "plusgarantie" in product_id.lower() and "pixel" in product_id.lower()
    ):
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
        logger.info(
            f"Lookup warranty details for default device: {product_id}"
        )
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

    from .image_fetcher import ImageFetcher
    image_fetcher = ImageFetcher()

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
    include_furniture = room_purpose == "redesign" or (room_type and room_type.lower() == "bedroom" and age_context)

    # Filter products by style tags - include both Home Decor and Furniture for redesigns
    matching_products = []
    for product in RetailContext.PRODUCT_CATALOG:
        # Include Home Decor products always, and Furniture products for redesigns
        if product.get("category") == "Home Decor" or (include_furniture and product.get("category") == "Furniture"):
            # Check if product's style_tags match user preferences
            product_styles = product.get("style_tags", [])
            if any(style in product_styles for style in matched_styles):
                # Filter by age_appropriate if age_context is provided
                if age_context and product.get("category") == "Furniture":
                    age_tags = product.get("age_appropriate", [])
                    # Only include if product matches the age context
                    if age_context in age_tags or not age_tags:
                        matching_products.append(product)
                else:
                    matching_products.append(product)

    # Further filter by color preferences if provided
    if color_preferences:
        color_filtered = []
        for product in matching_products:
            product_colors = product.get("color_palette", [])
            if any(color.lower() in [c.lower() for c in product_colors] for color in color_preferences):
                color_filtered.append(product)
        # If color filtering yields results, use those; otherwise keep style matches
        if color_filtered:
            matching_products = color_filtered

    # Further filter by room compatibility if provided
    if room_type:
        room_filtered = []
        for product in matching_products:
            compatible_rooms = product.get("room_compatibility", [])
            if room_type.lower() in [r.lower() for r in compatible_rooms]:
                room_filtered.append(product)
        # If room filtering yields results, use those; otherwise keep previous matches
        if room_filtered:
            matching_products = room_filtered

    # Determine product count based on room purpose
    # For redesigns, show more products (furniture + decor)
    # For decoration only, show fewer products (just decor)
    product_count = 10 if include_furniture else 6

    # Separate furniture and decor products for better curation
    if include_furniture:
        furniture_products = [p for p in matching_products if p.get("category") == "Furniture"]
        decor_products = [p for p in matching_products if p.get("category") == "Home Decor"]

        random.shuffle(furniture_products)
        random.shuffle(decor_products)

        # For redesigns: prioritize furniture, then add decor
        # Aim for 40% furniture, 60% decor
        furniture_count = min(4, len(furniture_products))
        decor_count = min(product_count - furniture_count, len(decor_products))

        moodboard_products = furniture_products[:furniture_count] + decor_products[:decor_count]
    else:
        random.shuffle(matching_products)
        moodboard_products = matching_products[:product_count]

    # Fetch images for selected products
    logger.info(f"Fetching images for {len(moodboard_products)} moodboard products...")
    image_results = image_fetcher.fetch_batch_images(moodboard_products)

    # Build moodboard response
    product_recommendations = []
    for product in moodboard_products:
        product_id = product["product_id"]
        fetched_image_url = image_results.get(product_id, product.get("image_url", "./assets/placeholder_home_decor.jpg"))

        product_recommendations.append({
            "product_id": product_id,
            "name": product["name"],
            "category": product.get("subcategory", product["category"]),
            "price": product["price"],
            "style_tags": product.get("style_tags", []),
            "color_palette": product.get("color_palette", []),
            "image_url": fetched_image_url,
        })

    # Create style description for the moodboard
    style_descriptions = [STYLE_CATALOG.get(s, {}).get("description", s) for s in matched_styles]

    moodboard_summary = {
        "status": "success",
        "customer_id": customer_id,
        "moodboard_id": f"MOOD-{random.randint(10000, 99999)}",
        "selected_styles": matched_styles,
        "style_descriptions": style_descriptions,
        "room_type": room_type,
        "color_palette": color_preferences if color_preferences else "open to all colors",
        "product_count": len(product_recommendations),
        "products": product_recommendations,
        "message": f"Created a {', '.join(matched_styles)} style moodboard with {len(product_recommendations)} curated products{f' for your {room_type}' if room_type else ''}."
    }

    logger.info(f"Moodboard created with {len(product_recommendations)} products")
    return moodboard_summary


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

    # Check if customer has an existing active session
    existing_session = state_manager.get_customer_session(customer_id)
    if existing_session and not existing_session.get("moodboard_generated", False):
        logger.info(f"[HOME DECOR] Found existing session {existing_session['session_id']}, continuing...")
        session_id = existing_session["session_id"]
    else:
        # Create new session
        session_id = f"DECOR-CONSULT-{random.randint(10000, 99999)}"
        state_manager.create_session(customer_id, session_id)
        logger.info(f"[HOME DECOR] Created new session {session_id}")

    # Try to detect room type from initial request
    detected_room = None
    if initial_request:
        request_lower = initial_request.lower()
        room_keywords = {
            "living room": ["living room", "lounge"],
            "bedroom": ["bedroom", "bed room"],
            "office": ["office", "home office", "workspace"],
            "dining room": ["dining room", "dining"],
            "kitchen": ["kitchen"],
            "bathroom": ["bathroom", "bath"],
            "entryway": ["entryway", "entry way", "hallway", "entrance"]
        }

        for room_type, keywords in room_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                detected_room = room_type
                logger.info(f"[HOME DECOR] Detected room from initial request: {detected_room}")
                # Update session with detected room
                state_manager.update_session(session_id, room_type=detected_room)
                break

    # If room was detected, skip room selector and proceed to style selection
    if detected_room:
        logger.info(f"[HOME DECOR] Room detected ({detected_room}), skipping room selector and proceeding to style selection")
        return continue_home_decor_consultation(
            customer_id=customer_id,
            session_id=session_id,
            room_type=detected_room
        )

    # Define the consultation stages
    consultation_flow = {
        "stage_1_room_identification": {
            "question": "Which room would you like to decorate?",
            "options": ["living room", "bedroom", "office", "dining room", "kitchen", "bathroom", "entryway"],
            "completed": False
        },
        "stage_2_style_discovery": {
            "question": "What decor style resonates with you?",
            "options": ["modern", "minimalist", "bohemian", "coastal", "industrial", "scandinavian", "traditional", "rustic"],
            "allow_multiple": True,
            "completed": False
        },
        "stage_3_color_preferences": {
            "question": "Are there specific colors you'd like to incorporate?",
            "examples": ["blue and white", "warm earth tones", "black and gold", "neutral palette"],
            "optional": True,
            "completed": False
        },
        "stage_4_generate_moodboard": {
            "action": "create_style_moodboard",
            "description": "Generate personalized moodboard with curated products",
            "completed": False
        }
    }

    # Build UI data for Phase 1 room selection
    room_options_ui = [
        {"id": "living_room", "label": "Living Room", "icon": "🛋️"},
        {"id": "bedroom", "label": "Bedroom", "icon": "🛏️"},
        {"id": "office", "label": "Office", "icon": "💼"},
        {"id": "dining_room", "label": "Dining Room", "icon": "🍽️"},
        {"id": "kitchen", "label": "Kitchen", "icon": "🍳"},
        {"id": "bathroom", "label": "Bathroom", "icon": "🚿"},
        {"id": "entryway", "label": "Entryway", "icon": "🚪"}
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
            "phase": "phase_1_initial_interest"
        }
    }

    logger.info(f"[HOME DECOR] Consultation started successfully. Session ID: {session_id}")
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

    Returns:
        A dictionary with the next step in the consultation or final moodboard.
    """
    logger.info(f"[HOME DECOR] Continuing consultation - room: {room_type}, purpose: {room_purpose}, age: {age_context}, styles: {style_preferences}, colors: {color_preferences}")

    state_manager = get_state_manager()

    # Get or validate session
    if not session_id:
        session = state_manager.get_customer_session(customer_id)
        if not session:
            logger.warning(f"[HOME DECOR] No session found for customer {customer_id}, creating new one")
            return start_home_decor_consultation(customer_id)
        session_id = session["session_id"]
    else:
        session = state_manager.get_session(session_id)
        if not session:
            logger.warning(f"[HOME DECOR] Session {session_id} not found")
            return {"status": "error", "message": "Session not found. Please start a new consultation."}

    # Update session state with new information
    state_manager.update_session(
        session_id=session_id,
        room_type=room_type,
        room_purpose=room_purpose,
        age_context=age_context,
        constraints=constraints,
        style_preferences=style_preferences,
        color_preferences=color_preferences
    )

    # Get current state
    session = state_manager.get_session(session_id)
    collected = session["collected_data"]

    # If we have all required information, generate the moodboard
    if collected["room_type"] and collected["style_preferences"]:
        logger.info(f"[HOME DECOR] All information collected, generating moodboard...")

        # Call the moodboard creation function with all context
        moodboard_result = create_style_moodboard(
            customer_id=customer_id,
            style_preferences=collected["style_preferences"],
            room_type=collected["room_type"],
            color_preferences=collected["color_preferences"],
            age_context=collected.get("age_context"),
            room_purpose=collected.get("room_purpose"),
            constraints=collected.get("constraints")
        )

        # Mark session as completed
        state_manager.mark_moodboard_generated(session_id)

        logger.info(f"[HOME DECOR] Moodboard generated successfully for session {session_id}")

        return {
            "status": "consultation_completed",
            "session_id": session_id,
            "stage": "completed",
            "moodboard": moodboard_result,
            "message": f"Based on your {', '.join(collected['style_preferences'])} style preferences for your {collected['room_type']}, I've created a personalized moodboard!",
            "next_action": "Present the moodboard products to the customer and offer to add any to their cart."
        }

    # Determine what information we still need
    if not collected["room_type"]:
        state_manager.update_session(session_id, stage="stage_1_room_identification")
        logger.info(f"[HOME DECOR] Awaiting room type from customer")
        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_1_room_identification",
            "missing_info": "room_type",
            "question": "Which room would you like to decorate?",
            "options": ["living room", "bedroom", "office", "dining room", "kitchen", "bathroom", "entryway"],
            "message": "Let's start by identifying which room you'd like to transform."
        }

    # Ask about room purpose (for bedrooms - decoration vs redesign)
    if collected["room_type"].lower() == "bedroom" and not collected.get("room_purpose"):
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
            "instructions": "Ask if they want to just add decorative items or if they need furniture too."
        }

    # Ask about age context (for bedrooms in redesign mode)
    if collected["room_type"].lower() == "bedroom" and collected.get("room_purpose") == "redesign" and not collected.get("age_context"):
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
            "instructions": "Ask about the age of the person who will use the room so we can recommend age-appropriate furniture."
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
            "examples": ["The bookshelf stays, everything else goes", "Keep the desk and chair", "Start fresh, replace everything", "Just the storage unit stays"]
        }

    # Phase 3: Request room photos (for redesigns after constraints)
    if collected.get("room_purpose") == "redesign" and collected.get("constraints") and not collected.get("room_photos_analyzed"):
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
                    "Include any furniture you mentioned keeping"
                ],
                "interaction_mode": "camera_upload",
                "phase": "phase_3_photo_analysis"
            }
        }

    if not collected["style_preferences"]:
        state_manager.update_session(session_id, stage="stage_2_style_discovery")
        logger.info(f"[HOME DECOR] Awaiting style preferences from customer")

        # Build UI data for Phase 1 style selection with room-specific images
        # Convert room_type to match our image naming convention
        # Map room names to image filenames
        room_image_map = {
            "living room": "living_room",
            "bedroom": "bedroom",
            "office": "home_office",
            "home office": "home_office",
            "dining room": "dining_room",
            "kitchen": "kitchen",
            "bathroom": "bathroom",
            "entryway": "living_room"  # Fallback to living_room for entryway
        }

        room_key = room_image_map.get(collected["room_type"].lower(), "living_room")

        style_options_ui = [
            {"id": "modern", "label": "Modern", "description": "Clean lines, minimal ornamentation", "image_url": f"./assets/{room_key}_modern.jpg"},
            {"id": "minimalist", "label": "Minimalist", "description": "Less is more, simple & functional", "image_url": f"./assets/{room_key}_minimalist.jpg"},
            {"id": "bohemian", "label": "Bohemian", "description": "Eclectic mix, rich colors & patterns", "image_url": f"./assets/{room_key}_bohemian.jpg"},
            {"id": "coastal", "label": "Coastal", "description": "Light & airy, nautical themes", "image_url": f"./assets/{room_key}_coastal.jpg"},
            {"id": "industrial", "label": "Industrial", "description": "Exposed materials, urban loft", "image_url": f"./assets/{room_key}_industrial.jpg"},
            {"id": "scandinavian", "label": "Scandinavian", "description": "Natural materials, hygge coziness", "image_url": f"./assets/{room_key}_scandinavian.jpg"},
            {"id": "traditional", "label": "Traditional", "description": "Classic elegance, timeless pieces", "image_url": f"./assets/{room_key}_traditional.jpg"},
            {"id": "rustic", "label": "Rustic", "description": "Natural materials, country charm", "image_url": f"./assets/{room_key}_rustic.jpg"}
        ]

        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_2_style_discovery",
            "missing_info": "style_preferences",
            "question": "What decor style resonates with you? You can choose multiple!",
            "options": ["modern", "minimalist", "bohemian", "coastal", "industrial", "scandinavian", "traditional", "rustic"],
            "message": f"Great! Now let's explore styles for your {collected['room_type']}.",
            # NEW: UI display data for Phase 1 style selection
            "ui_data": {
                "display_type": "style_selector",
                "title": f"Perfect! Now, what style speaks to you for your {collected['room_type']}?",
                "subtitle": "Choose one or more styles that resonate with you",
                "style_options": style_options_ui,
                "interaction_mode": "multi_select",
                "phase": "phase_1_style_discovery"
            }
        }

    # If we're here but don't have colors, ask about them (optional)
    if not collected["color_preferences"]:
        state_manager.update_session(session_id, stage="stage_3_color_preferences")
        logger.info(f"[HOME DECOR] Awaiting color preferences (optional) from customer")

        # Build UI data for Phase 1 color selection
        color_options_ui = [
            {"id": "blue", "label": "Blue", "hex": "#4A90E2", "description": "Calming & serene"},
            {"id": "white", "label": "White", "hex": "#FFFFFF", "description": "Clean & bright"},
            {"id": "gray", "label": "Gray", "hex": "#9B9B9B", "description": "Neutral & modern"},
            {"id": "beige", "label": "Beige", "hex": "#D4C5B9", "description": "Warm & inviting"},
            {"id": "black", "label": "Black", "hex": "#000000", "description": "Bold & dramatic"},
            {"id": "gold", "label": "Gold", "hex": "#D4AF37", "description": "Luxe & elegant"},
            {"id": "green", "label": "Green", "hex": "#7ED321", "description": "Fresh & natural"},
            {"id": "pink", "label": "Pink", "hex": "#F8B4D8", "description": "Soft & playful"},
            {"id": "brown", "label": "Brown", "hex": "#8B5A3C", "description": "Earthy & grounded"},
            {"id": "cream", "label": "Cream", "hex": "#F5E6D3", "description": "Soft & cozy"}
        ]

        return {
            "status": "awaiting_input",
            "session_id": session_id,
            "stage": "stage_3_color_preferences",
            "missing_info": "color_preferences",
            "question": "Are there any specific colors you'd like to incorporate? (optional)",
            "examples": ["blue and white", "warm earth tones", "black and gold", "neutral palette", "no preference"],
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
                "skip_allowed": True
            }
        }

    return {
        "status": "error",
        "message": "Unable to determine next step in consultation."
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
    logger.info(f"[ORDER HISTORY] Retrieving orders for customer {customer_id}, category filter: {product_category}")

    # MOCK ORDER HISTORY - In production, this would query order database
    # For demo, simulate past furniture orders
    mock_orders = []

    # Example: Customer bought furniture 4 years ago
    if customer_id:
        # Simulate order from 4 years ago with children's furniture
        mock_orders.append({
            "order_id": f"ORD-{random.randint(10000, 99999)}",
            "order_date": (datetime.now() - timedelta(days=4*365)).strftime("%Y-%m-%d"),
            "products": [
                {
                    "product_id": "BED-TODDLER-HOUSE",
                    "name": "Birch House Bed - Toddler",
                    "category": "Furniture",
                    "subcategory": "Children's Beds",
                    "price": 299.00,
                    "quantity": 1,
                    "age_appropriate": ["toddler"],
                    "years_ago": 4
                },
                {
                    "product_id": "BOOKSHELF-CUBE-MODULAR",
                    "name": "Modular Cube Bookshelf System 3x3",
                    "category": "Furniture",
                    "subcategory": "Bookcases",
                    "price": 199.00,
                    "quantity": 1,
                    "years_ago": 4
                }
            ],
            "total": 498.00
        })

    # Filter by category if specified
    filtered_orders = []
    for order in mock_orders:
        if product_category:
            filtered_products = [p for p in order["products"] if p.get("category") == product_category]
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
            identified_products.append({
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "purchase_date": order["order_date"],
                "years_since_purchase": product.get("years_ago", 0),
                "age_appropriate": product.get("age_appropriate", [])
            })

    logger.info(f"[ORDER HISTORY] Found {len(filtered_orders)} orders with {len(identified_products)} products")

    return {
        "status": "success",
        "customer_id": customer_id,
        "order_count": len(filtered_orders),
        "orders": filtered_orders,
        "identified_products": identified_products,
        "message": f"Found {len(identified_products)} products from past orders" + (f" in category: {product_category}" if product_category else "")
    }


def analyze_room_with_history(
    image_data: str,
    customer_id: str,
    session_id: str,
    age_context: Optional[str] = None,
    room_type: Optional[str] = None,
) -> dict:
    """
    Analyzes room photos and cross-references with customer order history.
    This is Phase 3 of the home decor journey: photo analysis + order history.

    Args:
        image_data: Base64 encoded image data of the room.
        customer_id: The ID of the customer.
        session_id: The consultation session ID.
        age_context: Optional age context (e.g., "school-age").
        room_type: Optional room type hint.

    Returns:
        A dictionary with room analysis, order history matches, and next steps.
    """
    logger.info(f"[PHASE 3] Analyzing room with history for customer {customer_id}, session {session_id}")

    # First, analyze the room photo
    room_analysis_result = analyze_room_for_decor(
        image_data=image_data,
        customer_id=customer_id,
        room_type_hint=room_type
    )

    if room_analysis_result.get("status") != "success":
        return room_analysis_result

    # Get customer's furniture order history
    order_history = get_customer_order_history(
        customer_id=customer_id,
        product_category="Furniture"
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
            if any(keyword in product_name_lower for keyword in furniture.lower().split()):
                matched_furniture.append({
                    **product,
                    "identified_in_photo": True,
                    "still_appropriate": age_context not in product.get("age_appropriate", []) if age_context else False
                })
                break

    # Check if furniture has outgrown its purpose
    outgrown_furniture = [f for f in matched_furniture if not f.get("still_appropriate", True)]

    # Update session state to mark photos as analyzed
    state_manager = get_state_manager()
    state_manager.update_session(
        session_id=session_id,
        room_photos_analyzed=True,
        photo_analysis=room_analysis,
        order_history=identified_products
    )

    logger.info(f"[PHASE 3] Matched {len(matched_furniture)} furniture items from order history")
    logger.info(f"[PHASE 3] {len(outgrown_furniture)} items no longer age-appropriate")

    return {
        "status": "success",
        "message": f"I can see your {room_analysis.get('room_type', 'room')}! I've identified furniture from your past orders.",
        "room_analysis": room_analysis,
        "order_history_matches": matched_furniture,
        "outgrown_furniture": outgrown_furniture,
        "next_step": "interact_with_child",
        "instructions": f"The room analysis is complete. I've identified the {', '.join([f['name'] for f in matched_furniture])} from {matched_furniture[0]['years_since_purchase']} years ago. Now, address the child directly: Ask '{age_context if age_context else 'them'}' what they like doing most in their room. Be warm and encouraging - speak directly to the child, not the parent."
    }


def analyze_room_photos_batch(
    customer_id: str,
    session_id: str,
    image_data_list: List[str],
    age_context: Optional[str] = None,
    room_type: Optional[str] = None,
) -> dict:
    """
    Analyzes multiple room photos at once and cross-references with order history.
    This handles batch photo uploads from the UI.

    Args:
        customer_id: The ID of the customer.
        session_id: The consultation session ID.
        image_data_list: List of base64 encoded image data.
        age_context: Optional age context.
        room_type: Optional room type hint.

    Returns:
        Combined analysis from all photos.
    """
    logger.info(f"[BATCH PHOTOS] Analyzing {len(image_data_list)} photos for customer {customer_id}, session {session_id}")

    if not image_data_list or len(image_data_list) == 0:
        return {
            "status": "error",
            "message": "No photos provided for analysis."
        }

    # Analyze the first photo in detail (main view)
    main_photo_result = analyze_room_with_history(
        image_data=image_data_list[0],
        customer_id=customer_id,
        session_id=session_id,
        age_context=age_context,
        room_type=room_type
    )

    # For additional photos, do quick analysis to supplement the main view
    additional_insights = []
    if len(image_data_list) > 1:
        logger.info(f"[BATCH PHOTOS] Analyzing {len(image_data_list) - 1} additional photos")
        for i, image_data in enumerate(image_data_list[1:], start=2):
            try:
                additional_result = analyze_room_for_decor(
                    image_data=image_data,
                    customer_id=customer_id,
                    room_type_hint=room_type
                )
                if additional_result.get("status") == "success":
                    additional_insights.append({
                        "photo_number": i,
                        "analysis": additional_result.get("analysis", {})
                    })
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
        "message": combined_message
    }


def analyze_room_for_decor(
    image_data: Optional[str] = None,
    customer_id: Optional[str] = None,
    room_type_hint: Optional[str] = None,
) -> dict:
    """
    Analyzes a room photo using Gemini Vision API to provide home decor recommendations.

    Args:
        image_data: Optional base64 encoded image data of the room (data URI format or raw base64).
        customer_id: Optional customer ID for context.
        room_type_hint: Optional hint about the room type (e.g., "living room", "bedroom").

    Returns:
        A dictionary containing room analysis and decor recommendations.
    """
    logger.info(
        f"Analyzing room photo for customer {customer_id}. Room hint: {room_type_hint}"
    )

    if not image_data:
        logger.warning("No image data provided to analyze_room_for_decor tool.")
        return {
            "status": "error",
            "message": "This tool requires an image of the room to analyze. Please provide a photo of your space.",
            "analysis": None,
            "recommendations": [],
        }

    # Extract base64 data if in data URI format
    if image_data.startswith("data:"):
        image_base64 = (
            image_data.split(",")[1] if "," in image_data else image_data
        )
    else:
        image_base64 = image_data

    # Check for minimal image data
    if len(image_base64) < 1000:
        return {
            "status": "failure",
            "message": "The image quality is too low for accurate analysis. Please provide a clearer photo.",
            "analysis": None,
            "recommendations": [],
        }

    # Use Gemini Vision API for room analysis
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
        vision_model = (
            "gemini-2.0-flash-exp"
            if "flash" in RECOMMENDATION_MODEL.lower()
            else "gemini-1.5-pro"
        )

        logger.info(f"Using {vision_model} for room analysis")

        response = client.models.generate_content(
            model=vision_model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes, mime_type="image/jpeg"
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1000,
            ),
        )

        # Parse the JSON response
        import json
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

        logger.info(f"Room analysis completed: {room_analysis.get('room_type', 'Unknown')} - {room_analysis.get('current_style', 'Unknown')}")

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
                    if room_type and any(room_type.lower() in r.lower() for r in compatible_rooms):
                        matching_products.append({
                            "product_id": product["product_id"],
                            "name": product["name"],
                            "category": product.get("subcategory", "Home Decor"),
                            "price": product["price"],
                            "why_recommended": f"Complements your {room_analysis.get('current_style', 'existing')} style"
                        })

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
