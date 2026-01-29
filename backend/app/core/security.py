"""
Security utilities for input sanitization and SQL injection prevention
"""

import re
import html
import logging
from typing import Any, Optional, List, Dict, Union
from bleach import clean, ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class InputSanitizer:
    """
    Comprehensive input sanitization utility class
    """
    
    # Allowed HTML tags for rich text fields (very restrictive)
    ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'u']
    ALLOWED_HTML_ATTRIBUTES = {}
    
    # Dangerous patterns to detect and remove
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',               # JavaScript URLs
        r'on\w+\s*=',                # Event handlers (onclick, onload, etc.)
        r'data:text/html',           # Data URLs with HTML
        r'vbscript:',                # VBScript URLs
        r'<iframe[^>]*>.*?</iframe>', # Iframe tags
        r'<object[^>]*>.*?</object>', # Object tags
        r'<embed[^>]*>.*?</embed>',   # Embed tags
        r'<link[^>]*>',              # Link tags
        r'<meta[^>]*>',              # Meta tags
        r'<style[^>]*>.*?</style>',   # Style tags
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)',
        r'(--|#|/\*|\*/)',           # SQL comments
        r'(\bOR\b.*=.*\bOR\b)',      # OR-based injections
        r'(\bAND\b.*=.*\bAND\b)',    # AND-based injections
        r'(\";|;)',                  # Semicolon injections (removed single quote to allow apostrophes in names)
        r'(\bxp_cmdshell\b)',        # Command execution
        r'(\bsp_executesql\b)',      # SQL Server stored procedures
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None, 
                       allow_html: bool = False, strict: bool = True) -> str:
        """
        Sanitize a string input for security
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow safe HTML tags
            strict: Whether to apply strict sanitization
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes and control characters
        value = value.replace('\x00', '').replace('\r', '').replace('\n', ' ')
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        if strict:
            # Remove dangerous patterns
            for pattern in cls.DANGEROUS_PATTERNS:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
            
            # Check for SQL injection patterns
            for pattern in cls.SQL_INJECTION_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"Potential SQL injection attempt detected: {pattern}")
                    # Remove the dangerous content
                    value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        # HTML sanitization
        if allow_html:
            # Use bleach to clean HTML
            value = clean(
                value,
                tags=cls.ALLOWED_HTML_TAGS,
                attributes=cls.ALLOWED_HTML_ATTRIBUTES,
                strip=True
            )
        else:
            # Escape HTML entities
            value = html.escape(value)
        
        # Enforce length limits
        if max_length and len(value) > max_length:
            value = value[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        return value
    
    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """
        Sanitize user names with specific rules
        
        Args:
            name: User name to sanitize
            
        Returns:
            Sanitized name
        """
        if not name:
            raise ValueError("Name cannot be empty")
        
        # Basic sanitization
        name = cls.sanitize_string(name, max_length=255, allow_html=False, strict=True)
        
        # Remove special characters except spaces, hyphens, and apostrophes
        name = re.sub(r'[^a-zA-Z0-9\s\-\'\.]', '', name)
        
        # Normalize spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        if not name:
            raise ValueError("Name contains only invalid characters")
        
        if len(name) < 1:
            raise ValueError("Name is too short")
        
        return name
    
    @classmethod
    def sanitize_text_field(cls, text: str, max_length: int = 1000) -> str:
        """
        Sanitize general text fields (descriptions, constraints, etc.)
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove URLs first (before other sanitization that might break them)
        text = re.sub(r'https?://[^\s]+', '[URL_REMOVED]', text, flags=re.IGNORECASE)
        text = re.sub(r'www\.[^\s]+', '[URL_REMOVED]', text, flags=re.IGNORECASE)
        
        # Apply comprehensive sanitization
        text = cls.sanitize_string(text, max_length=max_length, allow_html=False, strict=True)
        
        # Additional text-specific cleaning
        # Remove excessive punctuation
        text = re.sub(r'[!@#$%^&*()_+=\[\]{}|\\:";\'<>?,./]{3,}', '', text)
        
        # Remove path traversal patterns
        text = re.sub(r'\.\.[\\/]', '', text)  # Remove ../ and ..\
        text = re.sub(r'%2e%2e%2f', '', text, flags=re.IGNORECASE)  # Remove URL encoded ../
        
        return text.strip()
    
    @classmethod
    def sanitize_list_field(cls, items: List[str], max_items: int = 50, 
                           max_item_length: int = 100) -> List[str]:
        """
        Sanitize list fields (allergies, foods to avoid, etc.)
        
        Args:
            items: List of items to sanitize
            max_items: Maximum number of items allowed
            max_item_length: Maximum length per item
            
        Returns:
            Sanitized list
        """
        if not items:
            return []
        
        if not isinstance(items, list):
            raise ValueError("Expected a list")
        
        if len(items) > max_items:
            logger.warning(f"List truncated to {max_items} items")
            items = items[:max_items]
        
        sanitized_items = []
        for item in items:
            if isinstance(item, str) and item.strip():
                # Sanitize each item
                sanitized_item = cls.sanitize_string(
                    item, 
                    max_length=max_item_length, 
                    allow_html=False, 
                    strict=True
                )
                
                # Additional cleaning for list items
                sanitized_item = re.sub(r'[^a-zA-Z0-9\s\-\']', '', sanitized_item)
                sanitized_item = sanitized_item.strip().lower()
                
                if sanitized_item and len(sanitized_item) >= 2:
                    sanitized_items.append(sanitized_item)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in sanitized_items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        
        return unique_items
    
    @classmethod
    def validate_uuid_string(cls, uuid_str: str) -> bool:
        """
        Validate UUID string format
        
        Args:
            uuid_str: UUID string to validate
            
        Returns:
            True if valid UUID format
        """
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, uuid_str, re.IGNORECASE))
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Sanitize email addresses with specific rules
        
        Args:
            email: Email address to sanitize
            
        Returns:
            Sanitized email address
        """
        if not email:
            raise ValueError("Email cannot be empty")
        
        # Basic sanitization
        email = cls.sanitize_string(email, max_length=255, allow_html=False, strict=True)
        
        # Convert to lowercase for consistency
        email = email.lower().strip()
        
        # Basic email format validation (simple regex)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        # Additional security checks
        # Remove any remaining dangerous characters
        email = re.sub(r'[<>"\'\\\x00-\x1f\x7f-\x9f]', '', email)
        
        if not email:
            raise ValueError("Email contains only invalid characters")
        
        return email
    
    @classmethod
    def sanitize_json_field(cls, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize JSON field data recursively
        
        Args:
            json_data: JSON data to sanitize
            
        Returns:
            Sanitized JSON data
        """
        if not isinstance(json_data, dict):
            return {}
        
        sanitized = {}
        for key, value in json_data.items():
            # Sanitize key
            clean_key = cls.sanitize_string(str(key), max_length=100, allow_html=False, strict=True)
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '', clean_key)
            
            if not clean_key:
                continue
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = cls.sanitize_string(value, max_length=500, allow_html=False, strict=True)
            elif isinstance(value, (int, float)):
                sanitized[clean_key] = value
            elif isinstance(value, bool):
                sanitized[clean_key] = value
            elif isinstance(value, list):
                # Sanitize list elements
                clean_list = []
                for item in value[:20]:  # Limit list size
                    if isinstance(item, str):
                        clean_item = cls.sanitize_string(item, max_length=200, allow_html=False, strict=True)
                        if clean_item:
                            clean_list.append(clean_item)
                    elif isinstance(item, (int, float, bool)):
                        clean_list.append(item)
                sanitized[clean_key] = clean_list
            elif isinstance(value, dict):
                # Recursively sanitize nested objects (limit depth)
                sanitized[clean_key] = cls.sanitize_json_field(value)
        
        return sanitized


