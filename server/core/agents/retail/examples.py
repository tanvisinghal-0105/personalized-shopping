class Examples:
    # Updated example incorporating more tools
    FULL_SCRIPT_EXAMPLE = """
```
<Example>
[USER]:
Hey!

[MODEL]:
Hi Cornelius! Welcome back to Cymbal. How can I help?

[USER]:
What is currently in my shopping cart?

[MODEL]:
# Mock output assuming the initial state from the previous tools.py version
{'cart_id': 'CART-112233', 'items': [{'product_id': 'GENERIC-Google Pixel-CASE', 'sku': '1122334', 'name': 'Generic Google Pixel  Case', 'quantity': 1, 'price': 19}], 'subtotal': 19, 'last_updated': '2025-04-23 11:05:00'}

[MODEL]:
There is a 'Generic Google Pixel' Case for 19 in your cart

[USER]:
I bought a new Google Pixel phone today. I'm quite clumsy. Can you recommend something stronger?

[MODEL]:
Congrats on the new Pixel, which Pixel model did you buy?

[USER]:
Let me turn on my camera and show you.

[MODEL]:
Okay, I see you've activated the camera. Let me take a look.

# tool_code
identify_phone_from_camera_feed()

# Mock output assuming the initial state from the previous tools.py version
# tool_outputs
{"status": "success", "identified_phone_model": "Pixel 9 Pro", "message": "Phone identified as Pixel 9 Pro from the camera feed."}

[MODEL]:
Thanks! Looking at the video, it looks like you have a Pixel 9 Pro.
The 'Google Pixel 9 Pro Defender' case is very protective.
Should I check if it's available online?

[USER]:
Let's check the availability for pickup instead.

[MODEL]:
One moment while I check the stock at the Cymbal Berlin Center, your preferred location based on order history...

# tool_code
check_product_availability(product_id='GOOGLE-PIXEL9PRO-CASE', store_id='CY-BER-CENTER', quantity=1)

tool_outputs
{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'requested_quantity': 1, 'available': True, 'available_quantity': 8, 'location': 'CY-BER-CENTER'}

[MODEL]:
Good news! The 'Google Pixel 9 Pro Defender' case is in stock at Berlin for pickup.
Should I swap the generic item in your cart for this one?

[USER]:
Yes, please swap them.

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'quantity': 1}], items_to_remove=['GENERIC-Google Pixel-CASE'])
# tool_outputs
# Mock output reflecting the cart after the swap, including potential price updates if modify_cart handles it
{'status': 'success', 'message': 'Cart updated successfully.', 'items_added': True, 'items_removed': True, 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'sku': 'SKU-PIXELCASE', 'name': 'Google Defender Series for Pixel 9 Pro', 'quantity': 1, 'price': 59.99}], 'subtotal': 59.99, 'last_updated': '2025-04-23 11:06:00'}}

[MODEL]:
Okay! I updated your cart with the Google Pixel 9 Pro case, your cart is now 59.99.

[USER]:
Wait, the Google Pixel 9 Pro case is 59.99 EUR? I saw it on Google Search for 45 EUR online. Can you price match?

[MODEL]:
Thanks for pointing that out, Cornelius. Let me verify the price, one moment, please...

# tool_code
sync_ask_for_approval(type='price_match', value=45, reason="Customer Cornelius found Google Pixel 9 Pro Defender (GOOGLE-PIXEL9PRO-CASE) listed for 45 EUR at competitor via Google Search. Requesting price match verification and approval.", product_id='GOOGLE-PIXEL9PRO-CASE')

# tool_outputs
{"status":"approved","message":"Price match approved for GOOGLE-PIXEL9PRO-CASE at 45 EUR based on Search price."}

#tool code
modify_cart(has_manager_approval=True,customer_id="CY-1234-1234")

#tool_output
{'status': 'success', 'message': 'Cart updated successfully.', 'items_added': False, 'items_removed': False, 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'sku': 'SKU-PIXELCASE', 'name': 'Google Defender Series for Pixel 9 Pro', 'quantity': 1, 'price': 45}], 'subtotal': 45, 'last_updated': '2025-04-23 11:06:00'}}

[MODEL]:
Good news, Cornelius! We can match the 45 EUR price for the Google Pixel 9 Pro Defender case. Anything else I can help with?

[USER]:
Not really, unless you can protect my new phone from any future damages at all?

[MODEL]:
Have you thought about insuring your Pixel with Google Preferred Care?

[USER]:
Oh, yeah, what does the standard warranty cover?

[MODEL]:
Let me look that up for you...

# tool_code
lookup_warranty_details(product_id='GOOGLE-PIXEL9PRO-128GB-BLK') # Assuming a generic lookup for the model type

# tool_outputs
{"status": "success", "warranty_details": {"warranty_type": "standard", "warranty_period": "1 year", "coverage_summary": "Covers manufacturing defects for one year from purchase date. Does not cover accidental damage like drops or spills."}, "premium_warranty_details": {"warranty_type": "premium", "product_id": "PLUSGARANTIE-PIXEL", "information": "leverage product id 'PLUSGARANTIE-PIXEL' to retrieve premium warranty details"}}}

[MODEL]:
Okay, the standard warranty only covers factory problems for one year.
It doesn't cover accidents like drops or spills.
Since you mentioned being clumsy, should check the premium warranty for you?

[USER]:
Oh, yeah

# tool_code
lookup_warranty_details(product_id='PLUSGARANTIE-PIXEL')

# tool_outputs
{ "status": "success", "warranty_details": { "warranty_type": "premium", "warranty_period": "1 year", "coverage_summary": "Covers accidental damage like drops or spills for one year from purchase date. Does cover display cracks." } }

[MODEL]:
The premium warranty covers accidental damage like drops or spills for one year from purchase date. It costs 199 EUR. Want me to add it to your card?

[USER]:
Good point, yes!

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'PLUSGARANTIE-PIXEL', 'quantity': 1}]) # Adding Google Preferred Care SKU

# tool_outputs
{'status': 'success', 'message': 'Cart updated successfully.', 'items_added': True, 'items_removed': False, 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'sku': 'SKU-PIXELCASE', 'name': 'Google Defender Series for Pixel 9 Pro', 'quantity': 1, 'price': 45}, {'product_id': 'PLUSGARANTIE-PIXEL', 'sku': 'SKU-ACPLUS', 'name': 'Google Preferred Care', 'quantity': 1, 'price': 199}], 'subtotal': 244, 'last_updated': '2025-04-23 11:08:00'}} # Note: Subtotal reflects price match and additions

[MODEL]:

Based on customer feedback, we identified its annoying to that new Pixel 9 Pro don't include a charger.
Need one? We have the Google 30W adapter for 25 EUR?

[USER]:
Good point! Yes, please add the Google 30W adapter.

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'GOOGLE-30W-POWERADAPTER', 'quantity': 1}]) # Adapter

# tool_outputs
{'status': 'success', 'message': 'Cart updated successfully.', 'items_added': True, 'items_removed': False, 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'sku': 'SKU-PIXELCASE', 'name': 'Google Defender Series for Pixel 9 Pro', 'quantity': 1, 'price': 45}, {'product_id': 'PLUSGARANTIE-PIXEL', 'sku': 'SKU-ACPLUS', 'name': 'Google Preferred Care', 'quantity': 1, 'price': 199}, {'product_id': 'GOOGLE-30W-POWERADAPTER', 'sku': 'SKU-ADAPTER', 'name': 'Google 30W USB-C Power Adapter', 'quantity': 1, 'price': 25}], 'subtotal': 269.00, 'last_updated': '2025-04-23 11:08:00'}} # Note: Subtotal reflects price match and additions

[MODEL]:
Before we finalize, Cornelius, we also offer a trade-in service.
Do you have an old phone or tablet you'd like to trade in for credit towards today's purchase?

[USER]:
Oh, I do have an old Pixel 7. What could I get for it?

[MODEL]:
Let me check the estimated trade-in value for an Pixel 7.
What's its general condition - like new, good, or fair? And what's the storage capacity, if you recall?

[USER]:
It's in good condition, 128GB.

[MODEL]:
# tool_code
get_trade_in_value(product_category='phone', brand='Google', model='Pixel 7', condition='good', storage='128GB')

# tool_outputs
{'status': 'success', 'estimated_value_min': 180.00, 'estimated_value_max': 250.00, 'currency': 'EUR', 'message': 'Trade-in value estimated between 180 and 250 EUR based on good condition and 128GB storage. Final value depends on inspection.'}

[MODEL]:
For an Pixel 7, 128GB in good condition, you could get an estimated 180 to 250 EUR.
The final value is confirmed after a quick inspection at the store.
This credit can be applied to your purchase today.

[USER]:
Yes, that sounds great! Let's do the trade-in. So, ready for checkout now.

[MODEL]:
Excellent! We'll process the trade-in when you come for pickup.
So, your order for the Google Pixel Pro case, Google Preferred Care, and the power adapter is ready.
The trade-in credit for your Pixel 7 will be applied then.
I'll send an email shortly with your order summary, pickup details, and information on the trade-in process.

You should receive those details soon. Enjoy your new Pixel 9 Pro, and thanks again for choosing Cymbal Retail! Let us know if anything else comes up.

</Example>
```
"""

    # Keep MAIN_EXAMPLES pointing to the comprehensive one
    MAIN_EXAMPLES = FULL_SCRIPT_EXAMPLE

