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
│   └── overview.md
├── api/                     # API documentation
│   └── reference.md         # Placeholder — not yet written
├── cli/                     # CLI documentation
│   └── reference.md         # Placeholder — not yet written
└── guides/                  # How-to guides
    ├── deployment.md
    ├── development.md
    ├── configuration.md
    └── security.md
```

Only pages that exist are listed. `database`, `authentication`, `events`, `websocket`,
`testing` and the per-endpoint API and CLI pages are planned but not written yet.

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

Documentation is written in Markdown and built with MkDocs Material. See [CONTRIBUTING.md](https://github.com/Nortaq-PlayNexus/FreeStack/blob/main/CONTRIBUTING.md) for guidelines.