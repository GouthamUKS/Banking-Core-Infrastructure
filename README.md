# Enterprise-Grade Infrastructure-as-Code (IaC) Deployment System

## Overview

A comprehensive Python and Docker-based Infrastructure-as-Code solution that automates the provisioning and management of secure, multi-container web environments. This system demonstrates enterprise-grade practices in cloud infrastructure automation, reducing manual engineering time and ensuring consistent deployment across teams.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                      │
│                (Port: 80/443, Load Balancing)               │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐       ┌────▼────┐
    │   Flask │        │  PostgreSQL│       │ Logging │
    │   Web   │        │  Database  │       │ Monitor │
    │   App   │        │  (Port 5432)      │        │
    │(5000)   │        │            │       │        │
    └─────────┘        └────────────┘       └────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    IaC Network (172.20.0.0/16)
```

## Key Features

### 1. **Multi-Container Orchestration**
- Docker Compose for container management
- Automated service discovery and networking
- Health checks and automatic restart policies
- Resource limits and constraints

### 2. **Database Management**
- PostgreSQL 15 with Alpine Linux for minimal footprint
- Automated schema initialization
- Migration support
- Backup and recovery mechanisms
- Audit logging

### 3. **Web Application Stack**
- Flask-based REST API
- SQLAlchemy ORM for database abstraction
- RESTful endpoint design
- Error handling and logging
- CORS support

### 4. **Security**
- Non-root container users
- Secrets management via environment variables
- Network isolation
- Security headers via Nginx
- Minimal base images (Alpine Linux)
- No new privileges for containers

### 5. **Monitoring & Health Checks**
- Kubernetes-style health checks
- Service status endpoints
- Health metrics tracking
- Application performance monitoring
- Deployment history logging

### 6. **Automation**
- Python-based deployment orchestration
- Pre-deployment validation
- Automated migrations
- Database initialization
- Comprehensive logging

## Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (1.29+)
- Python 3.8+
- Git

### Installation

1. **Clone/Setup the Project**
```bash
cd /path/to/Enterprise-Grade\ IaC
```

2. **Initialize Environment**
```bash
chmod +x scripts/init.sh
./scripts/init.sh
```

3. **Configure Environment**
```bash
# Copy example configuration
cp .env.example .env

# Edit with your values
nano .env
```

4. **Deploy**
```bash
python3 src/deploy.py deploy --config config/deployment.yaml
```

5. **Verify Deployment**
```bash
python3 src/deploy.py status --config config/deployment.yaml
```

## File Structure

```
Enterprise-Grade IaC/
├── src/
│   └── deploy.py                 # Main deployment orchestration script
├── web/
│   ├── app.py                    # Flask application
│   ├── Dockerfile                # Web container definition
│   └── requirements.txt           # Python dependencies
├── database/
│   ├── init/                     # Database initialization scripts
│   │   ├── 01_init_schema.sql   # Schema creation
│   │   └── 02_sample_data.sql   # Sample data
│   └── migrations/               # Database migrations
│       └── 001_add_api_keys_table.sql
├── config/
│   ├── deployment.yaml           # Deployment configuration
│   ├── nginx.conf               # Nginx reverse proxy config
│   └── ssl/                     # SSL certificates (production)
├── scripts/
│   ├── init.sh                  # Initialization script
│   └── deploy.sh                # Deployment wrapper
├── tests/                        # Test suite
├── docker-compose.yml            # Container orchestration
├── .env.example                 # Environment template
├── requirements.txt             # Root Python dependencies
└── README.md                    # Documentation
```

## Deployment Scenarios

### Development Environment

```bash
# Edit .env for development
ENVIRONMENT=development
DB_PASSWORD=dev-password
SECRET_KEY=dev-key

# Deploy
python3 src/deploy.py deploy --config config/deployment.yaml
```

### Production Environment

```bash
# Create production config
cp config/deployment.yaml config/production.yaml
# Edit production.yaml with production settings

# Deploy with backup
python3 src/deploy.py deploy \
  --config config/production.yaml \
  --backup
```

## API Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /health/deep` - Comprehensive health check
- `GET /api/v1/info` - Application information

### Applications Management
- `GET /api/v1/applications` - List all applications
- `POST /api/v1/applications` - Create new application
- `GET /api/v1/applications/{id}` - Get specific application
- `PUT /api/v1/applications/{id}` - Update application
- `DELETE /api/v1/applications/{id}` - Delete application

### Health Metrics
- `GET /api/v1/health/metrics` - Get health metrics
- `POST /api/v1/health/record` - Record health metric

### Example Requests

**Create Application**
```bash
curl -X POST http://localhost:8080/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{"name": "MyApp", "description": "Test app"}'
```

**Get Applications**
```bash
curl http://localhost:8080/api/v1/applications
```

**Health Check**
```bash
curl http://localhost:8080/health
```

## Database Access

### Direct Connection
```bash
# From your local machine
psql -h localhost -p 5432 -U postgres -d enterprise_db

# Or via Docker
docker exec -it enterprise-iac-postgres psql -U postgres -d enterprise_db
```

### Backups

