# Operational Procedures

## Deployment Procedures

### Pre-Deployment Checklist

- [ ] Environment configuration updated (.env)
- [ ] Docker and Docker Compose installed
- [ ] Required ports available (5432, 8080, 80, 443)
- [ ] Sufficient disk space available
- [ ] Network connectivity verified
- [ ] Backup of existing data (if updating)

### Standard Deployment

```bash
# 1. Initialize environment
./scripts/init.sh

# 2. Deploy system
python3 src/deploy.py deploy --config config/deployment.yaml

# 3. Verify deployment
python3 src/deploy.py status --config config/deployment.yaml

# 4. Test system
curl http://localhost:8080/health/deep
```

### Backup Before Major Updates

```bash
python3 src/deploy.py deploy \
  --config config/deployment.yaml \
  --backup
```

## Daily Operations

### Health Monitoring

```bash
# Quick health check
curl http://localhost:8080/health

# Detailed health check
curl http://localhost:8080/health/deep

# View logs
docker compose logs -f web
docker compose logs -f postgres
```

### Container Management

```bash
# View running containers
docker compose ps

# View detailed container info
docker inspect enterprise-iac-web

# Restart containers
docker compose restart web
docker compose restart postgres

# View resource usage
docker stats
```

### Database Operations

#### Connecting to Database

```bash
# Via Docker
docker exec -it enterprise-iac-postgres psql -U postgres -d enterprise_db

# Via psql (local)
psql -h localhost -p 5432 -U postgres -d enterprise_db
```

#### Common Database Queries

```sql
-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check database size
SELECT pg_size_pretty(pg_database_size('enterprise_db'));

-- View recent audit logs
SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;
```

## Maintenance

### Regular Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Check disk space | Daily | `df -h` |
| Review logs | Daily | `docker compose logs` |
| Backup database | Daily | `python3 src/deploy.py deploy --backup` |
| Check health | Hourly | `curl /health/deep` |

### Database Maintenance

```bash
# Connect to database
docker exec -it enterprise-iac-postgres psql -U postgres -d enterprise_db

# Run vacuum (cleanup)
VACUUM ANALYZE;

# Reindex (if needed)
REINDEX DATABASE enterprise_db;
```

### Cleanup Operations

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove all unused resources
docker system prune -a -f
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs web

# Common causes:
# - Port already in use
# - Database not ready
# - Environment variables not set

# Solution: Check .env and port availability
lsof -i :5000
```

### Database Connection Issues

```bash
# Check if database container is running
docker ps | grep postgres

# Check database logs
docker compose logs postgres

# Verify connection
docker compose exec postgres pg_isready -U postgres
```

### Web Application Errors

```bash
# View application logs
docker compose logs -f web

# Test API endpoints
curl http://localhost:8080/api/v1/info

# Deep health check
curl http://localhost:8080/health/deep
```

### Performance Issues

```bash
# Monitor container resources
docker stats

# Check Docker disk usage
docker system df

# Analyze slow queries (if database issue)
# Connect to DB and enable query logging
ALTER DATABASE enterprise_db SET log_min_duration_statement = 1000;
```

## Scaling

### Horizontal Scaling

For multiple application instances, use Docker Compose scaling:

```bash
# Scale web service to 3 instances
docker compose up -d --scale web=3
```

### Vertical Scaling

Increase resource limits in docker-compose.yml:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'      # Increase from 0.5
          memory: 512M     # Increase from 256M
```

## Backup and Recovery

### Create Manual Backup

```bash
# Backup database
pg_dump -h localhost -p 5432 -U postgres -d enterprise_db > backup_$(date +%Y%m%d).sql

# Backup entire system
docker compose exec postgres pg_dump -U postgres -d enterprise_db > backup.sql
```

### Restore from Backup

```bash
# Stop services
python3 src/deploy.py stop --config config/deployment.yaml

# Restore database
psql -h localhost -p 5432 -U postgres enterprise_db < backup.sql

# Restart services
python3 src/deploy.py deploy --config config/deployment.yaml
```

### Automated Backup

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/Enterprise-Grade\ IaC && python3 src/deploy.py deploy --backup
```

## Updates and Upgrades

### Update Base Images

```bash
# Pull latest images
docker compose pull

# Rebuild application
docker compose build --no-cache

# Deploy with backup
python3 src/deploy.py deploy --config config/deployment.yaml --backup
```

### Update Dependencies

```bash
# Update Python packages
pip3 install --upgrade -r requirements.txt

# Rebuild web container
docker compose build --no-cache web

# Restart service
docker compose restart web
```

## Security Hardening

### SSL/TLS Configuration

1. Generate certificates:
```bash
mkdir -p config/ssl
# Use Let's Encrypt or generate self-signed certificates
certbot certonly --standalone -d yourdomain.com
```

2. Update docker-compose.yml:
```yaml
nginx:
  ports:
    - "443:443"
  volumes:
    - ./config/ssl:/etc/nginx/ssl
```

3. Update nginx.conf to use SSL certificates

### Access Control

```bash
# Create API authentication
# See web/app.py for authentication mechanisms

# Implement rate limiting via Nginx
# See config/nginx.conf for rate limiting configuration
```

### Secret Management

```bash
# Instead of .env, use:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Docker Secrets (for Swarm)

# Never commit secrets to Git
git config --global core.excludesfile ~/.gitignore_global
echo ".env" >> ~/.gitignore_global
```

## Monitoring and Alerting

### Health Endpoint Integration

```bash
# Prometheus scraping
# Add to prometheus.yml
scrape_configs:
  - job_name: 'enterprise-iac'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/health/deep'
```

### Alerting Rules

```bash
# Set up alerts for:
# - High CPU usage (>80%)
# - High memory usage (>80%)
# - Database connection failures
# - Health check failures
```

## Incident Response

### Service Down

1. Check container status: `docker compose ps`
2. Review logs: `docker compose logs`
3. Check resources: `docker stats`
4. Restart service: `docker compose restart`
5. If persistent: Run diagnostics

### Database Corruption

1. Check database logs
2. Attempt REINDEX
3. Restore from backup if necessary

### Security Breach

1. Immediately stop affected services
2. Change all credentials
3. Review audit logs
4. Deploy clean environment
5. Notify security team

## Support Contacts

- DevOps Team: devops@company.com
- Database Administrator: dba@company.com
- Security Team: security@company.com
