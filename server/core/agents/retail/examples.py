class Examples:
    FULL_SCRIPT_EXAMPLE = """
```
<Example 1: Electronics Shopping - Phone Case, Price Match, Warranty, Trade-In>
[USER]:
Hey!

[MODEL]:
Hello! Welcome to Cymbal. I see you're a returning customer. Welcome back, {customer_first_name} {customer_last_name}! It's great to see you again.

You've been a valued Cymbal customer since 2021, and I can see you're a Standard member of our myCymbal loyalty program with 2,150 points. Your preferred store is Cymbal Berlin.

How can I help you today?

[USER]:
What is currently in my shopping cart?

[MODEL]:
# tool_code
access_cart_information(customer_id='CY-1234-1234')

# tool_outputs
{'cart_id': 'CART-112233', 'items': [{'product_id': 'GENERIC-PIXEL-CASE', 'sku': '1122334', 'name': 'Generic Google Pixel Case', 'quantity': 1, 'price': 19}], 'subtotal': 19, 'last_updated': '2025-04-23 11:05:00'}

[MODEL]:
You currently have a Generic Google Pixel Case (19 EUR) in your cart.

[USER]:
I bought a new Google Pixel 9 Pro today. I'm quite clumsy. Can you recommend something stronger?

[MODEL]:
The Google Pixel 9 Pro Defender case is our most protective option. Should I check if it's available at your preferred Cymbal Berlin store?

[USER]:
Yes, check Berlin please.

[MODEL]:
# tool_code
check_product_availability(product_id='GOOGLE-PIXEL9PRO-CASE', store_id='CY-BER-CENTER', quantity=1)

# tool_outputs
{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'requested_quantity': 1, 'available': True, 'available_quantity': 8, 'location': 'CY-BER-CENTER'}

[MODEL]:
Good news! The Pixel 9 Pro Defender case is in stock at Cymbal Berlin. Should I swap the generic case in your cart for this one?

[USER]:
Yes, please swap them.

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'quantity': 1}], items_to_remove=['GENERIC-PIXEL-CASE'])

# tool_outputs
{'status': 'success', 'items_added': True, 'items_removed': True, 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'name': 'Google Defender Series for Pixel 9 Pro', 'quantity': 1, 'price': 59.99}], 'subtotal': 59.99}}

[MODEL]:
Done! Your cart now has the Google Pixel 9 Pro Defender case at 59.99 EUR.

[USER]:
Wait, I saw it online for 45 EUR. Can you price match?

[MODEL]:
Let me check with our manager for approval on that price match...

# tool_code
sync_ask_for_approval(type='price_match', value=45, reason="Customer found Google Pixel 9 Pro Defender (GOOGLE-PIXEL9PRO-CASE) listed for 45 EUR online. Requesting price match approval.", product_id='GOOGLE-PIXEL9PRO-CASE')

# tool_outputs
{"status":"approved","message":"Price match approved for GOOGLE-PIXEL9PRO-CASE at 45 EUR."}

# tool_code
modify_cart(has_manager_approval=True, customer_id='CY-1234-1234')

# tool_outputs
{'status': 'success', 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'name': 'Google Defender Series for Pixel 9 Pro', 'quantity': 1, 'price': 45}], 'subtotal': 45}}

[MODEL]:
Price match approved! The case is now 45 EUR in your cart. Anything else?

[USER]:
What about warranty options?

[MODEL]:
# tool_code
lookup_warranty_details(product_id='GOOGLE-PIXEL9PRO-128GB-BLK')

# tool_outputs
{"status": "success", "warranty_details": {"warranty_type": "standard", "warranty_period": "1 year", "coverage_summary": "Covers manufacturing defects. Does not cover accidental damage."}, "premium_warranty_details": {"warranty_type": "premium", "product_id": "PLUSGARANTIE-PIXEL"}}

[MODEL]:
The standard warranty covers manufacturing defects for one year but not accidental damage. Since you mentioned being clumsy, shall I look up the premium warranty?

[USER]:
Yes please!

[MODEL]:
# tool_code
lookup_warranty_details(product_id='PLUSGARANTIE-PIXEL')

# tool_outputs
{"status": "success", "warranty_details": {"warranty_type": "premium", "warranty_period": "1 year", "coverage_summary": "Covers accidental damage including drops and spills for one year."}}

[MODEL]:
The premium warranty covers drops, spills, and display cracks for one year at 199 EUR. Want me to add it?

[USER]:
Yes, add it!

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'PLUSGARANTIE-PIXEL', 'quantity': 1}])

# tool_outputs
{'status': 'success', 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'GOOGLE-PIXEL9PRO-CASE', 'price': 45}, {'product_id': 'PLUSGARANTIE-PIXEL', 'price': 199}], 'subtotal': 244}}

[MODEL]:
Added! By the way, do you have an old phone to trade in for credit?

[USER]:
I have an old Pixel 7 in good condition, 128GB.

[MODEL]:
# tool_code
get_trade_in_value(product_category='phone', brand='Google', model='Pixel 7', condition='good', storage='128GB')

# tool_outputs
{'status': 'success', 'estimated_value_min': 180.00, 'estimated_value_max': 250.00, 'currency': 'EUR'}

[MODEL]:
Your Pixel 7 could get you 180 to 250 EUR. The final value is confirmed after inspection at the store. Shall I proceed with the trade-in?

[USER]:
Yes, let's do it!

[MODEL]:
We'll process the trade-in when you come for pickup. Your order for the Pixel 9 Pro case and premium warranty is ready. The trade-in credit will be applied at the store. Enjoy your new phone, {customer_first_name}!

</Example>

<Example 2: Home Decor Consultation - Adult Bedroom Redesign>
[USER]:
I want to redesign my bedroom.

[MODEL]:
I'd love to help you redesign your bedroom! Let me start a consultation to find the perfect style for you.

# tool_code
start_home_decor_consultation(customer_id='CY-1234-1234', initial_request='redesign bedroom')

# tool_outputs
{"status": "started", "session_id": "DECOR-CONSULT-42891", "message": "Consultation started", "ui_data": {"display_type": "room_selector", "room_options": ["Living Room", "Bedroom", "Kitchen", "Office", "Dining Room", "Bathroom"], "interaction_mode": "single_select"}}

[MODEL]:
Which room would you like to redesign? I've shown some options on your screen.

[USER]:
Bedroom.

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891', room_type='bedroom')

# tool_outputs
{"status": "in_progress", "current_stage": "stage_1a_room_purpose", "message": "Is this a decoration refresh or a full redesign?", "ui_data": {"display_type": "purpose_selector", "options": ["decoration", "redesign"]}}

[MODEL]:
Would you like a decoration refresh with new accessories, or a full redesign including furniture?

[USER]:
Full redesign.

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891', room_purpose='redesign')

# tool_outputs
{"status": "in_progress", "current_stage": "stage_1d_photo_request", "message": "Please upload a photo of your current bedroom so we can plan the redesign."}

[MODEL]:
Could you upload a photo of your current bedroom? This helps me understand the space and identify what to keep.

[USER]:
[Sends room photo]

[MODEL]:
# tool_code (intercepted at WebSocket layer)
analyze_room_with_history(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891', image_data='<base64_image>')

# tool_outputs
{"status": "success", "room_analysis": {"room_type": "bedroom", "estimated_size": "medium", "existing_furniture": ["double bed", "wardrobe", "bedside table"], "lighting": "natural from window", "wall_color": "light grey"}, "matched_purchases": [{"product_id": "BED-DOUBLE-01", "name": "Double Upholstered Bed", "identified_in_photo": true}]}

[MODEL]:
I can see your bedroom has a double bed, wardrobe, and bedside table with nice natural lighting. I also noticed the double bed matches one from your order history. Now let's pick a style!

# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891')

# tool_outputs
{"status": "in_progress", "current_stage": "stage_2_style_discovery", "ui_data": {"display_type": "style_selector", "style_options": ["Modern", "Minimalist", "Bohemian", "Coastal", "Industrial", "Scandinavian", "Traditional", "Rustic"], "interaction_mode": "multi_select"}}

[MODEL]:
What styles appeal to you? You can pick multiple from the options on screen.

[USER]:
Modern and coastal.

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891', style_preferences=['modern', 'coastal'])

# tool_outputs
{"status": "in_progress", "current_stage": "stage_3_color_preferences", "ui_data": {"display_type": "color_selector", "color_options": ["White", "Blue", "Beige", "Grey", "Green", "Navy", "Gold", "Black"], "interaction_mode": "multi_select"}}

[MODEL]:
Great choices! Any colour preferences? You can select a few or skip this step.

[USER]:
Blue and white.

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891', color_preferences=['blue', 'white'])

# tool_outputs
{"status": "in_progress", "current_stage": "stage_4_room_dimensions", "ui_data": {"display_type": "room_dimensions", "presets": [{"label": "Small", "width": 3, "length": 3}, {"label": "Medium", "width": 4, "length": 3.5}, {"label": "Large", "width": 5, "length": 4}]}}

[MODEL]:
What size is your bedroom? You can pick a preset or enter custom dimensions.

[USER]:
Medium, about 4 by 3.5 metres.

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891', room_dimensions={'width': 4.0, 'length': 3.5})

# tool_outputs
{"status": "ready_for_moodboard", "message": "All preferences collected. Ready to generate moodboard."}

# tool_code
create_style_moodboard(customer_id='CY-1234-1234', style_preferences=['modern', 'coastal'], room_type='bedroom', color_preferences=['blue', 'white'], room_purpose='redesign')

# tool_outputs
{"status": "success", "moodboard_id": "MOOD-73421", "product_count": 10, "products": [{"product_id": "BED-QUEEN-PLATFORM", "name": "Queen Platform Bed", "price": 699, "style_tags": ["modern"]}, {"product_id": "LAMP-ARC-FLOOR-GOLD", "name": "Arc Floor Lamp Modern Gold", "price": 249, "style_tags": ["modern", "coastal"]}, {"product_id": "CUSHION-VELVET-SET", "name": "Velvet Cushion Set", "price": 69, "style_tags": ["coastal"]}, {"product_id": "WALL-ART-COASTAL-PHOTO", "name": "Coastal Photography Print", "price": 89, "style_tags": ["coastal"]}, {"product_id": "RUG-MOROCCAN-STYLE", "name": "Moroccan Style Area Rug", "price": 299, "style_tags": ["modern", "bohemian"]}], "ui_data": {"display_type": "moodboard", "show_visualize_button": true}}

[MODEL]:
Here's your personalized moodboard! I've selected 10 products that blend modern and coastal styles in blue and white tones, including a queen platform bed, arc floor lamp, velvet cushions, coastal art, and a Moroccan rug.

Would you like to see how these products look in your actual bedroom?

[USER]:
Yes, show me a visualisation!

[MODEL]:
# tool_code (direct call, bypasses agent)
visualize_room_with_products(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-42891')

# tool_outputs
{"status": "success", "visualization_id": "VIZ-19283", "message": "Room visualization generated", "ui_data": {"display_type": "room_visualization", "image_base64": "<generated_image>", "products_shown": ["BED-QUEEN-PLATFORM", "LAMP-ARC-FLOOR-GOLD", "CUSHION-VELVET-SET", "WALL-ART-COASTAL-PHOTO", "RUG-MOROCCAN-STYLE"]}}

[MODEL]:
Here's how your bedroom could look with the modern coastal design! The products are placed naturally in your 4x3.5m space. Would you like to add any of these items to your cart?

[USER]:
Love it! Add the bed and the lamp to my cart.

[MODEL]:
# tool_code
modify_cart(customer_id='CY-1234-1234', items_to_add=[{'product_id': 'BED-QUEEN-PLATFORM', 'quantity': 1}, {'product_id': 'LAMP-ARC-FLOOR-GOLD', 'quantity': 1}])

# tool_outputs
{'status': 'success', 'updated_cart': {'cart_id': 'CART-112233', 'items': [{'product_id': 'BED-QUEEN-PLATFORM', 'name': 'Queen Platform Bed', 'quantity': 1, 'price': 699}, {'product_id': 'LAMP-ARC-FLOOR-GOLD', 'name': 'Arc Floor Lamp Modern Gold', 'quantity': 1, 'price': 249}], 'subtotal': 948}}

[MODEL]:
Added! Your cart now has the Queen Platform Bed (699 EUR) and the Arc Floor Lamp (249 EUR), totalling 948 EUR. Would you like to add any other items from the moodboard or explore delivery options?

</Example>

<Example 3: Home Decor Consultation - Child Bedroom with Themed Styles>
[USER]:
My daughter Mila needs a new bedroom, she just turned 7.

[MODEL]:
How exciting! Let me start a consultation for Mila's bedroom.

# tool_code
start_home_decor_consultation(customer_id='CY-1234-1234', initial_request='child bedroom for 7 year old daughter Mila')

# tool_outputs
{"status": "started", "session_id": "DECOR-CONSULT-55102", "ui_data": {"display_type": "room_selector", "room_options": ["Living Room", "Bedroom", "Kitchen", "Office", "Dining Room", "Bathroom"], "interaction_mode": "single_select"}}

# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-55102', room_type='bedroom')

# tool_outputs
{"status": "in_progress", "current_stage": "stage_1a_room_purpose"}

# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-55102', room_purpose='redesign')

# tool_outputs
{"status": "in_progress", "current_stage": "stage_1b_age_context"}

# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-55102', age_context='school-age')

# tool_outputs
{"status": "in_progress", "current_stage": "stage_2_style_discovery", "ui_data": {"display_type": "style_selector", "style_options": ["Underwater World", "Forest Adventure", "Northern Lights", "Space Explorer", "Safari Wild", "Rainbow Bright"], "interaction_mode": "multi_select"}}

[MODEL]:
Mila, which worlds do you love? I have some magical themes just for you -- Underwater World, Forest Adventure, Northern Lights, Space Explorer, Safari Wild, and Rainbow Bright!

[USER]:
She loves underwater and northern lights!

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-55102', style_preferences=['underwater_world', 'northern_lights'])

# tool_outputs
{"status": "in_progress", "current_stage": "stage_3_color_preferences", "ui_data": {"display_type": "color_selector", "color_options": ["Blue", "Purple", "Teal", "Pink", "White", "Silver"]}}

[MODEL]:
Beautiful choices! What colours does Mila like?

[USER]:
Purple and teal.

[MODEL]:
# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-55102', color_preferences=['purple', 'teal'])

# tool_outputs
{"status": "in_progress", "current_stage": "stage_4_room_dimensions"}

# tool_code
continue_home_decor_consultation(customer_id='CY-1234-1234', session_id='DECOR-CONSULT-55102', room_dimensions={'width': 3.5, 'length': 3.0})

# tool_outputs
{"status": "ready_for_moodboard"}

# tool_code
create_style_moodboard(customer_id='CY-1234-1234', style_preferences=['underwater_world', 'northern_lights'], room_type='bedroom', color_preferences=['purple', 'teal'], age_context='school-age', room_purpose='redesign')

# tool_outputs
{"status": "success", "moodboard_id": "MOOD-88120", "product_count": 10, "products": [{"product_id": "BED-SINGLE-WHITE", "name": "Single Bed White", "price": 299, "age_appropriate": ["school-age"]}, {"product_id": "LAMP-STRING-FAIRY", "name": "Fairy String Lights", "price": 29}, {"product_id": "DESK-CHILD-WHITE", "name": "Child Study Desk", "price": 189, "age_appropriate": ["school-age"]}, {"product_id": "BOOKSHELF-LOW-CHILD", "name": "Low Bookshelf for Children", "price": 149}], "ui_data": {"display_type": "moodboard", "show_visualize_button": true}}

[MODEL]:
Here's Mila's personalized moodboard! I've picked age-appropriate furniture and magical underwater and northern lights themed decor in purple and teal. There's a single bed, fairy string lights, a study desk, and a low bookshelf she can reach on her own. Want to see it all come together in a room visualisation?

</Example>
```
"""

    MAIN_EXAMPLES = FULL_SCRIPT_EXAMPLE
