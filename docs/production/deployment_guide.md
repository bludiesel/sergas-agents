# Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Sergas Super Account Manager to production environments. The system supports multiple deployment strategies including Docker, Kubernetes, and traditional server deployments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Deployment Methods](#deployment-methods)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Monitoring Setup](#monitoring-setup)
8. [Security Hardening](#security-hardening)
9. [Post-Deployment Validation](#post-deployment-validation)
10. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Infrastructure Requirements

- **Compute**: 4+ vCPUs, 16GB+ RAM per instance
- **Storage**: 100GB+ SSD for application and logs
- **Database**: PostgreSQL 14+ with 50GB+ storage
- **Cache**: Redis 6+ with 4GB+ memory
- **Network**: TLS 1.3 support, public IP or load balancer
- **Container Runtime**: Docker 24+ or Kubernetes 1.27+

### Software Requirements

- Python 3.14+
- Docker 24.0+ and Docker Compose 2.20+
- PostgreSQL 14+ (can be containerized)
- Redis 6+ (can be containerized)
- Nginx 1.24+ (optional, for reverse proxy)

### Access Requirements

- **Zoho CRM**: OAuth client credentials with API access
- **Anthropic**: API key for Claude Agent SDK
- **AWS** (optional): Credentials for Secrets Manager
- **Domain**: SSL certificate for HTTPS

### Development Tools

```bash
# Install required tools
pip install --upgrade pip
pip install poetry alembic
```

---

## Architecture Overview

### Production Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer (Nginx)                    │
│                    TLS Termination (443)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│  App Instance 1 │            │  App Instance 2 │
│  (Docker/K8s)   │            │  (Docker/K8s)   │
│  • FastAPI      │            │  • FastAPI      │
│  • Agents       │            │  • Agents       │
│  • Workers      │            │  • Workers      │
└────────┬────────┘            └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│  PostgreSQL DB  │            │   Redis Cache   │
│  (Primary)      │            │  • Sessions     │
│  • Agent Data   │            │  • Rate Limits  │
│  • Audit Logs   │            │  • Dedup        │
└─────────────────┘            └─────────────────┘
         │
┌────────▼────────┐
│  Monitoring     │
│  • Prometheus   │
│  • Grafana      │
│  • AlertManager │
└─────────────────┘
```

### Component Responsibilities

| Component | Purpose | Scaling Strategy |
|-----------|---------|------------------|
| **Load Balancer** | Traffic distribution, TLS termination | Active-passive HA |
| **App Instances** | Agent orchestration, API endpoints | Horizontal (2-10 instances) |
| **PostgreSQL** | Persistent data storage | Primary-replica replication |
| **Redis** | Session cache, rate limiting | Sentinel for HA |
| **Monitoring** | Metrics, logs, alerts | Standalone cluster |

---

## Pre-Deployment Checklist

### Environment Preparation

- [ ] Production environment variables configured
- [ ] SSL certificates obtained and validated
- [ ] Database credentials generated and secured
- [ ] Zoho OAuth credentials created and tested
- [ ] Anthropic API key validated
- [ ] Network firewall rules configured
- [ ] DNS records created and propagated
- [ ] Backup and restore procedures tested
- [ ] Monitoring infrastructure ready
- [ ] Incident response plan documented

### Code Preparation

- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage above 80%
- [ ] Security scan completed (no critical issues)
- [ ] Dependencies updated and audited
- [ ] Database migrations tested
- [ ] Configuration validated
- [ ] Documentation up to date
- [ ] Release notes prepared
- [ ] Rollback plan documented

### Security Preparation

- [ ] Secrets stored in secure vault (AWS Secrets Manager)
- [ ] OAuth tokens encrypted at rest
- [ ] TLS certificates valid and auto-renewal configured
- [ ] IAM roles/policies configured (least privilege)
- [ ] Audit logging enabled
- [ ] PII detection and masking verified
- [ ] Rate limiting configured
- [ ] CORS policies validated
- [ ] Security headers configured

---

## Deployment Methods

### Method 1: Docker Compose (Recommended for Staging)

**Best for**: Small deployments, staging environments, single-server setups

#### Step 1: Prepare Environment

```bash
# Clone repository
git clone https://github.com/sergas/super-account-manager.git
cd super-account-manager

# Checkout production tag
git checkout v1.0.0

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or vim, use your preferred editor
```

#### Step 2: Configure Environment

Edit `.env` with production values:

```bash
# Critical production settings
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=sergas_prod
DATABASE_USER=sergas_prod_user
DATABASE_PASSWORD=<strong-password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password>

# Zoho CRM
ZOHO_MCP_CLIENT_ID=<your-client-id>
ZOHO_MCP_CLIENT_SECRET=<your-client-secret>
ZOHO_SDK_REFRESH_TOKEN=<your-refresh-token>

# Claude API
ANTHROPIC_API_KEY=<your-api-key>

# Security
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
SECRETS_MANAGER_ENABLED=true
AWS_REGION=us-east-1

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

#### Step 3: Initialize Database

```bash
# Start database only
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
docker-compose run --rm app alembic upgrade head

# Verify migrations
docker-compose exec postgres psql -U sergas_prod_user -d sergas_prod -c "\dt"
```

#### Step 4: Deploy Services

```bash
# Build and start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f app

# Verify health
curl http://localhost:8000/health
```

#### Step 5: Verify Deployment

```bash
# Check application health
curl http://localhost:8000/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "database": "connected",
#   "redis": "connected",
#   "zoho": "authenticated"
# }

# Check metrics
curl http://localhost:9090/metrics | grep sergas_

# Access Grafana
open http://localhost:3000
# Default credentials: admin/admin (change immediately)
```

---

### Method 2: Kubernetes (Recommended for Production)

**Best for**: Large deployments, high availability, auto-scaling

#### Step 1: Prepare Kubernetes Cluster

```bash
# Verify cluster access
kubectl cluster-info

# Create namespace
kubectl create namespace sergas-prod

# Set default namespace
kubectl config set-context --current --namespace=sergas-prod

# Verify namespace
kubectl get namespace sergas-prod
```

#### Step 2: Configure Secrets

```bash
# Create secret for environment variables
kubectl create secret generic sergas-env \
  --from-file=.env=.env.production \
  --dry-run=client -o yaml | kubectl apply -f -

# Create secret for Zoho credentials
kubectl create secret generic zoho-credentials \
  --from-literal=client-id=<client-id> \
  --from-literal=client-secret=<client-secret> \
  --from-literal=refresh-token=<refresh-token> \
  --dry-run=client -o yaml | kubectl apply -f -

# Create secret for Anthropic API key
kubectl create secret generic anthropic-credentials \
  --from-literal=api-key=<api-key> \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify secrets
kubectl get secrets
```

#### Step 3: Deploy Database

```bash
# Apply PostgreSQL configuration
kubectl apply -f kubernetes/base/postgres-statefulset.yaml
kubectl apply -f kubernetes/base/postgres-service.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Run database migrations
kubectl run migration-job --rm -i --tty \
  --image=sergas/super-account-manager:1.0.0 \
  --restart=Never \
  --env-from=secretref/sergas-env \
  -- alembic upgrade head
```

#### Step 4: Deploy Redis

```bash
# Apply Redis configuration
kubectl apply -f kubernetes/base/redis-statefulset.yaml
kubectl apply -f kubernetes/base/redis-service.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s

# Test Redis connection
kubectl run redis-test --rm -i --tty \
  --image=redis:7-alpine \
  --restart=Never \
  -- redis-cli -h redis -a <redis-password> ping
```

#### Step 5: Deploy Application

```bash
# Apply application deployment
kubectl apply -f kubernetes/overlays/production/deployment.yaml
kubectl apply -f kubernetes/overlays/production/service.yaml
kubectl apply -f kubernetes/overlays/production/ingress.yaml

# Wait for rollout
kubectl rollout status deployment/sergas-app

# Verify pods are running
kubectl get pods -l app=sergas-app

# Check logs
kubectl logs -l app=sergas-app -f
```

#### Step 6: Configure Ingress

```bash
# Install ingress controller (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Apply TLS certificate
kubectl create secret tls sergas-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem

# Verify ingress
kubectl get ingress
kubectl describe ingress sergas-ingress

# Get external IP
kubectl get svc -n ingress-nginx
```

#### Step 7: Deploy Monitoring

```bash
# Apply Prometheus
kubectl apply -f kubernetes/base/prometheus-config.yaml
kubectl apply -f kubernetes/base/prometheus-deployment.yaml

# Apply Grafana
kubectl apply -f kubernetes/base/grafana-config.yaml
kubectl apply -f kubernetes/base/grafana-deployment.yaml

# Verify monitoring stack
kubectl get pods -l app=prometheus
kubectl get pods -l app=grafana

# Access Grafana
kubectl port-forward svc/grafana 3000:3000
open http://localhost:3000
```

---

### Method 3: Traditional Server Deployment

**Best for**: Bare metal, VMs, existing infrastructure

#### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.14 python3.14-venv postgresql-14 redis-server nginx certbot

# Create application user
sudo useradd -m -s /bin/bash sergas
sudo usermod -aG sudo sergas

# Switch to application user
sudo su - sergas
```

#### Step 2: Install Application

```bash
# Clone repository
git clone https://github.com/sergas/super-account-manager.git
cd super-account-manager

# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env
```

#### Step 3: Configure Database

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql << EOF
CREATE DATABASE sergas_prod;
CREATE USER sergas_prod_user WITH PASSWORD '<strong-password>';
GRANT ALL PRIVILEGES ON DATABASE sergas_prod TO sergas_prod_user;
\q
EOF

# Exit postgres user
exit

# Run migrations
source venv/bin/activate
alembic upgrade head
```

#### Step 4: Configure Systemd Service

Create `/etc/systemd/system/sergas-app.service`:

```ini
[Unit]
Description=Sergas Super Account Manager
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=sergas
Group=sergas
WorkingDirectory=/home/sergas/super-account-manager
Environment="PATH=/home/sergas/super-account-manager/venv/bin"
EnvironmentFile=/home/sergas/super-account-manager/.env
ExecStart=/home/sergas/super-account-manager/venv/bin/uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --log-config logging.conf
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sergas-app
sudo systemctl start sergas-app
sudo systemctl status sergas-app
```

#### Step 5: Configure Nginx

Create `/etc/nginx/sites-available/sergas`:

```nginx
upstream sergas_backend {
    least_conn;
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 10M;

    location / {
        proxy_pass http://sergas_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /metrics {
        deny all;
        return 403;
    }
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/sergas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## Configuration

### Environment Variables

See `.env.example` for complete reference. Critical variables:

```bash
# Core
ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<generate-securely>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://:<password>@host:6379/0
REDIS_MAX_CONNECTIONS=50

# Zoho
ZOHO_MCP_CLIENT_ID=<client-id>
ZOHO_MCP_CLIENT_SECRET=<client-secret>
ZOHO_SDK_REFRESH_TOKEN=<refresh-token>

# Claude
ANTHROPIC_API_KEY=<api-key>
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Security
SECRETS_MANAGER_ENABLED=true
AWS_REGION=us-east-1
ENABLE_AUDIT_LOGGING=true

# Performance
MAX_CONCURRENT_ACCOUNTS=50
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
RETRY_MAX_ATTEMPTS=3
```

### Security Configuration

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate webhook secret
python -c "import secrets; print(secrets.token_hex(32))"

# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name sergas/production/app-secrets \
  --secret-string file://secrets.json
```

---

## Database Setup

### Initial Schema Creation

```bash
# Run all migrations
alembic upgrade head

# Verify schema
psql -d sergas_prod -c "\dt"

# Check migration history
alembic current
alembic history
```

### Database Performance Tuning

Add to `postgresql.conf`:

```ini
# Connection Settings
max_connections = 200
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 1GB
max_wal_size = 4GB

# Autovacuum
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 10s
```

### Backup Configuration

```bash
# Create backup script
cat > /usr/local/bin/backup-sergas-db.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/sergas"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sergas_prod_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

pg_dump -U sergas_prod_user -d sergas_prod | gzip > "$BACKUP_FILE"

# Keep last 30 days
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp "$BACKUP_FILE" s3://sergas-backups/database/

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x /usr/local/bin/backup-sergas-db.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-sergas-db.sh" | crontab -
```

---

## Monitoring Setup

### Prometheus Configuration

See `/docs/production/monitoring_guide.md` for complete setup.

Quick verification:

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=sergas_agent_sessions_total' | jq
```

### Grafana Dashboards

Import pre-built dashboards:

```bash
# Import from file
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @grafana/dashboards/sergas-overview.json
```

---

## Security Hardening

### Application Security

```bash
# Enable security headers
# Add to environment
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60

# Configure CORS
CORS_ORIGINS=https://your-domain.com
CORS_ALLOW_CREDENTIALS=true

# Enable audit logging
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_PATH=/var/log/sergas/audit.log
```

### Network Security

```bash
# Configure firewall (ufw)
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable

# Block direct access to app port
sudo ufw deny 8000/tcp
```

### Secrets Management

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name sergas/production/zoho \
  --secret-string '{
    "client_id": "xxx",
    "client_secret": "xxx",
    "refresh_token": "xxx"
  }'

# Update environment to use Secrets Manager
SECRETS_MANAGER_ENABLED=true
AWS_REGION=us-east-1
```

---

## Post-Deployment Validation

### Automated Health Checks

```bash
#!/bin/bash
# health-check.sh

API_URL="https://your-domain.com"

# Check API health
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
if [ $response -ne 200 ]; then
    echo "Health check failed: HTTP $response"
    exit 1
fi

# Check database connectivity
response=$(curl -s $API_URL/health | jq -r '.database')
if [ "$response" != "connected" ]; then
    echo "Database check failed"
    exit 1
fi

# Check Redis connectivity
response=$(curl -s $API_URL/health | jq -r '.redis')
if [ "$response" != "connected" ]; then
    echo "Redis check failed"
    exit 1
fi

# Check Zoho authentication
response=$(curl -s $API_URL/health | jq -r '.zoho')
if [ "$response" != "authenticated" ]; then
    echo "Zoho authentication failed"
    exit 1
fi

echo "All health checks passed"
exit 0
```

### Manual Verification Steps

1. **API Endpoints**
   ```bash
   # Health check
   curl https://your-domain.com/health

   # API version
   curl https://your-domain.com/api/v1/version

   # Metrics (should be blocked from public)
   curl https://your-domain.com/metrics
   ```

2. **Database Connectivity**
   ```bash
   psql -h <db-host> -U sergas_prod_user -d sergas_prod -c "SELECT NOW();"
   ```

3. **Redis Connectivity**
   ```bash
   redis-cli -h <redis-host> -a <password> ping
   ```

4. **Monitoring**
   - Access Grafana: https://your-domain.com:3000
   - Check all dashboards load correctly
   - Verify metrics are being collected

5. **Logs**
   ```bash
   # Application logs
   journalctl -u sergas-app -f

   # Nginx access logs
   tail -f /var/log/nginx/access.log

   # Nginx error logs
   tail -f /var/log/nginx/error.log
   ```

---

## Rollback Procedures

### Quick Rollback (Docker/Kubernetes)

```bash
# Kubernetes: Rollback to previous version
kubectl rollout undo deployment/sergas-app

# Verify rollback
kubectl rollout status deployment/sergas-app

# Docker Compose: Use previous image
docker-compose down
docker-compose up -d --no-build --force-recreate
```

### Database Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision-id>

# Restore from backup
gunzip < /var/backups/sergas/sergas_prod_20241019_020000.sql.gz | \
  psql -U sergas_prod_user -d sergas_prod
```

### Full System Rollback

1. Stop application
2. Restore database from backup
3. Deploy previous application version
4. Verify functionality
5. Monitor for errors

---

## Troubleshooting

### Common Issues

**Application won't start**
```bash
# Check logs
journalctl -u sergas-app -n 100

# Verify environment variables
systemctl show sergas-app --property=Environment

# Test configuration
source venv/bin/activate
python -c "from src.config import settings; print(settings.dict())"
```

**Database connection errors**
```bash
# Test connectivity
psql -h <host> -U <user> -d <db> -c "SELECT 1;"

# Check credentials
grep DATABASE_ .env

# Verify firewall
sudo ufw status
```

**High memory usage**
```bash
# Check process memory
ps aux | grep python

# Check database connections
psql -d sergas_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Restart services
sudo systemctl restart sergas-app
```

---

## Support

For deployment assistance:

- **Documentation**: `/docs/production/`
- **Runbooks**: `/docs/runbooks/`
- **Issues**: https://github.com/sergas/super-account-manager/issues
- **Email**: devops@sergas.com

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas DevOps Team
