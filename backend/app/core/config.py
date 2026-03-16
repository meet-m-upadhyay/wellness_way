"""
Configuration settings for WellnessWay Diet Planner
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, validator, SecretStr
from typing import Optional, Literal, List
import os
import secrets
from pathlib import Path

# Ensure .env files are loaded (repo root first, then backend/.env)
from dotenv import load_dotenv

# Paths
backend_dir = Path(__file__).parent.parent.parent  # backend directory
repo_root = backend_dir.parent

# Load repo root .env first (if present), then backend/.env
load_dotenv(repo_root / '.env')
load_dotenv(backend_dir / '.env')

# Import secure key manager
try:
    from app.core.secrets import get_secure_api_key
except ImportError:
    # Fallback if secrets module not available
    def get_secure_api_key(provider: str, encoded_key: Optional[str] = None) -> Optional[str]:
        return os.getenv(f"{provider.upper()}_API_KEY")


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    url: str = Field(
        default="postgresql+psycopg://wellnessway:password@database:5432/wellnessway_db",
        description="Database connection URL",
        env="DATABASE_URL"
    )
    pool_size: int = Field(default=5, ge=1, le=20)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=300)
    echo: bool = Field(default=False, description="Enable SQL query logging")
    
    def __init__(self, **kwargs):
        # Explicitly load environment variables
        import os
        if 'url' not in kwargs and os.getenv('DATABASE_URL'):
            kwargs['url'] = os.getenv('DATABASE_URL')
        super().__init__(**kwargs)
    
    @validator('url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+psycopg://')):
            raise ValueError('Database URL must be a PostgreSQL connection string')
        return v


class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    
    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    secret_key: SecretStr = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing",
        env="SECRET_KEY"
    )
    
    # JWT Settings
    jwt_secret_key: SecretStr = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key for token signing",
        env="JWT_SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    
    # Google OAuth Settings
    google_client_id: Optional[str] = Field(
        default=None,
        description="Google OAuth client ID",
        env="GOOGLE_CLIENT_ID"
    )
    google_client_secret: Optional[SecretStr] = Field(
        default=None,
        description="Google OAuth client secret",
        env="GOOGLE_CLIENT_SECRET"
    )
    
    def __init__(self, **kwargs):
        # Explicitly load environment variables for nested settings
        import os
        if 'google_client_id' not in kwargs and os.getenv('GOOGLE_CLIENT_ID'):
            kwargs['google_client_id'] = os.getenv('GOOGLE_CLIENT_ID')
        if 'google_client_secret' not in kwargs and os.getenv('GOOGLE_CLIENT_SECRET'):
            kwargs['google_client_secret'] = os.getenv('GOOGLE_CLIENT_SECRET')
        if 'jwt_secret_key' not in kwargs and os.getenv('JWT_SECRET_KEY'):
            kwargs['jwt_secret_key'] = os.getenv('JWT_SECRET_KEY')
        super().__init__(**kwargs)

    
    password_min_length: int = Field(default=8, ge=6)
    bcrypt_rounds: int = Field(default=12, ge=10, le=15)
    
    # CORS and Host settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "https://wellness-way.meetupadhyaykgp.workers.dev"],
        description="Allowed CORS origins",
        env="CORS_ORIGINS"
    )
    trusted_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0", "wellness-way-backend-1021198538658.us-central1.run.app"],
        description="Trusted hosts for middleware",
        env="TRUSTED_HOSTS"
    )
    cors_allow_credentials: bool = Field(default=True)
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if isinstance(v, str) and len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v
    
    @validator('jwt_secret_key')
    def validate_jwt_secret_key(cls, v):
        if isinstance(v, str) and len(v) < 32:
            raise ValueError('JWT secret key must be at least 32 characters long')
        return v


class AISettings(BaseSettings):
    """AI integration settings"""
    
    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # AI Provider Selection
    ai_provider: Literal["openai", "groq", "huggingface", "ollama", "mock"] = Field(
        default="groq", 
        description="AI provider to use for diet plan generation"
    )
    
    # OpenAI Settings
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key for diet plan generation"
    )
    openai_api_key_encoded: Optional[str] = Field(
        default=None,
        description="Encoded OpenAI API key for secure storage"
    )
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    
    # Groq Settings (Free alternative)
    groq_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Groq API key for diet plan generation"
    )
    groq_api_key_encoded: Optional[str] = Field(
        default=None,
        description="Encoded Groq API key for secure storage"
    )
    groq_model: str = Field(default="llama-3.1-8b-instant", description="Groq model to use")
    
    # Hugging Face Settings
    huggingface_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Hugging Face API key"
    )
    huggingface_api_key_encoded: Optional[str] = Field(
        default=None,
        description="Encoded Hugging Face API key for secure storage"
    )
    huggingface_model: str = Field(default="meta-llama/Llama-3.2-1B-Instruct", description="HF model to use")
    
    # Ollama Settings (Local)
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="llama3.1", description="Ollama model to use")
    
    # General AI Settings - OPTIMIZED FOR COST CONTROL
    openai_max_tokens: int = Field(default=400, ge=100, le=1000)  # Reduced from 2000
    openai_temperature: float = Field(default=0.4, ge=0.0, le=1.0)  # Reduced from 0.7
    openai_timeout: int = Field(default=30, ge=5, le=120)
    openai_max_retries: int = Field(default=3, ge=1, le=5)
    
    # AI safety settings
    max_plan_generation_time: int = Field(default=30, ge=10, le=120)
    enable_content_filtering: bool = Field(default=True)


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    format: Literal["json", "text"] = Field(default="json")
    enable_file_logging: bool = Field(default=True)
    log_file_path: str = Field(default="logs/app.log")
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=20)
    
    # Structured logging fields
    include_request_id: bool = Field(default=True)
    include_user_id: bool = Field(default=True)
    mask_sensitive_data: bool = Field(default=True)


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings"""
    
    sentry_dsn: Optional[SecretStr] = Field(default=None, description="Sentry DSN for error tracking")
    sentry_environment: str = Field(default="development")
    sentry_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Health check settings
    enable_health_checks: bool = Field(default=True)
    health_check_timeout: int = Field(default=5, ge=1, le=30)
    
    # Metrics
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)


