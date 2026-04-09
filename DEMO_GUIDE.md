# Cymbal Shopping AI - Complete Demo Guide

## Overview
This guide demonstrates the **Cymbal Personalized Shopping AI Assistant** with advanced **Home Decor Consultation** features, including real-time photo analysis and intelligent product recommendations.

---

## Quick Start

### Access the Application
1. **Open the deployed frontend URL** in your browser
2. **Sign in** with test credentials:
   - First Name: Nova
   - Last Name: Anderson
   - Email: nova.anderson@example.com
3. **Click the floating chat button** (bottom right)
4. **Wait for connection** ("Connected as Nova" appears)

---

## Demo Scenario: Redesigning a Child's Bedroom

### Persona
**Parent:** Nova Anderson
**Child:** Mila (6 years old, starting school)
**Goal:** Redesign Mila's bedroom with age-appropriate furniture and decor

### Order History Context
Nova purchased 4 years ago:
- Birch House Bed (Toddler) - €299
- Modular Cube Bookshelf 3x3 - €199

---

## Demo Script (9 minutes)

### PHASE 1: Initial Request (30 seconds)

**Say or Type:**
> "I need help redesigning Mila's bedroom. She's starting school soon and we need a desk, a bigger bed, and more storage."

**Expected AI Behavior:**
- Detects home decor intent ("redesigning" + "bedroom")
- Starts home decor consultation automatically
- **Shows Room Selector UI** with interactive cards
- Says: *"I can help you redesign Mila's bedroom! Let me ask a few questions to create the perfect space. Which room would you like to decorate?"*

**User Action:**
- Click "Bedroom" card (should already be pre-selected based on voice input)
- Click "Continue"

---

### PHASE 2: Consultation - Gathering Context (2 minutes)

#### Step 1: Room Purpose (30 seconds)

**Expected AI:**
- **Shows Purpose Selector** (Decoration vs Redesign)
- Asks: *"Are you looking to redecorate or completely redesign the room?"*

**Say or Type:**
> "Complete redesign - she needs new furniture."

**User Action:**
- Click "Redesign" option
- Click "Continue"

---

#### Step 2: Age Context (30 seconds)

**Expected AI:**
- **Shows Age Selector** (Toddler / School-age / Teen / Adult)
- Asks: *"To recommend the right furniture, could you tell me who the room is for?"*

**Say or Type:**
> "Mila is starting school this fall - she's 6 years old."

**Expected AI Response:**
- Identifies age context: "school-age"
- Says: *"Perfect! I'll recommend furniture appropriate for a school-age child."*

**User Action:**
- Click "School-age" option
- Click "Continue"

---

#### Step 3: Constraints - What to Keep (30 seconds)

**Expected AI:**
- Asks: *"Is there any existing furniture you'd like to keep in the room?"*

**Say or Type:**
> "We want to keep the cube shelf. Everything else can go."

**Expected AI Response:**
- Records constraint: keep cube shelf
- Says: *"Got it - we'll keep the cube shelf and design around it."*

---

### PHASE 3: Photo Analysis & Order History (1.5 minutes)

#### Step 1: Room Visualization Request (15 seconds)

**Expected AI:**
- **Shows Photo Upload UI** with guidelines
- Says: *"Perfect! To create the best recommendations, I'd love to see the space. Could you take 2-3 photos showing different angles of the room?"*

**Photo Guidelines Displayed:**
- Show the entrance view with bed and window
- Capture the opposite wall with existing furniture
- Include any furniture you mentioned keeping

---

#### Step 2: Upload Photos (30 seconds)

**User Action - Option A: Upload Photos**
1. Click "Upload Photos" button
2. Select 2-3 bedroom photos from your device
3. Click "Submit Photos"

**User Action - Option B: Use Camera**
1. Click "Use Camera" button
2. Allow camera permissions
3. Take 2-3 photos of the room
4. Click "Submit Photos"

