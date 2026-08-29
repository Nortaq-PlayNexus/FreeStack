# FreeStack Development Guide

This guide covers setting up and working with the FreeStack codebase.

## Development Environment

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Git
- (Optional) Docker & Docker Compose

### Setup

```bash
# Clone
git clone https://github.com/yourorg/freestack.git
cd freestack

# Run setup script
./scripts/dev-setup.sh

# Or manual setup:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
pre-commit install
cp config.example.yaml config.yaml
```

### Configuration

Edit `config.yaml` for local development:

```yaml
app:
  environment: "development"
  debug: true

database:
  url: "postgresql+asyncpg://freestack:freestack@localhost:5432/freestack"

redis:
  url: "redis://localhost:6379/0"

auth:
  secret_key: "dev-secret-key-change-in-production"
```

### Start Dependencies

```bash
# With Docker (recommended)
docker-compose up -d postgres redis

# Or install locally
```

### Run Migrations

```bash
freestack db upgrade
```

### Start Development Server

```bash
freestack api serve --reload
```

## Project Structure

```
freestack/
├── core/           # Core framework (config, DB, auth, events, health)
├── models/         # Data models (SQLAlchemy + Pydantic)
├── api/            # REST API (FastAPI)
│   ├── routes/     # Route modules
│   ├── middleware/ # Custom middleware
│   └── dependencies.py
├── cli/            # CLI commands (Typer)
├── services/       # Background services
│   ├── worker/     # Job queue worker
│   ├── scheduler/  # Task scheduler
│   └── websocket/  # WebSocket server
├── tests/          # Test suite
│   ├── unit/       # Unit tests
│   ├── integration/# Integration tests
│   └── fixtures/   # Test fixtures
├── scripts/        # Utility scripts
├── docs/           # Documentation
├── alembic/        # Database migrations
└── config/         # Configuration files
```

## Coding Standards

### Python Style
- **Formatter**: Black (line length 100)
- **Linter**: Ruff (with all rules enabled)
- **Imports**: isort (Black profile)
- **Types**: mypy (strict mode)

### Type Hints
- All functions must have type hints
- Use `from __future__ import annotations`
- Prefer `list[str]` over `List[str]` (Python 3.9+)
- Use `TypedDict` for dict schemas

### Async Patterns
- Use `async`/`await` for all I/O
- Avoid blocking calls in async functions
- Use `asyncio.gather` for parallel operations
- Use `async with` for context managers

### Error Handling
- Use custom exceptions for domain errors
- Log errors with structured logging
- Return appropriate HTTP status codes
- Don't leak internal details in responses

### Testing
- Unit tests for business logic
- Integration tests for API endpoints
- Use fixtures for common setup
- Mock external services
- Aim for >80% coverage

## Common Tasks

### Adding a New Model

1. Create model in `models/`:
```python
# models/item.py
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, IDMixin, TimestampMixin

class Item(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="items")
```

2. Add to `models/__init__.py`

3. Create migration:
```bash
freestack db revision -m "Add Item model"
```

4. Create Pydantic schemas in same file

### Adding a New API Endpoint

1. Create route module in `api/routes/`:
```python
# api/routes/items.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...api.dependencies import get_current_active_user
from ...models.item import Item, ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])

@router.post("", response_model=ItemResponse)
async def create_item(
    item_data: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Implementation
    pass
```

2. Register in `api/main.py`:
```python
from .routes import items
app.include_router(items.router)
```

### Adding a Background Job

1. Add job function in `services/worker/__init__.py`:
```python
async def process_item_job(ctx: JobContext, item_id: str) -> dict:
    # Implementation
    pass

JOBS["process_item"] = process_item_job
```

2. Enqueue from anywhere:
```python
from services.worker import enqueue_job_async

job_id = await enqueue_job_async("process_item", item_id="123")
```

### Adding a CLI Command

1. Add command in `cli/main.py`:
```python
@cli_app.command("process")
def process_items(
    item_id: str = typer.Argument(..., help="Item ID"),
):
    """Process an item."""
    # Implementation
    pass
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate from model changes
freestack db revision -m "Description of changes"

# Empty migration for manual SQL
freestack db revision -m "Manual migration" --no-autogenerate
```

### Running Migrations

```bash
# Upgrade to latest
freestack db upgrade

# Upgrade to specific revision
freestack db upgrade <revision>

# Downgrade
freestack db downgrade -1
```

### Migration Best Practices
- Always review auto-generated migrations
- Use `batch_alter_table` for SQLite compatibility
- Add indexes in separate migrations
- Test migrations on copy of production data
- Never modify applied migrations

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests (requires DB/Redis)
pytest tests/integration

# With coverage
pytest --cov=freestack --cov-report=html

# Watch mode
pytest-watch

# Specific test
pytest tests/unit/test_auth.py::TestAuth::test_login
```

## Code Quality

### Pre-commit Hooks
Run automatically on commit:
- Ruff (lint + format)
- MyPy (type check)
- Bandit (security)
- pip-audit (dependencies)

### Manual Checks
```bash
# Format
ruff format .

# Lint
ruff check . --fix

# Type check
mypy .

# Security
bandit -r .

# Dependencies
pip-audit
```

## Debugging

### Using the Shell
```bash
freestack shell
# or
freestack api shell
```

### Logging
```python
from core.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing item", item_id=item_id, user_id=user_id)
```

### Profiling
```bash
# CPU profiling
py-spy record -o profile.svg -- python -m freestack api serve

# Memory profiling
python -m memory_profiler scripts/profile_memory.py
```

## Git Workflow

### Branching
- `main` - Production ready
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `release/*` - Release preparation
- `hotfix/*` - Production hotfixes

### Commits
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat(api): add item search endpoint
fix(auth): handle expired refresh token
docs: update deployment guide
refactor(core): simplify event bus
test: add integration tests for items
```

### Pull Requests
1. Create feature branch
2. Make changes with tests
3. Run quality checks
4. Open PR with description
5. Code review
6. Squash and merge

## Releasing

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Create release tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# CI/CD will build and publish
```