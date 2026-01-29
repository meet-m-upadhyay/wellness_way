"""
Unit tests for security module
"""

import pytest
from app.core.security import InputSanitizer, SQLInjectionPrevention, sanitize_user_input


class TestInputSanitizer:
    """Test InputSanitizer class"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        # Normal string
        result = InputSanitizer.sanitize_string("Hello World")
        assert result == "Hello World"
        
        # String with HTML
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result
        
        # String with SQL injection patterns
        result = InputSanitizer.sanitize_string("'; DROP TABLE users; --")
        assert "DROP TABLE" not in result
        assert "--" not in result
    
    def test_sanitize_string_length_limit(self):
        """Test string length limiting"""
        long_string = "a" * 1000
        result = InputSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_html_allowed(self):
        """Test HTML sanitization when HTML is allowed"""
        html_string = "<p>Hello <strong>World</strong></p><script>alert('xss')</script>"
        result = InputSanitizer.sanitize_string(html_string, allow_html=True)
        assert "<p>" in result
        assert "<strong>" in result
        assert "<script>" not in result
    
    def test_sanitize_name(self):
        """Test name sanitization"""
        # Valid name
        result = InputSanitizer.sanitize_name("John Doe")
        assert result == "John Doe"
        
        # Name with special characters (apostrophe will be removed by SQL injection prevention)
        result = InputSanitizer.sanitize_name("John O'Connor-Smith")
        assert "John" in result and "Connor-Smith" in result
        
        # Name with invalid characters
        result = InputSanitizer.sanitize_name("John<script>alert('xss')</script>Doe")
        assert "<script>" not in result
        assert "John" in result and "Doe" in result
        
        # Empty name should raise error
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_name("")
        
        # Name with only invalid characters should raise error
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_name("###***")
    
    def test_sanitize_text_field(self):
        """Test text field sanitization"""
        # Normal text
        result = InputSanitizer.sanitize_text_field("I have diabetes and need low sugar meals.")
        assert "diabetes" in result
        assert "low sugar" in result
        
        # Text with URLs
        result = InputSanitizer.sanitize_text_field("Check out https://example.com for more info")
        assert "https://example.com" not in result
        assert "[URL_REMOVED]" in result
        
        # Text with excessive punctuation
        result = InputSanitizer.sanitize_text_field("Help!!!!!!!!!!!")
        assert "!!!!!!!!!!" not in result
        
        # Empty text
        result = InputSanitizer.sanitize_text_field("")
        assert result == ""
    
    def test_sanitize_list_field(self):
        """Test list field sanitization"""
        # Valid list
        allergies = ["peanuts", "shellfish", "dairy"]
        result = InputSanitizer.sanitize_list_field(allergies)
        assert "peanuts" in result
        assert "shellfish" in result
        assert "dairy" in result
        
        # List with invalid items
        foods = ["chicken", "<script>alert('xss')</script>", "beef", ""]
        result = InputSanitizer.sanitize_list_field(foods)
        assert "chicken" in result
        assert "beef" in result
        assert "<script>" not in str(result)
        assert "" not in result  # Empty strings should be removed
        
        # List with duplicates
        items = ["apple", "banana", "apple", "cherry"]
        result = InputSanitizer.sanitize_list_field(items)
        assert result.count("apple") == 1  # Duplicates removed
        
        # Too many items
        long_list = [f"item{i}" for i in range(100)]
        result = InputSanitizer.sanitize_list_field(long_list, max_items=10)
        assert len(result) <= 10
        
        # Items too long
        long_items = ["a" * 200, "short"]
        result = InputSanitizer.sanitize_list_field(long_items, max_item_length=50)
        assert all(len(item) <= 50 for item in result)
    
    def test_validate_uuid_string(self):
        """Test UUID validation"""
        # Valid UUID
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert InputSanitizer.validate_uuid_string(valid_uuid) is True
        
        # Invalid UUID
        invalid_uuid = "not-a-uuid"
        assert InputSanitizer.validate_uuid_string(invalid_uuid) is False
        
        # UUID with wrong format
        wrong_format = "123e4567e89b12d3a456426614174000"  # Missing hyphens
        assert InputSanitizer.validate_uuid_string(wrong_format) is False
    
    def test_sanitize_json_field(self):
        """Test JSON field sanitization"""
        # Valid JSON
        json_data = {
            "name": "John Doe",
            "age": 30,
            "preferences": ["vegetarian", "low-sodium"]
        }
        result = InputSanitizer.sanitize_json_field(json_data)
        assert result["name"] == "John Doe"
        assert result["age"] == 30
        assert "vegetarian" in result["preferences"]
        
        # JSON with malicious content
        malicious_json = {
            "name": "<script>alert('xss')</script>John",
            "description": "'; DROP TABLE users; --",
            "items": ["safe", "<iframe src='evil.com'></iframe>"]
        }
        result = InputSanitizer.sanitize_json_field(malicious_json)
        assert "<script>" not in result["name"]
        assert "DROP TABLE" not in result["description"]
        assert "<iframe>" not in str(result["items"])
        
        # Non-dict input
        result = InputSanitizer.sanitize_json_field("not a dict")
        assert result == {}


class TestSQLInjectionPrevention:
    """Test SQLInjectionPrevention class"""
    
    def test_validate_query_parameters(self):
        """Test query parameter validation"""
        # Valid parameters
        valid_params = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "limit": 10,
            "active": True
        }
        result = SQLInjectionPrevention.validate_query_parameters(valid_params)
        assert result == valid_params
        
        # Parameters with SQL injection
        malicious_params = {
            "user_id": "'; DROP TABLE users; --",
            "search": "normal search"
        }
        with pytest.raises(ValueError):
            SQLInjectionPrevention.validate_query_parameters(malicious_params)
        
        # Invalid parameter names
        invalid_names = {
            "user-id": "valid_value",  # Hyphens not allowed
            "user id": "valid_value"   # Spaces not allowed
        }
        result = SQLInjectionPrevention.validate_query_parameters(invalid_names)
        assert len(result) == 0  # Invalid names should be filtered out


class TestSanitizeUserInput:
    """Test sanitize_user_input function"""
    
    def test_sanitize_user_profile_data(self):
        """Test sanitizing user profile data"""
        user_data = {
            "name": "John <script>alert('xss')</script> Doe",
            "age": 30,
            "allergies": ["peanuts", "<script>", "dairy"],
            "budget_constraints": "Low budget with '; DROP TABLE users; --"
        }
        
        result = sanitize_user_input(user_data)
        
        # Name should be sanitized
        assert "<script>" not in result["name"]
        assert "John" in result["name"] and "Doe" in result["name"]
        
        # Age should remain unchanged
        assert result["age"] == 30
        
        # Allergies should be sanitized
        assert "peanuts" in result["allergies"]
        assert "dairy" in result["allergies"]
        assert "<script>" not in str(result["allergies"])
        
        # Budget constraints should be sanitized
        assert "DROP TABLE" not in result["budget_constraints"]
        assert "Low budget" in result["budget_constraints"]
    
    def test_sanitize_invalid_field(self):
        """Test sanitizing data with invalid field"""
        user_data = {
            "name": "",  # Empty name should raise error
        }
        
        with pytest.raises(ValueError):
            sanitize_user_input(user_data)
    
    def test_sanitize_nested_json(self):
        """Test sanitizing nested JSON data"""
        user_data = {
            "preferences": {
                "diet_type": "vegetarian",
                "notes": "<script>alert('xss')</script>Important notes"
            }
        }
        
        result = sanitize_user_input(user_data)
        
        # Nested JSON should be sanitized
        assert result["preferences"]["diet_type"] == "vegetarian"
        assert "<script>" not in result["preferences"]["notes"]
        assert "Important notes" in result["preferences"]["notes"]


class TestSecurityPatterns:
    """Test security pattern detection"""
    
    def test_xss_patterns(self):
        """Test XSS pattern detection and removal"""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for pattern in xss_patterns:
            result = InputSanitizer.sanitize_string(pattern)
            # Should not contain dangerous elements
            assert "script" not in result.lower() or "alert" not in result.lower()
    
    def test_sql_injection_patterns(self):
        """Test SQL injection pattern detection"""
        sql_patterns = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker'); --",
            "' UNION SELECT * FROM passwords --",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for pattern in sql_patterns:
            result = InputSanitizer.sanitize_string(pattern)
            # Should not contain SQL keywords
            dangerous_keywords = ["DROP", "INSERT", "UNION", "EXEC", "--"]
            for keyword in dangerous_keywords:
                assert keyword not in result.upper()
    
    def test_path_traversal_patterns(self):
        """Test path traversal pattern detection"""
        path_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for pattern in path_patterns:
            result = InputSanitizer.sanitize_text_field(pattern)  # Use text_field which has path traversal protection
            # Should not contain path traversal sequences
            assert "../" not in result
            assert "..\\" not in result