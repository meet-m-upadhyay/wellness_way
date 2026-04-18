I want to significantly improve the meal generation quality in this diet 
planner app. The current approach produces meals that feel like random 
food items stitched together to hit macros, and the nutrition data is 
often inaccurate for Indian cuisine (currently using API Ninjas / USDA, 
which is US-centric).

We're going to build a new, parallel system. DO NOT modify or delete the 
existing `food_items` table or the current meal generation flow — keep 
them running as-is. Create new tables and new service/route files 
alongside the existing ones. Once the new system is validated, we'll 
migrate and deprecate the old one. Name new tables and modules clearly 
(e.g., prefix with `v2_` or put under a `meal_engine/` module) so the 
separation is obvious.

=== GOALS ===

1. Meals should feel like REAL dishes someone would actually eat, not 
   macro-optimized ingredient piles. A grandmother should recognize it 
   as a meal.

2. Nutrition data should be accurate per cuisine — especially for Indian 
   food, which USDA handles poorly.

3. Meals should be scored for quality before being shown to the user, 
   with auto-regeneration for low scores.

4. Macros should be displayed in priority order based on the user's goal.

=== IFCT DATA SOURCE ===

Use the npm package `@ifct2017/compositions` (MIT licensed) as the 
source for seeding v2_ingredients. It provides 528 foods from the 
official IFCT 2017 publication with regional names across 15 Indian 
languages and ~151 nutrient fields per food.

Implementation:
1. Write a one-time seed script (seed_ifct.js or similar) that:
   - Loads @ifct2017/compositions
   - Iterates all 528 foods
   - Maps IFCT fields to v2_ingredients schema
   - Extends each row with additional app-specific fields I'll populate 
     later: common_serving_units (JSON), custom_aliases (array), 
     cooked_or_raw flag, meal_archetype_roles (array of roles this 
     ingredient can fill: "grain", "protein", "gravy_base", etc.)
   - Sets data_source = 'ifct_2017'
   - Sets confidence = 'verified'

2. If the main backend isn't Node.js, keep the seed script as a 
   standalone Node.js utility under scripts/seed/, invoked manually.

3. Design v2_ingredients schema to accommodate:
   - All IFCT composition fields (macros + micronutrients)
   - Regional name search (store the `lang` field; add a GIN/full-text 
     index for multilingual lookup)
   - Per-100g basis (IFCT standard)
   - App-specific extensions listed above

4. Build the nutrition provider so Indian cuisine lookups query 
   v2_ingredients first, with Nutritionix/Edamam as fallback for 
   composite dishes or items not in IFCT's 528.

5. Flag IFCT entries that are "raw" vs "cooked" clearly, because the 
   LLM will output both and mixing them up causes large errors.