class CacheSettings(BaseSettings):
    """Cache configuration settings"""
    
    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL for caching"
    )
    redis_timeout: int = Field(default=5, ge=1, le=30)
    redis_max_connections: int = Field(default=10, ge=1, le=50)
    
    # Cache TTL settings (in seconds)
    user_profile_ttl: int = Field(default=3600, ge=300)  # 1 hour
    diet_plan_ttl: int = Field(default=86400, ge=3600)   # 24 hours
    health_context_ttl: int = Field(default=7200, ge=600)  # 2 hours


class EmailSettings(BaseSettings):
    """Email / SMTP configuration for notifications"""

    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )

    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host", env="SMTP_HOST")
    smtp_port: int = Field(default=587, ge=1, le=65535, description="SMTP server port", env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username (email)", env="SMTP_USER")
    smtp_password: Optional[SecretStr] = Field(default=None, description="SMTP password or app-password", env="SMTP_PASSWORD")
    from_email: Optional[str] = Field(default=None, description="Sender email address", env="FROM_EMAIL")
    admin_email: Optional[str] = Field(default=None, description="Admin email to receive notifications", env="ADMIN_EMAIL")
    enable_notifications: bool = Field(default=False, description="Master switch for email notifications", env="ENABLE_EMAIL_NOTIFICATIONS")
    app_base_url: str = Field(default="http://localhost:3000", description="Frontend base URL for links in emails", env="APP_BASE_URL")

    def __init__(self, **kwargs):
        import os
        for key in ('smtp_user', 'smtp_password', 'from_email', 'admin_email', 'app_base_url'):
            env_key = key.upper()
            if key not in kwargs and os.getenv(env_key):
                kwargs[key] = os.getenv(env_key)
        if 'enable_notifications' not in kwargs and os.getenv('ENABLE_EMAIL_NOTIFICATIONS'):
            kwargs['enable_notifications'] = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() in ('true', '1', 'yes')
        super().__init__(**kwargs)


class Settings(BaseSettings):
    """Main application settings"""
    
    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=True)
    testing: bool = Field(default=False)
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_prefix: str = Field(default="/api/v1")
    
    # Application metadata
    app_name: str = Field(default="WellnessWay Diet Planner")
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(default="AI-powered wellness and diet planning application")
    
    # Feature flags
    enable_user_registration: bool = Field(default=True)
    enable_ai_generation: bool = Field(default=True)
    enable_plan_regeneration: bool = Field(default=True)
    enable_analytics: bool = Field(default=False)
    enable_ml_pipeline: bool = Field(default=False)
    
    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ai: AISettings = Field(default_factory=AISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    
    @validator('environment')
    def validate_environment(cls, v):
        if v == "production":
            # Additional production validations can be added here
            pass
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.testing
    
    def get_database_url(self) -> str:
        """Get database URL with proper formatting"""
        return self.database.url
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key with secure fallback options"""
        # Try encoded key first, then regular key, then secure manager
        encoded_key = getattr(self.ai, 'openai_api_key_encoded', None)
        if encoded_key:
            secure_key = get_secure_api_key("openai", encoded_key)
            if secure_key:
                return secure_key
        
        # Fallback to regular key
        if self.ai.openai_api_key:
            return self.ai.openai_api_key.get_secret_value()
        
        return None
    
    def get_groq_api_key(self) -> Optional[str]:
        """Get Groq API key with secure fallback options"""
        # Try encoded key first, then regular key, then secure manager
        encoded_key = getattr(self.ai, 'groq_api_key_encoded', None)
        if encoded_key:
            secure_key = get_secure_api_key("groq", encoded_key)
            if secure_key:
                return secure_key
        
        # Fallback to regular key
        if self.ai.groq_api_key:
            return self.ai.groq_api_key.get_secret_value()
        
        return None
    
    def get_huggingface_api_key(self) -> Optional[str]:
        """Get Hugging Face API key with secure fallback options"""
        # Try encoded key first, then regular key, then secure manager
        encoded_key = getattr(self.ai, 'huggingface_api_key_encoded', None)
        if encoded_key:
            secure_key = get_secure_api_key("huggingface", encoded_key)
            if secure_key:
                return secure_key
        
        # Fallback to regular key
        if self.ai.huggingface_api_key:
            return self.ai.huggingface_api_key.get_secret_value()
        
        return None
    
    def get_secret_key(self) -> str:
        """Get secret key as string"""
        return self.security.secret_key.get_secret_value()
    
    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key as string"""
        return self.security.jwt_secret_key.get_secret_value()
    
    def get_google_client_secret(self) -> Optional[str]:
        """Get Google OAuth client secret"""
        if self.security.google_client_secret:
            return self.security.google_client_secret.get_secret_value()
        return None
    
    def setup_logging_directory(self) -> None:
        """Ensure logging directory exists"""
        if self.logging.enable_file_logging:
            log_path = Path(self.logging.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure logging directory exists on import
settings.setup_logging_directory()


def get_settings() -> Settings:
    """Get global settings instance"""
    return settings