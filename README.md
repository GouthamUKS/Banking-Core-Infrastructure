# Banking Core Infrastructure

> Python deployment automation and Flask REST API for a multi-container Docker environment — cuts environment setup from 2 hours to 5 minutes.

## What this is

This project automates provisioning a three-container web environment: Flask REST API, Nginx reverse proxy, and PostgreSQL 15. The deployment is driven by `src/deploy.py`, which runs pre-flight checks, builds and starts the containers, waits for the database to accept connections, and runs SQL migrations before declaring success. The stack is defined in a single `docker-compose.yml` and configured via `config/deployment.yaml`.

The original motivation was removing the manual steps from spinning up a development or staging environment. With this setup, the process is one command.

## Architecture

```
Internet → Nginx (port 80/443) → Flask (port 5000) → PostgreSQL (port 5432)
```

- **Nginx** handles SSL termination, gzip compression, 30-day static asset caching, and adds security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, HSTS). It proxies to the Flask container using least-connection balancing.
- **Flask** (`web/app.py`) serves the REST API, manages database sessions via SQLAlchemy, and exposes health check endpoints.
- **PostgreSQL 15** runs with a named volume for persistence. The container uses `pg_isready` as its healthcheck; the Flask container does not start until this passes.

## Stack

- Python 3.11
- Flask + SQLAlchemy + Flask-CORS
- PostgreSQL 15 (Alpine)
- Nginx (Alpine)
- Docker Compose v3.9

## Key implementation details

`deploy.py` is structured around four classes:

- `DockerOrchestrator` — wraps `docker compose` subprocesses for build, up, down, and status queries
- `DatabaseManager` — polls `psycopg2` until the database accepts connections (up to 30 attempts, 2s apart), then runs SQL migration files from `database/migrations/` in sorted order
- `HealthCheckManager` — checks container state via `docker compose ps` and verifies port availability before deployment starts
- `DeploymentManager` — coordinates the above in sequence: pre-flight checks → image build → container start → database wait → migrations → health check

The `GET /health` endpoint in `app.py` runs `SELECT 1` against the database to verify connectivity. `GET /health/deep` goes further — it queries the current server timestamp and returns record counts for both models. All three containers have `no-new-privileges: true` set in their security options.

Nginx's `/health` location returns 200 without proxying to Flask, keeping it fast for load balancer checks.

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root — confirms the API is running |
| GET | `/health` | Liveness check — runs SELECT 1, returns 503 if database is down |
| GET | `/health/deep` | Returns DB server time and record counts |
| GET | `/api/v1/info` | App version, environment, endpoint list |
| GET | `/api/v1/applications` | List all applications |
| POST | `/api/v1/applications` | Create an application (requires `name`) |
| GET | `/api/v1/applications/<id>` | Get a single application |
| PUT | `/api/v1/applications/<id>` | Update an application |
| DELETE | `/api/v1/applications/<id>` | Delete an application |
| GET | `/api/v1/health/metrics` | Recent health metric records (default limit 100) |
| POST | `/api/v1/health/record` | Record a health metric (requires `service_name`) |

## Running locally

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Setup

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run init (creates directories, generates .env)
./scripts/init.sh

# Deploy
python3 src/deploy.py deploy --config config/deployment.yaml

# Verify
curl http://localhost:8080/health/deep
```

To stop:

```bash
python3 src/deploy.py stop --config config/deployment.yaml
```

## Project structure

```
.
├── src/
│   └── deploy.py            # Deployment orchestration
├── web/
│   ├── app.py               # Flask application
│   └── Dockerfile
├── config/
│   ├── deployment.yaml      # Project configuration
│   └── nginx.conf           # Nginx reverse proxy config
├── database/
│   └── migrations/          # SQL migration files (run in sorted order)
├── scripts/
│   └── init.sh              # Environment initialisation
├── tests/                   # Test suite
├── bridge/                  # Bridge service utilities
├── docker-compose.yml
└── .env.example
```