6. Run seed validation checks:
    After seeding completes, run basic data integrity checks and log 
    warnings (don't fail the seed):
    - All foods in `grup` groups like "Cereals and Millets", "Green Leafy 
    Vegetables", "Fruits", "Roots and Tubers" should have cholesterol = 0
    - All foods in "Milk and Milk Products", "Egg and Egg Products", 
    "Fish, Shellfish", "Meat and Poultry" should have cholesterol > 0
    - Report any violations as potential data issues
    - Report count of foods per food_group
    - Report count of foods with form = 'unspecified' (needs manual review)

=== IFCT DATA STRUCTURE (based on actual package output) ===

The @ifct2017/compositions package returns per-100g nutrition data 
with ~150 fields per food. Key facts the seed script must handle:

## Unit Conventions (CRITICAL — get this wrong and all macros break)
- enerc: energy in kilojoules (kJ). Store as-is but ALSO compute and 
  store kcal = enerc / 4.184 for app display.
- Macros (protcnt, fatce, choavldf, fibtg, water, ash): grams per 100g
- Minerals (ca, fe, mg, zn, na, k, p, etc.): grams per 100g — multiply 
  by 1000 to display as mg, which is what users expect
- Vitamins: grams per 100g — convert to mg or mcg for display 
  depending on nutrient (vita, vitd in mcg; vitc, vitb in mg)
- Fatty acids (fasat, fams, fapu, fatrn, facn3, facn6): grams per 100g

## Field Selection — Store Only What's Needed
The package returns ~150 fields. Do NOT store all of them. The 
v2_ingredients schema should have a curated column set:

REQUIRED (macro display + macros that feed scoring):
- kcal (derived from enerc)
- enerc_kj (raw)
- protcnt (protein, g)
- fatce (total fat, g)
- choavldf (available carbs, g) — use this, not `cho`
- fibtg (fiber, g)
- water, ash

IMPORTANT (for scoring, diet filters, advanced display):
- fasat (saturated fat)
- fams (MUFA), fapu (PUFA), fatrn (trans fat)
- facn3 (omega-3), facn6 (omega-6)
- fsugar (free sugars)
- starch
- Key minerals: ca, fe, mg, zn, na, k, p
- Key vitamins: vita, vitc, vitd, vitb, vite, folsum (folate)
- cholc (cholesterol — note: 0 for plant foods, useful for heart-health diets)

STORE AS JSON BLOB (raw passthrough for future use):
- Everything else (individual amino acids, specific fatty acids, 
  polyphenols, organic acids) → store in a `raw_ifct_data` JSONB column 
  so we never have to re-seed if we want a nutrient later.

ERROR/UNCERTAINTY FIELDS:
- IFCT provides `_e` fields for every nutrient (e.g., protcnt_e).
- Don't create 150 extra columns. Store as JSONB in a `nutrient_errors` 
  column for any future confidence work.

## Regional Names — Parse the `lang` Field
The `lang` field is a single string like:
"A. Paneer; B. Chena; E. Cottage Cheese; G. Paneer; H. Chhena; Kan. Tali; ..."

Each prefix maps to a language:
  A. = Assamese, B. = Bengali, E. = English, G. = Gujarati,
  H. = Hindi, Kan. = Kannada, Kash. = Kashmiri, Kh. = Khasi,
  Kon. = Konkani, Mal. = Malayalam, M. = Manipuri, O. = Odia,
  P. = Punjabi, Tam. = Tamil, Tel. = Telugu, U. = Urdu

During seed:
- Parse this string into a structured `regional_names` JSONB field 
  mapped by language code
- ALSO flatten into a separate `search_aliases` array (e.g., 
  ["Paneer", "Chena", "Cottage Cheese", "Chhena", "Tali", ...])
- Create a GIN index on search_aliases for fast multilingual lookup 
  when the LLM outputs "chhena" or "chenna" instead of "paneer"

## Region Codes
The `regn` field is numeric (1-6). Verify the mapping by inspecting 
multiple foods — likely corresponds to India's six geographic zones 
(North, South, East, West, Central, North-East). Create a 
v2_regions lookup table.

## Cooked vs Raw Inference
IFCT doesn't flag this explicitly. During seed, infer from the `name` 
field using keyword matching:
- Contains "raw", "uncooked", "dry" → form = 'raw'
- Contains "cooked", "boiled", "steamed", "fried", "roasted" → 
  form = 'cooked'
- Otherwise → form = 'unspecified', flag for manual review

Store `form` as an enum column. This is critical because rice (raw) 
vs rice (cooked) has ~3x different calorie density per gram.

## Diet Tags
The `tags` field contains space-separated diet labels:
"vegetarian eggetarian fishetarian veg"

Split into a `diet_tags` array column. Use for filtering in meal 
generation (e.g., user is vegetarian → exclude foods without 
"vegetarian" tag).

## Schema Summary (v2_ingredients key columns)
- id, code (IFCT code like L003), name, scientific_name
- food_group (from `grup`)
- region_code (from `regn`)
- regional_names (JSONB)
- search_aliases (text[], indexed)
- diet_tags (text[])
- form (enum: raw/cooked/unspecified)
- kcal, enerc_kj, protein_g, fat_g, carbs_g, fiber_g, 
  sugar_g, starch_g, sat_fat_g, mufa_g, pufa_g, trans_fat_g, 
  omega3_g, omega6_g, cholesterol_mg
- Minerals (mg): calcium, iron, magnesium, zinc, sodium, 
  potassium, phosphorus
- Vitamins: vit_a_mcg, vit_c_mg, vit_d_mcg, vit_b_mg, 
  vit_e_mg, folate_mcg
- raw_ifct_data (JSONB) — full original payload
- nutrient_errors (JSONB) — all _e fields
- data_source ('ifct_2017')
- confidence ('verified')
- app_serving_units (JSONB) — populated later by unit normalizer 
  (e.g., {"katori": 150, "cup": 200, "tbsp": 15})
- meal_archetype_roles (text[]) — populated later (e.g., 
  ["protein", "dairy"] for paneer)
- created_at, updated_at

## Seed Script Behavior
- Load all 528 foods from @ifct2017/compositions
- Transform per the rules above (unit conversion, regional name 
  parsing, form inference, diet tag splitting)
- Idempotent: re-running should update existing rows, not duplicate
- Log any food where form inference fails for manual review
- Log the count per food_group at the end for sanity checking

## Implications for Meal Scoring
Now that we have reliable per-food data including:
- Sugar (fsugar) — add to scoring: penalize meals with excessive 
  added sugars unless the goal is bulking
- Sodium (na) — add to scoring: flag high-sodium meals for users 
  with hypertension goals
- Omega-3/omega-6 ratio — optional bonus points for meals with 
  healthy fat balance
- Saturated fat ratio — penalize if saturated fat > 10% of kcal

Update the scoring module to include these as optional dimensions 
that are activated based on user health goals/conditions.

## Implications for LLM Prompt
Since we now have detailed per-ingredient data:
- The LLM output JSON should still be ingredients + grams
- The nutrition layer looks up each ingredient in v2_ingredients by 
  name (with fallback to search_aliases)
- If the LLM outputs "paneer" and we match code L003, great
- If the LLM outputs "chenna" (Bengali name), the search_aliases 
  index finds it
- If the LLM outputs something ambiguous like "rice" — the match 
  logic must disambiguate by form (cooked vs raw) based on context 
  in the recipe, OR the LLM prompt should be updated to always 
  specify "cooked rice, 100g" or "raw rice, 30g" to remove ambiguity

Recommended: Update the meal generation prompt to require the LLM 
to specify cooked vs raw for every ingredient where it matters 
(grains, legumes, meats). This eliminates a huge class of errors.

## 2. Fuzzy Matching Layer

The LLM will sometimes output ingredient names that don't match any 
IFCT name or alias exactly ("mixed veg sabzi", "homestyle dal", 
"masala chai"). Build a cascading match layer:

1. Exact match on `name` (case-insensitive)
2. Exact match on any entry in `search_aliases`
3. Fuzzy string match (trigram similarity, threshold ~0.6) against 
   name + aliases
4. Semantic match via embeddings (cosine similarity, threshold ~0.75)

For step 4:
- During seed, generate an embedding for each food using a 
  concatenation of: name + scientific_name + food_group + top 3 
  regional aliases
- Store in an `embedding` vector column (use pgvector if Postgres, 
  otherwise closest equivalent)
- Use a small, cheap embedding model (text-embedding-3-small or 
  equivalent) — we're matching food names, not doing deep semantics
- At query time, embed the LLM's output ingredient name and find 
  nearest neighbor

Return match confidence with every lookup:
  { ingredient: "paneer", matched_code: "L003", 
    match_method: "exact" | "alias" | "fuzzy" | "embedding", 
    confidence: 0.0-1.0 }

Log low-confidence matches (<0.8) for manual review — these become 
candidates for adding to search_aliases over time.

## 3. Indian Unit Normalizer

LLMs output things like "1 katori dal" or "2 phulkas." Build a 
normalizer module that maps Indian serving units to grams:
- katori ≈ 150g (liquid/semi-liquid)
- roti ≈ 40g, phulka ≈ 30g, paratha ≈ 60g
- cup, tbsp, tsp standard conversions
- Make this a config file so values can be tuned.

## 4. Meal Archetype System

Create a table or config file `v2_meal_archetypes` defining meal 
structures per cuisine. Examples for Indian:
- thali: 1 sabzi + 1 dal + 1 grain + 1 side
- one_pot: biryani/khichdi/pulao + 1 accompaniment
- curry_bread: 1 gravy + 1 bread + 1 side
- tiffin: 1 main (idli/dosa/poha/upma) + chutney + optional sambar

Do the same for Mediterranean (grain bowl, mezze plate, protein + 
salad + pita) and Italian (pasta + side, protein + starch + veg).

Each archetype has slots, and each slot has allowed food groups.

## 5. Pairing Matrix (Indian-specific)

Create a `v2_pairing_rules` table or config that encodes culturally 
valid pairings, e.g.:
- rajma → rice (preferred), roti (acceptable)
- sambar → rice, idli, dosa, vada (NOT roti)
- chole → bhature, rice, roti
- palak paneer → roti, naan (rice acceptable but uncommon)

The meal validator will use this to reject culturally odd outputs.

## 6. Revised Meal Generation Prompt

Rewrite the LLM meal-generation prompt to:
- Pick an archetype first, then fill slots
- Use culturally coherent pairings from the matrix
- Adjust PORTION SIZES (not ingredient swaps) to hit macros within ±5%
- Output structured JSON with: archetype, dish_name, components 
  (name, grams, role, food_group), estimated_macros, cultural_note, 
  prep_time_minutes
- Break composite dishes into base ingredients with grams, so the 
  nutrition layer can look up each ingredient individually and sum.

## 7. Meal Scoring System

Implement a scoring module that rates each generated meal 0-100 across:
- Macro Accuracy (30 pts) — deviation from target
- Plate Composition (20 pts) — protein + carb + fat + veg all present
- Culinary Coherence (20 pts) — matches archetype, pairings are valid
- Micronutrient Diversity (15 pts) — count of distinct food groups
- Goal Alignment (10 pts) — priority macro is prominent for the goal
- Practicality (5 pts) — reasonable portions, common ingredients

Use a hybrid approach:
- Deterministic rules for macros, composition, food groups, pairings.
- LLM-as-judge for coherence and "does this feel like a real meal" — 
  a separate lightweight LLM call with a clear rubric.

Scoring bands:
- 85-100: serve
- 70-84: serve but log for review
- <70: auto-regenerate (cap at 3 retries, then return best attempt 
  with a quality warning)

## 8. Meal Record Schema

When storing a generated meal, each ingredient component must store 
both the LLM's original name AND the resolved IFCT code + match 
confidence. This makes nutrition recomputation deterministic and 
enables future data quality improvements:

meal_components: [
  {
    llm_name: "paneer",
    resolved_code: "L003", 
    resolved_name: "Paneer",
    match_method: "exact",
    match_confidence: 1.0,
    grams: 80,
    role: "protein"
  }
]

## 9. Goal-Based Macro Display Ordering

Add a config mapping user goal → macro display order:
- muscle_gain: protein, carbs, fat, fiber
- weight_loss: calories, protein, fiber, carbs, fat
- keto: fat, protein, net_carbs
- endurance: carbs, protein, fat
- balanced: calories, protein, carbs, fat, fiber

Update the meal response API to return macros in the correct order for 
the user's goal, so the frontend just renders in order.

=== WHAT TO BUILD ===

## 1. New Nutrition Data Layer (cuisine-aware routing)

Build a nutrition provider abstraction with a router that picks the 
source based on cuisine:

- Indian cuisine → Local IFCT (Indian Food Composition Tables, ICMR-NIN 
  2017) database as primary source, with Nutritionix as fallback for 
  composite dishes, Edamam as secondary fallback, and finally an LLM 
  estimation with a confidence flag if all miss.
- Mediterranean / Italian / Western → USDA FoodData Central as primary, 
  Edamam as fallback.
- Keep API Ninjas only as a last-resort fallback.

Create a new table `v2_ingredients` (or similar) seeded with IFCT data. 

=== DELIVERABLES ===

1. New database tables (migrations) — do not touch existing tables
2. Nutrition provider router with pluggable sources
3. Indian unit normalizer
4. Meal archetypes + pairing rules (seeded)
5. New meal generation prompt + pipeline
6. Meal scoring module with hybrid deterministic + LLM-judge approach
7. Goal-based macro ordering in API responses
8. A feature flag or separate endpoint (e.g., /v2/generate-meal) so the 
   new flow runs alongside the old one — don't replace existing routes
9. Basic tests for: unit normalizer, scoring module, pairing validator
10. A short README in the new module explaining the architecture and 
    how to tune archetypes/pairings/scoring weights
11. Fuzzy matching layer with exact/alias/trigram/embedding cascade
12. Embedding generation as part of seed script
13. Meal record schema that stores resolved IFCT codes + match confidence
14. Seed validation and integrity reports

=== CONSTRAINTS ===

- Don't delete or alter the existing `food_items` table or its routes.
- Put all new code under a clearly separated module/folder.
- Use the same language/framework/patterns already in the codebase 
  (check existing files before starting).
- Make archetypes, pairings, unit conversions, and scoring weights 
  configurable (JSON/YAML or DB), not hardcoded in logic.
- Keep the nutrition provider interface clean so we can swap providers 
  without touching meal generation logic.

=== BEFORE YOU START ===

1. Read the current codebase structure and identify: the existing 
   meal generation flow, the `food_items` table schema, the nutrition 
   provider code, and the LLM prompt currently used.
2. Propose a brief implementation plan (file structure, table schemas, 
   module boundaries) and wait for my approval before writing code.
3. Flag any assumptions you're making about my stack or data.

Start with step 1 and 2 — show me the plan first.