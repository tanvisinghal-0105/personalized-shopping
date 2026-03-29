from datetime import datetime
import random
from config.config import LANGUAGE, LANGUAGE_CODE

DEFAULT_LANGUAGE = LANGUAGE or "English (United Kingdom)"

class RetailContext:
    CUSTOMER_PROFILE = {

        "language":DEFAULT_LANGUAGE,
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
                "level": "Standard", #
                "digital_receipts_enabled": True,
                "exclusive_offers_available": 2,
                "communication_preferences": {
                "email": True,
                "sms": True,
                "push_notifications": False
            }},
            "preferred_store": "Cymbal Berlin",
            "communication_preferences": {
                "email_newsletter": True,
                "sms_offers": False,
                "push_notifications_app": True,
                "postal_mail": False
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
