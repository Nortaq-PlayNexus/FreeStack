# FreeStack Deployment Guide

This guide covers deploying FreeStack to production environments.

## Deployment Options

### Docker Compose (Single Server)
Best for small deployments, staging, or development.

```bash
# Build image
docker build -t freestack:latest .

# Create environment file
cp .env.example .env.production
# Edit .env.production with production values

# Deploy
docker-compose --env-file .env.production up -d
```

### Kubernetes (Helm)
Best for production with scaling, self-healing, and rolling updates.

```bash
# Add Helm repo
helm repo add freestack https://charts.freestack.dev

# Install
helm install freestack freestack/freestack \
  --namespace freestack \
  --create-namespace \
  --set database.url=postgresql://... \
  --set redis.url=redis://... \
  --set auth.secretKey=...
```

### Manual Deployment
For custom infrastructure.

```bash
# Build
docker build -t freestack:latest .

# Run
docker run -d \
  --name freestack-api \
  -p 8000:8000 \
  -e FREESTACK_DATABASE_URL=postgresql://... \
  -e FREESTACK_REDIS_URL=redis://... \
  -e FREESTACK_SECRET_KEY=... \
  -e FREESTACK_ENVIRONMENT=production \
  freestack:latest
```

## Production Checklist

### Security
- [ ] Generate strong `FREESTACK_SECRET_KEY` (32+ bytes)
- [ ] Use strong database passwords
- [ ] Enable TLS with valid certificates
- [ ] Configure CORS for your domains only
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Configure firewall rules
- [ ] Set up WAF (Cloudflare, AWS WAF, etc.)
- [ ] Regular security scanning (`pip-audit`, `bandit`)

### Database
- [ ] Use managed PostgreSQL (RDS, Cloud SQL, etc.)
- [ ] Enable automated backups
- [ ] Configure read replicas
- [ ] Set up connection pooling (PgBouncer)
- [ ] Monitor query performance
- [ ] Set up alerts for disk space, connections

### Redis
- [ ] Use managed Redis (ElastiCache, Redis Cloud, etc.)
- [ ] Enable persistence (AOF)
- [ ] Configure memory policies
- [ ] Set up replication
- [ ] Monitor memory usage

### Monitoring
- [ ] Set up Prometheus + Grafana
- [ ] Configure alerting (PagerDuty, Opsgenie, etc.)
- [ ] Log aggregation (ELK, Loki, CloudWatch)
- [ ] Distributed tracing (Jaeger, Zipkin)
- [ ] Uptime monitoring (Pingdom, UptimeRobot)

### Reliability
- [ ] Health checks configured
- [ ] Graceful shutdown handling
- [ ] Circuit breakers for external services
- [ ] Retry policies with exponential backoff
- [ ] Dead letter queues for failed jobs
- [ ] Backup and restore procedures tested

### Performance
- [ ] CDN for static assets
- [ ] HTTP/2 enabled
- [ ] Compression (gzip/brotli)
- [ ] Database indexes optimized
- [ ] Query performance monitored
- [ ] Caching strategy implemented

## Environment Variables

Create `.env.production` with:

```bash
# Application
FREESTACK_APP__ENVIRONMENT=production
FREESTACK_APP__DEBUG=false

# Database
FREESTACK_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/freestack

# Redis
FREESTACK_REDIS_URL=redis://host:6379/0

# Authentication
FREESTACK_AUTH__SECRET_KEY=your-32-byte-secret-key-here
FREESTACK_AUTH__ACCESS_TOKEN_EXPIRE_MINUTES=30
FREESTACK_AUTH__REFRESH_TOKEN_EXPIRE_DAYS=7

# API
FREESTACK_API__HOST=0.0.0.0
FREESTACK_API__PORT=8000
FREESTACK_API__WORKERS=4
FREESTACK_API__CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
FREESTACK_API__RATE_LIMIT=100/minute

# Logging
FREESTACK_LOGGING__LEVEL=INFO
FREESTACK_LOGGING__FORMAT=json

# Metrics
FREESTACK_METRICS__ENABLED=true

# Tracing
FREESTACK_TRACING__ENABLED=true
FREESTACK_TRACING__OTLP__ENDPOINT=http://jaeger:4317
```

## Docker Compose Production Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: freestack:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  worker:
    image: freestack:latest
    command: freestack worker start --concurrency 8
    deploy:
      replicas: 2

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/prod.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
```

Deploy with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
```

## Kubernetes Deployment

### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: freestack
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: freestack-config
  namespace: freestack
data:
  FREESTACK_APP__ENVIRONMENT: "production"
  FREESTACK_API__WORKERS: "4"
  FREESTACK_LOGGING__FORMAT: "json"
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: freestack-secrets
  namespace: freestack
type: Opaque
stringData:
  FREESTACK_DATABASE_URL: "postgresql+asyncpg://..."
  FREESTACK_REDIS_URL: "redis://..."
  FREESTACK_AUTH__SECRET_KEY: "..."
```

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: freestack-api
  namespace: freestack
spec:
  replicas: 3
  selector:
    matchLabels:
      app: freestack-api
  template:
    metadata:
      labels:
        app: freestack-api
    spec:
      containers:
      - name: api
        image: freestack:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: freestack-config
        - secretRef:
            name: freestack-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: freestack-api
  namespace: freestack
spec:
  selector:
    app: freestack-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: freestack-ingress
  namespace: freestack
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: freestack-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: freestack-api
            port:
              number: 80
```

## Database Migrations

```bash
# Run migrations
freestack db upgrade

# Or with Docker
docker-compose exec api freestack db upgrade

# Or with Kubernetes
kubectl exec -n freestack deploy/freestack-api -- freestack db upgrade
```

## Rollback Procedure

```bash
# Docker Compose
docker-compose --env-file .env.production down
docker-compose --env-file .env.production up -d --scale api=3 freestack:previous-tag

# Kubernetes
kubectl rollout undo deployment/freestack-api -n freestack
```

## Backup & Restore

### Database Backup
```bash
# Automated (cron)
pg_dump -h host -U user freestack | gzip > backup_$(date +%F).sql.gz

# Restore
gunzip -c backup_2026-01-15.sql.gz | psql -h host -U user freestack
```

### Redis Backup
```bash
# Redis has built-in persistence (RDB/AOF)
# For manual backup:
redis-cli BGSAVE
```

## Scaling

### Horizontal Scaling
```bash
# Docker Compose
docker-compose --env-file .env.production up -d --scale api=5 --scale worker=3

# Kubernetes
kubectl scale deployment freestack-api --replicas=10 -n freestack
```

### Database Scaling
- Read replicas for SELECT queries
- Connection pooling (PgBouncer)
- Partitioning for large tables
- Consider read models for complex queries

## Troubleshooting

### Common Issues

**Database connection failures**
- Check network connectivity
- Verify credentials
- Check connection pool settings
- Monitor PostgreSQL logs

**Redis connection failures**
- Check Redis is running
- Verify URL and credentials
- Check memory limits
- Monitor Redis logs

**High latency**
- Check database query performance
- Enable query logging
- Add indexes
- Check for N+1 queries

**Memory issues**
- Check for memory leaks
- Monitor worker memory
- Adjust worker concurrency
- Profile with `py-spy`

### Debugging Commands
```bash
# View logs
docker-compose logs -f api

# Shell into container
docker-compose exec api bash

# Run migrations manually
docker-compose exec api freestack db upgrade

# Check health
curl http://localhost:8000/health/ready

# View metrics
curl http://localhost:9090/metrics
```