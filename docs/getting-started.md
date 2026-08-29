# Getting Started with FreeStack

This guide will help you get FreeStack up and running quickly.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- (Optional) Docker & Docker Compose

## Quick Start (Docker)

The fastest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/yourorg/freestack.git
cd freestack

# Copy example config
cp config.example.yaml config.yaml

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api freestack db upgrade

# Seed development data (optional)
docker-compose exec api freestack db seed
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8001

## Quick Start (Local Development)

### 1. Set up Python environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
uv pip install -e .

# Or using standard venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

### 2. Configure environment

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

Required settings:
- `database.url` - PostgreSQL connection string
- `redis.url` - Redis connection string
- `auth.secret_key` - Generate with `freestack generate secret`

### 3. Start dependencies

```bash
# Using Docker for just dependencies
docker-compose up -d postgres redis

# Or install locally
# PostgreSQL: https://www.postgresql.org/download/
# Redis: https://redis.io/download/
```

### 4. Run migrations

```bash
freestack db upgrade
```

### 5. Seed development data (optional)

```bash
freestack db seed
```

This creates:
- Admin user: `admin@freestack.local` / `admin123`
- Test user: `user@freestack.local` / `user123`

### 6. Start the API server

```bash
freestack api serve --reload
```

## Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/info

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@freestack.local", "password": "admin123"}'
```

## Next Steps

- Read the [Architecture Overview](architecture/overview.md)
- Explore the [API Reference](api/reference.md)
- Learn the [CLI Commands](cli/reference.md)
- Configure for [Production](guides/deployment.md)