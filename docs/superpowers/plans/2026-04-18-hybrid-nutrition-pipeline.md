# Hybrid Nutrition Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the DB-only discovery engine with an LLM + nutrition API hybrid that provides infinite food variety with verified macros, while keeping the existing assembler/validation pipeline intact as both the core math and the fallback path.

**Architecture:** LLM suggests ingredients (categorized as protein/starch/vegetables/fat). A nutrition resolver verifies macros via CalorieNinjas (primary) or USDA (fallback), caching results in the existing `food_items` table. The assembler receives the same `Dict[str, List[FoodItem]]` portfolio it always has. If the LLM or API path fails, the existing template-based discovery engine activates as fallback.

**Tech Stack:** FastAPI, SQLAlchemy, httpx (async HTTP), Pydantic v2, Groq LLM, CalorieNinjas API, USDA FoodData Central API, Alembic (migrations), pytest

**Spec:** `docs/superpowers/specs/2026-04-18-hybrid-nutrition-pipeline-design.md`

---

## File Map

### New Files

| File | Responsibility |
|---|---|
| `backend/app/services/ml_diet_pipeline/nutrition/providers/__init__.py` | Package init |
| `backend/app/services/ml_diet_pipeline/nutrition/providers/base.py` | `NutritionProvider` ABC + `NutritionResult` dataclass |
| `backend/app/services/ml_diet_pipeline/nutrition/providers/calorieninjas.py` | CalorieNinjas API provider |
| `backend/app/services/ml_diet_pipeline/nutrition/providers/usda.py` | USDA FoodData Central API provider |
| `backend/app/services/ml_diet_pipeline/nutrition/resolver.py` | `NutritionResolver` — cache + API + simplification + fallback |
| `backend/app/services/ml_diet_pipeline/suggestion/__init__.py` | Package init |
| `backend/app/services/ml_diet_pipeline/suggestion/schema.py` | Pydantic models for LLM suggestion input/output |
| `backend/app/services/ml_diet_pipeline/suggestion/service.py` | `LLMMealSuggester` — prompts LLM for ingredient lists |
| `backend/tests/test_nutrition_providers.py` | Unit tests for CalorieNinjas + USDA providers |
| `backend/tests/test_nutrition_resolver.py` | Unit tests for resolver cache/API/simplification flow |
| `backend/tests/test_llm_meal_suggester.py` | Unit tests for LLM suggestion + Pydantic validation |
| `backend/tests/test_orchestrator_hybrid.py` | Tests for orchestrator fallback behavior |

### Modified Files

| File | What Changes |
|---|---|
| `backend/app/models/food_items.py` | Add `api_verified` column |
| `backend/app/core/config.py` | Add `NutritionAPISettings` class + fields on `Settings` |
| `backend/app/services/ml_diet_pipeline/orchestrator.py` | New Step 1 with LLM path + fallback |
| `backend/alembic/versions/` | New migration for `api_verified` column |
| `backend/.env` | New env vars for nutrition API keys |

### Unchanged Files

| File | Why Unchanged |
|---|---|
| `backend/app/services/ml_diet_pipeline/daily_assembler.py` | Receives same portfolio shape |
| `backend/app/services/ml_diet_pipeline/validation/engine.py` | Validates same meal structure |
| `backend/app/services/ml_diet_pipeline/nutrition/engine.py` | Calculates totals from same meal dicts |
| `backend/app/services/ml_diet_pipeline/genai/service.py` | Names meals from same ingredients |
| `backend/app/services/ml_diet_pipeline/discovery_engine.py` | Kept as fallback, no changes |
| `backend/app/services/ml_diet_pipeline/meal_templates.py` | Kept as fallback, no changes |
| All frontend files | No API contract changes |

---

## Task 1: Database Migration — Add `api_verified` Column

**Files:**
- Modify: `backend/app/models/food_items.py`
- Create: `backend/alembic/versions/<auto>_add_api_verified_to_food_items.py`

- [ ] **Step 1: Add column to FoodItem model**

In `backend/app/models/food_items.py`, add the `api_verified` column after `is_deprecated`:

```python
# Add after line 29 (is_deprecated)
api_verified = Column(Boolean, default=False, nullable=False, server_default="false")
```

- [ ] **Step 2: Generate Alembic migration**

```bash
cd backend
python -m alembic revision --autogenerate -m "add api_verified to food_items"
```

Expected: New migration file created in `backend/alembic/versions/`

- [ ] **Step 3: Review the generated migration**

Open the generated migration file. Verify it contains:

```python
def upgrade():
    op.add_column('food_items', sa.Column('api_verified', sa.Boolean(), server_default='false', nullable=False))

def downgrade():
    op.drop_column('food_items', 'api_verified')
```

- [ ] **Step 4: Run the migration**

```bash
cd backend
python -m alembic upgrade head
```

Expected: Migration applies successfully. All existing rows get `api_verified=False`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/food_items.py backend/alembic/versions/
git commit -m "feat: add api_verified column to food_items table"
```

---

## Task 2: Configuration — Add Nutrition API Settings

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env`

- [ ] **Step 1: Add NutritionAPISettings class to config.py**

Add this class after the `AISettings` class (after ~line 242) in `backend/app/core/config.py`:

```python
class NutritionAPISettings(BaseSettings):
    """Nutrition API configuration for macro verification"""

    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Primary provider
    provider: str = Field(default="calorieninjas", description="Primary nutrition API provider")
    calorieninjas_api_key: Optional[str] = Field(default=None, description="CalorieNinjas API key")

    # Fallback provider
    fallback_provider: str = Field(default="usda", description="Fallback nutrition API provider")
    usda_api_key: Optional[str] = Field(default=None, description="USDA FoodData Central API key")

    # Feature flag
    enable_llm_meal_suggestions: bool = Field(default=False, description="Enable LLM-based meal suggestions")

    def __init__(self, **kwargs):
        import os
        if 'calorieninjas_api_key' not in kwargs and os.getenv('CALORIENINJAS_API_KEY'):
            kwargs['calorieninjas_api_key'] = os.getenv('CALORIENINJAS_API_KEY')
        if 'usda_api_key' not in kwargs and os.getenv('USDA_API_KEY'):
            kwargs['usda_api_key'] = os.getenv('USDA_API_KEY')
        if 'enable_llm_meal_suggestions' not in kwargs and os.getenv('ENABLE_LLM_MEAL_SUGGESTIONS'):
            kwargs['enable_llm_meal_suggestions'] = os.getenv('ENABLE_LLM_MEAL_SUGGESTIONS', '').lower() == 'true'
        super().__init__(**kwargs)
```

- [ ] **Step 2: Add nutrition_api field to Settings class**

In the `Settings` class (around line 370), add the `nutrition_api` attribute alongside the existing `ai` attribute:

```python
# Add after the 'ai: AISettings' line
nutrition_api: NutritionAPISettings = Field(default_factory=NutritionAPISettings)
```

- [ ] **Step 3: Add env vars to backend/.env**

Append to `backend/.env`:

```env
# Nutrition API Configuration
CALORIENINJAS_API_KEY=
USDA_API_KEY=
ENABLE_LLM_MEAL_SUGGESTIONS=false
```

- [ ] **Step 4: Verify config loads**

```bash
cd backend
python -c "from app.core.config import get_settings; s = get_settings(); print(f'provider={s.nutrition_api.provider}, llm_enabled={s.nutrition_api.enable_llm_meal_suggestions}')"
```

Expected: `provider=calorieninjas, llm_enabled=False`

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/.env
git commit -m "feat: add nutrition API settings to config"
```

---

## Task 3: Nutrition Provider Base — ABC + NutritionResult

**Files:**
- Create: `backend/app/services/ml_diet_pipeline/nutrition/providers/__init__.py`
- Create: `backend/app/services/ml_diet_pipeline/nutrition/providers/base.py`
- Create: `backend/tests/test_nutrition_providers.py`

- [ ] **Step 1: Create the providers package**

Create `backend/app/services/ml_diet_pipeline/nutrition/providers/__init__.py`:

```python
from .base import NutritionProvider, NutritionResult