**Expected AI Behavior:**
- **[IMAGE INTERCEPTOR]** log appears in server logs
- **WebSocket handler intercepts** the images
- **Directly calls** `analyze_room_for_decor()` with base64 image data
- **Analyzes room** using Gemini Vision API
- **Cross-references** with order history
- **Identifies** the Birch House Bed and Cube Bookshelf from 4 years ago

**Expected AI Response:**
- Says: *"I can see your bedroom! I've identified the birch house bed and cube shelf from your order 4 years ago. These items were perfect for a toddler, but now that Mila is starting school, it's time for an upgrade!"*

---

#### Step 3: Child Interaction (45 seconds)

**Expected AI:**
- **Addresses the child directly**
- Asks: *"Mila, what do you like doing most in your room?"*

**Say or Type (as parent):**
> "Drawing! And listening to stories. And my fox pillow lives there."

**Expected AI Response:**
- Warm, child-friendly tone
- Says: *"I love that you enjoy drawing and stories, Mila! We'll make sure your new room has a great space for both. And of course, your fox pillow will have a perfect spot!"*

---

### PHASE 4: Style Discovery - Themed Style Finder (2 minutes)

#### Step 1: Child-Themed Style Selection (1 minute)

**Expected AI:**
- Because the room is for a **school-age child**, the Style Finder shows **6 child-themed visual tiles** (not adult styles):
  - **Underwater World** - Soft blues with dolphins, shells & ocean vibes
  - **Forest Adventure** - Warm greens & browns, woodland creatures
  - **Northern Lights** - Cool pastels, aurora colours & starry skies
  - **Space Explorer** - Deep navy & silver, planets & rockets
  - **Safari Wild** - Earthy tones, jungle animals & adventure
  - **Rainbow Bright** - Bold primary colours, playful & cheerful
- Each tile shows a themed room image generated with Imagen 3
- Title: *"Style Finder: Which worlds do you love?"*
- Subtitle: *"Everyone pick your favourites! Tap as many as you like."*

**Narration Point:**
> "Notice the AI detected this is a child's room and switched to imaginative themed styles instead of standard adult styles like Modern or Scandinavian."

**User Action (as Mila):**
1. Click "Underwater World" tile (checkmark appears) - *"That one! With the dolphins!"*
2. Click "Northern Lights" tile (checkmark appears) - *"And the bright one. But no baby pink."*
3. Click "Continue"

**Expected AI Response:**
- Says: *"Great choices, Mila! Underwater World and Northern Lights combine beautifully -- ocean blues with cool aurora pastels. A dreamy room!"*

---

#### Step 2: Color Preferences (1 minute)

**Expected AI:**
- **Shows Color Selector UI** with color chips:
  - Blue, White, Gray, Beige, Black, Gold, Green, Pink, Brown, Cream
- Says: *"Any color palette in mind? (Optional - you can skip)"*

**User Action:**
1. Click "Blue" chip (selected)
2. Click "White" chip (selected)
3. Click "Continue" (or "Skip")

**Expected AI Response:**
- Says: *"Blue and white will complement the underwater and northern lights themes perfectly!"*

---

### PHASE 5: Room Dimensions (30 seconds)

**Expected AI:**
- **Shows Room Dimensions UI** with preset sizes and custom input
- Says: *"One last thing before I create your moodboard -- how big is Mila's bedroom? This helps me ensure the products fit your space perfectly."*

**UI Shows:**
- **3 preset cards:** Small (3m x 2.5m, ~7.5 m2), Medium (4m x 3.5m, ~14 m2), Large (5m x 4m, ~20 m2)
- **Custom input:** Length (m) x Width (m) number fields
- Calculated area display

**User Action:**
1. Click "Medium" preset card (or enter custom dimensions)
2. Click "Continue"

**Expected AI Response:**
- Records dimensions
- Says: *"A 14 square metre room gives us plenty to work with!"*

---

### PHASE 6: Moodboard Generation (1 minute)

