#!/bin/bash

# WellnessWay Diet Planner - Secrets Setup Script
# This script helps set up secrets for different environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to generate secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Function to setup development secrets
setup_development() {
    print_status "Setting up development environment secrets..."
    
    cd "$PROJECT_ROOT"
    
    # Copy example env file if .env doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
    else
        print_warning ".env already exists, skipping copy"
    fi
    
    # Generate development secret key if using default
    if grep -q "your-secret-key-here-change-in-production" .env; then
        DEV_SECRET=$(generate_secret 32)
        sed -i.bak "s/your-secret-key-here-change-in-production/dev-secret-key-$DEV_SECRET/" .env
        print_success "Generated development secret key"
    fi
    
    print_success "Development secrets setup complete!"
    print_warning "Remember to set your OPENAI_API_KEY in .env for AI features"
}

# Function to setup production secrets
setup_production() {
    print_status "Setting up production environment secrets..."
    
    # Check if running in Docker Swarm mode
    if docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null | grep -q "active"; then
        setup_docker_secrets
    else
        setup_production_env
    fi
}

# Function to setup Docker secrets
setup_docker_secrets() {
    print_status "Setting up Docker Swarm secrets..."
    
    # Generate secrets
    POSTGRES_USER="wellnessway_prod"
    POSTGRES_PASSWORD=$(generate_secret 24)
    SECRET_KEY=$(generate_secret 32)
    REDIS_PASSWORD=$(generate_secret 16)
    
    # Create Docker secrets
    echo "$POSTGRES_USER" | docker secret create postgres_user - 2>/dev/null || print_warning "postgres_user secret already exists"
    echo "$POSTGRES_PASSWORD" | docker secret create postgres_password - 2>/dev/null || print_warning "postgres_password secret already exists"
    echo "$SECRET_KEY" | docker secret create secret_key - 2>/dev/null || print_warning "secret_key secret already exists"
    echo "$REDIS_PASSWORD" | docker secret create redis_password - 2>/dev/null || print_warning "redis_password secret already exists"
    
    # Prompt for OpenAI API key
    read -p "Enter your OpenAI API key: " -s OPENAI_KEY
    echo
    echo "$OPENAI_KEY" | docker secret create openai_api_key - 2>/dev/null || print_warning "openai_api_key secret already exists"
    
    # Optional Sentry DSN
    read -p "Enter Sentry DSN (optional, press enter to skip): " SENTRY_DSN
    if [ ! -z "$SENTRY_DSN" ]; then
        echo "$SENTRY_DSN" | docker secret create sentry_dsn - 2>/dev/null || print_warning "sentry_dsn secret already exists"
    fi
    
    print_success "Docker secrets created successfully!"
}

# Function to setup production environment file
setup_production_env() {
    print_status "Setting up production .env file..."
    
    cd "$PROJECT_ROOT"
    
    # Create production env file
    cp .env.production .env.prod
    
    # Generate secure values
    SECRET_KEY=$(generate_secret 32)
    
    # Update production env file
    sed -i.bak "s/CHANGE_ME_IN_PRODUCTION/$SECRET_KEY/" .env.prod
    
    print_success "Production .env.prod file created"
    print_warning "Please update the following in .env.prod:"
    print_warning "  - DATABASE_URL (production database)"
    print_warning "  - OPENAI_API_KEY"
    print_warning "  - SENTRY_DSN (optional)"
    print_warning "  - CORS_ORIGINS (your production domains)"
    print_warning "  - REDIS_URL (production Redis)"
}

# Function to setup testing secrets
setup_testing() {
    print_status "Setting up testing environment secrets..."
    
    cd "$PROJECT_ROOT"
    
    # Copy testing env file
    cp .env.testing .env.test
    
    print_success "Testing environment setup complete!"
    print_status "Test database will be created automatically during tests"
}

# Function to validate secrets
validate_secrets() {
    print_status "Validating secrets configuration..."
    
    cd "$PROJECT_ROOT/backend"
    
    if [ -f "scripts/validate_config.py" ]; then
        python scripts/validate_config.py
    else
        print_warning "Configuration validation script not found"
    fi
}

# Function to show help
show_help() {
    echo "WellnessWay Diet Planner - Secrets Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev, development    Setup development environment secrets"
    echo "  prod, production    Setup production environment secrets"
    echo "  test, testing       Setup testing environment secrets"
    echo "  validate           Validate current secrets configuration"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev              # Setup development secrets"
    echo "  $0 production       # Setup production secrets"
    echo "  $0 validate         # Validate current configuration"
}

# Main script logic
main() {
    case "${1:-help}" in
        "dev"|"development")
            setup_development
            ;;
        "prod"|"production")
            setup_production
            ;;
        "test"|"testing")
            setup_testing
            ;;
        "validate")
            validate_secrets
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    if ! command -v openssl &> /dev/null; then
        print_error "openssl is required but not installed"
        exit 1
    fi
}

# Run the script
check_dependencies
main "$@"