__all__ = ["NutritionProvider", "NutritionResult"]
```

- [ ] **Step 2: Write the failing test for NutritionResult**

Create `backend/tests/test_nutrition_providers.py`:

```python
"""Tests for nutrition API providers"""

import pytest
from app.services.ml_diet_pipeline.nutrition.providers.base import NutritionResult


class TestNutritionResult:
    def test_create_result_with_valid_data(self):
        result = NutritionResult(
            name="Chicken Tikka",
            calories=150.0,
            protein=28.0,
            fat=3.5,
            carbohydrates=2.0,
            fiber=0.0,
            serving_size_g=100.0,
            source="calorieninjas",
        )
        assert result.name == "Chicken Tikka"
        assert result.calories == 150.0
        assert result.protein == 28.0
        assert result.source == "calorieninjas"

    def test_to_macros_dict(self):
        result = NutritionResult(
            name="Chicken Tikka",
            calories=150.0,
            protein=28.0,
            fat=3.5,
            carbohydrates=2.0,
            fiber=0.0,
            serving_size_g=100.0,
            source="calorieninjas",
        )
        macros = result.to_macros_dict()
        assert macros == {
            "calories": 150.0,
            "protein": 28.0,
            "fat": 3.5,
            "carbohydrates": 2.0,
            "fiber": 0.0,
        }

    def test_normalize_to_per_100g(self):
        # API returns macros for a 200g serving
        result = NutritionResult.from_serving(
            name="Brown Rice",
            calories=230.0,
            protein=4.8,
            fat=1.8,
            carbohydrates=46.0,
            fiber=3.6,
            serving_size_g=200.0,
            source="calorieninjas",
        )
        assert result.calories == pytest.approx(115.0)
        assert result.protein == pytest.approx(2.4)
        assert result.serving_size_g == 200.0  # original preserved
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd backend
python -m pytest tests/test_nutrition_providers.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.ml_diet_pipeline.nutrition.providers.base'`

- [ ] **Step 4: Implement NutritionProvider ABC and NutritionResult**

Create `backend/app/services/ml_diet_pipeline/nutrition/providers/base.py`:

```python
"""Base classes for nutrition API providers"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class NutritionResult:
    """Verified macros for a food item, normalized to per-100g."""

    name: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    fiber: float
    serving_size_g: float
    source: str

    def to_macros_dict(self) -> dict:
        return {
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbohydrates": self.carbohydrates,
            "fiber": self.fiber,
        }

    @classmethod
    def from_serving(
        cls,
        name: str,
        calories: float,
        protein: float,
        fat: float,
        carbohydrates: float,
        fiber: float,
        serving_size_g: float,
        source: str,
    ) -> NutritionResult:
        """Create a NutritionResult normalized to per-100g from a non-100g serving."""
        if serving_size_g <= 0:
            serving_size_g = 100.0
        factor = 100.0 / serving_size_g
        return cls(
            name=name,
            calories=calories * factor,
            protein=protein * factor,
            fat=fat * factor,
            carbohydrates=carbohydrates * factor,
            fiber=fiber * factor,
            serving_size_g=serving_size_g,
            source=source,
        )


class NutritionProvider(ABC):
    """Abstract base class for nutrition API providers."""

    @abstractmethod
    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        """Look up macros for an ingredient. Returns None if not found."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Provider identifier for dataset_source field."""
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/test_nutrition_providers.py -v
```

Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/nutrition/providers/ backend/tests/test_nutrition_providers.py
git commit -m "feat: add NutritionProvider ABC and NutritionResult dataclass"
```

---

## Task 4: CalorieNinjas Provider

**Files:**
- Create: `backend/app/services/ml_diet_pipeline/nutrition/providers/calorieninjas.py`
- Modify: `backend/tests/test_nutrition_providers.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_nutrition_providers.py`:

```python
import httpx
from unittest.mock import AsyncMock, patch

from app.services.ml_diet_pipeline.nutrition.providers.calorieninjas import CalorieNinjasProvider