```bash
# Manual backup
python3 src/deploy.py deploy --config config/deployment.yaml --backup

# Backups are stored in ./backups/ directory
ls -lah backups/
```

## Management Commands

### Deploy System
```bash
python3 src/deploy.py deploy --config config/deployment.yaml
```

### Stop System
```bash
python3 src/deploy.py stop --config config/deployment.yaml
```

### Check Status
```bash
python3 src/deploy.py status --config config/deployment.yaml
```

### View Logs
```bash
# All containers
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f postgres
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Project identifier | enterprise-iac |
| `ENVIRONMENT` | Deployment environment | development |
| `DB_NAME` | Database name | enterprise_db |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | SecurePassword123! |
| `DB_PORT` | Database port | 5432 |
| `WEB_PORT` | Web application port | 8080 |
| `FLASK_ENV` | Flask environment | development |
| `SECRET_KEY` | Flask secret key | dev-secret-key |
| `LOG_LEVEL` | Logging level | INFO |

### deployment.yaml Configuration

```yaml
project_name: "enterprise-iac"
environment: "development"

# Database
db_name: "enterprise_db"
db_user: "postgres"
db_password: "${DB_PASSWORD}"  # From .env

# Web Server
web_port: 8080
web_port_internal: 5000

# Security
backup_enabled: true
enable_ssl: false

# Monitoring
enable_health_checks: true
health_check_interval: 30
```

## Security Best Practices

### Implemented

1. **Container Security**
   - Non-root user execution
   - No new privileges flag
   - Minimal base images

2. **Network Security**
   - Isolated Docker network
   - Subnet configuration (172.20.0.0/16)
   - No exposed internal ports

3. **Data Security**
   - Environment variable secrets
   - Password-protected database
   - Backup retention policies

4. **Application Security**
   - Security headers (HSTS, CSP, etc.)
   - HTTPS ready (Nginx SSL)
   - CORS configuration
   - Input validation

### Recommendations for Production

1. **Use Secrets Management**
   - Implement AWS Secrets Manager
   - Or use HashiCorp Vault

2. **Enable SSL/TLS**
   - Generate certificates with Let's Encrypt
   - Configure in `config/ssl/`

3. **Database Security**
   - Use strong passwords
   - Implement connection pooling
   - Regular backups with encryption

4. **Monitoring**
   - Set up Prometheus/Grafana
   - CloudWatch integration
   - Alert notifications

5. **Access Control**
   - Implement API authentication
   - Rate limiting
   - RBAC

## Troubleshooting

### Docker Daemon Not Running
```bash
# macOS
open /Applications/Docker.app

# Linux
sudo systemctl start docker
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8080

# Kill process (if safe)
kill -9 <PID>
```

### Database Connection Failed
```bash
# Check if database container is running
docker ps | grep postgres

# View database logs
docker logs enterprise-iac-postgres

# Restart database
docker restart enterprise-iac-postgres
```

### Application Errors
```bash
# View application logs
docker logs enterprise-iac-web

# Check application health
curl http://localhost:8080/health/deep
```

## Performance Optimization

### Container Resources
```yaml
# docker-compose.yml adjustments
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### Database Optimization
- Connection pooling via SQLAlchemy
- Index creation on frequently queried columns
- Query optimization
- Vacuum and analyze regularly

### Application Optimization
- Gunicorn worker tuning
- Nginx caching policies
- Gzip compression
- CDN integration

## Monitoring & Logging

### Application Logs
```bash
docker compose logs -f web --tail 100
```

### Database Logs
```bash
docker compose logs -f postgres --tail 100
```

### System Metrics
```bash
# CPU and Memory usage
docker stats

# Network statistics
docker network inspect enterprise-iac_iac_network
```

## Disaster Recovery

### Backup Strategy
```bash
# Automated backup during deployment
python3 src/deploy.py deploy --config config/deployment.yaml --backup

# Manual backup
pg_dump -h localhost -p 5432 -U postgres enterprise_db > backup.sql
```

### Recovery
```bash
# Stop current deployment
python3 src/deploy.py stop --config config/deployment.yaml

# Restore from backup
psql -h localhost -p 5432 -U postgres enterprise_db < backup.sql

# Redeploy
python3 src/deploy.py deploy --config config/deployment.yaml
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy Infrastructure

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run initialization
        run: bash scripts/init.sh
      - name: Deploy system
        run: python3 src/deploy.py deploy --config config/deployment.yaml
```

### Jenkins Pipeline Example
```groovy
pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                sh 'bash scripts/init.sh'
            }
        }
        stage('Deploy') {
            steps {
                sh 'python3 src/deploy.py deploy --config config/deployment.yaml'
            }
        }
    }
}
```

## Support & Contributing

For issues, questions, or contributions:

1. Check the troubleshooting section
2. Review logs and error messages
3. Contact the DevOps team
4. Submit pull requests for improvements

## License

MIT License - See LICENSE file

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial release
- Multi-container orchestration
- PostgreSQL integration
- Flask API framework
- Comprehensive deployment automation
- Documentation and examples

---

**Built for Enterprise-Grade Cloud Infrastructure Deployment**
*Reducing manual engineering time and ensuring consistent deployments across teams.*
