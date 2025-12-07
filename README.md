# BazaarHub Backend

E-commerce microservices backend with FastAPI and MongoDB.

## Services

| Service  | Port | Description                      |
| -------- | ---- | -------------------------------- |
| Auth     | 8001 | User authentication & JWT tokens |
| Products | 8002 | Product catalog & search         |
| Cart     | 8003 | Shopping cart operations         |
| Orders   | 8004 | Checkout & order history         |

## Quick Start

```bash
# With Docker
docker-compose up -d

# Local development
uv sync
uv run uvicorn backend.services.auth.main:app --reload --port 8001
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Database](docs/DATABASE.md)