class TestCalorieNinjasProvider:
    @pytest.mark.asyncio
    async def test_source_name(self):
        provider = CalorieNinjasProvider(api_key="test-key")
        assert provider.source_name == "calorieninjas"

    @pytest.mark.asyncio
    async def test_lookup_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "items": [
                    {
                        "name": "chicken tikka",
                        "calories": 150.0,
                        "protein_g": 28.0,
                        "fat_total_g": 3.5,
                        "carbohydrates_total_g": 2.0,
                        "fiber_g": 0.0,
                        "serving_size_g": 100.0,
                    }
                ]
            },
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("chicken tikka")

        assert result is not None
        assert result.name == "chicken tikka"
        assert result.protein == 28.0
        assert result.source == "calorieninjas"

    @pytest.mark.asyncio
    async def test_lookup_empty_items(self):
        mock_response = httpx.Response(
            200,
            json={"items": []},
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("nonexistent food xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_api_error_returns_none(self):
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("chicken tikka")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_normalizes_to_per_100g(self):
        mock_response = httpx.Response(
            200,
            json={
                "items": [
                    {
                        "name": "brown rice",
                        "calories": 230.0,
                        "protein_g": 4.8,
                        "fat_total_g": 1.8,
                        "carbohydrates_total_g": 46.0,
                        "fiber_g": 3.6,
                        "serving_size_g": 200.0,
                    }
                ]
            },
            request=httpx.Request("GET", "https://api.calorieninjas.com/v1/nutrition"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = CalorieNinjasProvider(api_key="test-key")
            result = await provider.lookup("brown rice")

        assert result is not None
        assert result.calories == pytest.approx(115.0)
        assert result.protein == pytest.approx(2.4)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
python -m pytest tests/test_nutrition_providers.py::TestCalorieNinjasProvider -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement CalorieNinjas provider**

Create `backend/app/services/ml_diet_pipeline/nutrition/providers/calorieninjas.py`:

```python
"""CalorieNinjas nutrition API provider"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .base import NutritionProvider, NutritionResult

logger = logging.getLogger(__name__)

API_URL = "https://api.calorieninjas.com/v1/nutrition"


class CalorieNinjasProvider(NutritionProvider):
    """CalorieNinjas API — free tier: 10,000 requests/month."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "calorieninjas"

    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    API_URL,
                    params={"query": ingredient_name},
                    headers={"X-Api-Key": self._api_key},
                    timeout=15.0,
                )

            if response.status_code == 429:
                logger.warning("[DEBUG][NUTRITION_RATE_LIMITED] provider=calorieninjas")
                return None

            if response.status_code != 200:
                logger.error(
                    f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=calorieninjas "
                    f"status={response.status_code} ingredient={ingredient_name}"
                )
                return None

            data = response.json()
            items = data.get("items", [])
            if not items:
                logger.info(
                    f"[DEBUG][NUTRITION_NOT_FOUND] provider=calorieninjas ingredient={ingredient_name}"
                )
                return None

            item = items[0]
            serving_g = item.get("serving_size_g") or 100.0

            return NutritionResult.from_serving(
                name=item.get("name", ingredient_name),
                calories=item.get("calories", 0),
                protein=item.get("protein_g", 0),
                fat=item.get("fat_total_g", 0),
                carbohydrates=item.get("carbohydrates_total_g", 0),
                fiber=item.get("fiber_g", 0),
                serving_size_g=serving_g,
                source=self.source_name,
            )

        except httpx.TimeoutException:
            logger.error(f"[DEBUG][NUTRITION_TIMEOUT] provider=calorieninjas ingredient={ingredient_name}")
            return None
        except Exception as e:
            logger.error(f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=calorieninjas error={e}")
            return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/test_nutrition_providers.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/nutrition/providers/calorieninjas.py backend/tests/test_nutrition_providers.py
git commit -m "feat: add CalorieNinjas nutrition provider"
```

---

## Task 5: USDA FoodData Central Provider

**Files:**
- Create: `backend/app/services/ml_diet_pipeline/nutrition/providers/usda.py`
- Modify: `backend/tests/test_nutrition_providers.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_nutrition_providers.py`:

```python
from app.services.ml_diet_pipeline.nutrition.providers.usda import USDAProvider


class TestUSDAProvider:
    @pytest.mark.asyncio
    async def test_source_name(self):
        provider = USDAProvider(api_key="test-key")
        assert provider.source_name == "usda"

    @pytest.mark.asyncio
    async def test_lookup_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "description": "Chicken, broilers or fryers, breast, skinless",
                        "foodNutrients": [
                            {"nutrientName": "Energy", "unitName": "KCAL", "value": 165.0},
                            {"nutrientName": "Protein", "unitName": "G", "value": 31.0},
                            {"nutrientName": "Total lipid (fat)", "unitName": "G", "value": 3.6},
                            {"nutrientName": "Carbohydrate, by difference", "unitName": "G", "value": 0.0},
                            {"nutrientName": "Fiber, total dietary", "unitName": "G", "value": 0.0},
                        ],
                    }
                ]
            },
            request=httpx.Request("GET", "https://api.nal.usda.gov/fdc/v1/foods/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = USDAProvider(api_key="test-key")
            result = await provider.lookup("chicken breast")

        assert result is not None
        assert result.protein == 31.0
        assert result.calories == 165.0
        assert result.source == "usda"

    @pytest.mark.asyncio
    async def test_lookup_no_results(self):
        mock_response = httpx.Response(
            200,
            json={"foods": []},
            request=httpx.Request("GET", "https://api.nal.usda.gov/fdc/v1/foods/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = USDAProvider(api_key="test-key")
            result = await provider.lookup("nonexistent food xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_api_error_returns_none(self):
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.nal.usda.gov/fdc/v1/foods/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            provider = USDAProvider(api_key="test-key")
            result = await provider.lookup("chicken breast")

        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
python -m pytest tests/test_nutrition_providers.py::TestUSDAProvider -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement USDA provider**

Create `backend/app/services/ml_diet_pipeline/nutrition/providers/usda.py`:

```python
"""USDA FoodData Central nutrition API provider"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .base import NutritionProvider, NutritionResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# USDA nutrient name mapping
_NUTRIENT_MAP = {
    "Energy": "calories",
    "Protein": "protein",
    "Total lipid (fat)": "fat",
    "Carbohydrate, by difference": "carbohydrates",
    "Fiber, total dietary": "fiber",
}


class USDAProvider(NutritionProvider):
    """USDA FoodData Central — free, unlimited requests."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "usda"

    async def lookup(self, ingredient_name: str) -> Optional[NutritionResult]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    SEARCH_URL,
                    params={
                        "query": ingredient_name,
                        "api_key": self._api_key,
                        "pageSize": 1,
                        "dataType": "Foundation,SR Legacy",
                    },
                    timeout=15.0,
                )

            if response.status_code != 200:
                logger.error(
                    f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=usda "
                    f"status={response.status_code} ingredient={ingredient_name}"
                )
                return None

            data = response.json()
            foods = data.get("foods", [])
            if not foods:
                logger.info(f"[DEBUG][NUTRITION_NOT_FOUND] provider=usda ingredient={ingredient_name}")
                return None

            food = foods[0]
            nutrients = {n["nutrientName"]: n.get("value", 0) for n in food.get("foodNutrients", [])}

            macros = {}
            for usda_name, our_key in _NUTRIENT_MAP.items():
                macros[our_key] = nutrients.get(usda_name, 0)

            # USDA values are per 100g by default
            return NutritionResult(
                name=food.get("description", ingredient_name).title(),
                calories=macros.get("calories", 0),
                protein=macros.get("protein", 0),
                fat=macros.get("fat", 0),
                carbohydrates=macros.get("carbohydrates", 0),
                fiber=macros.get("fiber", 0),
                serving_size_g=100.0,
                source=self.source_name,
            )

        except httpx.TimeoutException:
            logger.error(f"[DEBUG][NUTRITION_TIMEOUT] provider=usda ingredient={ingredient_name}")
            return None
        except Exception as e:
            logger.error(f"[DEBUG][NUTRITION_PROVIDER_ERROR] provider=usda error={e}")
            return None
```

- [ ] **Step 4: Update providers __init__.py**

Update `backend/app/services/ml_diet_pipeline/nutrition/providers/__init__.py`:

```python
from .base import NutritionProvider, NutritionResult
from .calorieninjas import CalorieNinjasProvider
from .usda import USDAProvider

__all__ = ["NutritionProvider", "NutritionResult", "CalorieNinjasProvider", "USDAProvider"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/test_nutrition_providers.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/nutrition/providers/ backend/tests/test_nutrition_providers.py
git commit -m "feat: add USDA FoodData Central nutrition provider"
```

---

## Task 6: Nutrition Resolver — Cache + API + Simplification

**Files:**
- Create: `backend/app/services/ml_diet_pipeline/nutrition/resolver.py`
- Create: `backend/tests/test_nutrition_resolver.py`

- [ ] **Step 1: Write the failing test for cache hit**

Create `backend/tests/test_nutrition_resolver.py`:

```python
"""Tests for NutritionResolver — cache, API lookup, name simplification"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.ml_diet_pipeline.nutrition.resolver import NutritionResolver, simplify_name
from app.services.ml_diet_pipeline.nutrition.providers.base import NutritionResult


class TestSimplifyName:
    def test_remove_parenthetical(self):
        assert simplify_name("Paneer (Low Fat)") == "Paneer"

    def test_remove_leading_qualifier(self):
        assert simplify_name("Amritsari Fish Tikka") == "Fish Tikka"

    def test_remove_trailing_qualifier(self):
        assert simplify_name("Fish Tikka") == "Fish"

    def test_single_word_returns_none(self):
        assert simplify_name("Chicken") is None

    def test_already_simple_parenthetical(self):
        # After removing parenthetical, single word left
        assert simplify_name("Paneer") is None


class TestNutritionResolver:
    def _make_food_item(self, name="Chicken Tikka", api_verified=True, macros=None):
        """Create a mock FoodItem."""
        item = MagicMock()
        item.id = uuid4()
        item.canonical_name = name
        item.api_verified = api_verified
        item.macros = macros or {"calories": 150, "protein": 28, "fat": 3.5, "carbohydrates": 2, "fiber": 0}
        item.diet_flags = ["non-vegetarian"]
        item.cuisine_tags = ["indian"]
        item.allergen_flags = []
        item.dataset_source = "calorieninjas"
        return item

    @pytest.mark.asyncio
    async def test_cache_hit_verified_skips_api(self):
        """If an api_verified=True item exists in DB, no API call is made."""
        cached_item = self._make_food_item("Chicken Tikka", api_verified=True)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cached_item
        mock_db.query.return_value = mock_query

        mock_primary = AsyncMock()
        mock_primary.lookup = AsyncMock()  # should not be called

        resolver = NutritionResolver(
            db=mock_db,
            primary_provider=mock_primary,
            fallback_provider=None,
            llm_generator=None,
        )

        result = await resolver.resolve_one(
            ingredient_name="Chicken Tikka",
            diet_flags=["non-vegetarian"],
            cuisine_tags=["indian"],
            allergen_flags=[],
            category="protein",
        )

        assert result is not None
        assert result.canonical_name == "Chicken Tikka"
        mock_primary.lookup.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_calls_primary_api(self):
        """If nothing in DB, call primary provider and cache result."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # no cache hit
        mock_db.query.return_value = mock_query

        api_result = NutritionResult(
            name="mutton curry",
            calories=220, protein=24, fat=12,
            carbohydrates=3, fiber=0,
            serving_size_g=100, source="calorieninjas",
        )
        mock_primary = AsyncMock()
        mock_primary.lookup = AsyncMock(return_value=api_result)
        mock_primary.source_name = "calorieninjas"

        resolver = NutritionResolver(
            db=mock_db,
            primary_provider=mock_primary,
            fallback_provider=None,
            llm_generator=None,
        )

        result = await resolver.resolve_one(
            ingredient_name="Mutton Curry",
            diet_flags=["non-vegetarian"],
            cuisine_tags=["indian"],
            allergen_flags=[],
            category="protein",
        )

        assert result is not None
        assert result.macros["protein"] == 24
        mock_primary.lookup.assert_called_once_with("Mutton Curry")

    @pytest.mark.asyncio
    async def test_primary_miss_falls_to_fallback(self):
        """If primary returns None, try fallback provider."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        api_result = NutritionResult(
            name="lamb curry",
            calories=220, protein=24, fat=12,
            carbohydrates=3, fiber=0,
            serving_size_g=100, source="usda",
        )
        mock_primary = AsyncMock()
        mock_primary.lookup = AsyncMock(return_value=None)

        mock_fallback = AsyncMock()
        mock_fallback.lookup = AsyncMock(return_value=api_result)
        mock_fallback.source_name = "usda"

        resolver = NutritionResolver(
            db=mock_db,
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
            llm_generator=None,
        )

        result = await resolver.resolve_one(
            ingredient_name="Lamb Curry",
            diet_flags=["non-vegetarian"],
            cuisine_tags=["indian"],
            allergen_flags=[],
            category="protein",
        )

        assert result is not None
        assert result.macros["protein"] == 24
        mock_fallback.lookup.assert_called_once_with("Lamb Curry")

    @pytest.mark.asyncio
    async def test_all_miss_triggers_simplification(self):
        """If both providers miss, try simplified name."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        call_count = 0
        async def lookup_side_effect(name):
            nonlocal call_count
            call_count += 1
            # Fail for "Amritsari Fish Tikka", succeed for "Fish Tikka"
            if "fish tikka" in name.lower():
                return NutritionResult(
                    name="fish tikka", calories=140, protein=24, fat=4,
                    carbohydrates=2, fiber=0, serving_size_g=100, source="calorieninjas",
                )
            return None

        mock_primary = AsyncMock()
        mock_primary.lookup = AsyncMock(side_effect=lookup_side_effect)
        mock_primary.source_name = "calorieninjas"

        resolver = NutritionResolver(
            db=mock_db,
            primary_provider=mock_primary,
            fallback_provider=None,
            llm_generator=None,
        )

        result = await resolver.resolve_one(
            ingredient_name="Amritsari Fish Tikka",
            diet_flags=["non-vegetarian"],
            cuisine_tags=["indian"],
            allergen_flags=[],
            category="protein",
        )

        assert result is not None
        assert result.macros["protein"] == 24

    @pytest.mark.asyncio
    async def test_unresolvable_returns_none(self):
        """If nothing works, return None."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        mock_primary = AsyncMock()
        mock_primary.lookup = AsyncMock(return_value=None)

        resolver = NutritionResolver(
            db=mock_db,
            primary_provider=mock_primary,
            fallback_provider=None,
            llm_generator=None,
        )

        result = await resolver.resolve_one(
            ingredient_name="X",
            diet_flags=[],
            cuisine_tags=[],
            allergen_flags=[],
            category="protein",
        )

        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
python -m pytest tests/test_nutrition_resolver.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement NutritionResolver**

Create `backend/app/services/ml_diet_pipeline/nutrition/resolver.py`:

```python
"""Nutrition Resolver — resolves ingredient names to verified macros via cache + API"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.food_items import FoodItem
from .providers.base import NutritionProvider, NutritionResult

logger = logging.getLogger(__name__)


def simplify_name(name: str) -> Optional[str]:
    """Progressively simplify an ingredient name for fuzzy API lookup.

    Order:
      1. Remove parenthetical: "Paneer (Low Fat)" -> "Paneer"
      2. Remove leading qualifier: "Amritsari Fish Tikka" -> "Fish Tikka"
      3. Remove trailing qualifier: "Fish Tikka" -> "Fish"

    Returns None when the name can't be simplified further.
    """
    # 1. Remove parenthetical
    stripped = re.sub(r"\s*\(.*?\)\s*", "", name).strip()
    if stripped != name and stripped:
        return stripped

    # 2. Remove leading word
    parts = name.split()
    if len(parts) > 1:
        return " ".join(parts[1:])

    return None


class ResolvedIngredient:
    """FoodItem-compatible object returned by the resolver."""

    def __init__(
        self,
        id,
        canonical_name: str,
        macros: Dict[str, float],
        diet_flags: list,
        cuisine_tags: list,
        allergen_flags: list,
        dataset_source: str,
    ):
        self.id = id
        self.canonical_name = canonical_name
        self.macros = macros
        self.diet_flags = diet_flags
        self.cuisine_tags = cuisine_tags
        self.allergen_flags = allergen_flags
        self.dataset_source = dataset_source
        self.is_deprecated = False


class NutritionResolver:
    """Resolves ingredient names to verified macros.

    Resolution order:
      1. DB cache (api_verified=True)
      2. Primary nutrition API (e.g. CalorieNinjas)
      3. Fallback nutrition API (e.g. USDA)
      4. Name simplification + retry 1-3
      5. LLM substitution + retry 1-3
      6. Fail (return None)
    """

    MAX_SIMPLIFY_ROUNDS = 3

    def __init__(
        self,
        db: Session,
        primary_provider: Optional[NutritionProvider],
        fallback_provider: Optional[NutritionProvider],
        llm_generator: Optional[Callable],
    ):
        self._db = db
        self._primary = primary_provider
        self._fallback = fallback_provider
        self._llm_generator = llm_generator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve_portfolio(
        self,
        ingredients: List[Dict[str, Any]],
        diet_type: str,
        cuisine: str,
    ) -> Dict[str, List[ResolvedIngredient]]:
        """Resolve a list of LLM-suggested ingredients into a portfolio
        grouped by category (protein, starch, vegetables, fat)."""

        portfolio: Dict[str, List[ResolvedIngredient]] = {
            "protein": [], "starch": [], "vegetables": [], "fat": [],
        }
        resolved_count = 0
        total = len(ingredients)

        for ing in ingredients:
            result = await self.resolve_one(
                ingredient_name=ing["name"],
                diet_flags=ing.get("diet_flags", []),
                cuisine_tags=ing.get("cuisine_tags", []),
                allergen_flags=ing.get("allergen_flags", []),
                category=ing.get("category", "protein"),
            )
            if result:
                category = ing.get("category", "protein")
                if category in portfolio:
                    portfolio[category].append(result)
                resolved_count += 1

        logger.info(
            f"[DEBUG][NUTRITION_RESOLVE_COMPLETE] resolved={resolved_count}/{total}"
        )
        return portfolio

    async def resolve_one(
        self,
        ingredient_name: str,
        diet_flags: list,
        cuisine_tags: list,
        allergen_flags: list,
        category: str,
    ) -> Optional[ResolvedIngredient]:
        """Resolve a single ingredient through the full resolution chain."""

        # Step 1: DB cache lookup
        cached = self._cache_lookup(ingredient_name)
        if cached and cached.api_verified:
            logger.info(f"[DEBUG][NUTRITION_CACHE_HIT] ingredient=\"{ingredient_name}\"")
            return ResolvedIngredient(
                id=cached.id,
                canonical_name=cached.canonical_name,
                macros=dict(cached.macros),
                diet_flags=cached.diet_flags or diet_flags,
                cuisine_tags=cached.cuisine_tags or cuisine_tags,
                allergen_flags=cached.allergen_flags or allergen_flags,
                dataset_source=cached.dataset_source,
            )

        # Step 2-3: API lookup (primary then fallback)
        api_result = await self._api_lookup(ingredient_name)
        if api_result:
            resolved = self._cache_and_return(
                api_result, diet_flags, cuisine_tags, allergen_flags, cached,
            )
            return resolved

        # Step 4: Name simplification
        simplified = ingredient_name
        for _ in range(self.MAX_SIMPLIFY_ROUNDS):
            simplified = simplify_name(simplified)
            if simplified is None:
                break
            logger.info(
                f"[DEBUG][NUTRITION_SIMPLIFY] original=\"{ingredient_name}\" simplified=\"{simplified}\""
            )

            # Check cache for simplified name
            cached_simple = self._cache_lookup(simplified)
            if cached_simple and cached_simple.api_verified:
                return ResolvedIngredient(
                    id=cached_simple.id,
                    canonical_name=cached_simple.canonical_name,
                    macros=dict(cached_simple.macros),
                    diet_flags=cached_simple.diet_flags or diet_flags,
                    cuisine_tags=cached_simple.cuisine_tags or cuisine_tags,
                    allergen_flags=cached_simple.allergen_flags or allergen_flags,
                    dataset_source=cached_simple.dataset_source,
                )

            api_result = await self._api_lookup(simplified)
            if api_result:
                return self._cache_and_return(
                    api_result, diet_flags, cuisine_tags, allergen_flags, cached,
                )

        # Step 5: LLM substitution
        if self._llm_generator:
            substitute = await self._ask_llm_substitute(
                ingredient_name, diet_flags, cuisine_tags, category,
            )
            if substitute:
                api_result = await self._api_lookup(substitute)
                if api_result:
                    return self._cache_and_return(
                        api_result, diet_flags, cuisine_tags, allergen_flags, None,
                    )

        # Step 6: Fail
        logger.warning(f"[DEBUG][NUTRITION_UNRESOLVED] ingredient=\"{ingredient_name}\"")
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cache_lookup(self, name: str) -> Optional[FoodItem]:
        """Fuzzy lookup in food_items table."""
        return (
            self._db.query(FoodItem)
            .filter(
                FoodItem.canonical_name.ilike(f"%{name}%"),
                FoodItem.is_deprecated == False,
            )
            .first()
        )

    async def _api_lookup(self, name: str) -> Optional[NutritionResult]:
        """Try primary provider, then fallback."""
        if self._primary:
            logger.info(f"[DEBUG][NUTRITION_API_CALL] ingredient=\"{name}\" provider={self._primary.source_name}")
            result = await self._primary.lookup(name)
            if result:
                return result

        if self._fallback:
            logger.info(f"[DEBUG][NUTRITION_API_CALL] ingredient=\"{name}\" provider={self._fallback.source_name}")
            result = await self._fallback.lookup(name)
            if result:
                return result

        return None

    def _cache_and_return(
        self,
        api_result: NutritionResult,
        diet_flags: list,
        cuisine_tags: list,
        allergen_flags: list,
        existing_item: Optional[FoodItem],
    ) -> ResolvedIngredient:
        """Write API result to DB cache and return a ResolvedIngredient."""
        macros = api_result.to_macros_dict()

        if existing_item:
            # Update existing row with verified macros
            existing_item.macros = macros
            existing_item.api_verified = True
            existing_item.dataset_source = api_result.source
            if not existing_item.diet_flags:
                existing_item.diet_flags = diet_flags
            if not existing_item.cuisine_tags:
                existing_item.cuisine_tags = cuisine_tags
            try:
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(existing_item, "macros")
                self._db.commit()
                logger.info(
                    f"[DEBUG][NUTRITION_CACHE_UPDATE] ingredient=\"{existing_item.canonical_name}\" "
                    f"source={api_result.source} api_verified=True"
                )
            except Exception as e:
                self._db.rollback()
                logger.error(f"[DEBUG][NUTRITION_CACHE_WRITE_FAILED] error={e}")

            return ResolvedIngredient(
                id=existing_item.id,
                canonical_name=existing_item.canonical_name,
                macros=macros,
                diet_flags=existing_item.diet_flags or diet_flags,
                cuisine_tags=existing_item.cuisine_tags or cuisine_tags,
                allergen_flags=existing_item.allergen_flags or allergen_flags,
                dataset_source=api_result.source,
            )
        else:
            # Create new cached row
            new_id = uuid4()
            new_item = FoodItem(
                id=new_id,
                canonical_name=api_result.name.title(),
                dataset_source=api_result.source,
                dataset_food_id=f"{api_result.source}_{api_result.name.lower().replace(' ', '_')}",
                registry_version=1,
                macros=macros,
                diet_flags=diet_flags,
                allergen_flags=allergen_flags,
                cuisine_tags=cuisine_tags,
                is_deprecated=False,
                api_verified=True,
            )
            try:
                self._db.add(new_item)
                self._db.commit()
                logger.info(
                    f"[DEBUG][NUTRITION_CACHE_WRITE] ingredient=\"{api_result.name}\" "
                    f"source={api_result.source} api_verified=True"
                )
            except Exception as e:
                self._db.rollback()
                logger.error(f"[DEBUG][NUTRITION_CACHE_WRITE_FAILED] error={e}")

            return ResolvedIngredient(
                id=new_id,
                canonical_name=api_result.name.title(),
                macros=macros,
                diet_flags=diet_flags,
                cuisine_tags=cuisine_tags,
                allergen_flags=allergen_flags,
                dataset_source=api_result.source,
            )

    async def _ask_llm_substitute(
        self,
        original_name: str,
        diet_flags: list,
        cuisine_tags: list,
        category: str,
    ) -> Optional[str]:
        """Ask the LLM to suggest a common substitute ingredient."""
        if not self._llm_generator:
            return None

        try:
            import json
            diet_str = ", ".join(diet_flags) if diet_flags else "any"
            cuisine_str = ", ".join(cuisine_tags) if cuisine_tags else "any"
            payload = {
                "action": "suggest_substitute",
                "original_ingredient": original_name,
                "diet_type": diet_str,
                "cuisine": cuisine_str,
                "category": category,
            }
            raw = await self._llm_generator(payload)
            if raw and isinstance(raw, dict) and "substitute" in raw:
                substitute = raw["substitute"]
                logger.info(
                    f"[DEBUG][NUTRITION_LLM_SUBSTITUTE] original=\"{original_name}\" "
                    f"substitute=\"{substitute}\""
                )
                return substitute
        except Exception as e:
            logger.error(f"[DEBUG][NUTRITION_LLM_SUBSTITUTE_FAILED] error={e}")

        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/test_nutrition_resolver.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/nutrition/resolver.py backend/tests/test_nutrition_resolver.py
git commit -m "feat: add NutritionResolver with cache, API lookup, and name simplification"
```

---

## Task 7: LLM Meal Suggestion — Schema

**Files:**
- Create: `backend/app/services/ml_diet_pipeline/suggestion/__init__.py`
- Create: `backend/app/services/ml_diet_pipeline/suggestion/schema.py`

- [ ] **Step 1: Create the suggestion package**

Create `backend/app/services/ml_diet_pipeline/suggestion/__init__.py`:

```python
```

- [ ] **Step 2: Create Pydantic schemas for LLM input/output**

Create `backend/app/services/ml_diet_pipeline/suggestion/schema.py`:

```python
"""Pydantic schemas for LLM meal suggestion input/output"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class LLMIngredient(BaseModel):
    """A single ingredient suggested by the LLM."""
    name: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(protein|starch|vegetables|fat)$")
    diet_flags: List[str] = Field(default_factory=list)
    cuisine_tags: List[str] = Field(default_factory=list)
    allergen_flags: List[str] = Field(default_factory=list)


class LLMMealSuggestion(BaseModel):
    """A single meal suggested by the LLM."""
    meal_type: str = Field(..., min_length=1)
    ingredients: List[LLMIngredient] = Field(..., min_length=1)


class LLMSuggestionResponse(BaseModel):
    """Top-level LLM response containing one or more meals."""
    meals: List[LLMMealSuggestion] = Field(..., min_length=1)
```

- [ ] **Step 3: Verify schema works**

```bash
cd backend
python -c "
from app.services.ml_diet_pipeline.suggestion.schema import LLMSuggestionResponse
import json
data = {'meals': [{'meal_type': 'lunch', 'ingredients': [{'name': 'Chicken', 'category': 'protein', 'diet_flags': ['non-vegetarian']}]}]}
r = LLMSuggestionResponse.model_validate(data)
print(f'Parsed: {len(r.meals)} meals, {len(r.meals[0].ingredients)} ingredients')
"
```

Expected: `Parsed: 1 meals, 1 ingredients`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/suggestion/
git commit -m "feat: add Pydantic schemas for LLM meal suggestion"
```

---

## Task 8: LLM Meal Suggestion — Service

**Files:**
- Create: `backend/app/services/ml_diet_pipeline/suggestion/service.py`
- Create: `backend/tests/test_llm_meal_suggester.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_llm_meal_suggester.py`:

```python
"""Tests for LLM Meal Suggester service"""

import pytest
from unittest.mock import AsyncMock

from app.services.ml_diet_pipeline.suggestion.service import LLMMealSuggester


class TestLLMMealSuggester:
    @pytest.mark.asyncio
    async def test_suggest_meals_valid_response(self):
        mock_generator = AsyncMock(return_value={
            "meals": [
                {
                    "meal_type": "lunch",
                    "ingredients": [
                        {"name": "Chicken Tikka", "category": "protein", "diet_flags": ["non-vegetarian"], "cuisine_tags": ["indian"], "allergen_flags": []},
                        {"name": "Brown Rice", "category": "starch", "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"], "allergen_flags": []},
                        {"name": "Palak", "category": "vegetables", "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"], "allergen_flags": []},
                        {"name": "Ghee", "category": "fat", "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"], "allergen_flags": []},
                    ],
                }
            ]
        })

        suggester = LLMMealSuggester(generator=mock_generator)
        result = await suggester.suggest_meals(
            diet_type="non-vegetarian",
            cuisine="indian",
            meal_types=["lunch"],
            allergies=set(),
            foods_to_avoid=set(),
            exclude_ingredients=set(),
        )

        assert len(result) == 4
        assert result[0]["name"] == "Chicken Tikka"
        assert result[0]["category"] == "protein"

    @pytest.mark.asyncio
    async def test_suggest_meals_invalid_json_returns_empty(self):
        mock_generator = AsyncMock(return_value={"bad": "data"})

        suggester = LLMMealSuggester(generator=mock_generator)
        result = await suggester.suggest_meals(
            diet_type="non-vegetarian",
            cuisine="indian",
            meal_types=["lunch"],
            allergies=set(),
            foods_to_avoid=set(),
            exclude_ingredients=set(),
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_suggest_meals_generator_fails_returns_empty(self):
        mock_generator = AsyncMock(side_effect=Exception("LLM down"))

        suggester = LLMMealSuggester(generator=mock_generator)
        result = await suggester.suggest_meals(
            diet_type="vegetarian",
            cuisine="indian",
            meal_types=["breakfast"],
            allergies=set(),
            foods_to_avoid=set(),
            exclude_ingredients=set(),
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_prompt_includes_diet_priority(self):
        captured_payload = {}

        async def capture_generator(payload):
            captured_payload.update(payload)
            return {"meals": [{"meal_type": "lunch", "ingredients": [
                {"name": "Chicken", "category": "protein", "diet_flags": ["non-vegetarian"], "cuisine_tags": ["indian"], "allergen_flags": []}
            ]}]}

        suggester = LLMMealSuggester(generator=capture_generator)
        await suggester.suggest_meals(
            diet_type="non-vegetarian",
            cuisine="indian",
            meal_types=["lunch"],
            allergies=set(),
            foods_to_avoid=set(),
            exclude_ingredients=set(),
        )

        # Verify prompt mentions diet priority
        prompt = captured_payload.get("prompt", "")
        assert "non-vegetarian" in prompt.lower()
        assert "priority" in prompt.lower() or "prefer" in prompt.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
python -m pytest tests/test_llm_meal_suggester.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement LLMMealSuggester**

Create `backend/app/services/ml_diet_pipeline/suggestion/service.py`:

```python
"""LLM Meal Suggester — asks the LLM to suggest ingredients for meals"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from .schema import LLMSuggestionResponse

logger = logging.getLogger(__name__)

# Diet priority rules embedded in the prompt
_DIET_PRIORITY_RULES = {
    "non-vegetarian": (
        "The user follows a NON-VEGETARIAN diet. "
        "Prefer non-vegetarian items (chicken, mutton, fish, prawns) as the primary protein. "
        "Egg-based items are second preference. "
        "Vegetarian (paneer, dairy) and vegan (lentils, soy) are acceptable but lower priority."
    ),
    "eggetarian": (
        "The user follows an EGGETARIAN diet. No meat or fish. "
        "Prefer egg-based items as the primary protein. "
        "Vegetarian (paneer, dairy) and vegan (lentils, soy) are acceptable but lower priority."
    ),
    "vegetarian": (
        "The user follows a VEGETARIAN diet. No meat, fish, or eggs. "
        "Prefer dairy-based proteins (paneer, yogurt, cheese). "
        "Vegan proteins (lentils, soy, chickpeas) are acceptable but lower priority."
    ),
    "vegan": (
        "The user follows a VEGAN diet. No animal products at all. "
        "Use only plant-based proteins: lentils, chickpeas, soy, tofu, beans, nuts."
    ),
}


class LLMMealSuggester:
    """Asks the LLM to suggest meal ingredients categorized by role."""

    def __init__(self, generator: Callable[[Dict[str, Any]], Any]) -> None:
        self._generator = generator

    async def suggest_meals(
        self,
        diet_type: str,
        cuisine: str,
        meal_types: List[str],
        allergies: Set[str],
        foods_to_avoid: Set[str],
        exclude_ingredients: Set[str],
        primary_goal: str = "maintain",
        budget_constraints: Optional[str] = None,
        lifestyle_constraints: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Ask the LLM to suggest ingredients for the given meals.

        Returns a flat list of ingredient dicts with keys:
          name, category, diet_flags, cuisine_tags, allergen_flags

        Returns empty list if the LLM fails or returns invalid data.
        """
        diet_rule = _DIET_PRIORITY_RULES.get(diet_type, "")

        constraints_text = f"Cuisine: {cuisine}. Goal: {primary_goal}."
        if allergies:
            constraints_text += f" MUST AVOID allergens: {', '.join(allergies)}."
        if foods_to_avoid:
            constraints_text += f" MUST AVOID foods: {', '.join(foods_to_avoid)}."
        if exclude_ingredients:
            constraints_text += f" For variety, do NOT use these ingredients: {', '.join(exclude_ingredients)}."
        if budget_constraints:
            constraints_text += f" Budget: {budget_constraints}."
        if lifestyle_constraints:
            constraints_text += f" Lifestyle: {lifestyle_constraints}."

        meals_requested = ", ".join(meal_types)

        prompt = f"""Suggest realistic, commonly eaten meals for: {meals_requested}.

{diet_rule}
{constraints_text}

For EACH meal, suggest exactly 4 ingredients categorized as:
- "protein" (1 item): the main protein source
- "starch" (1 item): rice, bread, roti, pasta, etc.
- "vegetables" (1 item): a vegetable or salad
- "fat" (1 item): cooking fat, dressing, or healthy fat

Use common ingredient names that a nutrition database would recognize.
Do NOT suggest brand names or overly specific regional variations.

For each ingredient, also classify:
- diet_flags: which diets it fits (from: "vegan", "vegetarian", "eggetarian", "non-vegetarian")
- cuisine_tags: which cuisines it belongs to (e.g. "indian", "mediterranean", "italian")
- allergen_flags: common allergens it contains (e.g. "dairy", "gluten", "nuts", "eggs", "fish", "shellfish")

Respond ONLY with a JSON object:
{{
  "meals": [
    {{
      "meal_type": "lunch",
      "ingredients": [
        {{"name": "Chicken Tikka", "category": "protein", "diet_flags": ["non-vegetarian"], "cuisine_tags": ["indian"], "allergen_flags": []}},
        {{"name": "Brown Rice", "category": "starch", "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"], "allergen_flags": []}},
        {{"name": "Palak (Spinach)", "category": "vegetables", "diet_flags": ["vegan", "vegetarian", "eggetarian"], "cuisine_tags": ["indian"], "allergen_flags": []}},
        {{"name": "Ghee", "category": "fat", "diet_flags": ["vegetarian", "eggetarian"], "cuisine_tags": ["indian"], "allergen_flags": ["dairy"]}}
      ]
    }}
  ]
}}"""

        payload = {
            "action": "suggest_meals",
            "prompt": prompt,
            "diet_type": diet_type,
            "cuisine": cuisine,
        }

        try:
            logger.info(
                f"[DEBUG][LLM_SUGGEST_START] diet={diet_type} cuisine={cuisine} "
                f"meals={meals_requested}"
            )
            raw = await self._generator(payload)

            if not raw or not isinstance(raw, dict):
                logger.warning("[DEBUG][LLM_SUGGESTION_INVALID] response is not a dict")
                return []

            validated = LLMSuggestionResponse.model_validate(raw)
            logger.info(f"[DEBUG][LLM_SUGGEST_SUCCESS] meals={len(validated.meals)}")

            # Flatten all ingredients from all meals into a single list
            all_ingredients = []
            for meal in validated.meals:
                for ing in meal.ingredients:
                    all_ingredients.append(ing.model_dump())
            return all_ingredients

        except Exception as e:
            logger.warning(f"[DEBUG][LLM_SUGGESTION_INVALID] error={e}")
            return []
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/test_llm_meal_suggester.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/suggestion/service.py backend/tests/test_llm_meal_suggester.py
git commit -m "feat: add LLM Meal Suggester service with diet priority prompting"
```

---

## Task 9: Orchestrator Integration — LLM Path + Fallback

**Files:**
- Modify: `backend/app/services/ml_diet_pipeline/orchestrator.py`
- Create: `backend/tests/test_orchestrator_hybrid.py`

- [ ] **Step 1: Write the failing test for fallback behavior**

Create `backend/tests/test_orchestrator_hybrid.py`:

```python
"""Tests for orchestrator hybrid LLM path + fallback"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ml_diet_pipeline.orchestrator import MLPipelineOrchestrator


class TestOrchestratorFallback:
    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_to_discovery_engine(self):
        """When LLM path throws, orchestrator falls back to template-based discovery."""

        mock_discovery = MagicMock()
        mock_portfolio = {
            "protein": [MagicMock(canonical_name="Paneer", macros={"calories": 200, "protein": 20, "fat": 12, "carbohydrates": 4, "fiber": 0}, diet_flags=["vegetarian"], cuisine_tags=["indian"], allergen_flags=[])],
            "starch": [MagicMock(canonical_name="Rice", macros={"calories": 130, "protein": 3, "fat": 0.5, "carbohydrates": 28, "fiber": 1}, diet_flags=["vegan"], cuisine_tags=["indian"], allergen_flags=[])],
            "vegetables": [MagicMock(canonical_name="Spinach", macros={"calories": 40, "protein": 3, "fat": 1, "carbohydrates": 6, "fiber": 4}, diet_flags=["vegan"], cuisine_tags=["indian"], allergen_flags=[])],
            "fat": [MagicMock(canonical_name="Ghee", macros={"calories": 900, "protein": 0, "fat": 100, "carbohydrates": 0, "fiber": 0}, diet_flags=["vegetarian"], cuisine_tags=["indian"], allergen_flags=[])],
        }
        mock_discovery.discover_daily_portfolio.return_value = mock_portfolio

        # Mock the meal suggester to fail
        mock_suggester = AsyncMock()
        mock_suggester.suggest_meals = AsyncMock(side_effect=Exception("LLM down"))

        # Create orchestrator with mocked components
        orchestrator = MLPipelineOrchestrator()
        orchestrator.discovery_engine = mock_discovery
        orchestrator.meal_suggester = mock_suggester

        # The _get_portfolio_with_fallback should catch the exception and use discovery engine
        portfolio = await orchestrator._get_portfolio_with_fallback(
            db=MagicMock(),
            constraints=MagicMock(
                diet_type=MagicMock(value="vegetarian"),
                cuisine="indian",
                allergies=set(),
                primary_goal="maintain",
                foods_to_avoid=set(),
            ),
            exclude_ingredients=set(),
            enable_llm=True,
        )

        assert portfolio == mock_portfolio
        mock_discovery.discover_daily_portfolio.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_disabled_uses_discovery_engine(self):
        """When enable_llm=False, always use discovery engine."""

        mock_discovery = MagicMock()
        mock_portfolio = {"protein": [], "starch": [], "vegetables": [], "fat": []}
        mock_discovery.discover_daily_portfolio.return_value = mock_portfolio

        orchestrator = MLPipelineOrchestrator()
        orchestrator.discovery_engine = mock_discovery
        orchestrator.meal_suggester = None

        portfolio = await orchestrator._get_portfolio_with_fallback(
            db=MagicMock(),
            constraints=MagicMock(
                diet_type=MagicMock(value="vegetarian"),
                cuisine="indian",
                allergies=set(),
                primary_goal="maintain",
                foods_to_avoid=set(),
            ),
            exclude_ingredients=set(),
            enable_llm=False,
        )

        assert portfolio == mock_portfolio
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
python -m pytest tests/test_orchestrator_hybrid.py -v
```

Expected: FAIL — `AttributeError: 'MLPipelineOrchestrator' object has no attribute '_get_portfolio_with_fallback'`

- [ ] **Step 3: Add `_get_portfolio_with_fallback` method to orchestrator**

In `backend/app/services/ml_diet_pipeline/orchestrator.py`, add these imports at the top of the file (after existing imports):

```python
from app.services.ml_diet_pipeline.suggestion.service import LLMMealSuggester
from app.services.ml_diet_pipeline.nutrition.resolver import NutritionResolver
```

Add `meal_suggester`, `nutrition_resolver` attributes to `__init__` (add after `self.nutrition_db` initialization around line 72):

```python
        self.meal_suggester: Optional[Any] = None
        self.nutrition_resolver: Optional[Any] = None
```

Add the `_get_portfolio_with_fallback` method (add before `_extract_constraints`, around line 488):

```python
    async def _get_portfolio_with_fallback(
        self,
        db: Session,
        constraints,
        exclude_ingredients: Set[str],
        enable_llm: bool = False,
    ) -> Dict[str, List]:
        """Get ingredient portfolio via LLM+API path, falling back to template-based discovery.

        Returns Dict[str, List] with keys: protein, starch, vegetables, fat.
        """
        if enable_llm and self.meal_suggester and self.nutrition_resolver:
            try:
                meals_per_day = constraints.meals_per_day or 3
                if meals_per_day != 3:
                    meals_per_day = 3

                meal_types = ["breakfast", "lunch", "dinner"][:meals_per_day]

                llm_ingredients = await self.meal_suggester.suggest_meals(
                    diet_type=constraints.diet_type.value,
                    cuisine=constraints.cuisine,
                    meal_types=meal_types,
                    allergies=constraints.allergies,
                    foods_to_avoid=constraints.foods_to_avoid,
                    exclude_ingredients=exclude_ingredients,
                    primary_goal=constraints.primary_goal,
                    budget_constraints=getattr(constraints, 'budget_constraints', None),
                    lifestyle_constraints=getattr(constraints, 'lifestyle_constraints', None),
                )

                if not llm_ingredients:
                    raise ValueError("LLM returned empty ingredient list")

                portfolio = await self.nutrition_resolver.resolve_portfolio(
                    ingredients=llm_ingredients,
                    diet_type=constraints.diet_type.value,
                    cuisine=constraints.cuisine,
                )

                # Check threshold: if any category is completely empty, fallback
                total_resolved = sum(len(v) for v in portfolio.values())
                if total_resolved < len(llm_ingredients) * 0.5:
                    logger.warning(
                        f"[DEBUG][NUTRITION_RESOLVE_THRESHOLD] resolved={total_resolved}/{len(llm_ingredients)}"
                    )
                    raise ValueError("Too many ingredients failed resolution")

                logger.info(f"[DEBUG][LLM_PORTFOLIO_SUCCESS] items={total_resolved}")
                return portfolio

            except Exception as e:
                logger.warning(f"[DEBUG][ML_PIPELINE_FALLBACK] reason=\"{e}\"")

        # Fallback to template-based discovery engine
        return self.discovery_engine.discover_daily_portfolio(
            db=db,
            diet_type=constraints.diet_type.value,
            allergies=constraints.allergies,
            cuisine=constraints.cuisine,
            primary_goal=constraints.primary_goal,
            foods_to_avoid=constraints.foods_to_avoid,
            exclude_ingredients=exclude_ingredients,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/test_orchestrator_hybrid.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Replace discovery engine calls in generate_daily_plan**

In `generate_daily_plan` (around lines 105-119), replace the existing Step 1 discovery block:

```python
            # STEP 1: Discover Portfolio (Finding ingredients)
            logger.info(f"[ML_STEP_1] Daily Portfolio Discovery")

            # Combine variety exclusions
            variety_exclusions = set(exclude_templates or [])

            from app.core.config import get_settings
            settings = get_settings()
            enable_llm = settings.nutrition_api.enable_llm_meal_suggestions

            portfolio = await self._get_portfolio_with_fallback(
                db=db,
                constraints=constraints,
                exclude_ingredients=variety_exclusions,
                enable_llm=enable_llm,
            )
```

- [ ] **Step 6: Replace discovery engine calls in generate_weekly_plan**

In `generate_weekly_plan` (around lines 274-283), replace the portfolio discovery inside the for loop:

```python
                from app.core.config import get_settings
                settings = get_settings()
                enable_llm = settings.nutrition_api.enable_llm_meal_suggestions

                portfolio = await self._get_portfolio_with_fallback(
                    db=db,
                    constraints=constraints,
                    exclude_ingredients=previous_day_ingredients,
                    enable_llm=enable_llm,
                )
```

- [ ] **Step 7: Replace discovery engine calls in regenerate_meal**

In `regenerate_meal` (around lines 426-435), replace the portfolio discovery:

```python
        from app.core.config import get_settings
        settings = get_settings()
        enable_llm = settings.nutrition_api.enable_llm_meal_suggestions

        portfolio = await self._get_portfolio_with_fallback(
            db=db,
            constraints=constraints,
            exclude_ingredients=exclude_ingredients or set(),
            enable_llm=enable_llm,
        )
```

- [ ] **Step 8: Wire up meal_suggester and nutrition_resolver in build_ml_pipeline_components**

In `build_ml_pipeline_components` (around line 711), add after the existing component building:

```python
    # Build hybrid pipeline components (LLM + nutrition API)
    from app.core.config import get_settings
    settings = get_settings()

    meal_suggester = None
    nutrition_resolver = None

    if settings.nutrition_api.enable_llm_meal_suggestions:
        from app.services.ml_diet_pipeline.suggestion.service import LLMMealSuggester
        from app.services.ml_diet_pipeline.nutrition.resolver import NutritionResolver
        from app.services.ml_diet_pipeline.nutrition.providers.calorieninjas import CalorieNinjasProvider
        from app.services.ml_diet_pipeline.nutrition.providers.usda import USDAProvider

        # Reuse the existing groq generator for meal suggestions
        meal_suggester = LLMMealSuggester(generator=get_groq_generator())

        # Build nutrition providers
        primary_provider = None
        fallback_provider = None

        cn_key = settings.nutrition_api.calorieninjas_api_key
        if cn_key:
            primary_provider = CalorieNinjasProvider(api_key=cn_key)

        usda_key = settings.nutrition_api.usda_api_key
        if usda_key:
            fallback_provider = USDAProvider(api_key=usda_key)

        nutrition_resolver = NutritionResolver(
            db=db,
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
            llm_generator=get_groq_generator(),
        )
```

Add `meal_suggester` and `nutrition_resolver` to the returned components dict:

```python
    components["meal_suggester"] = meal_suggester
    components["nutrition_resolver"] = nutrition_resolver
```

- [ ] **Step 9: Update orchestrator __init__ to accept new components**

In `MLPipelineOrchestrator.__init__` (around line 51), add handling for the new components after the existing ones:

```python
        self.meal_suggester = components.get("meal_suggester") if components else None
        self.nutrition_resolver = components.get("nutrition_resolver") if components else None
```

- [ ] **Step 10: Run all tests**

```bash
cd backend
python -m pytest tests/test_orchestrator_hybrid.py tests/test_nutrition_providers.py tests/test_nutrition_resolver.py tests/test_llm_meal_suggester.py -v
```

Expected: All tests PASS

- [ ] **Step 11: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/orchestrator.py backend/tests/test_orchestrator_hybrid.py
git commit -m "feat: integrate LLM meal suggestion path with fallback in orchestrator"
```

---

## Task 10: Handle `suggest_substitute` Action in Groq Generator

**Files:**
- Modify: `backend/app/services/ml_diet_pipeline/orchestrator.py`

- [ ] **Step 1: Add substitute handling to get_groq_generator**

In `get_groq_generator()`, inside the `generate(payload)` async function, add a new action handler after the `generate_supplement_note` block and before the `else` (recipe generation) block (around line 599):

```python
                elif action == "suggest_substitute":
                    original = payload.get("original_ingredient", "unknown")
                    diet = payload.get("diet_type", "any")
                    cuisine_val = payload.get("cuisine", "any")
                    category = payload.get("category", "protein")
                    prompt = f"""
                    The ingredient "{original}" could not be found in our nutrition database.
                    Suggest ONE common substitute that:
                    - Is a {category} item
                    - Fits a {diet} diet
                    - Belongs to {cuisine_val} cuisine
                    - Has a simple, widely recognized name (e.g. "Chicken Breast" not "Amritsari Tandoori Chicken")

                    Respond ONLY with a JSON object:
                    {{ "substitute": "Simple Ingredient Name" }}
                    """

                elif action == "suggest_meals":
                    prompt = payload.get("prompt", "")
```

- [ ] **Step 2: Verify file parses**

```bash
cd backend
python -c "import ast; ast.parse(open('app/services/ml_diet_pipeline/orchestrator.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ml_diet_pipeline/orchestrator.py
git commit -m "feat: add suggest_substitute and suggest_meals actions to Groq generator"
```

---

## Task 11: End-to-End Manual Verification

**Files:** None (testing only)

- [ ] **Step 1: Set environment variables**

Add your API keys to `backend/.env`:

```env
CALORIENINJAS_API_KEY=your_actual_key_here
USDA_API_KEY=your_actual_key_here
ENABLE_LLM_MEAL_SUGGESTIONS=true
```

Sign up for free keys at:
- CalorieNinjas: https://calorieninjas.com/api
- USDA: https://fdc.nal.usda.gov/api-key-signup.html

- [ ] **Step 2: Run the migration**

```bash
cd backend
python -m alembic upgrade head
```

- [ ] **Step 3: Start the backend**

```bash
cd backend
python start_backend.py
```

- [ ] **Step 4: Generate a daily plan via API**

```bash
curl -X POST http://localhost:8000/api/v1/diet-plans-ml/generate-daily \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

Verify in the logs:
- `[DEBUG][LLM_SUGGEST_START]` — LLM path was attempted
- `[DEBUG][NUTRITION_API_CALL]` or `[DEBUG][NUTRITION_CACHE_HIT]` — macros resolved
- If fallback: `[DEBUG][ML_PIPELINE_FALLBACK]` — should still produce a plan

- [ ] **Step 5: Test with feature flag off**

Set `ENABLE_LLM_MEAL_SUGGESTIONS=false` in `.env`, restart server, generate a plan. Verify it uses the old template-based pipeline (no `[DEBUG]` logs from the new path).

- [ ] **Step 6: Test each diet type**

Generate a plan for each: non-vegetarian, eggetarian, vegetarian, vegan. Verify ingredients match the diet type.

- [ ] **Step 7: Final commit**

```bash
git add backend/.env
git commit -m "chore: configure nutrition API keys for hybrid pipeline"
```

---

## Summary

| Task | What it builds | Dependencies |
|---|---|---|
| 1 | `api_verified` column migration | None |
| 2 | Nutrition API config settings | None |
| 3 | NutritionProvider ABC + NutritionResult | None |
| 4 | CalorieNinjas provider | Task 3 |
| 5 | USDA provider | Task 3 |
| 6 | NutritionResolver (cache + API + simplification) | Tasks 3, 4, 5 |
| 7 | LLM suggestion Pydantic schemas | None |
| 8 | LLM Meal Suggester service | Task 7 |
| 9 | Orchestrator integration + fallback | Tasks 6, 8 |
| 10 | Groq generator action handlers | Task 9 |
| 11 | End-to-end manual verification | All |
