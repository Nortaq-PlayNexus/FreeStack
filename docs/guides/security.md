# FreeStack Security Guide

Security best practices for FreeStack applications.

## Authentication Security

### JWT Tokens
- Use strong secret keys (32+ bytes, randomly generated)
- Rotate keys periodically
- Use short access token lifetimes (15-30 minutes)
- Use refresh tokens with longer lifetimes (7-30 days)
- Implement token blacklisting for logout
- Store tokens securely (HttpOnly cookies or secure storage)

### Password Security
- Enforce strong password policies (12+ chars, mixed case, numbers, symbols)
- Use bcrypt with high cost factor (12+)
- Never log passwords
- Implement rate limiting on auth endpoints
- Use constant-time comparison

### Session Management
- Secure, HttpOnly, SameSite cookies
- Short session timeouts
- Rotate session IDs on privilege changes
- Invalidate sessions on password change
- Track concurrent sessions

## API Security

### Rate Limiting
- Implement per-user and per-IP limits
- Use sliding window algorithm
- Return standard headers (Retry-After, X-RateLimit-*)
- Configure different limits for different endpoints

### Input Validation
- Validate all input with Pydantic models
- Use allow-lists for enums
- Sanitize user-generated content
- Limit request sizes
- Prevent mass assignment

### CORS
- Restrict origins to known domains
- Don't use wildcard with credentials
- Set appropriate headers

### Security Headers
Always include:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## Database Security

### Connection Security
- Use SSL/TLS for database connections
- Use connection pooling
- Limit database user permissions
- Use separate users for app vs migrations

### Data Protection
- Encrypt sensitive fields at rest
- Use parameterized queries (SQLAlchemy handles this)
- Implement row-level security for multi-tenancy
- Audit sensitive data access

### Migrations
- Review all migrations before applying
- Test on staging data first
- Have rollback procedures
- Never modify applied migrations

## Infrastructure Security

### Network
- Private networks for internal services
- Load balancers with WAF
- Security groups / firewalls
- VPC peering for cross-region

### Containers
- Run as non-root user
- Read-only root filesystem
- Drop unnecessary capabilities
- Use distroless or minimal base images
- Scan images for vulnerabilities

### Secrets
- Never in code or config files
- Use secret managers
- Rotate regularly
- Audit access

### Monitoring
- Alert on failed auth attempts
- Alert on unusual API patterns
- Audit log aggregation
- Intrusion detection

## Common Vulnerabilities

### OWASP Top 10 Mitigations

| Vulnerability | Mitigation |
|---------------|------------|
| Broken Access Control | RBAC, resource-level permissions, deny by default |
| Cryptographic Failures | TLS 1.3, strong ciphers, proper key management |
| Injection | Parameterized queries, input validation, ORM |
| Insecure Design | Threat modeling, security requirements, secure patterns |
| Security Misconfiguration | Hardened defaults, automated config checks |
| Vulnerable Components | Dependency scanning, automated updates, SBOM |
| Identification/Authentication Failures | MFA, rate limiting, secure session management |
| Software/Data Integrity Failures | Signed artifacts, CI/CD integrity, supply chain security |
| Security Logging/Monitoring Failures | Structured logging, centralized logs, alerting |
| Server-Side Request Forgery | URL validation, allow-lists, network segmentation |

## Secure Development Practices

### Code Review
- Security-focused review checklist
- Automated security scanning in CI
- Threat modeling for new features

### Dependency Management
- Pin dependency versions
- Regular updates (`pip-audit`, `dependabot`)
- Minimal dependencies
- Verify package integrity

### Testing
- Security unit tests
- Penetration testing
- Fuzzing for parsers
- SAST/DAST in pipeline

## Incident Response

### Preparation
- Incident response plan
- Runbooks for common scenarios
- Contact lists
- Communication templates

### Detection
- Automated alerting
- Log analysis
- User reports

### Response
- Contain the incident
- Eradicate the threat
- Recover systems
- Post-incident review

### Communication
- Internal stakeholders
- Affected users (if applicable)
- Regulatory bodies (if required)

## Compliance

### GDPR
- Data minimization
- Right to deletion
- Data portability
- Privacy by design
- DPIA for high-risk processing

### SOC 2
- Access controls
- Audit logging
- Encryption
- Monitoring
- Incident response

### HIPAA (if applicable)
- PHI encryption
- Access controls
- Audit trails
- Business associate agreements

## Security Checklist for Releases

- [ ] Dependency scan passed
- [ ] Static analysis passed
- [ ] Secrets scan passed
- [ ] Container scan passed
- [ ] Penetration test completed
- [ ] Security regression tests passed
- [ ] Threat model updated
- [ ] Documentation updated