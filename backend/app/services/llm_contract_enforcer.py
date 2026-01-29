"""
LLM Contract Enforcer - Hard schema gate for LLM outputs

This module implements absolute contract enforcement for LLM responses.
Any response containing forbidden nutrition fields is immediately rejected.

CRITICAL RULES:
- Zero tolerance for nutrition fields in LLM output
- Recursive field checking (nested objects)
- Fail fast - no processing of invalid responses
- Count violations as failed generation attempts
"""

import json
import logging
from typing import Dict, Any, List, Set, Tuple
from app.utils.safe_logging import log_success, log_error, log_warning

logger = logging.getLogger(__name__)


class LLMContractViolation(Exception):
    """
    FATAL contract violation - do NOT retry, do NOT switch providers.
    
    This indicates the LLM fundamentally violated the contract and
    retrying will likely produce the same violation.
    """
    def __init__(self, message: str, forbidden_fields: List[str]):
        self.message = message
        self.reason = message  # For compatibility
        self.forbidden_fields = forbidden_fields
        super().__init__(message)


class RetryableLLMError(Exception):
    """
    Retryable LLM error - JSON formatting issues that can be retried.
    
    This indicates the LLM output is malformed but the request can be retried.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class LLMContractEnforcer:
    """Enforces hard contract rules on LLM outputs"""
    
    # FORBIDDEN FIELDS - Global, recursive check
    FORBIDDEN_FIELDS: Set[str] = {
        "nutrition", "calories", "protein", "fat", "carbohydrates", 
        "fiber", "sodium", "daily_totals", "macros", "nutrients",
        "kcal", "cal", "energy", "carbs", "fats", "proteins"
    }
    
    def __init__(self):
        self.violation_count = 0
        self.success_count = 0
    
    def enforce_contract(self, llm_response: str, request_id: str = None) -> Dict[str, Any]:
        """
        Enforce LLM contract on response.
        
        Args:
            llm_response: Raw LLM response string
            request_id: Optional request ID for logging
            
        Returns:
            Parsed and validated response
            
        Raises:
            LLMContractViolation: If response contains forbidden fields
        """
        # CRITICAL JSON GUARD: Check if response starts with JSON
        response_stripped = llm_response.strip()
        if not response_stripped.startswith("{"):
            logger.error(f"[LLM_JSON_GUARD] Non-JSON response detected (request_id: {request_id})")
            logger.error(f"[LLM_JSON_ERROR] request_id={request_id} first_200_chars={response_stripped[:200]!r}")
            raise RetryableLLMError("Non-JSON LLM output")
        
        try:
            # Parse JSON response
            parsed_response = json.loads(llm_response)
        except json.JSONDecodeError as e:
            logger.error(f"[LLM_JSON_ERROR] request_id={request_id} first_200_chars={llm_response[:200]!r}")
            log_warning(logger, f"Initial JSON parse failed (request_id: {request_id}): {e}")
            
            # Try to repair common JSON issues
            try:
                repaired_response = self._repair_json(llm_response)
                parsed_response = json.loads(repaired_response)
                log_success(logger, f"JSON repaired successfully (request_id: {request_id})")
            except (json.JSONDecodeError, Exception) as repair_error:
                log_error(logger, f"LLM response is not valid JSON (request_id: {request_id}): {e}")
                log_error(logger, f"JSON repair also failed: {repair_error}")
                raise RetryableLLMError(f"Invalid JSON response: {e}")
        
        # Check for forbidden fields recursively
        forbidden_found = self._find_forbidden_fields(parsed_response)
        
        if forbidden_found:
            self.violation_count += 1
            violation_msg = f"LLM CONTRACT VIOLATION: Found forbidden fields {forbidden_found}"
            
            log_error(logger, f"Forbidden fields found: {forbidden_found}")
            log_error(logger, f"   Violation count: {self.violation_count}")
            log_error(logger, f"   Response preview: {str(parsed_response)[:200]}...")
            
            raise LLMContractViolation(violation_msg, forbidden_found)
        
        # Contract enforced successfully
        self.success_count += 1
        log_success(logger, f"LLM contract enforced - no nutrition fields detected (request_id: {request_id})")
        logger.debug(f"   Success count: {self.success_count}")
        
        return parsed_response
    
    def _repair_json(self, json_str: str) -> str:
        """
        ROBUST JSON repair for LLM responses with truncation handling.
        
        Handles the specific "Unterminated string" error by:
        1. Detecting truncated JSON (incomplete structures)
        2. Removing incomplete elements that can't be repaired
        3. Ensuring valid JSON structure
        
        Args:
            json_str: Malformed JSON string
            
        Returns:
            Repaired JSON string
        """
        import re
        
        # Remove any text before the first {
        json_str = json_str.strip()
        start_idx = json_str.find('{')
        if start_idx > 0:
            json_str = json_str[start_idx:]
        
        # STRATEGY: Find the last valid, complete JSON structure
        # This is more reliable than trying to fix incomplete strings
        
        lines = json_str.split('\n')
        valid_lines = []
        brace_count = 0
        bracket_count = 0
        in_string = False
        escape_next = False
        
        for line_num, line in enumerate(lines):
            line_valid = True
            temp_brace_count = brace_count
            temp_bracket_count = bracket_count
            temp_in_string = in_string
            temp_escape_next = escape_next
            
            # Check if this line would create valid JSON
            for char in line:
                if temp_escape_next:
                    temp_escape_next = False
                    continue
                    
                if char == '\\':
                    temp_escape_next = True
                    continue
                    
                if char == '"' and not temp_escape_next:
                    temp_in_string = not temp_in_string
                    continue
                    
                if not temp_in_string:
                    if char == '{':
                        temp_brace_count += 1
                    elif char == '}':
                        temp_brace_count -= 1
                    elif char == '[':
                        temp_bracket_count += 1
                    elif char == ']':
                        temp_bracket_count -= 1
            
            # If this line ends with an unterminated string, it's invalid
            if temp_in_string:
                logger.info(f"Detected unterminated string at line {line_num + 1}, truncating here")
                line_valid = False
            
            if line_valid:
                valid_lines.append(line)
                brace_count = temp_brace_count
                bracket_count = temp_bracket_count
                in_string = temp_in_string
                escape_next = temp_escape_next
            else:
                # Stop processing at the first invalid line
                break
        
        # Reconstruct JSON from valid lines
        json_str = '\n'.join(valid_lines)
        
        # Close any open structures
        while bracket_count > 0:
            json_str += ']'
            bracket_count -= 1
        
        while brace_count > 0:
            json_str += '}'
            brace_count -= 1
        
        # Apply standard JSON fixes
        # 1. Fix trailing commas (very common)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 2. Fix single quotes to double quotes (common)
        json_str = json_str.replace("'", '"')
        
        # 3. Fix unquoted property names (common)
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        # 4. Fix already quoted property names that got double-quoted
        json_str = re.sub(r'""(\w+)"":', r'"\1":', json_str)
        
        # 5. Remove duplicate commas
        json_str = re.sub(r',,+', ',', json_str)
        
        return json_str
    
    def _find_forbidden_fields(self, obj: Any, path: str = "") -> List[str]:
        """
        Recursively find forbidden fields in nested objects.
        
        Args:
            obj: Object to check (dict, list, or primitive)
            path: Current path for debugging
            
        Returns:
            List of forbidden field paths found
        """
        forbidden_found = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if key itself is forbidden
                if key.lower() in self.FORBIDDEN_FIELDS:
                    forbidden_found.append(current_path)
                
                # Recursively check nested values
                nested_forbidden = self._find_forbidden_fields(value, current_path)
                forbidden_found.extend(nested_forbidden)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                nested_forbidden = self._find_forbidden_fields(item, current_path)
                forbidden_found.extend(nested_forbidden)
        
        return forbidden_found
    
    def get_stats(self) -> Dict[str, int]:
        """Get contract enforcement statistics"""
        return {
            "violations": self.violation_count,
            "successes": self.success_count,
            "total_checks": self.violation_count + self.success_count
        }


# Global enforcer instance
_contract_enforcer = LLMContractEnforcer()

def enforce_llm_contract(llm_response: str, request_id: str = None) -> Dict[str, Any]:
    """
    Global function to enforce LLM contract.
    
    Args:
        llm_response: Raw LLM response string
        request_id: Optional request ID for logging
        
    Returns:
        Parsed and validated response
        
    Raises:
        LLMContractViolation: If response contains forbidden fields
    """
    return _contract_enforcer.enforce_contract(llm_response, request_id)

def get_contract_stats() -> Dict[str, int]:
    """Get global contract enforcement statistics"""
    return _contract_enforcer.get_stats()