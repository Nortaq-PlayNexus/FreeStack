# Architecture Overview

FreeStack follows a modular, layered architecture designed for scalability, maintainability, and developer experience.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FreeStack Application                        │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│   CLI App    │   REST API   │  WebSocket   │   Background Jobs     │
│  (cli/)      │   (api/)     │  (services/) │   (services/worker)   │
└──────┬───────┴──────┬───────┴──────┬───────┴───────────┬───────────┘
       │              │              │                   │
       └──────────────┴──────────────┴───────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    Core Layer     │
                    │  (core/, models/) │
                    │  - Config         │
                    │  - Logging        │
                    │  - Database       │
                    │  - Auth           │
                    │  - Events         │
                    │  - Health         │
                    └─────────┬─────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
│  PostgreSQL │       │    Redis    │       │  Message    │
│  (Primary)  │       │  (Cache/    │       │  Queue      │
│             │       │   PubSub)   │       │  (RabbitMQ/ │
│             │       │             │       │   Redis)    │
└─────────────┘       └─────────────┘       └─────────────┘
```

## Core Principles

### 1. Separation of Concerns
Each layer has a single responsibility:
- **Core**: Shared infrastructure (config, DB, auth, logging, events)
- **Models**: Data models and schemas (SQLAlchemy + Pydantic)
- **API**: HTTP layer (FastAPI, routing, middleware)
- **CLI**: Command-line interface (Typer, Rich)
- **Services**: Background processing (workers, scheduler, WebSocket)

### 2. Dependency Injection
FastAPI's dependency injection system is used throughout for:
- Database sessions
- Authentication
- Configuration
- External services

### 3. Async-First
All I/O operations use async/await:
- Database: SQLAlchemy 2.0 async
- HTTP: httpx, FastAPI
- Redis: redis-py async
- WebSockets: websockets library

### 4. Type Safety
Full type annotations with:
- Pydantic for validation
- SQLAlchemy 2.0 typed models
- mypy for static checking
- py.typed marker for library consumers

### 5. Configuration as Code
Layered configuration with validation:
1. Default values (code)
2. YAML config file
3. Environment variables
4. CLI arguments

## Core Components

### Configuration (`core/config.py`)
- Pydantic Settings with nested models
- Environment variable support with `FREESTACK_` prefix
- YAML file loading with layered overrides
- Type validation and defaults

### Database (`core/database.py`)
- SQLAlchemy 2.0 async engine/session
- Connection pooling with health checks
- Repository pattern for data access
- Alembic migrations

### Authentication (`core/auth.py`)
- JWT tokens (access + refresh)
- bcrypt password hashing
- Role-based access control (RBAC)
- Permission system with hierarchy

### Events (`core/events.py`)
- Typed event bus (sync + async handlers)
- Middleware support
- Outbox pattern for reliability
- Event store for event sourcing

### Health Checks (`core/health.py`)
- Liveness probe (basic)
- Readiness probe (critical deps)
- Extensible check framework
- Prometheus metrics integration

## Data Flow

### Request Flow (API)
```
Client Request
     │
     ▼
┌─────────────────┐
│  Middleware     │  ← Correlation ID, Logging, Security Headers, Rate Limit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Router         │  ← FastAPI routing, validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dependencies   │  ← DB session, Auth, Pagination
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Handler        │  ← Business logic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │  ← Pydantic serialization
└─────────────────┘
```

### Background Job Flow
```
Enqueue Job
     │
     ▼
┌─────────────────┐
│  Redis Queue    │  ← Arq job queue
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Worker         │  ← Concurrency control, retries
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Job Handler    │  ← Business logic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Result/Events  │  ← Store result, emit events
└─────────────────┘
```

## Security Architecture

### Defense in Depth
1. **Network**: Private networks, load balancers, WAF
2. **Transport**: TLS 1.3, HSTS, secure headers
3. **Application**: Input validation, rate limiting, CORS
4. **Authentication**: JWT, API keys, OAuth2/OIDC
5. **Authorization**: RBAC, resource-level permissions
6. **Data**: Encryption at rest, field-level encryption
7. **Audit**: Comprehensive audit logging

### Secrets Management
- Never commit secrets to version control
- Use environment variables or secret managers
- Rotate secrets regularly
- Audit secret access

## Scalability Patterns

### Horizontal Scaling
- Stateless API servers (add more workers)
- Redis for session/cache sharing
- Database connection pooling
- Read replicas for queries

### Caching Strategy
- Redis for distributed caching
- HTTP caching headers
- Query result caching
- Template fragment caching

### Database Optimization
- Connection pooling (PgBouncer)
- Read replicas
- Partitioning for large tables
- Proper indexing

## Monitoring & Observability

### Metrics (Prometheus)
- HTTP request rate, latency, errors
- Database query performance
- Queue depth, job duration
- Business metrics

### Logging (Structured JSON)
- Correlation IDs for request tracing
- Structured fields for querying
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation

### Tracing (OpenTelemetry)
- Distributed tracing
- Span attributes for debugging
- Integration with Jaeger/Zipkin

### Health Checks
- Liveness: Process is running
- Readiness: Dependencies available
- Startup: Initialization complete

## Deployment Architecture

### Development
```
┌─────────────┐
│  Developer  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  docker-compose │  ← All services local
└─────────────────┘
```

### Staging/Production
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Users     │────▶│  Load Bal.  │────▶│  API Pods   │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                    ┌──────▼──────┐     ┌──────▼──────┐
                    │   Redis     │     │ PostgreSQL  │
                    │  (Cluster)  │     │  (Primary + │
                    └─────────────┘     │  Replicas)  │
                                       └─────────────┘
```

## Technology Choices

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python 3.11+ | Async support, ecosystem, type hints |
| API Framework | FastAPI | Performance, auto-docs, validation |
| Database | PostgreSQL | Reliability, features, JSON support |
| ORM | SQLAlchemy 2.0 | Async, type-safe, flexible |
| Cache/Queue | Redis | Performance, pub/sub, streams |
| Auth | JWT + bcrypt | Stateless, standard, secure |
| CLI | Typer + Rich | Modern, type-safe, beautiful |
| Testing | pytest + testcontainers | Async, fixtures, real dependencies |
| Linting | ruff | Fast, comprehensive |
| Formatting | black | Opinionated, consistent |
| Types | mypy | Static analysis |
| Docs | MkDocs Material | Beautiful, searchable |
| Container | Docker | Portability, reproducibility |
| Orchestration | Kubernetes/Compose | Scaling, self-healing |

## Future Considerations

- GraphQL API layer
- gRPC for internal services
- WebAssembly for edge computing
- Multi-tenancy support
- Plugin system for extensibility