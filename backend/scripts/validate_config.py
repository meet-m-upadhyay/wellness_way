#!/usr/bin/env python3
"""
Configuration validation script for WellnessWay Diet Planner

This script validates the application configuration and checks for common issues.
Run this before deploying to production or when troubleshooting configuration problems.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.environments import get_config, validate_production_config
from app.core.secrets import load_all_secrets
from app.database.connection import DatabaseManager
import logging


def validate_environment_files():
    """Validate that required environment files exist"""
    print("🔍 Checking environment files...")
    
    required_files = [".env.example"]
    optional_files = [".env", ".env.production", ".env.testing"]
    
    issues = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            issues.append(f"Required file missing: {file_path}")
    
    for file_path in optional_files:
        if Path(file_path).exists():
            print(f"  ✅ Found: {file_path}")
        else:
            print(f"  ⚠️  Optional file missing: {file_path}")
    
    if issues:
        print("  ❌ Issues found:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    
    print("  ✅ Environment files OK")
    return True


def validate_secrets():
    """Validate secrets and sensitive configuration"""
    print("\n🔐 Checking secrets and sensitive configuration...")
    
    try:
        secrets = load_all_secrets()
        issues = []
        warnings = []
        
        # Check for default/insecure values
        secret_key = secrets.get("SECRET_KEY", "")
        if "dev-secret-key" in secret_key or "change-in-production" in secret_key:
            if os.getenv("ENVIRONMENT", "development") == "production":
                issues.append("Default SECRET_KEY detected in production environment")
            else:
                warnings.append("Using default SECRET_KEY (OK for development)")
        
        # Check OpenAI API key
        openai_key = secrets.get("OPENAI_API_KEY", "")
        if not openai_key or openai_key == "your-openai-api-key-here":
            if os.getenv("ENVIRONMENT", "development") == "production":
                issues.append("OpenAI API key not configured")
            else:
                warnings.append("OpenAI API key not configured (may be OK for development)")
        
        # Check database URL
        db_url = secrets.get("DATABASE_URL", "")
        if "password" in db_url and "localhost" in db_url:
            if os.getenv("ENVIRONMENT", "development") == "production":
                warnings.append("Database URL appears to use default credentials")
        
        if issues:
            print("  ❌ Security issues found:")
            for issue in issues:
                print(f"    - {issue}")
        
        if warnings:
            print("  ⚠️  Warnings:")
            for warning in warnings:
                print(f"    - {warning}")
        
        if not issues and not warnings:
            print("  ✅ Secrets configuration OK")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"  ❌ Error loading secrets: {e}")
        return False


def validate_configuration():
    """Validate application configuration"""
    print("\n⚙️  Validating application configuration...")
    
    try:
        config = get_config()
        
        # Basic configuration checks
        print(f"  Environment: {config.environment}")
        print(f"  Debug mode: {config.debug}")
        print(f"  Testing mode: {config.testing}")
        
        # Production-specific validation
        if config.is_production:
            print("\n  🏭 Production environment detected - running additional checks...")
            validation_result = validate_production_config(config)
            
            if validation_result["issues"]:
                print("  ❌ Production configuration issues:")
                for issue in validation_result["issues"]:
                    print(f"    - {issue}")
            
            if validation_result["warnings"]:
                print("  ⚠️  Production configuration warnings:")
                for warning in validation_result["warnings"]:
                    print(f"    - {warning}")
            
            if validation_result["valid"]:
                print("  ✅ Production configuration is valid")
            
            return validation_result["valid"]
        else:
            print("  ✅ Configuration loaded successfully")
            return True
            
    except Exception as e:
        print(f"  ❌ Configuration validation failed: {e}")
        return False


def validate_database_connection():
    """Validate database connection"""
    print("\n🗄️  Testing database connection...")
    
    try:
        db_manager = DatabaseManager()
        
        if db_manager.check_connection():
            print("  ✅ Database connection successful")
            
            # Show connection info
            conn_info = db_manager.get_connection_info()
            print(f"  Database: {conn_info['url']}")
            print(f"  Pool size: {conn_info['pool_size']}")
            print(f"  Max overflow: {conn_info['max_overflow']}")
            
            return True
        else:
            print("  ❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False


def validate_dependencies():
    """Validate that required dependencies are available"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "psycopg2",
        "openai",
        "cryptography"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} (missing)")
    
    if missing_packages:
        print(f"\n  ❌ Missing packages: {', '.join(missing_packages)}")
        print("  Run: pip install -r requirements.txt")
        return False
    
    print("  ✅ All required dependencies available")
    return True


def main():
    """Main validation function"""
    print("🏥 WellnessWay Diet Planner - Configuration Validation")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all validation checks
    checks = [
        ("Environment Files", validate_environment_files),
        ("Dependencies", validate_dependencies),
        ("Secrets", validate_secrets),
        ("Configuration", validate_configuration),
        ("Database Connection", validate_database_connection),
    ]
    
    for check_name, check_function in checks:
        try:
            if not check_function():
                all_checks_passed = False
        except Exception as e:
            print(f"\n❌ {check_name} validation failed with error: {e}")
            all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("🎉 All validation checks passed!")
        print("✅ Configuration is ready for use")
        sys.exit(0)
    else:
        print("❌ Some validation checks failed")
        print("🔧 Please fix the issues above before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    main()