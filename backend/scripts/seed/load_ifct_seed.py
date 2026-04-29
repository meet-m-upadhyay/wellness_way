"""
Load IFCT seed data (JSON) into v2_ingredients + v2_regions tables.

Usage:
    cd backend
    python scripts/seed/load_ifct_seed.py --json-path ../ifct-test/ifct_seed_data.json

Applies:
  - N001 chicken leg kcal correction
  - Cholesterol patches for dairy/fish entries
  - 4 manual dairy entries (curd, greek yogurt, buttermilk, lassi)
  - Idempotent: re-running updates existing rows by IFCT code
"""

import argparse
import json
import sys
import os
import uuid

# Ensure backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.database.connection import get_engine, get_session_local

# ---------------------------------------------------------------------------
# Region seed data
# ---------------------------------------------------------------------------

REGIONS = {
    1: ("North India", "Jammu & Kashmir, Himachal Pradesh, Punjab, Haryana, Uttarakhand, UP, Delhi"),
    2: ("South India", "Andhra Pradesh, Karnataka, Kerala, Tamil Nadu, Telangana"),
    3: ("East India", "Bihar, Jharkhand, Odisha, West Bengal"),
    4: ("West India", "Goa, Gujarat, Maharashtra, Rajasthan"),
    5: ("Central India", "Chhattisgarh, Madhya Pradesh"),
    6: ("North-East India", "Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura"),
}

# ---------------------------------------------------------------------------
# Corrections per user decisions
# ---------------------------------------------------------------------------

KCAL_OVERRIDES = {
    # N001: chicken leg — stored 383.6 is wrong, use calculated 191.5
    "N001": {"kcal": 191.5, "data_quality": "kcal_corrected"},
}

CHOLESTEROL_PATCHES = {
    "L001": {"cholesterol_mg": 14.0, "data_quality": "cholesterol_patched"},   # Milk Buffalo
    "L002": {"cholesterol_mg": 12.0, "data_quality": "cholesterol_patched"},   # Milk Cow
    "L003": {"cholesterol_mg": 90.0, "data_quality": "cholesterol_patched"},   # Paneer
    "L004": {"cholesterol_mg": 80.0, "data_quality": "cholesterol_patched"},   # Khoa
    "S004": {"cholesterol_mg": 50.0, "data_quality": "cholesterol_patched"},   # Gold fish
}

# ---------------------------------------------------------------------------
# Manual dairy entries (IFCT has no curd/yogurt/buttermilk/lassi)
# ---------------------------------------------------------------------------

