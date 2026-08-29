# FreeStack Configuration Guide

Complete reference for all configuration options.

## Configuration Layers

FreeStack uses layered configuration (highest priority first):
1. CLI arguments
2. Environment variables (`FREESTACK_` prefix)
3. `config.yaml` file
4. Default values

## Configuration File

Create `config.yaml` from `config.example.yaml`:

```bash
cp config.example.yaml config.yaml
```

## Complete Configuration Reference

### Application

```yaml
app:
  name: "freestack"              # Application name
  environment: "development"     # development | staging | production
  debug: true                    # Enable debug mode
  timezone: "UTC"                # Application timezone
```

### Database

```yaml
database:
  url: "postgresql+asyncpg://user:pass@host:5432/db"
  pool_size: 20                  # Connection pool size
  max_overflow: 10               # Extra connections above pool_size
  pool_timeout: 30               # Seconds to wait for connection
  pool_recycle: 3600             # Recycle connections (seconds)
  pool_pre_ping: true            # Verify connections before use
  echo: false                    # Log SQL queries
  echo_pool: false               # Log pool events
```

### Redis

```yaml
redis:
  url: "redis://host:6379/0"
  max_connections: 50
  socket_timeout: 5
  socket_connect_timeout: 5
  retry_on_timeout: true
  health_check_interval: 30
```

### Authentication

```yaml
auth:
  secret_key: "your-secret-key"  # REQUIRED - 32+ bytes for production
  algorithm: "HS256"             # JWT algorithm
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  password_min_length: 12
  password_require_uppercase: true
  password_require_lowercase: true
  password_require_numbers: true
  password_require_symbols: true
  bcrypt_rounds: 12
```

### API Server

```yaml
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4                     # Gunicorn workers
  worker_class: "uvicorn.workers.UvicornWorker"
  cors_origins:
    - "http://localhost:3000"
  cors_allow_credentials: true
  cors_allow_methods:
    - "GET"
    - "POST"
    - "PUT"
    - "PATCH"
    - "DELETE"
    - "OPTIONS"
  cors_allow_headers:
    - "*"
  rate_limit: "100/minute"
  rate_limit_storage: "redis"
  request_timeout: 30
  max_request_size: 10485760
  docs_url: "/docs"
  redoc_url: "/redoc"
  openapi_url: "/openapi.json"
```

### CLI

```yaml
cli:
  theme: "dark"                  # dark | light
  show_progress: true
  confirm_destructive: true
  history_file: "~/.freestack_history"
  completion: true
```

### Logging

```yaml
logging:
  level: "INFO"                  # DEBUG | INFO | WARNING | ERROR
  format: "json"                 # json | console
  file: "logs/app.log"
  max_bytes: 10485760            # 10MB
  backup_count: 5
  encoding: "utf-8"
  include_timestamp: true
  include_level: true
  include_logger: true
  include_module: true
  include_function: true
  include_line: true
```

### Background Worker

```yaml
worker:
  concurrency: 4
  max_jobs: 1000
  job_timeout: 300
  retry_attempts: 3
  retry_backoff: 60
  dead_letter_queue: true
  queues:
    - "default"
    - "high"
    - "low"
```

### Scheduler

```yaml
scheduler:
  enabled: true
  timezone: "UTC"
  max_instances: 3
  coalesce: true
  misfire_grace_time: 30
```

### WebSocket

```yaml
websocket:
  host: "0.0.0.0"
  port: 8001
  ping_interval: 20
  ping_timeout: 10
  max_message_size: 1048576
  max_connections: 10000
```

### File Storage

```yaml
storage:
  provider: "local"              # local | s3 | gcs | azure
  local:
    root: "data/uploads"
    base_url: "/uploads"
  s3:
    bucket: ""
    region: "us-east-1"
    endpoint_url: ""
    access_key: ""
    secret_key: ""
    prefix: "uploads/"
```

### Email

```yaml
email:
  enabled: false
  provider: "smtp"               # smtp | sendgrid | mailgun | ses
  smtp:
    host: "localhost"
    port: 587
    username: ""
    password: ""
    use_tls: true
    use_ssl: false
  from_address: "noreply@freestack.local"
  from_name: "FreeStack"
```

### Webhooks

```yaml
webhooks:
  enabled: false
  secret: ""
  timeout: 10
  max_retries: 3
  retry_backoff: 5
```

### Metrics

```yaml
metrics:
  enabled: true
  path: "/metrics"
  port: 9090
```

### Tracing

```yaml
tracing:
  enabled: false
  service_name: "freestack"
  exporter: "otlp"               # otlp | jaeger | zipkin | console
  otlp:
    endpoint: "http://localhost:4317"
    headers: {}
  sample_rate: 1.0
```

### Security Headers

```yaml
security:
  headers:
    x_content_type_options: "nosniff"
    x_frame_options: "DENY"
    x_xss_protection: "1; mode=block"
    strict_transport_security: "max-age=31536000; includeSubDomains"
    content_security_policy: "default-src 'self'"
    referrer_policy: "strict-origin-when-cross-origin"
    permissions_policy: "geolocation=(), microphone=(), camera=()"
  cors:
    allow_origins: []
    allow_methods: []
    allow_headers: []
    allow_credentials: false
    max_age: 600
```

## Environment Variables

All settings can be overridden with environment variables using the `FREESTACK_` prefix and double underscores for nesting:

```bash
# Application
FREESTACK_APP__ENVIRONMENT=production
FREESTACK_APP__DEBUG=false

# Database
FREESTACK_DATABASE__URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
FREESTACK_REDIS__URL=redis://host:6379/0

# Auth
FREESTACK_AUTH__SECRET_KEY=your-secret-key
FREESTACK_AUTH__ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
FREESTACK_API__HOST=0.0.0.0
FREESTACK_API__PORT=8000
FREESTACK_API__WORKERS=4
FREESTACK_API__CORS_ORIGINS=https://app.example.com
FREESTACK_API__RATE_LIMIT=200/minute

# Logging
FREESTACK_LOGGING__LEVEL=INFO
FREESTACK_LOGGING__FORMAT=json

# Worker
FREESTACK_WORKER__CONCURRENCY=8
```

## Environment-Specific Configs

### Development (`config.development.yaml`)
```yaml
app:
  environment: "development"
  debug: true
logging:
  level: "DEBUG"
  format: "console"
api:
  workers: 1
```

### Staging (`config.staging.yaml`)
```yaml
app:
  environment: "staging"
  debug: false
logging:
  level: "INFO"
  format: "json"
api:
  workers: 2
```

### Production (`config.production.yaml`)
```yaml
app:
  environment: "production"
  debug: false
logging:
  level: "WARNING"
  format: "json"
api:
  workers: 4
  cors_origins:
    - "https://yourdomain.com"
security:
  headers:
    strict_transport_security: "max-age=31536000; includeSubDomains; preload"
```

## Secrets Management

### Never Commit Secrets
- Add `config.yaml` to `.gitignore`
- Use environment variables in production
- Use secret managers (AWS Secrets Manager, HashiCorp Vault, etc.)

### Generating Secret Key
```bash
# Using CLI
freestack generate secret

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL
openssl rand -hex 32
```

### Docker Secrets
```yaml
# docker-compose.yml
services:
  api:
    secrets:
      - secret_key
      - database_url

secrets:
  secret_key:
    file: ./secrets/secret_key.txt
  database_url:
    file: ./secrets/database_url.txt
```

## Validation

Configuration is validated on startup. Invalid config will cause the application to fail fast with clear error messages.

Run validation manually:
```bash
freestack config validate
```