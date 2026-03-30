from ..core.agents.retail.tools import modify_cart


def test_modify_cart():
    arguments = {
        "customer_id": "GR-1234-1234",
        "items_to_remove": [
            {"quantity": 1, "product_id": "GENERIC-PIXEL-CASE"}
        ],
        "items_to_add": [
            {"quantity": 1, "product_id": "GOOGLE-PIXEL9PRO-CASE"},
            {"product_id": "ZAGG-IS-PIXEL9PRO", "quantity": 1},
        ],
    }
    cart = modify_cart(**arguments)
    expected_output = {
        "status": "success",
        "message": "Cart updated successfully.",
        "items_added": True,
        "items_removed": True,
        "updated_cart": {
            "cart_id": "CART-112233",
            "items": [
                {
                    "product_id": "GOOGLE-PIXEL9PRO-CASE",
                    "name": "Google Defender Series for Pixel 9 Pro",
                    "price": 59.99,
                    "sku": "SKU-OTTER",
                    "quantity": 1,
                }
            ],
            "subtotal": 59.99,
            "last_updated": "2025-04-29 11:11:47",
        },
    }

    assert cart["status"] == expected_output["status"]
    assert cart["message"] == expected_output["message"]
    assert cart["items_added"] == expected_output["items_added"]
    assert cart["items_removed"] == expected_output["items_removed"]
    assert (
        cart["updated_cart"]["items"]
        == expected_output["updated_cart"]["items"]
    )


def test_modify_cart_with_list_of_items_to_remove():
    arguments = {
        "customer_id": "GR-1234-1234",
        "items_to_add": [
            {"product_id": "GOOGLE-PIXEL9PRO-CASE", "quantity": 1}
        ],
        "items_to_remove": ["GENERIC-PIXEL-CASE"],
    }
    cart = modify_cart(**arguments)
    expected_output = {
        "status": "success",
        "message": "Cart updated successfully.",
        "items_added": True,
        "items_removed": True,
        "updated_cart": {
            "cart_id": "CART-112233",
            "items": [
                {
                    "product_id": "GOOGLE-PIXEL9PRO-CASE",
                    "name": "Google Defender Series for Pixel 9 Pro",
                    "price": 59.99,
                    "sku": "SKU-OTTER",
                    "quantity": 1,
                }
            ],
            "subtotal": 59.99,
            "last_updated": "2025-04-29 12:52:11",
        },
    }
    assert cart["status"] == "success"
    assert cart["message"] == "Cart updated successfully."
    assert cart["items_added"]
    assert cart["items_removed"]
    assert (
        cart["updated_cart"]["items"]
        == expected_output["updated_cart"]["items"]
    )


def test_modify_cart_with_warranty():
    arguments = {
        "items_to_remove": ["GENERIC-PIXEL-CASE"],
        "items_to_add": [
            {"quantity": 1, "product_id": "GOOGLE-PIXEL9PRO-CASE"}
        ],
        "customer_id": "GR-1234-1234",
    }
    cart = modify_cart(**arguments)

    arguments = {
        "items_to_add": [{"quantity": 1, "product_id": "PLUSGARANTIE-PIXEL"}],
        "customer_id": "GR-1234-1234",
    }
    cart = modify_cart(**arguments)
    expected_output = {
        "status": "success",
        "message": "Cart updated successfully.",
        "items_added": True,
        "items_removed": False,
        "updated_cart": {
            "cart_id": "CART-112233",
            "items": {
                "GOOGLE-PIXEL9PRO-CASE": {
                    "name": "Google Defender Series for Pixel 9 Pro",
                    "price": 59.99,
                    "sku": "SKU-OTTER",
                    "quantity": 1,
                },
                "PLUSGARANTIE-PIXEL": {
                    "name": "Google Preferred Care for Pixel Pro 9 (Discounted)",
                    "price": 199,
                    "sku": "SKU-ACPLUS",
                    "quantity": 1,
                },
            },
            "subtotal": 258.99,
            "last_updated": "2025-04-29 13:54:09",
        },
    }
    assert cart["status"] == expected_output["status"]
    assert cart["message"] == expected_output["message"]
    assert cart["items_added"] == expected_output["items_added"]
    assert cart["items_removed"] == expected_output["items_removed"]
    assert (
        cart["updated_cart"]["items"]
        == expected_output["updated_cart"]["items"]
    )


def test_modify_cart_changes_cart():
    pass