MANUAL_DAIRY = [
    {
        "code": "MAN001",
        "name": "Dahi / Curd (whole milk, cow)",
        "scientific_name": None,
        "food_group": "Milk and Milk Products",
        "region_code": None,
        "regional_names": {
            "hindi": "Dahi",
            "tamil": "Thayir",
            "telugu": "Perugu",
            "kannada": "Mosaru",
            "bengali": "Doi",
            "gujarati": "Dahi",
            "malayalam": "Thayir",
            "marathi": "Dahi",
        },
        "search_aliases": [
            "dahi", "curd", "yogurt", "yoghurt", "plain yogurt",
            "thayir", "perugu", "mosaru", "doi", "set curd",
        ],
        "diet_tags": ["vegetarian", "eggetarian"],
        "form": "prepared",
        "kcal": 60.0,
        "enerc_kj": 60.0 * 4.184,
        "protein_g": 3.5,
        "fat_g": 3.3,
        "carbs_g": 4.7,
        "fiber_g": 0.0,
        "sugar_g": 4.7,
        "starch_g": 0.0,
        "calcium_mg": 149.0,
        "data_source": "manual_seed",
        "data_quality": "manual_entry",
        "confidence": "verified",
    },
    {
        "code": "MAN002",
        "name": "Greek Yogurt / Hung Curd",
        "scientific_name": None,
        "food_group": "Milk and Milk Products",
        "region_code": None,
        "regional_names": {"hindi": "Hung Dahi", "english": "Greek Yogurt"},
        "search_aliases": [
            "greek yogurt", "hung curd", "hung dahi", "strained yogurt",
            "chakka dahi", "shrikhand base",
        ],
        "diet_tags": ["vegetarian", "eggetarian"],
        "form": "prepared",
        "kcal": 97.0,
        "enerc_kj": 97.0 * 4.184,
        "protein_g": 9.0,
        "fat_g": 5.0,
        "carbs_g": 4.0,
        "fiber_g": 0.0,
        "sugar_g": 4.0,
        "starch_g": 0.0,
        "calcium_mg": 110.0,
        "data_source": "manual_seed",
        "data_quality": "manual_entry",
        "confidence": "verified",
    },
    {
        "code": "MAN003",
        "name": "Buttermilk / Chaas",
        "scientific_name": None,
        "food_group": "Milk and Milk Products",
        "region_code": None,
        "regional_names": {
            "hindi": "Chaas, Mattha",
            "tamil": "Moru",
            "telugu": "Majjiga",
            "kannada": "Majjige",
            "gujarati": "Chaas",
            "marathi": "Taak",
        },
        "search_aliases": [
            "buttermilk", "chaas", "mattha", "moru", "majjiga",
            "majjige", "taak", "neer moru",
        ],
        "diet_tags": ["vegetarian", "eggetarian"],
        "form": "prepared",
        "kcal": 40.0,
        "enerc_kj": 40.0 * 4.184,
        "protein_g": 3.3,
        "fat_g": 0.9,
        "carbs_g": 4.8,
        "fiber_g": 0.0,
        "sugar_g": 4.8,
        "starch_g": 0.0,
        "calcium_mg": 116.0,
        "data_source": "manual_seed",
        "data_quality": "manual_entry",
        "confidence": "verified",
    },
    {
        "code": "MAN004",
        "name": "Lassi (sweet, plain)",
        "scientific_name": None,
        "food_group": "Milk and Milk Products",
        "region_code": None,
        "regional_names": {"hindi": "Lassi", "punjabi": "Lassi"},
        "search_aliases": [
            "lassi", "sweet lassi", "plain lassi", "meethi lassi",
        ],
        "diet_tags": ["vegetarian", "eggetarian"],
        "form": "prepared",
        "kcal": 95.0,
        "enerc_kj": 95.0 * 4.184,
        "protein_g": 2.5,
        "fat_g": 2.0,
        "carbs_g": 17.0,
        "fiber_g": 0.0,
        "sugar_g": 17.0,
        "starch_g": 0.0,
        "calcium_mg": 100.0,
        "data_source": "manual_seed",
        "data_quality": "manual_entry",
        "confidence": "verified",
    },
]

# ---------------------------------------------------------------------------
# Column mapping: JSON key → V2Ingredient column
# ---------------------------------------------------------------------------

COLUMN_MAP = [
    "code", "name", "scientific_name", "food_group", "region_code",
    "regional_names", "search_aliases", "diet_tags", "form",
    "kcal", "enerc_kj", "protein_g", "fat_g", "carbs_g", "fiber_g",
    "sugar_g", "starch_g",
    "sat_fat_g", "mufa_g", "pufa_g", "trans_fat_g", "omega3_g", "omega6_g",
    "cholesterol_mg",
    "calcium_mg", "iron_mg", "magnesium_mg", "zinc_mg",
    "sodium_mg", "potassium_mg", "phosphorus_mg",
    "vit_a_mcg", "vit_c_mg", "vit_d_mcg", "vit_b_mg", "vit_e_mg", "folate_mcg",
    "water_g", "ash_g",
    "raw_ifct_data", "nutrient_errors",
    "data_quality", "data_source", "confidence",
    "app_serving_units", "meal_archetype_roles", "custom_aliases",
]


def load_regions(session):
    """Insert or update the 6 IFCT regions."""
    for code, (name, desc) in REGIONS.items():
        session.execute(
            text("""
                INSERT INTO v2_regions (code, name, description)
                VALUES (:code, :name, :desc)
                ON CONFLICT (code) DO UPDATE SET name = :name, description = :desc
            """),
            {"code": code, "name": name, "desc": desc},
        )
    session.commit()
    print(f"  Loaded {len(REGIONS)} regions")


