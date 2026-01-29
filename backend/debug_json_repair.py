#!/usr/bin/env python3
"""
Debug JSON repair logic
"""

import json
import re

def debug_repair_json(json_str: str) -> str:
    """Debug version of the repair function"""
    print(f"Input JSON: {repr(json_str)}")
    
    # Remove any text before the first {
    json_str = json_str.strip()
    start_idx = json_str.find('{')
    if start_idx > 0:
        json_str = json_str[start_idx:]
    
    print(f"After cleanup: {repr(json_str)}")
    
    lines = json_str.split('\n')
    print(f"Lines: {len(lines)}")
    for i, line in enumerate(lines):
        print(f"  {i}: {repr(line)}")
    
    valid_lines = []
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for line_num, line in enumerate(lines):
        print(f"\nProcessing line {line_num}: {repr(line)}")
        print(f"  Before: brace_count={brace_count}, bracket_count={bracket_count}, in_string={in_string}")
        
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
        
        print(f"  After: temp_brace_count={temp_brace_count}, temp_bracket_count={temp_bracket_count}, temp_in_string={temp_in_string}")
        
        # If this line ends with an unterminated string, it's invalid
        if temp_in_string:
            print(f"  INVALID: Line ends while in string (unterminated string)")
            line_valid = False
        
        if line_valid:
            print(f"  VALID: Adding line")
            valid_lines.append(line)
            brace_count = temp_brace_count
            bracket_count = temp_bracket_count
            in_string = temp_in_string
            escape_next = temp_escape_next
        else:
            print(f"  INVALID: Stopping here")
            break
    
    # Reconstruct JSON from valid lines
    json_str = '\n'.join(valid_lines)
    print(f"\nReconstructed from valid lines: {repr(json_str)}")
    
    # Close any open structures
    while bracket_count > 0:
        json_str += ']'
        bracket_count -= 1
        print(f"Added closing bracket")
    
    while brace_count > 0:
        json_str += '}'
        brace_count -= 1
        print(f"Added closing brace")
    
    print(f"After closing structures: {repr(json_str)}")
    
    # Apply standard JSON fixes
    # 1. Fix trailing commas (very common)
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    print(f"After fixing trailing commas: {repr(json_str)}")
    
    return json_str

def test_debug():
    malformed_json = '''{\n  "plan_type": "daily",\n  "date": "2024-01-26",\n  "breakfast": {\n    "name": "Greek Yogurt and Hemp Seed Bowl",\n    "ingredients": [\n      {"name": "greek yogurt (plain)", "quantity": 150, "unit": "'''
    
    try:
        repaired = debug_repair_json(malformed_json)
        print(f"\nFinal repaired JSON: {repr(repaired)}")
        
        # Try to parse it
        parsed = json.loads(repaired)
        print('✅ JSON repair successful!')
        print('Keys:', list(parsed.keys()))
        return True
        
    except Exception as e:
        print(f'❌ JSON repair failed: {e}')
        return False

if __name__ == "__main__":
    test_debug()