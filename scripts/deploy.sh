#!/usr/bin/env bash
# FreeStack Deployment Script
# Run this script to deploy FreeStack to production

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"

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

validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"

    case "$ENVIRONMENT" in
        production|staging)
            log_success "Valid environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT. Use 'production' or 'staging'"
            exit 1
            ;;
    esac
}

check_requirements() {
    log_info "Checking deployment requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose not found"
        exit 1
    fi

    # Check environment file
    ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Create it from .env.example"
        exit 1
    fi

    log_success "Requirements check passed"
}

build_image() {
    log_info "Building Docker image: freestack:$VERSION"
    cd "$PROJECT_ROOT"
    docker build -t "freestack:$VERSION" -t "freestack:latest" .
    log_success "Docker image built"
}

run_migrations() {
    log_info "Running database migrations..."
    cd "$PROJECT_ROOT"
    docker-compose --env-file ".env.$ENVIRONMENT" run --rm api freestack db upgrade
    log_success "Migrations completed"
}

deploy_services() {
    log_info "Deploying services..."
    cd "$PROJECT_ROOT"
    docker-compose --env-file ".env.$ENVIRONMENT" up -d --remove-orphans
    log_success "Services deployed"
}

health_check() {
    log_info "Waiting for services to be healthy..."
    cd "$PROJECT_ROOT"

    # Wait for API to be ready
    for i in {1..30}; do
        if docker-compose --env-file ".env.$ENVIRONMENT" exec -T api curl -f http://localhost:8000/health/ready &> /dev/null; then
            log_success "API is ready"
            break
        fi
        sleep 2
    done

    # Check all services
    docker-compose --env-file ".env.$ENVIRONMENT" ps
}

show_deployment_info() {
    echo
    log_success "Deployment complete!"
    echo
    echo "Environment: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo
    echo "Services:"
    echo "  API:        http://localhost:8000"
    echo "  WebSocket:  ws://localhost:8001"
    echo "  Metrics:    http://localhost:9090/metrics"
    echo
    echo "Useful commands:"
    echo "  View logs:     docker-compose --env-file .env.$ENVIRONMENT logs -f"
    echo "  Scale API:     docker-compose --env-file .env.$ENVIRONMENT up -d --scale api=3"
    echo "  Stop:          docker-compose --env-file .env.$ENVIRONMENT down"
    echo
}

main() {
    echo "========================================="
    echo "  FreeStack Deployment"
    echo "========================================="
    echo

    validate_environment
    check_requirements
    build_image
    run_migrations
    deploy_services
    health_check
    show_deployment_info
}

main "$@"