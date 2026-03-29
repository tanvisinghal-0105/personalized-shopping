class Examples:
    # Updated example incorporating more tools and customer information queries
    FULL_SCRIPT_EXAMPLE = """
```
<Example 1: Customer Login and Profile Information>
[USER]:
Hey!

[MODEL]:
Hello! Welcome to Cymbal. I see you're a returning customer. Welcome back, Cornelius Koch! It's great to see you again.

You've been a valued Cymbal customer since 2021, and I can see you're a Standard member of our myCymbal loyalty program with 2,150 points. Your preferred store is Cymbal Berlin.

How can I help you today?

[USER]:
Can you tell me more about my account and order history?

[MODEL]:
Of course, Cornelius! Let me share your account details:

**Account Information:**
- Account Number: {+account_number}+
- Customer ID: CY-1234-1234
- Email: Cornelius.koch@example.com
- Phone: +49-89-555-1234
- Member Since: August 15, 2021 (4 years as customer)

**Loyalty Program:**
- Program: myCymbal Standard Level
- Points Balance: 2,150 points
- Card Number: 2951 XXXX XXXX XXXX

**Recent Order History:**
1. **March 1, 2024** - Order #ORD-XXXXX
   - Logitech MX Master 3S Performance Mouse (€105.00)
   - Anker PowerCore III 20000mAh Power Bank (€49.00)
   - Total: €154.00

2. **November 10, 2023** - Order #ORD-XXXXX
   - Sony WH-1000XM5 Noise-Cancelling Headphones (€369.00)
   - Total: €369.00

3. **May 20, 2023** - Order #ORD-XXXXX
   - Samsung QE55QN90B Neo QLED TV (€1,599.00)
   - Extended warranty 3 years for TV (€139.00)
   - Total: €1,738.00

**Registered Devices:**
- Samsung QE55QN90B Neo QLED TV (purchased May 2023, warranty until May 2026 with extended warranty)
- Sony WH-1000XM5 (purchased November 2023, warranty until November 2025)

**Upcoming Appointments:**
- Smartphone Repair Drop-off on April 18, 2025 at 14:00 at CY-BERLIN store

Is there anything specific from your order history you'd like to discuss, or can I help you with something new today?

[USER]:
Great! What is currently in my shopping cart?

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

<Example 2: Product Browsing with Catalog Knowledge>
[USER]:
Hi, I'm looking for a new TV for my living room.

[MODEL]:
Hello! I'd be happy to help you find the perfect TV. We have several excellent options available:

**Large Screen 4K/8K TVs:**
1. **Samsung QLED 4K TV 65-inch** - €1,199.00 (In Stock)
   - Brilliant QLED display with quantum dot technology

2. **Samsung QE55QN90B Neo QLED TV** - €1,599.00 (In Stock)
   - Premium Neo QLED with mini-LED technology

3. **LG OLED C3 55-inch 4K TV** - €1,499.00 (In Stock)
   - Perfect blacks with OLED technology

4. **Sony BRAVIA XR 65-inch** - €1,799.00 (In Stock)
   - Sony's premium cognitive processor

What's your budget, and what size are you looking for?

[USER]:
I'm thinking around €1,200-€1,500 range, and 55-65 inches would be perfect.

[MODEL]:
Perfect! Based on your budget and size preference, I'd recommend either:

1. **Samsung QLED 4K TV 65-inch** at €1,199.00 - This gives you the largest screen at the lower end of your budget with excellent picture quality.

2. **LG OLED C3 55-inch** at €1,499.00 - Slightly smaller but OLED technology provides superior contrast and perfect blacks, ideal for movie watching.

Both are in stock. I also notice from your profile that you purchased a Samsung TV in 2023, so you might appreciate Samsung's ecosystem compatibility. Would you like me to check availability at your preferred Cymbal Berlin store?

[USER]:
Let me go with the Samsung 65-inch. Can you add it to my cart?

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'SAMSUNG-QLED-65', 'quantity': 1}])

# tool_outputs
{'status': 'success', 'message': 'Cart updated successfully.', 'items_added': True, 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'SAMSUNG-QLED-65', 'sku': '2000001', 'name': 'Samsung QLED 4K TV 65-inch', 'quantity': 1, 'price': 1199.00}], 'subtotal': 1199.00}}

[MODEL]:
Great choice! I've added the Samsung QLED 4K TV 65-inch (€1,199.00) to your cart.

Since you're investing in a premium TV, would you like me to add:
1. **Extended warranty 3 years for TV** (€139.00) - Covers manufacturing defects and repairs
2. **TV Installation and Setup Service** (€149.00) - Professional mounting and calibration

Also, I see you have a Sonos Beam soundbar would pair perfectly with this TV if you're interested in upgrading your audio setup!

</Example>
```
"""

    # Keep MAIN_EXAMPLES pointing to the comprehensive one
    MAIN_EXAMPLES = FULL_SCRIPT_EXAMPLE

