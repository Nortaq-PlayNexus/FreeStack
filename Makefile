# FreeStack Makefile

.PHONY: help install test lint format type-check security build docs clean dev-setup

# Default target
help:
	@echo "FreeStack - Available targets:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"
	@echo "  make type-check    - Run type checker"
	@echo "  make security      - Run security scans"
	@echo "  make build         - Build Docker image"
	@echo "  make docs          - Build documentation"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make dev-setup     - Run development setup script"

# Install dependencies
install:
	uv pip install -r requirements.txt -r requirements-dev.txt
	uv pip install -e .

# Run tests
test:
	pytest tests/ -v --cov=freestack --cov-report=term-missing

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

# Run linter
lint:
	ruff check .

# Format code
format:
	ruff format .

# Type checking
type-check:
	mypy .

# Security scans
security:
	pip-audit --desc
	bandit -r . -x tests,scripts

# Build Docker image
build:
	docker build -t freestack:latest .

# Build documentation
docs:
	mkdocs build --strict

# Serve documentation locally
docs-serve:
	mkdocs serve

# Clean build artifacts
clean:
	rm -rf build dist *.egg-info htmlcov .coverage .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Development setup
dev-setup:
	./scripts/dev-setup.sh

# Run pre-commit on all files
pre-commit-run:
	pre-commit run --all-files

# Database migrations
db-upgrade:
	freestack db upgrade

db-downgrade:
	freestack db downgrade -1

db-revision:
	freestack db revision -m "$(MSG)"

db-seed:
	freestack db seed

# Start development servers
api-serve:
	freestack api serve --reload

worker-start:
	freestack worker start

scheduler-start:
	freestack scheduler start

ws-serve:
	freestack ws serve

# Docker Compose
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-ps:
	docker-compose ps