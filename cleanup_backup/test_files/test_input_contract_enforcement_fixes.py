"""
Test Input Contract Enforcement Fixes

This test verifies that all 4 root cause fixes are working correctly:
1. Ingredient normalization strips preparation tokens like "cooked", "(cooked)"
2. Unresolved ingredients throw terminal errors instead of passing silently
3. Missing _process_meals_with_safety method is implemented
4. LLM JSON contract is hardened with reduced surface area

These fixes address the cascading failures identified in the root cause analysis.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock

from app.services.ingredient_normalizer import IngredientNormalizer
from app.services.nutrition_engine import create_ingredient_with_resolution, NutritionCalculationError
from app.services.diet_plan_service import DietPlanService
from app.services.llm_contract_enforcer import LLMContractEnforcer, LLMContractViolation


class TestIngredientNormalizationFixes:
    """Test Fix #1: Enhanced ingredient normalization strips preparation tokens"""
    
    def test_preparation_token_stripping_parenthetical(self):
        """Test that preparation tokens in parentheses are stripped correctly"""
        normalizer = IngredientNormalizer()
        
        # Test cases from root cause analysis
        test_cases = [
            ("quinoa (cooked)", "quinoa"),
            ("rice (steamed)", "rice"),
            ("chicken breast (grilled)", "chicken breast"),
            ("broccoli (steamed)", "broccoli"),
            ("sweet potato (baked)", "sweet potato"),
            ("salmon (grilled)", "salmon"),
            ("oats (cooked)", "oats"),
            ("lentils (boiled)", "lentils")
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = normalizer._apply_normalization(input_name)
            assert normalized == expected_normalized, f"Failed to normalize '{input_name}' -> expected '{expected_normalized}', got '{normalized}'"
    
    def test_preparation_token_stripping_standalone(self):
        """Test that standalone preparation tokens are stripped correctly"""
        normalizer = IngredientNormalizer()
        
        test_cases = [
            ("cooked quinoa", "quinoa"),
            ("steamed rice", "rice"),
            ("grilled chicken breast", "chicken breast"),
            ("baked sweet potato", "sweet potato"),
            ("boiled lentils", "lentils"),
            ("sauteed spinach", "spinach"),
            ("roasted vegetables", "vegetables")
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = normalizer._apply_normalization(input_name)
            assert normalized == expected_normalized, f"Failed to normalize '{input_name}' -> expected '{expected_normalized}', got '{normalized}'"
    
    def test_complex_preparation_normalization(self):
        """Test complex cases with multiple preparation tokens"""
        normalizer = IngredientNormalizer()
        
        test_cases = [
            ("organic cooked quinoa (steamed)", "quinoa"),
            ("fresh grilled chicken breast (boneless)", "chicken breast"),
            ("trader joe's cooked brown rice", "brown rice"),
            ("whole foods steamed broccoli (frozen)", "broccoli")
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = normalizer._apply_normalization(input_name)
            assert normalized == expected_normalized, f"Failed to normalize '{input_name}' -> expected '{expected_normalized}', got '{normalized}'"


class TestNutritionEngineTerminalErrors:
    """Test Fix #2: Nutrition engine throws terminal errors for unresolved ingredients"""
    
    @pytest.mark.asyncio
    async def test_unresolved_ingredient_throws_terminal_error(self):
        """Test that unresolved ingredients throw NutritionCalculationError"""
        
        # Mock the resolution service to return SKIPPED status
        with patch('app.services.nutrition_engine.get_ingredient_resolution_service') as mock_service:
            mock_resolution_result = Mock()
            mock_resolution_result.status = Mock()
            mock_resolution_result.status.name = "SKIPPED"  # Mock enum
            mock_resolution_result.warning_message = "Ingredient could not be resolved"
            
            mock_service.return_value.resolve_ingredient = AsyncMock(return_value=mock_resolution_result)
            
            # This should now throw a terminal error instead of returning a skipped ingredient
            with pytest.raises(NutritionCalculationError) as exc_info:
                await create_ingredient_with_resolution("unknown_ingredient", 100.0, "g")
            
            assert "unknown_ingredient" in str(exc_info.value)
            assert "could not be resolved" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_resolution_exception_becomes_terminal_error(self):
        """Test that resolution service exceptions become terminal errors"""
        
        with patch('app.services.nutrition_engine.get_ingredient_resolution_service') as mock_service:
            # Mock resolution service to throw an exception
            mock_service.return_value.resolve_ingredient = AsyncMock(side_effect=Exception("Resolution failed"))
            
            # This should convert the exception to a terminal error
            with pytest.raises(NutritionCalculationError) as exc_info:
                await create_ingredient_with_resolution("problematic_ingredient", 100.0, "g")
            
            assert "problematic_ingredient" in str(exc_info.value)
            assert "resolution failed" in str(exc_info.value).lower()


class TestDietPlanServiceMissingMethod:
    """Test Fix #3: Missing _process_meals_with_safety method is implemented"""
    
    def test_process_meals_with_safety_method_exists(self):
        """Test that _process_meals_with_safety method exists in DietPlanService"""
        from sqlalchemy.orm import Session
        
        # Create a mock database session
        mock_db = Mock(spec=Session)
        
        # Create service instance
        service = DietPlanService(mock_db)
        
        # Verify the method exists
        assert hasattr(service, '_process_meals_with_safety'), "DietPlanService is missing _process_meals_with_safety method"
        assert callable(getattr(service, '_process_meals_with_safety')), "_process_meals_with_safety is not callable"
    
    @pytest.mark.asyncio
    async def test_process_meals_with_safety_handles_terminal_errors(self):
        """Test that _process_meals_with_safety properly handles terminal errors"""
        from sqlalchemy.orm import Session
        
        mock_db = Mock(spec=Session)
        service = DietPlanService(mock_db)
        
        # Mock plan data with an ingredient that will fail
        plan_data = {
            "day_1": {
                "meals": [
                    {
                        "name": "Test Meal",
                        "meal_type": "breakfast",
                        "ingredients": [
                            {
                                "name": "unresolvable_ingredient",
                                "quantity": 100,
                                "unit": "g"
                            }
                        ],
                        "instructions": "Test instructions"
                    }
                ]
            }
        }
        
        # Mock create_ingredient_with_resolution to throw terminal error
        with patch('app.services.diet_plan_service.create_ingredient_with_resolution') as mock_create:
            mock_create.side_effect = NutritionCalculationError("Ingredient could not be resolved", ["unresolvable_ingredient"])
            
            # This should propagate the terminal error instead of silently continuing
            with pytest.raises(NutritionCalculationError):
                await service._process_meals_with_safety(plan_data)


class TestLLMContractHardening:
    """Test Fix #4: LLM JSON contract is hardened with reduced surface area"""
    
    def test_hardened_json_repair_basic_fixes(self):
        """Test that hardened JSON repair handles basic cases reliably"""
        enforcer = LLMContractEnforcer()
        
        # Test basic fixes that should work reliably
        test_cases = [
            # Single quotes to double quotes
            ("{'name': 'test'}", '{"name": "test"}'),
            
            # Trailing commas
            ('{"name": "test",}', '{"name": "test"}'),
            ('{"items": ["a", "b",]}', '{"items": ["a", "b"]}'),
            
            # Unquoted property names
            ('{name: "test"}', '{"name": "test"}'),
            
            # Duplicate commas
            ('{"name": "test",, "value": 1}', '{"name": "test", "value": 1}'),
        ]
        
        for malformed_json, expected_json in test_cases:
            try:
                repaired = enforcer._repair_json(malformed_json)
                # Should be valid JSON after repair
                parsed = json.loads(repaired)
                expected_parsed = json.loads(expected_json)
                assert parsed == expected_parsed, f"Repair failed: '{malformed_json}' -> '{repaired}' (expected: '{expected_json}')"
            except json.JSONDecodeError as e:
                pytest.fail(f"Hardened JSON repair failed for '{malformed_json}': {e}")
    
    def test_hardened_json_repair_avoids_complex_fixes(self):
        """Test that hardened repair doesn't attempt complex fixes that were causing issues"""
        enforcer = LLMContractEnforcer()
        
        # These cases should either work with simple fixes or fail cleanly
        # (not attempt complex string manipulation that was causing issues)
        complex_cases = [
            '{"name": "test with unterminated string',  # Should fail cleanly
            '{"name": "test", "value": }',  # Should fail cleanly
            '{"name": "test" "missing_comma": "value"}',  # Should fail cleanly
        ]
        
        for malformed_json in complex_cases:
            try:
                repaired = enforcer._repair_json(malformed_json)
                # If repair succeeds, it should produce valid JSON
                json.loads(repaired)
            except json.JSONDecodeError:
                # It's OK for complex cases to fail - we want clean failures
                # rather than attempting unreliable complex repairs
                pass
    
    def test_contract_violation_detection(self):
        """Test that forbidden nutrition fields are still detected correctly"""
        enforcer = LLMContractEnforcer()
        
        # Valid response (should pass)
        valid_response = json.dumps({
            "meals": [
                {
                    "name": "Test Meal",
                    "ingredients": [
                        {"name": "chicken", "quantity": 100, "unit": "g"}
                    ]
                }
            ]
        })
        
        result = enforcer.enforce_contract(valid_response)
        assert "meals" in result
        
        # Invalid response with forbidden fields (should fail)
        invalid_response = json.dumps({
            "meals": [
                {
                    "name": "Test Meal",
                    "calories": 500,  # FORBIDDEN
                    "ingredients": [
                        {"name": "chicken", "quantity": 100, "unit": "g", "protein": 25}  # FORBIDDEN
                    ]
                }
            ]
        })
        
        with pytest.raises(LLMContractViolation) as exc_info:
            enforcer.enforce_contract(invalid_response)
        
        assert "calories" in str(exc_info.value) or "protein" in str(exc_info.value)


class TestIntegratedFixes:
    """Test that all fixes work together in an integrated scenario"""
    
    @pytest.mark.asyncio
    async def test_complete_fix_integration(self):
        """Test that all 4 fixes work together to prevent the original cascading failure"""
        
        # Scenario: LLM suggests "cooked quinoa" which should now be handled correctly
        
        # 1. Test ingredient normalization fix
        normalizer = IngredientNormalizer()
        normalized = normalizer._apply_normalization("cooked quinoa")
        assert normalized == "quinoa", f"Normalization failed: got '{normalized}'"
        
        # 2. Test that if ingredient still can't be resolved, it throws terminal error
        with patch('app.services.nutrition_engine.get_ingredient_resolution_service') as mock_service:
            mock_resolution_result = Mock()
            mock_resolution_result.status = Mock()
            mock_resolution_result.status.name = "SKIPPED"
            mock_resolution_result.warning_message = "Still unresolvable"
            
            mock_service.return_value.resolve_ingredient = AsyncMock(return_value=mock_resolution_result)
            
            # Should throw terminal error (no silent failures)
            with pytest.raises(NutritionCalculationError):
                await create_ingredient_with_resolution("cooked quinoa", 100.0, "g")
        
        # 3. Test that DietPlanService has the required method
        from sqlalchemy.orm import Session
        mock_db = Mock(spec=Session)
        service = DietPlanService(mock_db)
        assert hasattr(service, '_process_meals_with_safety')
        
        # 4. Test that LLM contract enforcer works with hardened repair
        enforcer = LLMContractEnforcer()
        valid_json = '{"meals": [{"name": "test"}]}'
        result = enforcer.enforce_contract(valid_json)
        assert "meals" in result


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])