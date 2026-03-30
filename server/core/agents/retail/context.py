from datetime import datetime
import random
from config.config import LANGUAGE

DEFAULT_LANGUAGE = LANGUAGE or "English (United Kingdom)"

class RetailContext:
    # Product Catalog - Available products in store (Latest Models 2024-2025)
    PRODUCT_CATALOG = [
        # Electronics - Smartphones & Tablets (Latest 2024-2025 Models)
        # Apple iPhone 16 Series - Latest
        {"product_id": "APPLE-IPHONE-16", "sku": "1000001", "name": "Apple iPhone 16 128GB", "category": "Smartphones", "price": 999.00, "in_stock": True},
        {"product_id": "APPLE-IPHONE-16-PLUS", "sku": "1000002", "name": "Apple iPhone 16 Plus 256GB", "category": "Smartphones", "price": 1099.00, "in_stock": True},
        {"product_id": "APPLE-IPHONE-16-PRO", "sku": "1000003", "name": "Apple iPhone 16 Pro 256GB", "category": "Smartphones", "price": 1199.00, "in_stock": True},
        {"product_id": "APPLE-IPHONE-16-PRO-MAX", "sku": "1000004", "name": "Apple iPhone 16 Pro Max 512GB", "category": "Smartphones", "price": 1399.00, "in_stock": True},

        # Google Pixel 9 Series - Latest
        {"product_id": "GOOGLE-PIXEL-9", "sku": "1000005", "name": "Google Pixel 9 128GB", "category": "Smartphones", "price": 799.00, "in_stock": True},
        {"product_id": "GOOGLE-PIXEL-9-PRO", "sku": "1000006", "name": "Google Pixel 9 Pro 256GB", "category": "Smartphones", "price": 899.00, "in_stock": True},
        {"product_id": "GOOGLE-PIXEL-9-PRO-XL", "sku": "1000007", "name": "Google Pixel 9 Pro XL 512GB", "category": "Smartphones", "price": 1099.00, "in_stock": True},
        {"product_id": "GOOGLE-PIXEL-9-PRO-FOLD", "sku": "1000008", "name": "Google Pixel 9 Pro Fold", "category": "Smartphones", "price": 1799.00, "in_stock": True},

        # Samsung Galaxy S24 Series - Latest
        {"product_id": "SAMSUNG-GALAXY-S24", "sku": "1000009", "name": "Samsung Galaxy S24 256GB", "category": "Smartphones", "price": 899.00, "in_stock": True},
        {"product_id": "SAMSUNG-GALAXY-S24-PLUS", "sku": "1000010", "name": "Samsung Galaxy S24 Plus 512GB", "category": "Smartphones", "price": 1099.00, "in_stock": True},
        {"product_id": "SAMSUNG-GALAXY-S24-ULTRA", "sku": "1000011", "name": "Samsung Galaxy S24 Ultra 512GB", "category": "Smartphones", "price": 1299.00, "in_stock": True},
        {"product_id": "SAMSUNG-GALAXY-Z-FOLD6", "sku": "1000012", "name": "Samsung Galaxy Z Fold 6", "category": "Smartphones", "price": 1899.00, "in_stock": True},
        {"product_id": "SAMSUNG-GALAXY-Z-FLIP6", "sku": "1000013", "name": "Samsung Galaxy Z Flip 6", "category": "Smartphones", "price": 1099.00, "in_stock": True},

        # Latest Tablets
        {"product_id": "APPLE-IPAD-PRO-M4", "sku": "1000014", "name": "Apple iPad Pro M4 13-inch 512GB", "category": "Tablets", "price": 1499.00, "in_stock": True},
        {"product_id": "APPLE-IPAD-AIR-M2", "sku": "1000015", "name": "Apple iPad Air M2 11-inch 256GB", "category": "Tablets", "price": 699.00, "in_stock": True},
        {"product_id": "SAMSUNG-TAB-S10-ULTRA", "sku": "1000016", "name": "Samsung Galaxy Tab S10 Ultra", "category": "Tablets", "price": 1199.00, "in_stock": True},
        {"product_id": "SAMSUNG-TAB-S10-PLUS", "sku": "1000017", "name": "Samsung Galaxy Tab S10 Plus", "category": "Tablets", "price": 899.00, "in_stock": True},

        # Electronics - TVs & Displays (Latest 2024-2025 Models)
        {"product_id": "SAMSUNG-QLED-QN90D-65", "sku": "2000001", "name": "Samsung QN90D Neo QLED 4K TV 65-inch (2024)", "category": "TVs", "price": 1799.00, "in_stock": True},
        {"product_id": "SAMSUNG-QLED-QN85D-55", "sku": "2000002", "name": "Samsung QN85D Neo QLED 4K TV 55-inch (2024)", "category": "TVs", "price": 1399.00, "in_stock": True},
        {"product_id": "LG-OLED-C4-55", "sku": "2000003", "name": "LG OLED evo C4 55-inch 4K TV (2024)", "category": "TVs", "price": 1599.00, "in_stock": True},
        {"product_id": "LG-OLED-G4-65", "sku": "2000004", "name": "LG OLED evo G4 65-inch 4K TV (2024)", "category": "TVs", "price": 2499.00, "in_stock": True},
        {"product_id": "SONY-BRAVIA-XR-A95L", "sku": "2000005", "name": "Sony BRAVIA XR A95L OLED 65-inch (2024)", "category": "TVs", "price": 2799.00, "in_stock": True},
        {"product_id": "SONY-BRAVIA-9-75", "sku": "2000006", "name": "Sony BRAVIA 9 Mini LED 75-inch (2024)", "category": "TVs", "price": 3299.00, "in_stock": True},
        {"product_id": "SAM-TV-QE55QN90B", "sku": "2789123", "name": "Samsung QE55QN90B Neo QLED TV", "category": "TVs", "price": 1199.00, "in_stock": True},

        # Electronics - Audio (Latest 2024-2025 Models)
        {"product_id": "SONY-WH1000XM6", "sku": "3000001", "name": "Sony WH-1000XM6 Noise-Cancelling Headphones (2024)", "category": "Audio", "price": 399.00, "in_stock": True},
        {"product_id": "SONY-WH1000XM5S", "sku": "2812345", "name": "Sony WH-1000XM5 Noise-Cancelling Headphones", "category": "Audio", "price": 349.00, "in_stock": True},
        {"product_id": "APPLE-AIRPODS-PRO-2-USBC", "sku": "3000002", "name": "Apple AirPods Pro 2 with USB-C (2024)", "category": "Audio", "price": 249.00, "in_stock": True},
        {"product_id": "APPLE-AIRPODS-MAX-2", "sku": "3000003", "name": "Apple AirPods Max 2nd Gen USB-C (2024)", "category": "Audio", "price": 549.00, "in_stock": True},
        {"product_id": "BOSE-QC-ULTRA", "sku": "3000004", "name": "Bose QuietComfort Ultra Headphones (2024)", "category": "Audio", "price": 429.00, "in_stock": True},
        {"product_id": "SONOS-ARC-ULTRA", "sku": "3000005", "name": "Sonos Arc Ultra Soundbar (2024)", "category": "Audio", "price": 999.00, "in_stock": True},
        {"product_id": "SONOS-BEAM-GEN2", "sku": "3000006", "name": "Sonos Beam Gen 2 Soundbar", "category": "Audio", "price": 449.00, "in_stock": True},

        # Computers & Accessories (Latest 2024-2025 Models)
        {"product_id": "APPLE-MACBOOK-AIR-M4", "sku": "4000001", "name": "Apple MacBook Air M4 13-inch 16GB/512GB (2025)", "category": "Laptops", "price": 1499.00, "in_stock": True},
        {"product_id": "APPLE-MACBOOK-PRO-M4", "sku": "4000002", "name": "Apple MacBook Pro M4 14-inch 24GB/1TB (2024)", "category": "Laptops", "price": 2299.00, "in_stock": True},
        {"product_id": "APPLE-MACBOOK-PRO-M4-MAX", "sku": "4000003", "name": "Apple MacBook Pro M4 Max 16-inch (2024)", "category": "Laptops", "price": 3499.00, "in_stock": True},
        {"product_id": "DELL-XPS-15-9530", "sku": "4000004", "name": "Dell XPS 15 9530 Intel Ultra 7 (2024)", "category": "Laptops", "price": 1799.00, "in_stock": True},
        {"product_id": "LENOVO-THINKPAD-X1-GEN12", "sku": "4000005", "name": "Lenovo ThinkPad X1 Carbon Gen 12 (2024)", "category": "Laptops", "price": 1999.00, "in_stock": True},
        {"product_id": "MICROSOFT-SURFACE-LAPTOP-7", "sku": "4000006", "name": "Microsoft Surface Laptop 7 Snapdragon X Elite (2024)", "category": "Laptops", "price": 1599.00, "in_stock": True},
        {"product_id": "LOGI-MX-MASTER3S", "sku": "2754678", "name": "Logitech MX Master 3S Performance Mouse", "category": "Accessories", "price": 105.00, "in_stock": True},
        {"product_id": "LOGITECH-MX-KEYS", "sku": "4000004", "name": "Logitech MX Keys Wireless Keyboard", "category": "Accessories", "price": 119.00, "in_stock": True},
        {"product_id": "ANKER-POWERCORE-20K", "sku": "2699887", "name": "Anker PowerCore III 20000mAh Power Bank", "category": "Accessories", "price": 49.00, "in_stock": True},

        # Fashion - Footwear
        {"product_id": "ADIDAS-SNEAKER-ORIG", "sku": "5000001", "name": "Adidas Originals Sneaker", "category": "Footwear", "price": 99.00, "in_stock": True},
        {"product_id": "NIKE-AIR-MAX-90", "sku": "5000002", "name": "Nike Air Max 90", "category": "Footwear", "price": 129.00, "in_stock": True},
        {"product_id": "NIKE-REVOLUTION-6", "sku": "5000005", "name": "Nike Revolution 6 Running Shoes", "category": "Footwear", "price": 89.00, "in_stock": True},
        {"product_id": "CONVERSE-CHUCK-TAYLOR", "sku": "5000003", "name": "Converse Chuck Taylor All Star", "category": "Footwear", "price": 65.00, "in_stock": True},
        {"product_id": "PUMA-SUEDE-CLASSIC", "sku": "5000004", "name": "Puma Suede Classic", "category": "Footwear", "price": 75.00, "in_stock": True},

        # Fashion - Clothing
        {"product_id": "LEVIS-501-JEANS", "sku": "6000001", "name": "LEVI'S 501 Original Jeans", "category": "Clothing", "price": 89.00, "in_stock": False},
        {"product_id": "NIKE-TECH-FLEECE", "sku": "6000002", "name": "Nike Tech Fleece Hoodie", "category": "Clothing", "price": 119.00, "in_stock": True},
        {"product_id": "ADIDAS-TRACK-JACKET", "sku": "6000003", "name": "Adidas Originals Track Jacket", "category": "Clothing", "price": 85.00, "in_stock": True},
        {"product_id": "TOMMY-HILFIGER-POLO", "sku": "6000004", "name": "Tommy Hilfiger Classic Polo", "category": "Clothing", "price": 69.00, "in_stock": True},

        # Home & Kitchen
        {"product_id": "WMF-COFFEEMACHINE", "sku": "7000001", "name": "WMF Coffee Machine", "category": "Kitchen", "price": 749.00, "in_stock": True},
        {"product_id": "KITCHENAID-MIXER", "sku": "7000002", "name": "KitchenAid Stand Mixer", "category": "Kitchen", "price": 449.00, "in_stock": True},
        {"product_id": "DYSON-V15-VACUUM", "sku": "7000003", "name": "Dyson V15 Detect Cordless Vacuum", "category": "Home", "price": 649.00, "in_stock": True},
        {"product_id": "NESPRESSO-VERTUO", "sku": "7000004", "name": "Nespresso Vertuo Next", "category": "Kitchen", "price": 169.00, "in_stock": True},
        {"product_id": "PHILIPS-AIR-FRYER", "sku": "7000005", "name": "Philips Airfryer XXL", "category": "Kitchen", "price": 299.00, "in_stock": True},

        # Smart Home
        {"product_id": "NEST-THERMOSTAT", "sku": "8000001", "name": "Google Nest Learning Thermostat", "category": "Smart Home", "price": 249.00, "in_stock": True},
        {"product_id": "RING-DOORBELL-PRO", "sku": "8000002", "name": "Ring Video Doorbell Pro 2", "category": "Smart Home", "price": 269.00, "in_stock": True},
        {"product_id": "PHILIPS-HUE-KIT", "sku": "8000003", "name": "Philips Hue White & Color Starter Kit", "category": "Smart Home", "price": 199.00, "in_stock": True},
        {"product_id": "AMAZON-ECHO-SHOW", "sku": "8000004", "name": "Amazon Echo Show 10", "category": "Smart Home", "price": 249.00, "in_stock": True},

        # Gaming
        {"product_id": "PS5-CONSOLE", "sku": "9000001", "name": "PlayStation 5 Console", "category": "Gaming", "price": 499.00, "in_stock": True},
        {"product_id": "XBOX-SERIES-X", "sku": "9000002", "name": "Xbox Series X", "category": "Gaming", "price": 499.00, "in_stock": True},
        {"product_id": "NINTENDO-SWITCH-OLED", "sku": "9000003", "name": "Nintendo Switch OLED", "category": "Gaming", "price": 349.00, "in_stock": True},
        {"product_id": "STEAM-DECK", "sku": "9000004", "name": "Steam Deck 512GB", "category": "Gaming", "price": 649.00, "in_stock": True},
        {"product_id": "GAMEMAX-PC-RTX4070", "sku": "9000005", "name": "GAMEMAX Gaming PC RTX 4070", "category": "Gaming", "price": 1599.00, "in_stock": True},

        # Cameras & Photography
        {"product_id": "CANON-EOS-R6", "sku": "10000001", "name": "Canon EOS R6 Mark II", "category": "Cameras", "price": 2499.00, "in_stock": True},
        {"product_id": "SONY-A7-IV", "sku": "10000002", "name": "Sony Alpha 7 IV", "category": "Cameras", "price": 2499.00, "in_stock": True},
        {"product_id": "GOPRO-HERO12", "sku": "10000003", "name": "GoPro HERO12 Black", "category": "Cameras", "price": 399.00, "in_stock": True},
        {"product_id": "DJI-MINI-4-PRO", "sku": "10000004", "name": "DJI Mini 4 Pro Drone", "category": "Cameras", "price": 759.00, "in_stock": True},

        # Accessories & Cases
        {"product_id": "GENERIC-PIXEL-CASE", "sku": "1122334", "name": "Generic Google Pixel Case", "category": "Accessories", "price": 19.00, "in_stock": True},
        {"product_id": "GOOGLE-PIXEL9PRO-CASE", "sku": "11000001", "name": "Google Pixel 9 Pro Defender Series Case", "category": "Accessories", "price": 59.99, "in_stock": True},
        {"product_id": "APPLE-LEATHER-CASE", "sku": "11000002", "name": "Apple iPhone 16 Leather Case", "category": "Accessories", "price": 59.00, "in_stock": True},
        {"product_id": "GOOGLE-PIXEL-30W-CHARGER", "sku": "11000003", "name": "Google 30W USB-C Charger", "category": "Accessories", "price": 29.00, "in_stock": True},

        # Wearables
        {"product_id": "APPLE-WATCH-SERIES-9", "sku": "12000001", "name": "Apple Watch Series 9", "category": "Wearables", "price": 399.00, "in_stock": True},
        {"product_id": "SAMSUNG-GALAXY-WATCH6", "sku": "12000002", "name": "Samsung Galaxy Watch 6", "category": "Wearables", "price": 299.00, "in_stock": True},
        {"product_id": "FITBIT-CHARGE-6", "sku": "12000003", "name": "Fitbit Charge 6", "category": "Wearables", "price": 159.00, "in_stock": True},

        # Services
        {"product_id": "PLUSGARANTIE-TV-3J", "sku": "8765432", "name": "Extended warranty 3 years for TV up to 1650 EUR", "category": "Services", "price": 139.00, "type": "service"},
        {"product_id": "PREFERRED-CARE-PHONE", "sku": "13000001", "name": "Preferred Care Protection for Smartphones", "category": "Services", "price": 99.00, "type": "service"},
        {"product_id": "SETUP-SERVICE-TV", "sku": "13000002", "name": "TV Installation and Setup Service", "category": "Services", "price": 149.00, "type": "service"},
    ]

    CUSTOMER_PROFILE = {

        "language":DEFAULT_LANGUAGE,
        "available_products": None,  # Will be populated after class definition
        "product_catalog_raw": PRODUCT_CATALOG,  # Raw data for tools to access
        "customer_profile": {
            "account_number":f"AN-{random.randint(100000000, 999999999)}",
            "customer_id": "CY-1234-1234",
            "customer_first_name": "Cornelius",
            "customer_last_name": "Koch",
            "email": "Cornelius.koch@example.com",
            "phone_number": "+49-89-555-1234",
            "customer_start_date": "2021-08-15",
            "years_as_customer": 4,
            "billing_address": {
                "street": "ul. Grunwaldzka 472",
                "city": "Berlin",
                "state": "Pomeranian Voivodeship",
                "zip": "80-309",
                "country": "PL"
            },
            "shipping_address": {
                "street": "ul. Grunwaldzka 472",
                "city": "Berlin",
                "state": "Pomeranian Voivodeship",
                "zip": "80-309",
                "country": "PL"
            },

            "order_history": [
                {
                    "order_id": f"ORD-{random.randint(10000, 99999)}",
                    "date": "2023-05-20",
                    "items": [
                        {"product_id": "SAM-TV-QE55QN90B", "sku": "2789123", "name": "Samsung QE55QN90B Neo QLED TV", "quantity": 1, "type": "product", "price": 1599.00},
                        {"product_id": "PLUSGARANTIE-TV-3J", "sku": "8765432", "name": "Extended warranty 3 years for TV up to 1650 EUR", "quantity": 1, "type": "service", "price": 139.00}
                    ],
                    "total_amount": 1738.00,
                    "store_id": "CY-BER-CENTER",
                    "channel": "instore"
                },
                {
                    "order_id": f"ORD-{random.randint(10000, 99999)}",
                    "date": "2023-11-10",
                    "items": [
                        {"product_id": "SONY-WH1000XM5S", "sku": "2812345", "name": "Sony WH-1000XM5 Noise-Cancelling Headphones", "quantity": 1, "type": "product", "price": 369.00}
                    ],
                    "total_amount": 369.00,
                    "store_id": "CY-BER-CENTER",
                    "channel": "instore"
                },
                {
                    "order_id": f"ORD-{random.randint(10000, 99999)}",
                    "date": "2024-03-01",
                    "items": [
                         {"product_id": "LOGI-MX-MASTER3S", "sku": "2754678", "name": "Logitech MX Master 3S Performance Mouse", "quantity": 1, "type": "product", "price": 105.00},
                         {"product_id": "ANKER-POWERCORE-20K", "sku": "2699887", "name": "Anker PowerCore III 20000mAh Power Bank", "quantity": 1, "type": "product", "price": 49.00}
                    ],
                    "total_amount": 154.00,
                    "store_id": "CY-BER-CENTER",
                    "channel": "instore"
                }
            ],
             "current_cart": {
                "cart_id": f"CART-{random.randint(100000, 999999)}",
                "items": [
                    {"product_id": "GENERIC-PIXEL-CASE", "sku": "1122334", "name": "Generic Google Pixel Case", "quantity": 1, "price": 19},
                ],
                "subtotal": 19, # Adjust subtotal accordingly
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "loyalty_points": 133,
            "preferred_store": "Cymbal Berlin",
            "communication_preferences": {
                "email": True,
                "sms": True,
                "push_notifications": False
            },
            "loyalty_program": {
                "program_name": "myCymbal",
                "card_number": f"2951 {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "member_since": "2021-08-15",
                "points_balance": 2150,
                "level": "Standard",
                "digital_receipts_enabled": True,
                "exclusive_offers_available": 2,
                "communication_preferences": {
                    "email": True,
                    "sms": True,
                    "push_notifications": False
                }
            },
            "interests": ["Smart Home", "Audio", "Mobile Computing", "Photography"],
            "registered_devices": [
                {"product_id": "SAM-TV-QE55QN90B", "name": "Samsung QE55QN90B Neo QLED TV", "purchase_date": "2023-05-20", "warranty_expires": "2026-05-19", "has_extended_warranty": True},
                {"product_id": "SONY-WH1000XM5S", "name": "Sony WH-1000XM5", "purchase_date": "2023-11-10", "warranty_expires": "2025-11-09", "has_extended_warranty": False}
            ],

            "scheduled_appointments": {
                    "appointment_id": f"APP-{random.randint(1000, 9999)}",
                    "service_type": "Smartphone Repair Drop-off",
                    "date_time": "2025-04-18 14:00:00",
                    "store_id": "CY-BERLIN",
                    "status": "Scheduled"
                }
        },
        "current_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Format product catalog as readable markdown table for the model
def _format_product_catalog():
    """Format the product catalog as a readable markdown table."""
    lines = [
        "| Product ID | SKU | Name | Category | Price (EUR) | In Stock |",
        "|------------|-----|------|----------|-------------|----------|"
    ]
    for product in RetailContext.PRODUCT_CATALOG:
        lines.append(
            f"| {product['product_id']} | {product['sku']} | {product['name']} | "
            f"{product['category']} | €{product['price']:.2f} | "
            f"{'Yes' if product.get('in_stock', True) else 'No'} |"
        )
    return "\n".join(lines)

# Populate the available_products field with formatted catalog
RetailContext.CUSTOMER_PROFILE["available_products"] = _format_product_catalog()

def create_customer_profile(customer_id=None, first_name=None, last_name=None, email=None):
    """
    Create a dynamic customer profile based on provided customer information.
    If no information is provided, returns the default profile.

    Args:
        customer_id: Customer ID (e.g., "CY-1234-5678")
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email address

    Returns:
        dict: Customer profile with personalized information
    """
    # Start with a copy of the default profile
    import copy
    profile = copy.deepcopy(RetailContext.CUSTOMER_PROFILE)

    # Update with provided customer information
    if customer_id:
        profile["customer_profile"]["customer_id"] = customer_id
    if first_name:
        profile["customer_profile"]["customer_first_name"] = first_name
    if last_name:
        profile["customer_profile"]["customer_last_name"] = last_name
    if email:
        profile["customer_profile"]["email"] = email

    # For new customers (not the default), clear order history and adjust other fields
    if customer_id and customer_id != "CY-1234-1234":
        # New customer - clear historical data
        profile["customer_profile"]["order_history"] = []
        profile["customer_profile"]["loyalty_points"] = 0
        profile["customer_profile"]["loyalty_program"]["points_balance"] = 0
        profile["customer_profile"]["registered_devices"] = []
        profile["customer_profile"]["scheduled_appointments"] = {}
        profile["customer_profile"]["current_cart"]["items"] = []
        profile["customer_profile"]["current_cart"]["subtotal"] = 0
        # Update customer start date to today
        profile["customer_profile"]["customer_start_date"] = datetime.now().strftime("%Y-%m-%d")
        profile["customer_profile"]["loyalty_program"]["member_since"] = datetime.now().strftime("%Y-%m-%d")
        profile["customer_profile"]["years_as_customer"] = 0

    return profile
