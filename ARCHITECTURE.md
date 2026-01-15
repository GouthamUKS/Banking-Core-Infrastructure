# Architecture and Design Documentation

## System Architecture

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          Load Balancer / Nginx                   │
│                    (Reverse Proxy, SSL Termination)              │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
         ┌──────────▼──────────┐    ┌──────────▼──────────┐
         │   Flask Web App      │    │  Flask Web App      │
         │  (Port 5000)         │    │  (Port 5000)        │
         │  Container 1         │    │  Container 2        │
         └──────────┬───────────┘    └──────────┬──────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼────────────┐
                    │    PostgreSQL Database   │
                    │    (Port 5432)           │
                    │    Volume Storage        │
                    └──────────────────────────┘
```

### Component Breakdown

#### 1. Nginx Reverse Proxy
- **Port**: 80 (HTTP), 443 (HTTPS)
- **Responsibilities**: 
  - Request routing
  - SSL/TLS termination
  - Load balancing
  - Security headers
  - Logging and monitoring

#### 2. Flask Web Application
- **Port**: 5000 (internal), 8080 (external)
- **Components**:
  - REST API endpoints
  - SQLAlchemy ORM
  - CORS support
  - Health check endpoints
  - Request logging

#### 3. PostgreSQL Database
- **Port**: 5432
- **Version**: 15 (Alpine)
- **Features**:
  - ACID compliance
  - JSON support
  - Full-text search
  - Automated backups
  - Audit logging

## Network Architecture

### Docker Network: iac_network (172.20.0.0/16)

```
Service Discovery (DNS):
- postgres → 172.20.0.2
- web → 172.20.0.3
- nginx → 172.20.0.4

Communication Flow:
Internet → Nginx (Port 80/443) → Flask Web (5000) → PostgreSQL (5432)
```

## Data Flow

### Request Flow

```
1. Client Request
   ↓
2. Nginx (Load Balancer, SSL)
   ↓
3. Flask Application
   - Route matching
   - Request validation
   - Business logic
   ↓
4. SQLAlchemy ORM
   - Query building
   - Transaction management
   ↓
5. PostgreSQL Database
   - Query execution
   - Data retrieval/storage
   ↓
6. Response Flow (Reverse)
   Flask → JSON Response
   Nginx → Client
```

## Deployment Model

### Multi-Container Architecture Benefits

1. **Separation of Concerns**
   - Each service has single responsibility
   - Independent scaling
   - Simplified maintenance

2. **Resilience**
   - Container isolation
   - Health checks with restart
   - Service failure doesn't affect others

3. **Resource Efficiency**
   - Lightweight containers
   - Shared kernel
   - Efficient resource utilization

4. **Development Productivity**
   - Reproducible environments
   - Consistent across teams
   - Easy onboarding

## Security Architecture

### Defense in Depth

```
Layer 1: Network Security
├─ Isolated Docker network
├─ No external port exposure (except 80/443)
└─ Service-to-service communication via private network

Layer 2: Container Security
├─ Non-root user execution
├─ Read-only filesystems where possible
├─ Resource limits (CPU, memory)
└─ No new privileges flag

Layer 3: Application Security
├─ Input validation
├─ SQL injection prevention (ORM)
├─ CORS configuration
└─ Security headers

Layer 4: Data Security
├─ Environment-based secrets
├─ Database authentication
├─ Encrypted backups
└─ Audit logging
```

## Data Persistence

### Volume Management

```
Named Volume: postgres_data
├─ Location: /var/lib/docker/volumes/postgres_data/_data
├─ Owner: postgres user
├─ Backup: Regular automated backups
└─ Recovery: Database restore from backup

Log Files:
├─ Nginx logs: stdout (json-file driver)
├─ Application logs: stdout (json-file driver)
├─ Retention: 3 files, 10MB each
└─ Archival: Move to external storage (S3, GCS)
```

## Scalability Considerations

### Horizontal Scaling

```
Current Setup (Single Instance):
Nginx → Web (1) → PostgreSQL (1)

Scaled Setup (Multiple Instances):
Nginx → Web (1) → PostgreSQL (1)
    → Web (2)
    → Web (3)

Implementation:
docker compose up -d --scale web=3
```

### Vertical Scaling

```
Resource Limits in docker-compose.yml:

Small:
- CPU: 0.5 cores
- Memory: 256MB