def upsert_ingredient(session, item):
    """Upsert a single ingredient by code."""
    # Build values dict from item, only including keys that exist
    vals = {"id": str(uuid.uuid4())}
    for col in COLUMN_MAP:
        if col in item:
            vals[col] = item[col]

    # Ensure JSON types are properly serialized
    for json_col in ("regional_names", "raw_ifct_data", "nutrient_errors", "app_serving_units"):
        if json_col in vals and vals[json_col] is not None:
            if isinstance(vals[json_col], (dict, list)):
                vals[json_col] = json.dumps(vals[json_col])

    # Build the SQL dynamically
    cols = list(vals.keys())
    insert_cols = ", ".join(cols)
    insert_vals = ", ".join(f":{c}" for c in cols)
    # On conflict, update everything except code and id
    update_set = ", ".join(f"{c} = :{c}" for c in cols if c not in ("code", "id"))

    sql = f"""
        INSERT INTO v2_ingredients ({insert_cols})
        VALUES ({insert_vals})
        ON CONFLICT (code) DO UPDATE SET {update_set}
    """
    session.execute(text(sql), vals)


def load_ingredients(session, json_path):
    """Load all IFCT ingredients from seed JSON, apply corrections, add manual entries."""
    with open(json_path, "r") as f:
        data = json.load(f)

    count = 0
    corrected = 0

    for item in data:
        code = item["code"]

        # Clamp region_code to valid range (1-6), set invalid to None
        if item.get("region_code") is not None and item["region_code"] not in (1, 2, 3, 4, 5, 6):
            item["region_code"] = None

        # Apply kcal overrides
        if code in KCAL_OVERRIDES:
            for k, v in KCAL_OVERRIDES[code].items():
                item[k] = v
            corrected += 1

        # Apply cholesterol patches
        if code in CHOLESTEROL_PATCHES:
            for k, v in CHOLESTEROL_PATCHES[code].items():
                item[k] = v
            corrected += 1

        upsert_ingredient(session, item)
        count += 1

    # Add manual dairy entries
    for item in MANUAL_DAIRY:
        # Fill in defaults for missing nutrition fields
        for col in COLUMN_MAP:
            if col not in item:
                item[col] = None
        if item.get("raw_ifct_data") is None:
            item["raw_ifct_data"] = {}
        upsert_ingredient(session, item)
        count += 1

    session.commit()
    print(f"  Loaded {count} ingredients ({corrected} corrections applied, {len(MANUAL_DAIRY)} manual entries)")


def run_validation(session):
    """Post-seed validation report."""
    print("\n=== POST-SEED VALIDATION ===\n")

    # Count per food group
    result = session.execute(text(
        "SELECT food_group, COUNT(*) FROM v2_ingredients GROUP BY food_group ORDER BY COUNT(*) DESC"
    ))
    print("--- Food Group Counts ---")
    total = 0
    for group, count in result:
        print(f"  {count:>3}  {group}")
        total += count
    print(f"  Total: {total}")

    # Data quality flag summary
    result = session.execute(text(
        "SELECT COALESCE(data_quality, 'clean'), COUNT(*) FROM v2_ingredients GROUP BY data_quality ORDER BY COUNT(*) DESC"
    ))
    print("\n--- Data Quality Flags ---")
    for flag, count in result:
        print(f"  {flag}: {count}")

    # Form distribution
    result = session.execute(text(
        "SELECT form, COUNT(*) FROM v2_ingredients GROUP BY form ORDER BY COUNT(*) DESC"
    ))
    print("\n--- Form Distribution ---")
    for form, count in result:
        print(f"  {form}: {count}")

    # Duplicate common names
    print("\n--- Duplicate Common Names ---")
    common = ["ghee", "rice", "dal", "paneer", "chicken", "milk", "curd", "wheat", "egg", "fish"]
    for name in common:
        result = session.execute(
            text("SELECT code, name FROM v2_ingredients WHERE LOWER(name) LIKE :pat"),
            {"pat": f"%{name}%"},
        )
        rows = result.fetchall()
        if len(rows) > 1:
            print(f"  '{name}' -> {len(rows)} entries")

    print("\n=== VALIDATION COMPLETE ===")


def main():
    parser = argparse.ArgumentParser(description="Load IFCT seed data into v2_ingredients")
    parser.add_argument("--json-path", required=True, help="Path to ifct_seed_data.json")
    args = parser.parse_args()

    if not os.path.exists(args.json_path):
        print(f"ERROR: File not found: {args.json_path}")
        sys.exit(1)

    SessionLocal = get_session_local()
    session = SessionLocal()

    try:
        print("Loading regions...")
        load_regions(session)

        print("Loading ingredients...")
        load_ingredients(session, args.json_path)

        run_validation(session)
    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
