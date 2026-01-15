# Quick Start Guide

## 5-Minute Setup

### Step 1: Prerequisites Check (1 minute)

```bash
# Verify Docker is installed
docker --version
docker compose version

# Verify Python is installed
python3 --version
```

### Step 2: Initialize Project (1 minute)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run initialization
./scripts/init.sh
```

This will:
- ✓ Verify Docker installation
- ✓ Check Python dependencies
- ✓ Create necessary directories
- ✓ Generate .env file

### Step 3: Configure Environment (1 minute)

```bash
# Edit configuration
nano .env

# Update these if desired:
# - DB_PASSWORD
# - SECRET_KEY
# - ENVIRONMENT (dev/staging/prod)
```

### Step 4: Deploy System (2 minutes)

```bash
# Deploy infrastructure
python3 src/deploy.py deploy --config config/deployment.yaml

# Wait for containers to start (30-40 seconds)
```

### Step 5: Verify Deployment (1 minute)

```bash
# Check system status
python3 src/deploy.py status --config config/deployment.yaml

# Test the API
curl http://localhost:8080/health/deep
```

## Verify Success

You should see:

```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "server_time": "2024-01-15T...",
    "applications": 5,
    "health_records": 4
  },
  "timestamp": "2024-01-15T..."
}
```

## Common First Steps

### Create an Application

```bash
curl -X POST http://localhost:8080/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyFirstApp",
    "description": "My first application"
  }'
```

### View Applications

```bash
curl http://localhost:8080/api/v1/applications | jq
```

### Access Web Application

Open browser to: http://localhost:8080

### Connect to Database

```bash
docker exec -it enterprise-iac-postgres psql \
  -U postgres \
  -d enterprise_db
```

Then in psql:
```sql
SELECT * FROM applications;
\dt  -- list tables
```

## Next Steps

1. **Read Full Documentation**: See [README.md](README.md)
2. **Review Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Operational Procedures**: See [OPERATIONS.md](OPERATIONS.md)
4. **Customize Deployment**: Edit `config/deployment.yaml`
5. **Implement SSL**: Follow security section in README

## Troubleshooting

### Port Already in Use

```bash
# Find process on port 8080
lsof -i :8080

# Kill if needed
kill -9 <PID>
```

### Database Not Starting

```bash
# Check logs
docker compose logs postgres

# Restart
docker compose restart postgres
```

### Web App Not Responding

```bash
# Check logs
docker compose logs web

# Check if running
docker compose ps

# Restart
docker compose restart web
```

## Stop System

```bash
python3 src/deploy.py stop --config config/deployment.yaml
```

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Root endpoint |
| `GET /health` | Health check |
| `GET /health/deep` | Detailed health |
| `GET /api/v1/info` | API information |
| `GET /api/v1/applications` | List apps |
| `POST /api/v1/applications` | Create app |
| `GET /api/v1/applications/{id}` | Get app |
| `PUT /api/v1/applications/{id}` | Update app |
| `DELETE /api/v1/applications/{id}` | Delete app |

## Key Files

| File | Purpose |
|------|---------|
| `src/deploy.py` | Deployment orchestration |
| `docker-compose.yml` | Container definitions |
| `config/deployment.yaml` | Configuration |
| `.env` | Environment variables |
| `web/app.py` | Flask application |
| `database/init/` | Database schema |

## Performance Tips

- For development: Use default settings
- For production: Review OPERATIONS.md for tuning
- Monitor with: `docker stats`
- Check health: `curl http://localhost:8080/health`

## Support

For issues or questions:
1. Check TROUBLESHOOTING section in README.md
2. Review logs: `docker compose logs -f`
3. Check architecture: ARCHITECTURE.md

---

**You're now running an enterprise-grade infrastructure!**