class SQLInjectionPrevention:
    """
    SQL injection prevention utilities
    """
    
    @staticmethod
    def validate_query_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize query parameters
        
        Args:
            params: Query parameters to validate
            
        Returns:
            Validated parameters
        """
        validated = {}
        
        for key, value in params.items():
            # Validate parameter names (only allow alphanumeric and underscore)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                logger.warning(f"Invalid parameter name: {key}")
                continue
            
            # Validate parameter values
            if isinstance(value, str):
                # Check for SQL injection patterns
                for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f"Potential SQL injection in parameter {key}: {value}")
                        raise ValueError(f"Invalid characters in parameter {key}")
                
                validated[key] = value
            elif isinstance(value, (int, float, bool)):
                validated[key] = value
            else:
                logger.warning(f"Unsupported parameter type for {key}: {type(value)}")
        
        return validated
    
    @staticmethod
    def safe_execute_query(session: Session, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Safely execute a raw SQL query with parameter validation
        
        Args:
            session: SQLAlchemy session
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        if params:
            params = SQLInjectionPrevention.validate_query_parameters(params)
        
        # Use SQLAlchemy's text() with bound parameters for safety
        try:
            result = session.execute(text(query), params or {})
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise


def sanitize_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to sanitize user input data
    
    Args:
        data: Dictionary of user input data
        
    Returns:
        Sanitized data dictionary
    """
    sanitized = {}
    
    for key, value in data.items():
        try:
            if key == 'name' and isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_name(value)
            elif key in ['budget_constraints', 'lifestyle_constraints'] and isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_text_field(value, max_length=500)
            elif key in ['allergies', 'foods_to_avoid'] and isinstance(value, list):
                sanitized[key] = InputSanitizer.sanitize_list_field(value)
            elif isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_string(value, max_length=1000)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_json_field(value)
            else:
                sanitized[key] = value
        except ValueError as e:
            logger.warning(f"Sanitization failed for field {key}: {e}")
            raise ValueError(f"Invalid input for field {key}: {e}")
    
    return sanitized


# Decorator for automatic input sanitization
def sanitize_input(func):
    """
    Decorator to automatically sanitize function inputs
    """
    def wrapper(*args, **kwargs):
        # Sanitize keyword arguments
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, dict):
                sanitized_kwargs[key] = sanitize_user_input(value)
            elif isinstance(value, str):
                sanitized_kwargs[key] = InputSanitizer.sanitize_string(value)
            else:
                sanitized_kwargs[key] = value
        
        return func(*args, **sanitized_kwargs)
    
    return wrapper