**Expected AI Behavior (Behind the Scenes):**
1. **Filters furniture** by age-appropriate tags (school-age only)
2. **Matches style tags** via theme keywords (underwater_world -> coastal/nautical, northern_lights -> scandinavian/modern/pastel)
3. **Coordinates colors** (blue + white palette)
4. **Balances categories:** 40% furniture + 60% decor
5. **Respects constraints:** No duplicate storage (cube shelf stays)
6. **Fetches images** for all recommended products
7. **Generates moodboard** with 10 curated items

**Expected AI Response:**
- **Shows Moodboard UI** with product cards
- **"Visualize in my room" button** at the bottom (gradient purple with sparkle icon)
- Says: *"I've created a personalized moodboard for Mila's Underwater World and Northern Lights bedroom! Here are 10 carefully curated products that work perfectly together."*

**Moodboard Contains (examples):**
- **Single Bed (White, School-age)** - ocean-blue bedding
- **Child's Desk (White)** - workspace ready
- **Study Chair (Blue)** - matches underwater palette
- **Coastal-themed Wall Art** - dolphins, ocean scene
- **Desk Lamp (Modern White)** - clean Northern Lights style
- **Area Rug (Blue/White)** - wave-pattern or aurora colours
- **Velvet Cushions (Blue)** - ocean-themed
- **Wall Shelves (White)** - for books and display
- Plus additional decor items matching the combined themes

**Total Value:** ~€1,200-1,500

---

### PHASE 7: Room Visualization with Imagen 3 (1 minute)

**User Action:**
- Click **"Visualize in my room"** button on the moodboard

**Expected AI Behavior (Behind the Scenes):**
1. **Calls** `visualize_room_with_products()` tool
2. **Builds prompt** from style preferences, room type, dimensions, and product names
3. **If room photo was uploaded:** Uses Imagen 3 `edit_image` (inpainting) to render products into the actual room photo
4. **If no room photo:** Uses Imagen 3 `generate_images` to create a fresh styled room rendering
5. **Returns** base64 image for display

**Expected AI Response:**
- **Shows Room Visualization UI** with:
  - Photorealistic rendering of Mila's bedroom with the selected products
  - Room dimensions label (4m x 3.5m, ~14 m2)
  - Product tags showing items in the visualization
  - **"Add All to Cart"** button
  - **"Try Another Look"** button for regeneration
- Says: *"Here is how Mila's bedroom could look with the modern Scandinavian design! All the products fit beautifully in the 14 m2 space."*

**Narration Point:**
> "The AI just rendered all the moodboard products directly into the customer's actual room using Imagen 3 -- they can see exactly how the new bedroom will look before buying."

---

### PHASE 8: Cart & Recommendations (1 minute)

#### Step 1: Add to Cart (30 seconds)

**Say or Type:**
> "Add the bed and desk to my cart."

**Expected AI Response:**
- **Calls modify_cart tool** with product IDs
- Updates cart state
- Says: *"I've added the Single Bed (White) and Child's Desk (White) to your cart. Your subtotal is €398."*

**User Action:**
- Click "Shopping Cart" icon (top right)
- **Verify:** 2 items in cart

---

#### Step 2: Complementary Suggestions (30 seconds)

**Expected AI (Proactive):**
- Says: *"These would pair beautifully with your selections:*
  - *Study Chair (Blue) - €79*
  - *Desk Lamp (Modern White) - €45*

  *Would you like to add any of these?"*

**Say or Type:**
> "Not right now, but I'll save this moodboard."

**Expected AI Response:**
- Says: *"Perfect! Your moodboard is saved. You can return anytime to browse the other items like the wardrobe, rug, or decor pieces when you're ready!"*

---

## Key Features to Highlight

### 1. Intelligent Intent Detection
- Automatically detects "redesigning bedroom" from voice
- Starts consultation without manual trigger

### 2. Multimodal Photo Analysis
- **NEW ARCHITECTURE:** WebSocket handler intercepts images
- Directly calls analysis tools with base64 image data
- No more "asking for clearer photos" bug
- Analyzes room using Gemini Vision API
- Supports both static photos and live camera

### 3. Order History Integration
- Cross-references past purchases
- Identifies furniture age (4 years = outgrown for school child)
- Suggests upgrades based on child's new age

