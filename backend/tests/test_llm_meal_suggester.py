"""Unit tests for LLMMealSuggester service."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from app.services.ml_diet_pipeline.suggestion.service import LLMMealSuggester


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_response(meal_type: str = "breakfast") -> dict:
    """Build a minimal valid LLMSuggestionResponse payload."""
    return {
        "meals": [
            {
                "meal_type": meal_type,
                "ingredients": [
                    {
                        "name": "chicken breast",
                        "category": "protein",
                        "diet_flags": ["non-vegetarian"],
                        "cuisine_tags": ["indian"],
                        "allergen_flags": [],
                    },
                    {
                        "name": "brown rice",
                        "category": "starch",
                        "diet_flags": ["vegan", "vegetarian"],
                        "cuisine_tags": ["indian"],
                        "allergen_flags": [],
                    },
                    {
                        "name": "spinach",
                        "category": "vegetables",
                        "diet_flags": ["vegan", "vegetarian"],
                        "cuisine_tags": ["indian"],
                        "allergen_flags": [],
                    },
                    {
                        "name": "olive oil",
                        "category": "fat",
                        "diet_flags": ["vegan", "vegetarian"],
                        "cuisine_tags": ["indian"],
                        "allergen_flags": [],
                    },
                ],
            }
        ]
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_suggest_meals_valid_response():
    """Mock generator returns valid JSON — verify flat ingredient list is returned."""
    mock_generator = AsyncMock(return_value=_make_valid_response("breakfast"))
    suggester = LLMMealSuggester(generator=mock_generator)

    result = await suggester.suggest_meals(
        diet_type="non-vegetarian",
        cuisine="indian",
        meal_types=["breakfast"],
    )

    # Should return a flat list of ingredient dicts
    assert isinstance(result, list)
    assert len(result) == 4  # 4 ingredients from the one meal

    # Each item should be a dict with the expected keys
    for item in result:
        assert isinstance(item, dict)
        assert "name" in item
        assert "category" in item
        assert "diet_flags" in item
        assert "cuisine_tags" in item
        assert "allergen_flags" in item

    # Verify specific ingredient names
    names = [item["name"] for item in result]
    assert "chicken breast" in names
    assert "brown rice" in names
    assert "spinach" in names
    assert "olive oil" in names

    # Generator must have been called exactly once
    mock_generator.assert_awaited_once()


@pytest.mark.asyncio
async def test_suggest_meals_invalid_json_returns_empty():
    """Mock returns structurally bad data — verify empty list is returned."""
    mock_generator = AsyncMock(return_value={"bad": "data"})
    suggester = LLMMealSuggester(generator=mock_generator)

    result = await suggester.suggest_meals(
        diet_type="vegetarian",
        cuisine="indian",
        meal_types=["lunch"],
    )

    assert result == []
    mock_generator.assert_awaited_once()


@pytest.mark.asyncio
async def test_suggest_meals_generator_fails_returns_empty():
    """Mock generator raises an exception — verify empty list is returned gracefully."""
    mock_generator = AsyncMock(side_effect=Exception("LLM service unavailable"))
    suggester = LLMMealSuggester(generator=mock_generator)

    result = await suggester.suggest_meals(
        diet_type="vegan",
        cuisine="mediterranean",
        meal_types=["dinner"],
    )

    assert result == []
    mock_generator.assert_awaited_once()


@pytest.mark.asyncio
async def test_prompt_includes_diet_priority():
    """Capture the payload sent to the generator and verify it contains diet type and priority language."""
    captured_payloads: list[dict] = []

    async def capturing_generator(payload: dict) -> dict:
        captured_payloads.append(payload)
        # Return a valid response so the service completes normally
        return _make_valid_response("breakfast")

    suggester = LLMMealSuggester(generator=capturing_generator)

    await suggester.suggest_meals(
        diet_type="eggetarian",
        cuisine="south-indian",
        meal_types=["breakfast"],
        allergies=["nuts"],
        foods_to_avoid=["mushrooms"],
        exclude_ingredients=["paneer"],
        primary_goal="weight loss",
    )

    assert len(captured_payloads) == 1
    payload = captured_payloads[0]

    # action must be "suggest_meals"
    assert payload.get("action") == "suggest_meals"

    # prompt must be present
    assert "prompt" in payload
    prompt: str = payload["prompt"]

    # Prompt must mention the specific diet type
    assert "eggetarian" in prompt

    # Prompt must contain diet priority language
    assert "priority" in prompt.lower() or "diet priority" in prompt.lower()

    # Prompt should mention the key diet rule for eggetarian
    assert "No meat/fish" in prompt

    # Prompt should include the cuisine
    assert "south-indian" in prompt

    # Prompt should include allergy info
    assert "nuts" in prompt

    # Prompt should include exclusions
    assert "paneer" in prompt