Medium:
- CPU: 1.0 cores
- Memory: 512MB

Large:
- CPU: 2.0 cores
- Memory: 1GB
```

## High Availability Considerations

### For Production

1. **Database Replication**
   ```
   Primary PostgreSQL → Standby PostgreSQL (streaming replication)
   ```

2. **Application Redundancy**
   ```
   Load Balancer → App Node 1
                → App Node 2
                → App Node 3
   ```

3. **Health Checks**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 40s
   ```

## Monitoring and Observability

### Metrics Collection

```
Application Metrics:
- Request rate
- Response time
- Error rate
- Database query time

System Metrics:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

Business Metrics:
- Applications created/deleted
- Service health status
- API usage by endpoint
```

### Logging Strategy

```
Log Levels:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical issues

Log Destinations:
- Application: stdout (captured by Docker)
- Database: PostgreSQL logs
- Nginx: Access and error logs
- Central: ELK stack / CloudWatch
```

## Disaster Recovery

### Recovery Time Objectives (RTO) & Recovery Point Objectives (RPO)

| Scenario | RTO | RPO |
|----------|-----|-----|
| Container restart | < 1 minute | 0 |
| Single container failure | < 5 minutes | 0 |
| Database backup restore | < 30 minutes | 1 day |
| Complete infrastructure loss | < 1 hour | 1 hour |

### Backup Strategy

```
Daily Backups:
- Time: 2 AM (automated)
- Retention: 30 days
- Storage: S3 with versioning

Recovery Testing:
- Monthly restore tests
- Documented procedures
- Documented RTO/RPO
```

## Performance Optimization

### Application Level

```python
# Connection pooling
pool_size=10
max_overflow=20

# Query optimization
- Index key columns
- Use selective joins
- Pagination for large datasets

# Caching
- Redis for session storage
- HTTP caching headers
- Database query caching
```

### Infrastructure Level

```yaml
# Nginx optimization
- Gzip compression enabled
- Static file caching (30 days)
- Keepalive connections

# Database optimization
- VACUUM ANALYZE regularly
- Query logging and analysis
- Connection pooling (PgBouncer)

# Container optimization
- Multi-stage builds
- Minimal base images
- Resource limits appropriate
```

## Technology Stack Rationale

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Container Runtime | Docker | Industry standard, ecosystem |
| Orchestration | Docker Compose | Simplicity for single-host |
| Language | Python 3.11 | Rapid development, DevOps-friendly |
| Framework | Flask | Lightweight, flexible, proven |
| Database | PostgreSQL 15 | ACID, reliability, feature-rich |
| Proxy | Nginx | High performance, low resource usage |
| Base Image | Alpine Linux | Minimal, secure, small footprint |

## Design Patterns

### Implemented Patterns

1. **Repository Pattern**
   - Centralized data access (SQLAlchemy models)
   - Easy to switch backends

2. **Factory Pattern**
   - DeploymentManager creates orchestrators
   - Flexible component creation

3. **Singleton Pattern**
   - Flask app instance
   - Docker client

4. **Health Check Pattern**
   - Multiple health check endpoints
   - Liveness and readiness probes

5. **Audit Pattern**
   - Event logging
   - Change tracking
   - Compliance requirements

## API Design

### RESTful Principles

```
Resources:
- /api/v1/applications - Collection
- /api/v1/applications/{id} - Individual resource
- /api/v1/health/metrics - Metrics

HTTP Methods:
- GET: Retrieve resources
- POST: Create resources
- PUT: Update resources
- DELETE: Remove resources

Response Format:
{
  "status": "success|error",
  "data": {...},
  "message": "...",
  "timestamp": "ISO8601"
}
```

## Deployment Strategies

### Blue-Green Deployment

```
Current (Blue):
- Version 1.0.0
- Production traffic

New (Green):
- Version 1.1.0
- Testing environment

Switch: Route traffic from Blue to Green after validation
```

### Canary Deployment

```
Phase 1: 10% traffic to new version
Phase 2: 25% traffic to new version
Phase 3: 50% traffic to new version
Phase 4: 100% traffic to new version (full rollout)
```

### Rolling Updates

```
Update 1 instance at a time:
1. Stop instance 1
2. Update instance 1
3. Start instance 1
4. Repeat for remaining instances
```

---

**Architecture designed for scalability, reliability, and operational excellence.**
