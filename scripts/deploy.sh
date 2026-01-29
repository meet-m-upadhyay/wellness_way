#!/bin/bash

# WellnessWay Deployment Script
# Usage: ./deploy.sh [environment] [version]
# Example: ./deploy.sh staging v1.0.0

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
PROJECT_NAME="health-buddy"
REGISTRY="ghcr.io"
REPO_NAME="health-buddy-diet-planner"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    log_info "Loading environment configuration..."
    
    case $ENVIRONMENT in
        development)
            ENV_FILE=".env"
            COMPOSE_FILE="docker-compose.yml"
            ;;
        staging)
            ENV_FILE=".env.testing"
            COMPOSE_FILE="docker-compose.yml"
            ;;
        production)
            ENV_FILE=".env.production"
            COMPOSE_FILE="docker-compose.prod.yml"
            ;;
    esac
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        exit 1
    fi
    
    # Export environment variables
    set -a
    source "$ENV_FILE"
    set +a
    
    log_success "Environment configuration loaded from $ENV_FILE"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    
    if [ "$VERSION" != "latest" ]; then
        # Pull specific version
        docker pull "$REGISTRY/$REPO_NAME-backend:$VERSION" || log_warning "Backend image not found for version $VERSION"
        docker pull "$REGISTRY/$REPO_NAME-frontend:$VERSION" || log_warning "Frontend image not found for version $VERSION"
    else
        # Pull latest images
        docker-compose -f "$COMPOSE_FILE" pull || log_warning "Some images could not be pulled"
    fi
    
    log_success "Docker images pulled"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Start database service if not running
    docker-compose -f "$COMPOSE_FILE" up -d database
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker-compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head
    
    log_success "Database migrations completed"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services deployed"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check backend health
    BACKEND_URL="http://localhost:8000"
    if [ "$ENVIRONMENT" = "production" ]; then
        BACKEND_URL="https://api.wellnessway.com"
    fi
    
    for i in {1..10}; do
        if curl -f "$BACKEND_URL/health" &> /dev/null; then
            log_success "Backend health check passed"
            break
        else
            log_warning "Backend health check failed (attempt $i/10)"
            sleep 10
        fi
        
        if [ $i -eq 10 ]; then
            log_error "Backend health check failed after 10 attempts"
            exit 1
        fi
    done
    
    # Check frontend
    FRONTEND_URL="http://localhost:3000"
    if [ "$ENVIRONMENT" = "production" ]; then
        FRONTEND_URL="https://wellnessway.com"
    fi
    
    for i in {1..10}; do
        if curl -f "$FRONTEND_URL" &> /dev/null; then
            log_success "Frontend health check passed"
            break
        else
            log_warning "Frontend health check failed (attempt $i/10)"
            sleep 10
        fi
        
        if [ $i -eq 10 ]; then
            log_error "Frontend health check failed after 10 attempts"
            exit 1
        fi
    done
    
    log_success "All health checks passed"
}

# Cleanup old images
cleanup() {
    log_info "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old images (keep last 3 versions)
    docker images "$REGISTRY/$REPO_NAME-backend" --format "table {{.Tag}}\t{{.ID}}" | tail -n +4 | awk '{print $2}' | xargs -r docker rmi || true
    docker images "$REGISTRY/$REPO_NAME-frontend" --format "table {{.Tag}}\t{{.ID}}" | tail -n +4 | awk '{print $2}' | xargs -r docker rmi || true
    
    log_success "Cleanup completed"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start with previous version (assuming 'previous' tag exists)
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting deployment of WellnessWay Diet Planner"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    validate_environment
    check_prerequisites
    load_environment
    
    # Set trap for rollback on error
    trap rollback ERR
    
    pull_images
    run_migrations
    deploy_services
    health_check
    cleanup
    
    log_success "Deployment completed successfully!"
    log_info "Application is now running:"
    
    case $ENVIRONMENT in
        development)
            log_info "  Frontend: http://localhost:3000"
            log_info "  Backend: http://localhost:8000"
            log_info "  API Docs: http://localhost:8000/docs"
            ;;
        staging)
            log_info "  Frontend: http://staging.wellnessway.com"
            log_info "  Backend: http://api-staging.wellnessway.com"
            log_info "  API Docs: http://api-staging.wellnessway.com/docs"
            ;;
        production)
            log_info "  Frontend: https://wellnessway.com"
            log_info "  Backend: https://api.wellnessway.com"
            log_info "  API Docs: https://api.wellnessway.com/docs"
            ;;
    esac
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "WellnessWay Deployment Script"
        echo ""
        echo "Usage: $0 [environment] [version]"
        echo ""
        echo "Environments:"
        echo "  development  - Local development environment"
        echo "  staging      - Staging environment"
        echo "  production   - Production environment"
        echo ""
        echo "Examples:"
        echo "  $0 staging latest"
        echo "  $0 production v1.0.0"
        echo "  $0 development"
        exit 0
        ;;
    --rollback)
        rollback
        exit 0
        ;;
    *)
        main
        ;;
esac