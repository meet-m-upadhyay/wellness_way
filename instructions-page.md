Decisions on each item:

1. Suspect macros:
   - C006, G026: keep as-is (fiber explains it)
   - E033 lemon juice: keep stored kcal, flag for runtime warning 
     if used >20g in a meal
   - N001 chicken leg: OVERRIDE with calculated kcal (191.5), 
     mark data_quality='kcal_corrected'
   - Q001, S007, S009 shellfish: keep as-is (chitin/glycogen)

2. Cholesterol patching: manually patch the 5 non-egg-white entries 
   with conservative published values. Mark 
   data_quality='cholesterol_patched'. Use these values:
   - L001 Milk Buffalo: 14 mg/100g
   - L002 Milk Cow: 12 mg/100g
   - L003 Paneer: 90 mg/100g
   - L004 Khoa: 80 mg/100g
   - S004 Gold fish: 50 mg/100g
   Leave M002/M005 egg whites at 0 (biologically correct).

3. Canonical defaults: approved as proposed. One addition — check 
   if IFCT has olive oil in Edible Oils and Fats (14 entries). If 
   yes, add "oil (mediterranean/italian)" → olive oil. If no, no 
   default needed for those cuisines since routing goes to USDA.

4. CRITICAL — manually seed 4 dairy entries IFCT is missing:
   - Dahi/Curd (whole milk cow): 60 kcal, 3.5g protein, 3.3g fat, 
     4.7g carbs per 100g
   - Greek yogurt / hung curd: 97 kcal, 9g protein, 5g fat, 4g 
     carbs per 100g
   - Buttermilk / chaas: 40 kcal, 3.3g protein, 0.9g fat, 4.8g 
     carbs per 100g
   - Lassi (sweet, plain): 95 kcal, 2.5g protein, 2g fat, 17g 
     carbs per 100g
   Set data_source='manual_seed', data_quality='manual_entry', 
   food_group='Milk and Milk Products'. Add appropriate 
   search_aliases (dahi, curd, yogurt, chaas, lassi, hung curd, 
   shrikhand-base, etc.).

5. Food group to archetype slot mapping — use this:
   - protein_animal: Animal Meat, Poultry, Marine Fish, Fresh 
     Water Fish and Shellfish, Marine Shellfish, Marine Mollusks, 
     Egg and Egg Products
   - protein_dairy: Milk and Milk Products
   - protein_legume: Grain Legumes
   - grain: Cereals and Millets
   - vegetable: Other Vegetables, Mushrooms
   - starchy_vegetable: Roots and Tubers (separate slot — don't 
     let potato count as vegetable when rice is also present)
   - leafy_green: Green Leafy Vegetables
   - fruit: Fruits
   - nuts_seeds: Nuts and Oil Seeds
   - fat_cooking: Edible Oils and Fats
   - spice: Condiments and Spices
   - sweetener: Sugars
   - misc: Miscellaneous Foods

6. Schema changes approved: expand form enum, add llm_confidence 
   FLOAT nullable.

Proceed with:
- Load seed data to DB with corrections (N001 chicken, 
  cholesterol patches, 4 manual dairy entries)
- Add canonical_foods.json config
- Then Groq form classification (dry run 10, then full 506)
- Stop at next checkpoint before archetype/pairing config work.