### 4. Child-Centered Interaction
- Addresses child directly when appropriate
- Warm, encouraging tone
- Remembers personal details (fox pillow)

### 5. Smart Product Curation
- Filters 150+ products by:
  - Age-appropriateness
  - Style tags
  - Color palette
  - Room compatibility
- Balances furniture (40%) and decor (60%)
- Respects constraints (no duplicate storage)

### 6. Room Size Collection
- Preset size cards (Small / Medium / Large) tailored per room type
- Custom dimension input (length x width in metres)
- Calculated area display
- Ensures product recommendations fit the space

### 7. Room Visualization with Imagen 3
- Generates photorealistic room renderings with selected products
- Uses Imagen 3 inpainting when a customer room photo is available
- Falls back to fresh generation when no photo exists
- "Visualize in my room" button directly on the moodboard
- "Add All to Cart" and "Try Another Look" actions

### 8. Interactive Visual UI
- Room selector cards
- Style selector with bedroom images
- Color palette chips
- Room dimensions presets + custom input
- Photo upload interface
- Moodboard product grid with visualize button
- Room visualization display

### 9. Seamless Cart Integration
- Add items via voice or UI
- Real-time cart updates
- Proactive complementary suggestions

---

## Troubleshooting During Demo

### Issue: WebSocket not connecting
**Fix:**
- Check browser console for errors
- Verify backend is deployed and running
- Check `/tmp/server.log` for connection logs

### Issue: Photo analysis not working
**Fix:**
- Check server logs for `[IMAGE INTERCEPTOR]` logs
- Should see: "Active home decor session found"
- Should see: "Calling analyze_room_for_decor directly"
- Should NOT see: "asking for clearer photos"

### Issue: Moodboard not showing products
**Fix:**
- Check if products match selected styles
- Verify age_appropriate tags exist
- Check console for tool_result data

### Issue: Cart not updating
**Fix:**
- Check for modify_cart tool call in logs
- Verify product_id matches catalog exactly
- Check cart state in browser console

---

## Demo Success Metrics

### Must Work:
- [ ] Intent detection from voice
- [ ] Photo upload and analysis
- [ ] Order history cross-reference
- [ ] Child interaction (addressing Mila)
- [ ] Style selector UI
- [ ] Room dimensions collection
- [ ] Moodboard generation with 10 products
- [ ] Room visualization with Imagen 3
- [ ] Add to cart functionality

### Impressive Moments:
1. **"I've identified the birch house bed from 4 years ago"** - Order history magic
2. **"Mila, what do you like doing most in your room?"** - Child-centered approach
3. **Instant photo analysis** - No "clearer photos" bug
4. **Room dimensions UI** - Presets + custom input for spatial accuracy
5. **Curated moodboard** - 10 perfectly matched products
6. **"Visualize in my room"** - Imagen 3 renders products into the actual room
7. **Proactive suggestions** - "These would pair beautifully..."

---

## Recording Tips

### Camera Angles
1. **Wide shot:** Show full screen during style selection
2. **Close-up:** Highlight photo upload UI
3. **Split screen:** User speaking + moodboard appearing

### Narration Points
- "Notice how it detected 'redesigning' automatically"
- "The AI just analyzed the room photos in real-time"
- "See how it's addressing the child directly"
- "All 10 products match the modern Scandinavian style"

### Timing
- **Total:** 9 minutes
- **Sweet spot:** 6 minutes (skip color selection and room dimensions)
- **Quick demo:** 4 minutes (skip constraints, child interaction, and visualization)

---

## Advanced Features (Optional to Demo)

### 1. Live Video Analysis
Instead of uploading photos, click "Use Camera" and pan around the room. The AI receives 1 frame per second for real-time analysis.

### 2. Voice-Only Interaction
Complete the entire consultation using only voice commands. The AI handles everything via audio.

### 3. Multi-Language Support
Change language in settings to demonstrate international capability.

### 4. Interrupt & Correct
While AI is speaking, interrupt to correct information:
> "Actually, Mila is 7, not 6"
