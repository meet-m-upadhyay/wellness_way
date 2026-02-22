# Complete ML Pipeline Architecture - Detailed Explanation

## Table of Contents
1. [Overview](#overview)
2. [Current System Architecture](#current-system-architecture)
3. [ML Pipeline Components](#ml-pipeline-components)
4. [How Ingredients Are Fetched](#how-ingredients-are-fetched)
5. [How Recipes Are Generated](#how-recipes-are-generated)
6. [Role of AI in Current System](#role-of-ai-in-current-system)
7. [Data Flow](#data-flow)
8. [Why Recipes Repeat](#why-recipes-repeat)
9. [Future Improvements](#future-improvements)

---

## Overview

After implementing the ML pipeline, your application now has **TWO separate pipelines** running side-by-side:

1. **AI Pipeline** (Original) - Currently DISABLED in UI
2. **ML Pipeline** (New) - Currently ACTIVE in UI

The ML pipeline uses **deterministic templates** with **minimal AI involvement**, making it faster and more predictable than the AI pipeline.

---

## Current System Architecture

### High-Level Flow
```
User Request
    ↓
Frontend (React)
    ↓
API Endpoints (/diet-plans-ml/*)
    ↓
ML Pipeline Orchestrator
    ↓
[6 Components Working Together]
    ↓
Database (PostgreSQL)
    ↓
Frontend Display
```

### Two Pipelines Comparison

| Aspect | AI Pipeline (Disabled) | ML Pipeline (Active) |
|--------|----------------------|---------------------|
| **Endpoints** | `/diet-plans/*` | `/diet-plans-ml/*` |
| **Ingredient Selection** | AI chooses ingredients | Hardcoded templates |
| **Recipe Generation** | AI generates recipes | Template-based + fallback text |
| **Nutrition Calculation** | Deterministic | Deterministic (same) |
| **Speed** | Slow (2-5 sec/meal) | Fast (1-2 sec/meal) |
| **Variety** | High (AI creativity) | Limited (17 templates) |
| **Reliability** | Can fail/retry | Always succeeds |
| **UI Buttons** | 🤖 (commented out) | 🧠 (visible) |

---

## ML Pipeline Components

The ML pipeline consists of **6 main components** that work together:

### 1. Orchestrator (`orchestrator.py`)
**Role**: Master coordinator that glues everything together

**What it does**:
- Receives user request (daily or weekly plan)
- Calls all other components in sequence
- Handles errors gracefully
- Returns complete meal plan

**Key Methods**:
- `generate_daily_plan()` - Creates one day of meals
- `generate_weekly_plan()` - Creates 7 days (calls daily 7 times)
- `_build_meal_from_template()` - Converts template to actual meal

### 2. Meal Template Registry (`meal_templates.py`)
**Role**: Stores hardcoded meal templates

**What it contains**:
- **17 predefined meal templates**
- Each template has:
  - Template ID (e.g., "protein_scramble")
  - Name (e.g., "Protein Scramble")
  - Meal slot (breakfast/lunch/dinner/snack)
  - **Hardcoded ingredient list** (e.g., ["eggs (whole)", "spinach", "olive oil"])
  - Diet types it supports (vegetarian, vegan, etc.)
  - Tags (high-protein, quick, etc.)

**Example Template**:
```python
MealTemplate(
    template_id="protein_scramble",
    name="Protein Scramble",
    meal_slot=MealSlot.BREAKFAST,
    ingredients=["eggs (whole)", "spinach", "olive oil", "tomatoes"],
    diet_types={DietType.VEGETARIAN, DietType.EGGETARIAN},
    tags=["high-protein", "quick"]
)
```

**THIS IS WHY RECIPES REPEAT** - Only 17 templates exist!

### 3. Meal Template Selector (`meal_template_selector.py`)
**Role**: Chooses which template to use for each meal

**How it works**:
1. Filters templates by diet type (vegetarian, vegan, etc.)
2. Filters out templates with allergens
3. Scores remaining templates using heuristics:
   - Base score: 50 points
   - High-protein bonus: +15 points
   - Vegan match: +10 points
   - Quick breakfast: +5 points
   - Random variety: ±5 points
4. Selects highest-scoring template
5. Tracks used templates to avoid immediate repeats

**Scoring Example**:
```
Template: "protein_scramble"
- Base score: 50
- High-protein match: +15 (user needs protein)
- Quick breakfast: +5 (breakfast slot)
- Random factor: +2.3
= Total: 72.3 points
```

### 4. Nutrition Engine Adapter (`nutrition_engine_adapter.py`)
**Role**: Calculates nutrition using existing nutrition database

**What it does**:
- Looks up ingredients in nutrition database
- Calculates calories, protein, carbs, fat, fiber
- **100% deterministic** - no AI involved
- Aggregates nutrition for meals and days

**Process**:
```python
# For each ingredient:
nutrition = nutrition_db.get_nutrition(
    food_name="eggs (whole)",
    weight_g=100  # Initial portion
)
# Returns: {calories: 143, protein: 12.6g, ...}
```

### 5. Scaling Engine (`scaling_engine.py`)
**Role**: Adjusts portion sizes to meet calorie/protein targets

**How it works**:
1. Calculates current meal nutrition
2. Compares to target (e.g., 600 calories)
3. Calculates scale factor (e.g., 1.5x)
4. Multiplies all ingredient quantities by scale factor
5. Recalculates nutrition with new portions

**Example**:
```
Original: 100g eggs = 143 calories
Target: 600 calories for meal
Scale factor: 600/400 = 1.5x
New: 150g eggs = 215 calories
```

**Soft Acceptance**: If target can't be met perfectly, accepts ±15% deviation

### 6. GenAI Text Generator (`genai_text_generator.py`)
**Role**: Generates meal names and cooking instructions

**IMPORTANT**: This is the ONLY place AI is used in ML pipeline!

**What AI generates**:
- Meal name (e.g., "Protein Scramble")
- Cooking instructions
- Meal description

**What AI CANNOT change**:
- Ingredients (read-only from template)
- Quantities (already calculated)
- Nutrition values (already calculated)

**Current Status**: Using **fallback text** (no AI calls yet)
```python
# Deterministic fallback:
meal_name = f"{ingredient1} and {ingredient2} {meal_type}"
instructions = "1. Prepare ingredients\n2. Cook\n3. Serve"
```

---


## How Ingredients Are Fetched

### Current Implementation (ML Pipeline)

**Ingredients are NOT fetched - they are HARDCODED in templates!**

Here's the complete flow:

#### Step 1: Template Selection
```python
# User wants breakfast, vegetarian
template = selector.select_template(
    diet_type=DietType.VEGETARIAN,
    meal_slot=MealSlot.BREAKFAST
)

# Returns template with HARDCODED ingredients:
template.ingredients = [
    "eggs (whole)",
    "spinach", 
    "olive oil",
    "tomatoes"
]
```

#### Step 2: Ingredient Validation
```python
# Check if ingredients exist in nutrition database
for ingredient_name in template.ingredients:
    nutrition = nutrition_db.get_nutrition(
        food_name=ingredient_name,
        weight_g=100
    )
    # If not found, skip ingredient
    # If found, use it
```

#### Step 3: Nutrition Lookup
```python
# For "eggs (whole)":
nutrition_db.get_nutrition("eggs (whole)", 100)
# Returns from database:
{
    "calories": 143,
    "protein": 12.6,
    "carbohydrates": 0.7,
    "fat": 9.5,
    "fiber": 0
}
```

### Nutrition Database Source

The nutrition database (`nutrition_database.py`) contains:
- **Pre-loaded food data** from USDA or similar sources
- Stored in PostgreSQL database
- Accessed via `get_nutrition(food_name, weight_g)`

**Key Point**: Ingredients must match EXACTLY what's in the database:
- ✅ "eggs (whole)" - works
- ❌ "eggs" - might not work
- ❌ "whole eggs" - might not work

This is why templates use specific names like:
- "oats (rolled, dry)"
- "brown rice (dry)"
- "greek yogurt (plain)"

### Ingredient Canonicalizer (Currently Unused)

There's an ML component (`ingredient_canonicalizer.py`) that COULD:
- Take fuzzy ingredient names (e.g., "egg")
- Use sentence transformers to find closest match
- Return canonical name (e.g., "eggs (whole)")

**But it's not being used** because templates already have exact names!

---

## How Recipes Are Generated

### Complete Recipe Generation Flow

#### 1. User Requests Plan
```
User clicks: "🧠 Generate Plan (ML)"
    ↓
Frontend: POST /diet-plans-ml/daily
    ↓
Backend: orchestrator.generate_daily_plan()
```

#### 2. Template Selection (Per Meal)
```python
# For breakfast:
breakfast_template = selector.select_template(
    diet_type="vegetarian",
    meal_slot="breakfast",
    calorie_target=600,
    protein_target=20
)
# Returns: "protein_scramble" template
```

#### 3. Build Meal from Template
```python
meal = {
    "type": "breakfast",
    "name": "Protein Scramble",  # From template
    "ingredients": [
        {
            "name": "eggs (whole)",
            "quantity": 100,  # Initial
            "unit": "g",
            "nutrition": {
                "calories": 143,
                "protein": 12.6,
                ...
            }
        },
        {
            "name": "spinach",
            "quantity": 100,
            "unit": "g",
            "nutrition": {...}
        },
        ...
    ],
    "nutrition": {
        "calories": 400,  # Sum of all ingredients
        "protein": 25,
        ...
    }
}
```

#### 4. Scale to Target
```python
# Current: 400 calories
# Target: 600 calories
# Scale factor: 1.5x

scaled_meal = scaling_engine.scale_meal_to_target(
    meal=meal,
    target_calories=600,
    target_protein=20
)

# Now all quantities are multiplied by 1.5:
# eggs: 100g → 150g
# spinach: 100g → 150g
# calories: 400 → 600
```

#### 5. Generate Text (AI or Fallback)
```python
text = text_generator.generate_meal_text(
    ingredients=scaled_meal["ingredients"],
    meal_type="breakfast",
    diet_type="vegetarian"
)

# Currently returns fallback:
{
    "name": "Eggs and Spinach Breakfast",
    "instructions": "1. Prepare ingredients\n2. Cook\n3. Serve",
    "description": "A nutritious vegetarian breakfast..."
}
```

#### 6. Validate
```python
validation = validator.validate_daily_plan(
    meals=[breakfast, lunch, dinner],
    diet_type="vegetarian",
    target_calories=2000
)

# Checks:
# - Diet compliance (no meat for vegetarian)
# - Calorie range (within ±15%)
# - Protein minimum met
# - No allergens

# Returns warnings, not errors (soft acceptance)
```

#### 7. Return to Frontend
```json
{
    "plan_type": "daily",
    "date": "2026-02-08",
    "meals": [
        {
            "type": "breakfast",
            "name": "Eggs and Spinach Breakfast",
            "ingredients": [
                {
                    "name": "eggs (whole)",
                    "quantity": 150,
                    "unit": "g",
                    "nutrition": {...}
                },
                ...
            ],
            "instructions": "1. Prepare...",
            "nutrition": {
                "calories": 600,
                "protein": 20,
                ...
            }
        },
        ...
    ],
    "daily_totals": {
        "calories": 2000,
        "protein": 80,
        ...
    }
}
```

---

## Role of AI in Current System

### AI Pipeline (Disabled - 🤖 Buttons)

**Full AI involvement**:
1. **Ingredient Selection**: AI chooses ingredients based on user preferences
2. **Quantity Determination**: AI suggests portions
3. **Recipe Creation**: AI writes full recipes
4. **Meal Names**: AI generates creative names
5. **Instructions**: AI writes detailed cooking steps

**Problems**:
- Slow (multiple AI API calls)
- Can fail or hallucinate
- Requires retries
- Expensive (API costs)

### ML Pipeline (Active - 🧠 Buttons)

**Minimal AI involvement**:
1. ❌ Ingredient Selection: **Hardcoded templates**
2. ❌ Quantity Determination: **Math-based scaling**
3. ❌ Nutrition Calculation: **Database lookup**
4. ✅ Meal Names: **AI generates** (currently fallback)
5. ✅ Instructions: **AI writes** (currently fallback)

**Current Reality**: **ZERO AI calls** - using fallback text!

**Why?**:
```python
# In genai_text_generator.py:
def generate_meal_text(...):
    try:
        # TODO: Call LLM with constrained prompt
        result = self._generate_fallback_text(...)  # Using this!
        return result
    except:
        return self._generate_fallback_text(...)
```

The AI integration is **prepared but not activated**. Currently using deterministic fallback text.

### AI vs ML Comparison

| Component | AI Pipeline | ML Pipeline |
|-----------|-------------|-------------|
| Ingredient Selection | ✅ AI | ❌ Templates |
| Quantities | ✅ AI | ❌ Math |
| Nutrition | ❌ Database | ❌ Database |
| Meal Names | ✅ AI | ⚠️ Fallback (AI ready) |
| Instructions | ✅ AI | ⚠️ Fallback (AI ready) |
| Speed | Slow | Fast |
| Reliability | Medium | High |
| Variety | High | Low |

---


## Data Flow - Complete Journey

### 1. User Clicks "Generate Plan"

```
Frontend: DietPlans.tsx
    ↓
handleGeneratePlan() called
    ↓
apiClient.generateDietPlan(userId, "daily", {useML: true})
    ↓
POST /api/v1/diet-plans-ml/daily
```

### 2. Backend Receives Request

```
diet_plans_ml.py: generate_daily_plan_ml()
    ↓
1. Get user's Health Context Document (HCD)
2. Extract: diet_type, calorie_target, protein_target, allergies
3. Call orchestrator.generate_daily_plan()
```

### 3. Orchestrator Generates Plan

```
orchestrator.py: generate_daily_plan()
    ↓
For each meal (breakfast, lunch, dinner):
    ↓
    A. Select Template
        ↓
        template_selector.select_template()
            ↓
            - Filter by diet type
            - Filter by allergies
            - Score templates
            - Return best match
    ↓
    B. Build Meal
        ↓
        For each ingredient in template:
            ↓
            nutrition_db.get_nutrition(ingredient, 100g)
                ↓
                Returns: {calories, protein, carbs, fat, fiber}
            ↓
            Add to ingredients list
        ↓
        Calculate meal nutrition (sum all ingredients)
    ↓
    C. Scale Meal
        ↓
        scaling_engine.scale_meal_to_target()
            ↓
            - Calculate scale factor (target/current)
            - Multiply all quantities by scale factor
            - Recalculate nutrition
    ↓
    D. Generate Text
        ↓
        text_generator.generate_meal_text()
            ↓
            Returns: {name, instructions, description}
            (Currently: deterministic fallback)
    ↓
    E. Add to meals list
    ↓
Next meal...
    ↓
F. Calculate Daily Totals
    ↓
    Sum all meal nutrition
    ↓
G. Validate Plan
    ↓
    validation_engine.validate_daily_plan()
        ↓
        - Check diet compliance
        - Check calorie range
        - Check protein minimum
        ↓
        Returns: {passed: true, warnings: [...]}
    ↓
H. Return Plan Data
```

### 4. Save to Database

```
diet_plans_ml.py:
    ↓
Create DietPlan object:
    - user_id
    - hcd_id
    - plan_type: "daily"
    - start_date
    - content: {plan_data}  # JSON
    ↓
db.add(diet_plan)
db.commit()
    ↓
flag_modified(plan, "content")  # Tell SQLAlchemy to save
    ↓
Return DietPlanResponse
```

### 5. Frontend Displays Plan

```
DietPlans.tsx:
    ↓
setCurrentPlan({...response.data})  # Force re-render
    ↓
Render DailyPlanView or WeeklyPlanView
    ↓
For each meal:
    ↓
    MealCard component:
        ↓
        Display:
        - Meal name
        - Nutrition (calories, protein, carbs, fat)
        - Ingredients (collapsible)
        - Instructions (collapsible)
        - 🧠 Regenerate button
```

### 6. User Clicks "Regenerate Meal"

```
MealCard: onClick={() => onRegenerate(true)}
    ↓
DietPlans.tsx: handleRegenerateMeal(dayIndex, mealType, useML=true)
    ↓
apiClient.regenerateMeal(planId, dayIndex, mealIndex, userId, useML=true)
    ↓
POST /api/v1/diet-plans-ml/{planId}/regenerate-meal-ml
    ↓
Backend:
    1. Get existing plan from database
    2. Generate NEW meal (same process as above)
    3. Replace meal at index
    4. Recalculate daily totals
    5. flag_modified(plan, "content")
    6. Save to database
    7. Return updated plan
    ↓
Frontend:
    setCurrentPlan({...response.data})
    ↓
UI updates with new meal
```

---

## Why Recipes Repeat

### Root Cause: Limited Template Library

**The system has only 17 hardcoded templates:**

#### Breakfast (4 templates)
1. Protein Scramble (eggs, spinach, olive oil, tomatoes)
2. Oatmeal Bowl (oats, milk, banana, almonds)
3. Vegan Smoothie Bowl (banana, berries, almond milk, chia seeds, oats)
4. Greek Yogurt Parfait (greek yogurt, berries, almonds)

#### Lunch (5 templates)
1. Chicken Rice Bowl (chicken, brown rice, broccoli, bell peppers, olive oil)
2. Lentil Curry (lentils, tomatoes, onions, spinach, brown rice, olive oil)
3. Quinoa Salad (quinoa, chickpeas, cucumber, tomatoes, olive oil)
4. Paneer Tikka Bowl (paneer, bell peppers, onions, brown rice, yogurt)
5. Tofu Stir Fry (tofu, broccoli, bell peppers, brown rice, olive oil)

#### Dinner (5 templates)
1. Grilled Salmon with Vegetables (salmon, sweet potato, broccoli, olive oil)
2. Chickpea Pasta (chickpeas, tomatoes, spinach, olive oil)
3. Egg Fried Rice (eggs, brown rice, bell peppers, onions, olive oil)
4. Black Bean Tacos (black beans, avocado, tomatoes, onions)
5. Turkey with Sweet Potato (turkey, sweet potato, broccoli, olive oil)

#### Snacks (3 templates)
1. Protein Shake (whey protein, banana, almond milk, peanut butter)
2. Hummus with Vegetables (hummus, bell peppers, cucumber)
3. Mixed Nuts and Fruit (almonds, walnuts, apple)

### Why You See Repeats

#### Daily Plan (3 meals)
- Breakfast: 4 options
- Lunch: 5 options (filtered by diet type)
- Dinner: 5 options (filtered by diet type)

**For vegetarian**:
- Breakfast: 4 options
- Lunch: 4 options (no chicken)
- Dinner: 4 options (no salmon, turkey)
- **Total combinations**: 4 × 4 × 4 = **64 possible daily plans**

#### Weekly Plan (7 days × 3 meals = 21 meals)
- With only 4-5 templates per meal slot
- You'll see repeats within the same week!

**Example Week**:
```
Monday Breakfast: Protein Scramble
Tuesday Breakfast: Oatmeal Bowl
Wednesday Breakfast: Smoothie Bowl
Thursday Breakfast: Yogurt Parfait
Friday Breakfast: Protein Scramble  ← REPEAT!
Saturday Breakfast: Oatmeal Bowl    ← REPEAT!
Sunday Breakfast: Smoothie Bowl     ← REPEAT!
```

### Variety Mechanism (Limited)

The template selector tries to add variety:

```python
# Track used templates
used_template_ids = set()

# For each meal:
template = select_template(
    constraints,
    exclude_templates=used_template_ids  # Don't use these
)

used_template_ids.add(template.template_id)
```

**But**:
- Only prevents repeats **within the same generation**
- If you regenerate a meal, it might pick the same template again
- Weekly plans will have repeats because 7 days > 4 breakfast templates

### Random Factor

Small randomness in scoring (±5 points):
```python
random_factor = random.uniform(-5.0, 5.0)
score += random_factor
```

This provides **slight** variety in which template is chosen, but doesn't solve the fundamental problem of limited templates.

---

## Future Improvements

### 1. Expand Template Library

**Current**: 17 templates
**Goal**: 100+ templates

Add more templates for each meal slot:
- 20+ breakfast options
- 30+ lunch options
- 30+ dinner options
- 20+ snack options

**Benefits**:
- More variety
- Less repetition
- Better user experience

### 2. Enable AI Text Generation

**Current**: Using fallback text
**Goal**: Activate AI for meal names and instructions

```python
# In genai_text_generator.py:
def generate_meal_text(...):
    # Call actual LLM API
    response = llm_api.generate(
        prompt=f"Generate a creative name for a meal with {ingredients}",
        max_tokens=50
    )
    return response
```

**Benefits**:
- Creative meal names
- Detailed cooking instructions
- Better user engagement

**Constraint**: Ingredients and nutrition stay deterministic!

### 3. Implement ML Template Selector

**Current**: Heuristic scoring
**Goal**: Train ML model to predict best template

```python
# Train model on user preferences:
model = LightGBM()
model.train(
    features=[diet_type, meal_slot, time_of_day, season, previous_meals],
    target=user_rating
)

# Use for selection:
best_template = model.predict(user_features)
```

**Benefits**:
- Personalized recommendations
- Learn user preferences over time
- Better template selection

### 4. Dynamic Ingredient Substitution

**Current**: Fixed ingredients per template
**Goal**: Allow ingredient swaps

```python
# Template with alternatives:
template = {
    "base": ["protein", "grain", "vegetable"],
    "protein_options": ["chicken", "tofu", "paneer", "eggs"],
    "grain_options": ["rice", "quinoa", "pasta"],
    "vegetable_options": ["broccoli", "spinach", "bell peppers"]
}

# Select based on user preferences:
meal = build_meal_with_substitutions(template, user_preferences)
```

**Benefits**:
- Infinite variety from limited templates
- Accommodate preferences
- Reduce repetition

### 5. User Feedback Loop

**Goal**: Learn from user actions

```python
# Track user behavior:
if user_regenerates_meal:
    # This template wasn't liked
    template_score -= 10

if user_completes_meal:
    # This template was good
    template_score += 5

# Use scores for future selections
```

**Benefits**:
- Personalized over time
- Avoid disliked meals
- Recommend favorites

### 6. Seasonal and Regional Templates

**Goal**: Add context-aware templates

```python
# Winter templates:
- Warm soups
- Hearty stews
- Hot beverages

# Summer templates:
- Cold salads
- Smoothies
- Grilled items

# Regional:
- Indian: dal, roti, sabzi
- Mediterranean: hummus, falafel, tabbouleh
- Asian: stir-fries, rice bowls, noodles
```

**Benefits**:
- Culturally relevant
- Seasonally appropriate
- More engaging

---

## Summary

### Current State

**ML Pipeline is Active**:
- ✅ Fast and reliable
- ✅ Deterministic nutrition
- ✅ No AI failures
- ❌ Limited variety (17 templates)
- ❌ Recipes repeat
- ❌ Generic text (fallback)

**AI Pipeline is Disabled**:
- ✅ High variety
- ✅ Creative recipes
- ❌ Slow
- ❌ Can fail
- ❌ Expensive

### How It Works

1. **Templates**: Hardcoded ingredient lists (17 total)
2. **Selection**: Heuristic scoring picks best template
3. **Nutrition**: Database lookup (deterministic)
4. **Scaling**: Math-based portion adjustment
5. **Text**: Fallback generation (AI ready but not active)
6. **Validation**: Rules-based checks (soft acceptance)

### Why Recipes Repeat

- Only 17 templates exist
- 4 breakfast, 5 lunch, 5 dinner, 3 snacks
- Weekly plans need 21 meals (7 days × 3 meals)
- **Math**: 21 meals > 17 templates = guaranteed repeats

### The Trade-off

**ML Pipeline** = Speed + Reliability - Variety
**AI Pipeline** = Variety + Creativity - Speed - Reliability

You chose **ML for production** because reliability > variety.

### Next Steps to Improve

1. **Short-term**: Add more templates (easy, no code changes)
2. **Medium-term**: Enable AI text generation (creative names/instructions)
3. **Long-term**: Implement ML model for personalization

---

**End of Document**
