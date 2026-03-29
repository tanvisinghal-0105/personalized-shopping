import random
import time
from typing import Optional, List, Dict, Any
import uuid
import requests
from ...logger import logger
from datetime import datetime, timedelta

from google.cloud import firestore
from .context import RetailContext
from config.config import RECOMMENDATION_MODEL

# Initialize Firestore client with error handling
db = None
CUSTOMER_CART_INFO = {
    'cart_id': 'CART-112233', # Use example ID for consistency
    'items': {
        'GENERIC-PIXEL-CASE': {'sku': '1122334', 'name': 'Generic Google Pixel Case', 'quantity': 1, 'price': 19}},
    'subtotal': 19,
    'last_updated': '2025-04-23 11:05:00' # Use example timestamp
}

try:
    logger.info("Connecting to Firestore...")
    db = firestore.Client()
    logger.info("Connected to Firestore")

    # Carts will be created dynamically per customer when needed
    # No need for hardcoded cart initialization
    logger.info("Firestore ready - carts will be created per customer dynamically")
except Exception as e:
    logger.warning(f"Firestore initialization failed: {e}. Running without Firestore support.")
    db = None


# Use the product catalog from context.py to ensure consistency
# Convert list of dicts to dict keyed by product_id for easy lookup
PRODUCT_CATALOG = {
    product['product_id']: {
        'name': product['name'],
        'price': product['price'],
        'sku': product['sku']
    }
    for product in RetailContext.PRODUCT_CATALOG
}

def send_call_companion_link(phone_number: str) -> str:
    """Sends a link to the user's phone number to connect the call with the companion app."""
    logger.info(f"Sending call companion link to {phone_number}...")
    return {"status": "success", "message": f"Link sent to {phone_number}"}

def approve_discount(type: str, value: float, reason: str, product_id: str = "") -> dict:
    """Approves a flat rate or percentage discount for a product or service, based on predefined rules."""
    logger.info(f"Attempting to approve discount: type={type}, value={value}, reason={reason}, product_id={product_id}")
    logger.info("INSIDE TOOL CALL")
    # Example: Apply price match approval from example.py logic
    if product_id == 'GOOGLE-PIXEL9PRO-CASE' and type == 'price_match' and value == 59.99:
         return {"status": "approved", "message": f"Price match to {value} EUR approved for {product_id}."}
    # Example: Apply bundle discount from example.py
    # if product_id == 'PLUSGARANTIE-PIXEL' and type == 'percentage' and value == 10:
    #      return {"status": "approved", "message": f"Discount of {value}{'%' if type == 'percentage' else 'EUR'} approved for {product_id}."}
    # Fallback generic approval
    return {"status": "approved", "message": f"Discount of {value}{'%' if type == 'percentage' else 'EUR'} approved."}

def sync_ask_for_approval(type: str, value: float, reason: str, product_id: str = "") -> str:
    """Asks a manager for approval synchronously (waits for a response)."""
    logger.info(f"Requesting sync manager approval for discount: type={type}, value={value}, reason={reason}, product_id={product_id}")
    url = "https://escalation-handler-243114688021.us-central1.run.app/request"
    payload = {
        "menuId": 36,
        "menuLang": "en",
        "customer_id": "GR-1234-1234",
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
            "error": "Sorry but I've had some trouble getting hold of my manager"
            },
        "escalationHost": "chat-escalation-243114688021.us-central1.run.app"
        }

    if db is not None:
        try:
            db.collection('customers').document("GR-1234-1234").set(payload)
        except Exception as e:
            logger.warning(f"Failed to save to Firestore: {e}")

    logger.info("Waiting for manager approval...")

    # poll for approval status. max of 5 minutes with 1 second intervals
    for i in range(300):
        if db is not None:
            try:
                doc = db.collection('customers').document("GR-1234-1234").get()
                if doc.exists:
                    if doc.to_dict()['approval_status'] == "approved":
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
    headers = {'Content-Type': 'application/json'}
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

