"""
V2 Ingredient model — IFCT-backed nutrition data for the v2 meal engine.
All nutrition values are per 100g.
"""

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text,
    CheckConstraint, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class V2Ingredient(Base):
    """IFCT 2017 food item with curated nutrition columns."""
    __tablename__ = "v2_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, unique=True)          # IFCT code e.g. "A001"
    name = Column(String(255), nullable=False)
    scientific_name = Column(String(255), nullable=True)
    food_group = Column(String(100), nullable=False)                # from `grup`
    region_code = Column(Integer, ForeignKey("v2_regions.code"), nullable=True)

    # Multilingual names
    regional_names = Column(JSONB, nullable=False, default=dict)    # {"hindi": "...", "tamil": "..."}
    search_aliases = Column(ARRAY(Text), nullable=False, default=list)  # flattened, lowercased
    diet_tags = Column(ARRAY(Text), nullable=False, default=list)   # ["vegetarian", "eggetarian", ...]

    # Cooked vs raw
    form = Column(String(20), nullable=False, server_default="unspecified")

    # --- Macros (per 100g) ---
    kcal = Column(Float, nullable=False)
    enerc_kj = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)
    sugar_g = Column(Float, nullable=True)
    starch_g = Column(Float, nullable=True)

    # --- Fat breakdown (g per 100g) ---
    sat_fat_g = Column(Float, nullable=True)
    mufa_g = Column(Float, nullable=True)
    pufa_g = Column(Float, nullable=True)
    trans_fat_g = Column(Float, nullable=True)
    omega3_g = Column(Float, nullable=True)
    omega6_g = Column(Float, nullable=True)
    cholesterol_mg = Column(Float, nullable=True)

    # --- Minerals (mg per 100g) ---
    calcium_mg = Column(Float, nullable=True)
    iron_mg = Column(Float, nullable=True)
    magnesium_mg = Column(Float, nullable=True)
    zinc_mg = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    potassium_mg = Column(Float, nullable=True)
    phosphorus_mg = Column(Float, nullable=True)

    # --- Vitamins ---
    vit_a_mcg = Column(Float, nullable=True)
    vit_c_mg = Column(Float, nullable=True)
    vit_d_mcg = Column(Float, nullable=True)
    vit_b_mg = Column(Float, nullable=True)
    vit_e_mg = Column(Float, nullable=True)
    folate_mcg = Column(Float, nullable=True)

    # --- Other composition ---
    water_g = Column(Float, nullable=True)
    ash_g = Column(Float, nullable=True)

    # --- Raw data passthrough ---
    raw_ifct_data = Column(JSONB, nullable=False)
    nutrient_errors = Column(JSONB, nullable=True)              # all _e fields

    # --- Data quality flag (set during seed) ---
    # NULL = clean, 'suspect_macros', 'energy_derived', 'suspect_fat',
    # 'kcal_corrected', 'cholesterol_patched', 'manual_entry', 'form_llm_inferred'
    data_quality = Column(String(50), nullable=True)

    # --- LLM classification confidence (0.0-1.0, set by Groq form classifier) ---
    llm_confidence = Column(Float, nullable=True)

    # --- Metadata ---
    data_source = Column(String(50), nullable=False, server_default="ifct_2017")
    confidence = Column(String(20), nullable=False, server_default="verified")

    # --- App-specific (populated later) ---
    app_serving_units = Column(JSONB, nullable=True)            # {"katori": 150, ...}
    meal_archetype_roles = Column(ARRAY(Text), nullable=True)   # ["protein", "dairy"]
    custom_aliases = Column(ARRAY(Text), nullable=True)         # manual additions

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "form IN ('raw', 'cooked', 'dry_ingredient', 'fresh', 'prepared', 'not_applicable', 'unspecified')",
            name="check_v2_ingredients_form",
        ),
        Index("ix_v2_ingredients_food_group", "food_group"),
        Index("ix_v2_ingredients_search_aliases", "search_aliases", postgresql_using="gin"),
        Index("ix_v2_ingredients_diet_tags", "diet_tags", postgresql_using="gin"),
        Index("ix_v2_ingredients_form", "form"),
    )
