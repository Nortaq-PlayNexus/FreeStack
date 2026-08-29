#!/usr/bin/env bash
# FreeStack Development Setup Script
# Run this script to set up the development environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_VERSION="3.11"

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

check_python() {
    log_info "Checking Python version..."
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        PYTHON_CMD="python${PYTHON_VERSION}"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$VERSION" != "$PYTHON_VERSION" ]]; then
            log_warning "Python $PYTHON_VERSION not found, using $VERSION"
        fi
    else
        log_error "Python 3 not found. Please install Python ${PYTHON_VERSION}+"
        exit 1
    fi
    log_success "Using $($PYTHON_CMD --version)"
}

check_uv() {
    log_info "Checking for uv..."
    if ! command -v uv &> /dev/null; then
        log_info "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    log_success "uv found: $(uv --version)"
}

create_venv() {
    log_info "Creating virtual environment..."
    if [[ -d "$VENV_DIR" ]]; then
        log_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Recreate? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            log_info "Using existing virtual environment"
            return
        fi
    fi

    $PYTHON_CMD -m venv "$VENV_DIR"
    log_success "Virtual environment created at $VENV_DIR"
}

install_dependencies() {
    log_info "Installing dependencies..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    # Install production dependencies
    pip install -r "$PROJECT_ROOT/requirements.txt"

    # Install development dependencies
    pip install -r "$PROJECT_ROOT/requirements-dev.txt"

    # Install package in editable mode
    pip install -e "$PROJECT_ROOT"

    log_success "Dependencies installed"
}

setup_pre_commit() {
    log_info "Setting up pre-commit hooks..."
    source "$VENV_DIR/bin/activate"
    pre-commit install
    pre-commit install --hook-type commit-msg
    log_success "Pre-commit hooks installed"
}

setup_config() {
    log_info "Setting up configuration..."
    CONFIG_FILE="$PROJECT_ROOT/config.yaml"
    EXAMPLE_CONFIG="$PROJECT_ROOT/config.example.yaml"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        if [[ -f "$EXAMPLE_CONFIG" ]]; then
            cp "$EXAMPLE_CONFIG" "$CONFIG_FILE"
            log_success "Created config.yaml from example"
            log_warning "Please edit config.yaml with your settings"
        else
            log_error "config.example.yaml not found"
        fi
    else
        log_info "config.yaml already exists"
    fi

    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/uploads"
}

setup_database() {
    log_info "Setting up database..."
    source "$VENV_DIR/bin/activate"

    # Check if PostgreSQL is available
    if command -v psql &> /dev/null; then
        log_info "PostgreSQL found, you can run migrations with:"
        echo "  freestack db upgrade"
    else
        log_warning "PostgreSQL not found. Using SQLite for development."
        log_info "Install PostgreSQL for production-like development."
    fi
}

setup_redis() {
    log_info "Checking Redis..."
    if command -v redis-server &> /dev/null; then
        log_success "Redis found"
    else
        log_warning "Redis not found. Install Redis for full functionality."
    fi
}

run_tests() {
    log_info "Running tests to verify setup..."
    source "$VENV_DIR/bin/activate"
    cd "$PROJECT_ROOT"

    if pytest tests/unit -x -q; then
        log_success "Unit tests passed"
    else
        log_error "Unit tests failed"
        return 1
    fi
}

print_next_steps() {
    echo
    log_success "Development environment setup complete!"
    echo
    echo "Next steps:"
    echo "  1. Activate the virtual environment:"
    echo "     source $VENV_DIR/bin/activate"
    echo
    echo "  2. Edit config.yaml with your settings:"
    echo "     $PROJECT_ROOT/config.yaml"
    echo
    echo "  3. Start the development services:"
    echo "     docker-compose up -d"
    echo
    echo "  4. Run database migrations:"
    echo "     freestack db upgrade"
    echo
    echo "  5. Seed the database (optional):"
    echo "     freestack db seed"
    echo
    echo "  6. Start the API server:"
    echo "     freestack api serve --reload"
    echo
    echo "  7. Open API docs:"
    echo "     http://localhost:8000/docs"
    echo
}

main() {
    echo "========================================="
    echo "  FreeStack Development Setup"
    echo "========================================="
    echo

    check_python
    check_uv
    create_venv
    install_dependencies
    setup_pre_commit
    setup_config
    setup_database
    setup_redis

    if run_tests; then
        print_next_steps
    else
        log_error "Setup completed but tests failed. Please check the output."
        exit 1
    fi
}

main "$@"