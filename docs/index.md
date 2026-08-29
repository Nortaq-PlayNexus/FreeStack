# FreeStack Documentation

Welcome to the FreeStack documentation. This site provides comprehensive guides, API references, and architectural documentation.

## Quick Links

- [Getting Started](getting-started.md)
- [Architecture Overview](architecture/overview.md)
- [API Reference](api/reference.md)
- [CLI Reference](cli/reference.md)
- [Deployment Guide](guides/deployment.md)
- [Development Guide](guides/development.md)

## Project Structure

```
docs/
├── index.md                 # This file
├── getting-started.md       # Quick start guide
├── architecture/            # Architecture documentation
│   ├── overview.md
│   ├── database.md
│   ├── authentication.md
│   ├── events.md
│   └── websocket.md
├── api/                     # API documentation
│   ├── reference.md
│   ├── authentication.md
│   ├── users.md
│   └── health.md
├── cli/                     # CLI documentation
│   ├── reference.md
│   ├── database.md
│   ├── api.md
│   └── worker.md
└── guides/                  # How-to guides
    ├── deployment.md
    ├── development.md
    ├── testing.md
    ├── configuration.md
    └── security.md
```

## Building Documentation

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Build locally
mkdocs serve

# Build for production
mkdocs build
```

## Contributing

Documentation is written in Markdown and built with MkDocs Material. See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.