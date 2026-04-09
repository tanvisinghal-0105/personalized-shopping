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

## Phase 4: Style Discovery

### Step 1: Style Selection
**Expected AI:** "Now let's explore styles for Mila's bedroom. Choose one or more that resonate with you!"
- Shows style selector cards: Modern, Minimalist, Bohemian, Coastal, Industrial, Scandinavian, Traditional, Rustic

**User (Nova):** "Modern and Scandinavian look perfect."

---

### Step 2: Color Preferences
**Expected AI:** "Any color palette in mind? (Optional - you can skip)"
- Shows color selector with options

**User (Nova):** "Blue and white would be lovely."

**Expected AI Response:**
- Validates choices: "Great choices! Modern and Scandinavian styles with blue and white will create a clean, calm space perfect for studying and playing."

---

## Phase 5: Moodboard Generation

**Expected AI Actions (Behind the Scenes):**
- Filters 23 furniture items by age-appropriateness (school-age)
- Matches style tags (modern, scandinavian)
- Coordinates with color palette (blue, white)
- Balances furniture (40%) and decor (60%)
- Respects constraints (keeps cube shelf, no duplicate storage)

**Expected AI Response:**
"I've created a personalized moodboard for Mila's room! Here are 10 curated products combining modern and scandinavian styles with your blue and white palette."

**Moodboard Contains:**
- 4 furniture pieces (bed, desk, chair, wardrobe)
- 6 decor items (wall art, lighting, textiles, plants)
- All items: age-appropriate, style-matched, color-coordinated

---

## Phase 6: Cart & Recommendations

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