def identify_phone_from_camera_feed(image_data: Optional[str] = None, customer_id: Optional[str] = None) -> dict:
    """
    Identifies a phone model from a camera feed.
    Currently mocks identification but acknowledges received image data.
    
    Args:
        image_data: Optional base64 encoded image data from the camera feed.
        customer_id: Optional customer ID for context or fetching session-specific data.
                     (Currently used for logging in this example).

    Returns:
        A dictionary containing the identified phone model and a message.
    """
    logger.info(f"Attempting to identify phone from camera feed. Customer ID: {customer_id}")

    # # In a real scenario, you would process the image_data here.
    # # For now, we mock the response.
    # return {
    #     "status": "success",
    #     "identified_phone_model": "Pixel 9 Pro",
    #     "message": "Phone identified as Pixel 9 Pro from the camera feed."
    # }
    if image_data:
        logger.info(f"Image data received (length: {len(image_data)} characters). Simulating processing...")
        identified_model = "Pixel 9 Pro" # Default mock
        message = f"Based on the camera feed, this looks like a {identified_model}."

        if "EXAMPLE_IPHONE_MARKER" in image_data:
            identified_model = "iPhone 15 Pro"
            message = f"The camera feed suggests this might be an {identified_model}."
        elif len(image_data) < 1000:
            identified_model = "Unknown Device (low quality image)"
            message = "The image data from the camera feed was minimal, making identification difficult."
            return {
                "status": "failure",
                "identified_phone_model": identified_model,
                "message": message,
                "image_data_processed": True
            }
        
        logger.info(f"Simulated identification result: {identified_model}")
        return {
            "status": "success",
            "identified_phone_model": identified_model,
            "message": message,
            "image_data_processed": True
        }
    else:
        logger.warning("No image data was provided to the identify_phone_from_camera_feed tool.")

        return {
            "status": "success",
            "identified_phone_model": "Pixel 9 Pro (default/no image provided)",
            "message": "Could not process specific image as none was provided to the tool. Assuming Pixel 9 Pro based on general context or default mock.",
            "image_data_processed": False
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
            mock_cart = db.collection('carts').document(customer_id).get()
            if mock_cart.exists:
                mock_cart = mock_cart.to_dict()
                # Convert items from dict to array if needed
                if mock_cart and 'items' in mock_cart and isinstance(mock_cart['items'], dict):
                    mock_cart['items'] = [
                        {
                            'product_id': product_id,
                            'name': data['name'],
                            'price': data['price'],
                            'sku': data['sku'],
                            'quantity': data['quantity']
                        } for product_id, data in mock_cart['items'].items()
                    ]
            else:
                # Cart doesn't exist yet, initialize empty cart
                logger.info(f"No cart found for customer {customer_id}, initializing empty cart")
                mock_cart = {
                    "cart_id": f"CART-{customer_id[-6:]}",
                    "items": [],
                    "subtotal": 0.0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.warning(f"Failed to access Firestore: {e}. Using empty cart.")
            mock_cart = {
                "cart_id": f"CART-{customer_id[-6:]}",
                "items": [],
                "subtotal": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    else:
        # No Firestore connection, return empty cart
        logger.info("No Firestore connection, returning empty cart")
        mock_cart = {
            "cart_id": f"CART-{customer_id[-6:]}",
            "items": [],
            "subtotal": 0.0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    return mock_cart


def modify_cart(customer_id: str, items_to_add: Optional[List[Dict[str, Any]]] = None, items_to_remove: Optional[List[str]] = None, has_manager_approval: bool = False) -> dict:
    """Modifies the user's shopping cart by adding and/or removing items."""
    logger.info(f"Modifying cart for customer ID: {customer_id}")
    items_added_flag = False
    items_removed_flag = False

    # --- MOCK BACKEND CART STATE ---
    # Use dynamic customer_id to fetch cart
    if db is not None:
        try:
            mock_cart = db.collection('carts').document(customer_id).get()
            if mock_cart.exists:
                current_mock_backend_cart = mock_cart.to_dict()
                # Ensure items is a dict for manipulation
                if 'items' not in current_mock_backend_cart or not isinstance(current_mock_backend_cart['items'], dict):
                    current_mock_backend_cart['items'] = {}
            else:
                # Cart doesn't exist yet, initialize empty cart for this customer
                logger.info(f"No cart found for customer {customer_id}, initializing empty cart")
                current_mock_backend_cart = {
                    'cart_id': f"CART-{customer_id[-6:]}",
                    'items': {},
                    'subtotal': 0.0,
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.warning(f"Failed to access Firestore: {e}. Using empty cart.")
            current_mock_backend_cart = {
                'cart_id': f"CART-{customer_id[-6:]}",
                'items': {},
                'subtotal': 0.0,
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    else:
        # No Firestore connection, use empty cart
        logger.info("No Firestore connection, using empty cart")
        current_mock_backend_cart = {
            'cart_id': f"CART-{customer_id[-6:]}",
            'items': {},
            'subtotal': 0.0,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


    if items_to_add:
        logger.info(f"Adding items: {items_to_add}")
        # Validate all product IDs BEFORE adding any items
        invalid_products = []
        for item in items_to_add:
            prod_id = item.get('product_id')
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
                    if any(word in valid_id.lower() for word in invalid_lower.split('-')[:2]):
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
                "updated_cart": access_cart_information(customer_id)
            }

        # All products valid, proceed with adding
        for item in items_to_add:
            prod_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            if prod_id in current_mock_backend_cart['items']:
                current_mock_backend_cart['items'][prod_id]['quantity'] += quantity
            else:
                current_mock_backend_cart['items'][prod_id] = {
                    'name': PRODUCT_CATALOG[prod_id]['name'],
                    'price': PRODUCT_CATALOG[prod_id]['price'],
                    'sku': PRODUCT_CATALOG[prod_id]['sku'],
                    'quantity': quantity
                }
            items_added_flag = True


    if items_to_remove:
        logger.info(f"Removing items: {items_to_remove}")
        # Mock removing items (expects list of product_ids)
        for prod_id in items_to_remove:
            if isinstance(prod_id, dict):
                prod_id = prod_id['product_id']
            if prod_id in current_mock_backend_cart['items']:
                del current_mock_backend_cart['items'][prod_id]
                items_removed_flag = True
            else:
                 logger.warning(f"Product ID {prod_id} not found in mock cart for removal.")


    # MOCK API RESPONSE - Construct based on the simulated backend cart
    if items_added_flag or items_removed_flag or has_manager_approval:
        # Recalculate subtotal for the mock cart
        new_subtotal = sum(item['price'] * item['quantity'] for item in current_mock_backend_cart['items'].values())
        # Apply price match adjustment specifically for OtterBox if present (as done in example checkout)
        if 'GOOGLE-PIXEL9PRO-CASE' in current_mock_backend_cart['items'] and has_manager_approval:
             original_price = PRODUCT_CATALOG['GOOGLE-PIXEL9PRO-CASE']['price']
             matched_price = 45 # From example
             price_diff = original_price - matched_price
             new_subtotal -= price_diff * current_mock_backend_cart['items']['GOOGLE-PIXEL9PRO-CASE']['quantity']
             # Reflect matched price in item data for clarity
             current_mock_backend_cart['items']['GOOGLE-PIXEL9PRO-CASE']['price'] = matched_price


        # Convert items dict to array for client compatibility
        updated_cart_list = [
            {
                'product_id': product_id,
                'name': data['name'],
                'price': data['price'],
                'sku': data['sku'],
                'quantity': data['quantity']
            } for product_id, data in current_mock_backend_cart['items'].items()
        ]

        # Construct the final updated cart structure
        final_updated_cart = {
            'cart_id': current_mock_backend_cart['cart_id'],
            'items': updated_cart_list,
            'subtotal': round(new_subtotal, 2),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Update timestamp
        }

        # Update the mock backend cart state using dynamic customer_id
        if db is not None:
            try:
                db.collection('carts').document(customer_id).set(final_updated_cart)
                logger.info(f"Cart updated in Firestore for customer {customer_id}")
            except Exception as e:
                logger.warning(f"Failed to update cart in Firestore: {e}")

        return {
            "status": "success",
            "message": "Cart updated successfully.",
            "items_added": items_added_flag,
            "items_removed": items_removed_flag,
            "updated_cart": final_updated_cart # Return the new state of the cart
        }
    else:
        # If no changes, fetch the current state using access_cart_information's logic
        current_cart_state = access_cart_information(customer_id)
        return {
            "status": "no_change",
            "message": "No changes were requested for the cart.",
            "items_added": False,
            "items_removed": False,
            "updated_cart": current_cart_state
        }


def get_product_recommendations(interest: str = "", customer_id: str = "", current_product_id: str = "") -> dict:
    """Provides product recommendations based on interests, purchase history, or related items using Gemini AI."""
    logger.info(f"Getting product recommendations for interest: {interest}, customer: {customer_id}, related_to: {current_product_id}")

    if not interest:
        # Return random products if no interest specified
        fallback_recommendations = []
        for product in RetailContext.PRODUCT_CATALOG:
            if product['product_id'] != current_product_id and product.get('in_stock', True):
                fallback_recommendations.append({
                    "product_id": product['product_id'],
                    "name": product['name'],
                    "description": f"{product['category']} - €{product['price']:.2f}"
                })
        random.shuffle(fallback_recommendations)
        return {"recommendations": fallback_recommendations[:3]}

    # Use Gemini to intelligently match products
    try:
        from google import genai
        from google.genai import types

        client = genai.Client()

        # Build a concise product catalog for Gemini
        catalog_text = "Available products:\n"
        for product in RetailContext.PRODUCT_CATALOG:
            if product['product_id'] != current_product_id:
                catalog_text += f"- {product['product_id']}: {product['name']} ({product['category']}) - €{product['price']:.2f}\n"

        prompt = f"""You are a product recommendation expert. Based on the customer's interest, recommend the 3 most relevant products from the catalog.

Customer interest: "{interest}"

{catalog_text}

Return ONLY a JSON array with exactly 3 product IDs, nothing else. Format: ["PRODUCT-ID-1", "PRODUCT-ID-2", "PRODUCT-ID-3"]

Choose products that best match the customer's interest. For example:
- "sneakers" or "shoes" → Footwear products (Nike, Adidas, etc.)
- "laptop" or "computer" → Laptop products
- "TV" or "television" → TV products
- "phone" or "smartphone" → Phone products"""

        response = client.models.generate_content(
            model=RECOMMENDATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=200
            )
        )

        # Parse the response to get product IDs
        import json
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        product_ids = json.loads(response_text)

        # Build recommendations from the matched product IDs
        recommendations = []
        for pid in product_ids[:3]:
            for product in RetailContext.PRODUCT_CATALOG:
                if product['product_id'] == pid:
                    recommendations.append({
                        "product_id": product['product_id'],
                        "name": product['name'],
                        "description": f"{product['category']} - €{product['price']:.2f}"
                    })
                    break

        logger.info(f"Gemini recommended {len(recommendations)} products for '{interest}'")

        if recommendations:
            return {"recommendations": recommendations[:3]}

    except Exception as e:
        logger.error(f"Error using Gemini for recommendations: {e}")
        # Fall through to fallback logic

    # Fallback: return random popular products if Gemini fails
    fallback_recommendations = []
    for product in RetailContext.PRODUCT_CATALOG:
        if product['product_id'] != current_product_id and product.get('in_stock', True):
            fallback_recommendations.append({
                "product_id": product['product_id'],
                "name": product['name'],
                "description": f"{product['category']} - €{product['price']:.2f}"
            })

    random.shuffle(fallback_recommendations)
    return {"recommendations": fallback_recommendations[:3]}


def check_product_availability(product_id: str, store_id: str = "GR-ONLINE", quantity: int = 1) -> dict:
    """Checks the availability of a product at a specified store or for online order."""
    logger.info(f"Checking availability for product ID: {product_id}, quantity: {quantity} at store/channel: {store_id}")
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
    elif product_id == "PLUSGARANTIE-PIXEL": # Service/Digital product
        available = True
        stock_quantity = 999 # Essentially unlimited
        location = "GR-ONLINE / In Store"
    elif product_id == "GOOGLE-30W-POWERADAPTER":
        available = True
        stock_quantity = random.randint(15, 60)
        location = "GR-ONLINE / GR-BERLIN" # Available both
    elif product_id == "PIXEL-6-128GB-BLK":
        available = random.choice([True, True, False]) # Simulate varying stock
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
    else: # Default for unlisted products
        available = random.choice([True, False])
        stock_quantity = random.randint(0, 15) if available else 0
        location = store_id if store_id else "GR-ONLINE"

    final_availability = available and stock_quantity >= quantity
    return {"product_id": product_id, "requested_quantity": quantity, "available": final_availability, "available_quantity": stock_quantity, "location": location}


def schedule_service_appointment(customer_id: str, service_type: str, date: str, time_slot: str, store_id: str = "GR-BERLIN", product_id: Optional[str] = None, issue_description: Optional[str] = None) -> dict:
    """Schedules a service appointment (e.g., repair drop-off, consultation)."""
    logger.info(f"Scheduling {service_type} for customer {customer_id} at {store_id} on {date} at {time_slot}.")
    if product_id: logger.info(f"Related Product: {product_id}")
    if issue_description: logger.info(f"Details: {issue_description}")

    # MOCK API RESPONSE - Replace with actual scheduling system API call
    appointment_id = f"APP-{random.randint(10000, 99999)}"
    # Extract start time for confirmation string, handle different formats
    try:
        start_time = time_slot.split('-')[0].strip()
        confirmation_datetime_str = f"{date} {start_time}:00"
    except:
        confirmation_datetime_str = f"{date} {time_slot}" # Fallback if format is unexpected

    return {
        "status": "success",
        "appointment_id": appointment_id,
        "service_type": service_type,
        "date": date,
        "time": time_slot,
        "confirmation_datetime": confirmation_datetime_str,
        "store_id": store_id
    }

def get_available_service_times(date: str, service_type: str, store_id: str = "GR-BERLIN", duration_minutes: int = 60) -> list:
    """Retrieves available time slots for a specific service type and date."""
    # Note: duration_minutes parameter added to match prompt, but not used in mock logic yet.
    logger.info(f"Retrieving available {service_type} times for {date} at {store_id} (duration: {duration_minutes} mins)")
    # MOCK API RESPONSE - Replace with actual scheduling system API call
    if date >= datetime.now().strftime("%Y-%m-%d"):
        return ["09:00-10:00", "10:00-11:00", "14:00-15:00", "16:00-17:00"]
    else:
        return [] 

def send_product_information(customer_id: str, product_id: str, info_type: str = "manual", delivery_method: str = "email") -> dict:
    """Sends product information (e.g., manual, warranty details, order summary) to the customer."""
    logger.info(f"Sending {info_type} for product {product_id} to customer: {customer_id} via {delivery_method}")
    # MOCK API RESPONSE - Replace with actual document/email sending logic
    if info_type == "order summary and pickup details":
         message = f"Order summary and pickup details for order related to {product_id} sent via {delivery_method}."
    else:
         message = f"Product information ({info_type}) for {product_id} sent via {delivery_method}."

    return {"status": "success", "message": message}

def generate_qr_code(customer_id: str, discount_value: float, discount_type: str = "percentage", expiration_days: int = 30, usage_limit: int = 1, description: str = "Loyalty Discount") -> dict:
    """Generates a QR code for a discount or offer."""
    logger.info(f"Generating QR code for customer: {customer_id} - {discount_value}{'%' if discount_type == 'percentage' else 'EUR'} discount. Desc: {description}")
    # MOCK API RESPONSE - Match example.py output format
    expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime("%Y-%m-%d")
    # Construct payload similar to example
    qr_code_payload = f"MOCK_QR_CODE_FOR_CUSTOMER:{customer_id};DISCOUNT:{discount_value};TYPE:{discount_type};EXP:{expiration_date};DESC:{description.replace(' ','_')};LIMIT:{usage_limit}"

    return {
        "status": "success",
        "qr_code_data": qr_code_payload,
        "description": description,
        "expiration_date": expiration_date,
        "usage_limit": usage_limit
    }


def process_exchange_request(customer_id: str, original_order_id: str, original_product_id: str, reason: str, desired_product_id: Optional[str] = None) -> dict:
    """Processes an exchange request for a product."""
    # Made desired_product_id Optional to match prompt
    logger.info(f"Processing exchange for customer {customer_id}, order {original_order_id}, product {original_product_id}. Reason: {reason}. New Product: {desired_product_id}")
    # Mock exchange processing - Replace with actual order management/RMA system API call
    exchange_id = f"EXCH-{random.randint(1000, 9999)}"
    policy_met = random.choice([True, False, True]) # More likely to meet policy for mock

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
            "price_difference": round(price_difference, 2)
        }
    else:
        return {
            "status": "rejected",
            "exchange_id": None,
            "message": "Exchange request could not be approved based on the return policy (e.g., outside return window, condition issues, non-exchangeable item).",
            "price_difference": None
        }

def get_trade_in_value(product_category: str, brand: str, model: str, condition: str, storage: Optional[str] = None) -> dict:
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
    logger.info(f"Calculating trade-in value for: Category='{product_category}', Brand='{brand}', Model='{model}', Condition='{condition}', Storage='{storage}'")

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
        elif "pixel tablet" in model.lower(): # Example for tablet
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
            "currency": currency
        }

    # Adjust value based on condition
    condition_multiplier = 1.0
    if condition.lower() == "like new":
        condition_multiplier = 1.0
    elif condition.lower() == "good":
        condition_multiplier = 0.8
    elif condition.lower() == "fair":
        condition_multiplier = 0.6
    elif condition.lower() == "damaged": # e.g., cracked screen but functional
        condition_multiplier = 0.3
    else: # unknown condition
        condition_multiplier = 0.5

    estimated_value = base_value * condition_multiplier

    # Provide a range
    estimated_value_min = max(0, estimated_value * 0.85) # e.g., 85% of estimate
    estimated_value_max = estimated_value * 1.10       # e.g., 110% of estimate

    # Round to sensible values
    estimated_value_min = round(estimated_value_min / 5) * 5 # Round to nearest 5 EUR
    estimated_value_max = round(estimated_value_max / 5) * 5

    if estimated_value_max > 0:
        status = "success"
        message = f"Trade-in value estimated between {estimated_value_min:.2f} and {estimated_value_max:.2f} {currency}. Final value depends on inspection."
    else:
        status = "success" # Still a success in terms of processing, but value is zero
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
            "storage": storage
        }
    }


def lookup_warranty_details(product_id: str) -> dict:
    """
    Looks up warranty details for a given product ID.
    
    Args:
        product_id: The ID of the product to look up warranty details for (e.g. Pixel 9 Pro, Pixel 9, etc.).

    Returns:
        A dictionary with the estimated trade-in value and related information.
    """

    if "pixel" in product_id.lower() and not "plusgarantie" in product_id.lower():
        logger.info(f"Lookup warranty details for Pixel device: {product_id}")
        return {
            "status": "success",
            "warranty_details": {
                "warranty_type": "standard",
                "warranty_period": "1 year",
                "coverage_summary": "Covers manufacturing defects for one year from purchase date. Does not cover accidental damage like drops or spills."
            },
            "premium_warranty_details": {
                "warranty_type": "premium",
                "product_id": "PLUSGARANTIE-PIXEL",
                "information": "leverage product id 'PLUSGARANTIE-PIXEL' to retrieve premium warranty details"
            }
        }

    elif "plusgarantie" in product_id.lower() and "pixel" in product_id.lower():
        logger.info(f"Lookup warranty details for PlusGarantie Pixel device: {product_id}")
        return {
            "status": "success",
            "warranty_details": {
                "warranty_type": "premium",
                "warranty_period": "1 year",
                "coverage_summary": "Covers accidental damage like drops or spills for one year from purchase date."
            }
        }
    else:
        logger.info(f"Lookup warranty details for default device: {product_id}")
        return {
            "status": "success",
            "warranty_details": {
                "warranty_type": "standard",
                "warranty_period": "1 year",
                "coverage_summary": "Covers manufacturing defects for one year from purchase date. Does not cover accidental damage like drops or spills."
            }
        }