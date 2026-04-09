# OTTO Home Decor Demo - Complete Dialog Script

## Phase 1: Initial Request & Room Selection

**User (Nova):** "I need help redesigning Mila's bedroom. She's starting school soon and we need a desk, a bigger bed, and more storage."

**Expected AI Response:**
- Detects "redesigning" + "bedroom" intent
- Shows room selector cards OR directly proceeds to purpose confirmation
- Message: "I can help you redesign Mila's bedroom! Let me ask a few questions to create the perfect space."

---

## Phase 2: Consultation - Gathering Context

### Step 1: Confirm Room Purpose
**Expected AI:** "Are you looking to redecorate or completely redesign the room?"

**User (Nova):** "Complete redesign - she needs new furniture."

---

### Step 2: Age Context
**Expected AI:** "To recommend the right furniture, could you tell me who the room is for?"

**User (Nova):** "Mila is starting school this fall - she's 6 years old."

**Expected AI Response:**
- Identifies age context: "school-age"
- Message: "Perfect! I'll recommend furniture appropriate for a school-age child."

---

### Step 3: Constraints - What to Keep/Remove
**Expected AI:** "Is there any existing furniture you'd like to keep in the room?"

**User (Nova):** "We want to keep the cube shelf. Everything else can go."

**Expected AI Response:**
- Records constraint: keep cube shelf
- Message: "Got it - we'll keep the cube shelf and design around it."

---

## Phase 3: Photo Analysis & Order History

### Step 1: Room Visualization Request
**Expected AI:** "Perfect! To create the best recommendations, I'd love to see the space. You can either take 2-3 photos or show me the room using your camera."

**User (Nova) - Option A (Photo Upload):** [Uploads 2 photos]
1. Entrance view showing bed and window
2. Opposite wall with the cube shelf

**User (Nova) - Option B (Live Video):** [Activates camera and pans around room]
- Shows entrance view with bed and window
- Pans to opposite wall with cube shelf
- AI receives 1 frame per second for real-time analysis

---

### Step 2: AI Analyzes Room + Order History
**Expected AI Response:**
- **If photos**: Analyzes uploaded images using Gemini Vision
- **If video**: Analyzes live video frames in real-time (1fps capture)
- Cross-references with order history
- Identifies: "Birch House Bed (Toddler)" and "Modular Cube Bookshelf" from 4 years ago
- Message: "I can see your bedroom! I've identified the birch house bed and cube shelf from your order 4 years ago."

---

### Step 3: Child Interaction - Address Mila
**Expected AI:** "Mila, what do you like doing most in your room?"

**User (Mila):** "Drawing! And listening to stories. And my fox pillow lives there."

**Expected AI Response:**
- Warm acknowledgment: "I love that you enjoy drawing and stories, Mila! We'll make sure your new room has a great space for both. And of course, your fox pillow will have a perfect spot!"

---

## Phase 4: Themed Style Finder

### Step 1: Child-Themed Style Selection
**Expected AI:** "Style Finder: Which worlds do you love? Everyone pick your favourites!"
- Because age context = school-age, the AI shows **6 child-themed tiles** (not adult styles):
  - Underwater World, Forest Adventure, Northern Lights, Space Explorer, Safari Wild, Rainbow Bright
- Each tile shows a themed room image generated with Imagen 3

**User (Mila):** "That one! With the dolphins!" [taps Underwater World]
**User (Mila):** "And the bright one. But no baby pink." [taps Northern Lights]
**User (Nova):** [clicks Continue]

**Expected AI Response:**
- Registers selections: underwater_world + northern_lights
- Message: "Great choices, Mila! Underwater World and Northern Lights combine beautifully -- ocean blues with cool aurora pastels."

---

### Step 2: Color Preferences
**Expected AI:** "Any color palette in mind? (Optional - you can skip)"
- Shows color selector with options

**User (Nova):** "Blue and white would be lovely."

**Expected AI Response:**
- Validates choices: "Blue and white will complement the underwater and northern lights themes perfectly!"

---

## Phase 5: Room Dimensions

**Expected AI:** "One last thing before I create your moodboard -- how big is Mila's bedroom? This helps me ensure the products fit your space perfectly."
- Shows preset size cards (Small / Medium / Large) and custom input fields

**User (Nova):** [Clicks "Medium" preset -- 4m x 3.5m, ~14 m2]

**Expected AI Response:**
- Records dimensions
- Message: "A 14 square metre room gives us plenty to work with!"

---

## Phase 6: Moodboard Generation

**Expected AI Actions (Behind the Scenes):**
- Filters furniture items by age-appropriateness (school-age)
- Matches style tags via theme keywords (underwater_world maps to coastal/nautical, northern_lights maps to scandinavian/modern/pastel)
- Coordinates with color palette (blue, white)
- Balances furniture (40%) and decor (60%)
- Respects constraints (keeps cube shelf, no duplicate storage)

**Expected AI Response:**
"I've created a personalized moodboard for Mila's room! Here are 10 curated products combining Underwater World and Northern Lights themes with your blue and white palette."

**Moodboard Contains:**
- 4 furniture pieces (bed, desk, chair, wardrobe)
- 6 decor items (wall art, lighting, textiles, plants)
- All items: age-appropriate, style-matched, color-coordinated
- **"Visualize in my room"** button at bottom of moodboard

---

## Phase 7: Room Visualization with Imagen 3

**User (Nova):** [Clicks "Visualize in my room" button on the moodboard]

**Expected AI Actions (Behind the Scenes):**
- Calls `visualize_room_with_products()` tool
- Builds detailed prompt from style (modern + scandinavian), room type (bedroom), dimensions (4m x 3.5m), and product names
- If room photos were uploaded earlier: uses Imagen 3 inpainting to render products into the actual room
- If no photos: generates a fresh photorealistic room rendering

**Expected AI Response:**
- Shows room visualization image with all selected products rendered in the space
- Displays room dimensions (4m x 3.5m, ~14 m2) and product tags
- Action buttons: "Add All to Cart" and "Try Another Look"
- Message: "Here is how Mila's bedroom could look with the modern Scandinavian design! All the products fit beautifully in the 14 m2 space."

**User (Nova):** "That looks amazing! Can you show me a different version?"

**Expected AI:** Regenerates visualization with same products in a slightly different arrangement.

---

## Phase 8: Cart & Recommendations

### Step 1: Add to Cart
**User (Nova):** "Add the bed and desk to my cart."

**Expected AI Response:**
- Adds items to cart
- Message: "I've added the Single Bed (White) and Child's Desk (White) to your cart. Total: €398."

---

### Step 2: Complementary Suggestions
**Expected AI:** "These would pair beautifully with your selections:
- Study Chair (Blue) - €79
- Desk Lamp (Modern White) - €45
Would you like to add any of these?"

**User (Nova):** "Not right now, but I'll save this moodboard."

**Expected AI Response:**
- Saves moodboard
- Message: "Perfect! Your moodboard is saved. You can return anytime to add the wardrobe, rug, or other items when you're ready."

---
