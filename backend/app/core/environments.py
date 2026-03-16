"""
Environment-specific configuration management
"""

from typing import Dict, Any
from .config import Settings


class DevelopmentConfig(Settings):
    """Development environment configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.environment = "development"
        self.debug = True
        self.testing = False
        
        # Development-specific overrides
        self.database.echo = True  # Enable SQL logging in development
        self.logging.level = "DEBUG"
        self.security.cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",  # Alternative dev port
        ]
        
        # Relaxed security for development
        self.security.access_token_expire_minutes = 60  # Longer tokens in dev
        self.ai.openai_timeout = 60  # Longer timeout for debugging


class StagingConfig(Settings):
    """Staging environment configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.environment = "staging"
        self.debug = False
        self.testing = False
        
        # Staging-specific overrides
        self.logging.level = "INFO"
        self.monitoring.sentry_environment = "staging"
        self.monitoring.sentry_sample_rate = 0.5  # Sample 50% of errors
        
        # More restrictive CORS for staging
        self.security.cors_origins = [
            "https://staging.wellnessway.com",
            "https://staging-app.wellnessway.com"
        ]


class ProductionConfig(Settings):
    """Production environment configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.environment = "production"
        self.debug = False
        self.testing = False
        
        # Production-specific overrides
        self.logging.level = "WARNING"
        self.monitoring.sentry_environment = "production"
        self.monitoring.sentry_sample_rate = 0.1  # Sample 10% of errors
        
        # Strict security for production
        self.security.bcrypt_rounds = 14  # Higher security
        self.security.access_token_expire_minutes = 15  # Shorter tokens
        self.security.cors_origins = [
            "https://wellnessway.com",
            "https://app.wellnessway.com",
            "https://wellness-way.meetupadhyaykgp.workers.dev"
        ]
        
        # Production performance settings
        self.database.pool_size = 10
        self.database.max_overflow = 20
        self.cache.redis_max_connections = 20


class TestingConfig(Settings):
    """Testing environment configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.environment = "development"
        self.debug = True
        self.testing = True
        
        # Testing-specific overrides
        self.database.url = "postgresql://test:test@localhost:5432/test_wellnessway_db"
        self.cache.redis_url = "redis://localhost:6379/1"  # Different Redis DB
        self.logging.level = "DEBUG"
        self.logging.enable_file_logging = False  # No file logging in tests
        
        # Disable external services in tests
        self.ai.openai_api_key = None
        self.monitoring.sentry_dsn = None
        self.enable_analytics = False
        
        # Fast settings for tests
        self.security.bcrypt_rounds = 4  # Faster password hashing
        self.ai.openai_timeout = 5


def get_config(environment: str = None) -> Settings:
    """
    Factory function to get configuration based on environment
    
    Args:
        environment: Environment name (development, staging, production, testing)
        
    Returns:
        Settings instance for the specified environment
    """
    import os
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "staging": StagingConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    config_class = config_map.get(environment, DevelopmentConfig)
    return config_class()


def validate_production_config(config: Settings) -> Dict[str, Any]:
    """
    Validate production configuration and return any issues
    
    Args:
        config: Settings instance to validate
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    if config.is_production:
        # Check required production settings
        if not config.get_openai_api_key():
            issues.append("OpenAI API key is required in production")
        
        if config.get_secret_key() == "dev-secret-key-change-in-production":
            issues.append("Default secret key detected in production")
        
        if config.debug:
            warnings.append("Debug mode is enabled in production")
        
        if config.database.echo:
            warnings.append("SQL logging is enabled in production")
        
        if config.logging.level == "DEBUG":
            warnings.append("Debug logging is enabled in production")
        
        # Check security settings
        if config.security.bcrypt_rounds < 12:
            warnings.append("BCrypt rounds should be at least 12 in production")
        
        if config.security.access_token_expire_minutes > 30:
            warnings.append("Access token expiry is longer than recommended for production")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }