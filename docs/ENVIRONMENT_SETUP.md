# Environment Variables and Secrets Management

This document explains how to configure environment variables and manage secrets for the WellnessWay Diet Planner application.

## Overview

The application uses a sophisticated configuration system that supports:

- **Environment-specific configurations** (development, staging, production, testing)
- **Secure secrets management** with encryption
- **Docker secrets support** for production deployments
- **Validation and safety checks** for production environments
- **Flexible configuration sources** (files, environment variables, Docker secrets)

## Configuration Structure

### Core Configuration Files

- `.env.example` - Template with all available configuration options
- `.env` - Local development configuration (created from example)
- `.env.production` - Production-specific settings template
- `.env.testing` - Testing environment configuration
- `backend/app/core/config.py` - Main configuration classes
- `backend/app/core/environments.py` - Environment-specific configurations
- `backend/app/core/secrets.py` - Secrets management utilities

### Configuration Categories

#### 1. Environment Configuration
```bash
ENVIRONMENT=development  # development, staging, production, testing
DEBUG=true              # Enable debug mode
TESTING=false           # Enable testing mode
```

#### 2. Database Configuration
```bash
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=false
```

#### 3. Security Configuration
```bash
SECRET_KEY=your-secret-key-here  # JWT signing key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
CORS_ORIGINS=http://localhost:3000
```

#### 4. AI Integration
```bash
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=30
```

#### 5. Caching (Redis)
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_TIMEOUT=5
REDIS_MAX_CONNECTIONS=10
USER_PROFILE_TTL=3600
DIET_PLAN_TTL=86400
```

#### 6. Logging and Monitoring
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_FILE_LOGGING=true
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=development
```

## Setup Instructions

### Development Environment

1. **Quick Setup (Recommended)**
   ```bash
   # Linux/macOS
   ./scripts/setup-secrets.sh dev
   
   # Windows PowerShell
   .\scripts\setup-secrets.ps1 dev
   ```

2. **Manual Setup**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit the .env file with your settings
   nano .env
   ```

3. **Required Changes for Development**
   - Set `OPENAI_API_KEY` to your OpenAI API key
   - Optionally set `SENTRY_DSN` for error tracking
   - Database settings should work with Docker Compose

### Production Environment

1. **Using Setup Script**
   ```bash
   # Linux/macOS
   ./scripts/setup-secrets.sh production
   
   # Windows PowerShell
   .\scripts\setup-secrets.ps1 production
   ```

2. **Manual Production Setup**
   ```bash
   # Copy production template
   cp .env.production .env.prod
   
   # Generate secure secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Update .env.prod with secure values
   ```

3. **Required Production Changes**
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=false`
   - Generate secure `SECRET_KEY`
   - Set production `DATABASE_URL`
   - Set `OPENAI_API_KEY`
   - Configure `CORS_ORIGINS` with your domains
   - Set up `SENTRY_DSN` for error tracking
   - Configure production `REDIS_URL`

### Testing Environment

```bash
# Setup testing environment
./scripts/setup-secrets.sh testing

# Or manually copy
cp .env.testing .env.test
```

## Docker Secrets (Production)

For production Docker deployments, use Docker secrets for sensitive data:

### 1. Create Docker Secrets
```bash
# Create secrets
echo "your-secret-key" | docker secret create secret_key -
echo "your-openai-key" | docker secret create openai_api_key -
echo "postgres-password" | docker secret create postgres_password -
```

### 2. Use Production Docker Compose
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Secrets are Mounted at Runtime
- Secrets are available at `/run/secrets/secret_name`
- Application automatically loads from these locations
- No secrets stored in environment variables or images

## Configuration Validation

### Automatic Validation
The application automatically validates configuration on startup:

- **Development**: Warns about missing optional settings
- **Production**: Fails startup if critical settings are missing or insecure
- **Testing**: Uses safe defaults for all settings

### Manual Validation
```bash
# Validate current configuration
python backend/scripts/validate_config.py

# Or use the setup script
./scripts/setup-secrets.sh validate
```

### Validation Checks
- ✅ Required secrets are present
- ✅ Secret keys are secure (not defaults)
- ✅ Database connection works
- ✅ Production settings are secure
- ✅ Dependencies are available

## Security Best Practices

### 1. Secret Key Management
- **Never** use default secret keys in production
- Generate keys with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Rotate keys regularly
- Use different keys for different environments

### 2. Database Security
- Use strong passwords
- Enable SSL connections in production
- Restrict database access by IP
- Regular security updates

### 3. API Keys
- Store API keys securely (environment variables or secrets management)
- Use different keys for different environments
- Monitor API key usage
- Rotate keys regularly

### 4. CORS Configuration
- Set specific origins in production (not wildcards)
- Use HTTPS in production
- Validate all origins

### 5. Logging Security
- Mask sensitive data in logs
- Use structured logging
- Set appropriate log levels for each environment
- Secure log storage and access

## Environment-Specific Behaviors

### Development
- SQL query logging enabled
- Detailed error messages
- Relaxed CORS settings
- Longer token expiry
- File-based logging

### Staging
- Production-like settings
- Error tracking enabled
- Moderate logging
- Realistic token expiry

### Production
- Minimal logging (WARNING level)
- Strict security settings
- Short token expiry
- Error tracking required
- No debug information exposed

### Testing
- Fast settings for quick tests
- Separate test database
- Minimal logging
- Disabled external services
- Permissive security for testing

## Troubleshooting

### Common Issues

1. **"Secret key validation failed"**
   - Generate a new secret key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Update `SECRET_KEY` in your environment file

2. **"Database connection failed"**
   - Check `DATABASE_URL` format
   - Ensure database server is running
   - Verify credentials and permissions

3. **"OpenAI API key not configured"**
   - Get API key from https://platform.openai.com/api-keys
   - Set `OPENAI_API_KEY` in your environment file

4. **"CORS error in browser"**
   - Add your frontend URL to `CORS_ORIGINS`
   - Ensure format is correct: `http://localhost:3000,https://yourdomain.com`

5. **"Configuration validation failed"**
   - Run validation script: `python backend/scripts/validate_config.py`
   - Check error messages and fix configuration issues

### Debug Configuration
```bash
# Check current configuration (development only)
curl http://localhost:8000/config-info

# Check application health
curl http://localhost:8000/health

# Check database health
curl http://localhost:8000/db-health
```

## Advanced Configuration

### Custom Configuration Classes
You can extend the configuration system by creating custom configuration classes in `backend/app/core/environments.py`.

### External Secrets Management
The system supports loading secrets from:
- Environment variables
- Docker secrets (`/run/secrets/`)
- Kubernetes secrets (`/var/secrets/`)
- Local encrypted files (development)
- External secret management systems (AWS Secrets Manager, HashiCorp Vault)

### Configuration Inheritance
Environments inherit from base settings and override specific values:
- `DevelopmentConfig` extends `Settings`
- `ProductionConfig` extends `Settings`
- `TestingConfig` extends `Settings`

This ensures consistency while allowing environment-specific customization.

## Support

If you encounter issues with configuration:

1. Run the validation script
2. Check the troubleshooting section
3. Review the application logs
4. Consult the configuration reference in the code
5. Create an issue with configuration details (excluding secrets)