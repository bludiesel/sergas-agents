# 🚀 Setup & Deployment

<div align="center">

![Deployment](https://img.shields.io/badge/Deployment-Ready-green?style=for-the-badge&logo=rocket)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestrated-purple?style=for-the-badge&logo=kubernetes)
![CI/CD](https://img.shields.io/badge/CI/CD-Automated-orange?style=for-the-badge&logo=github)

**Production-Ready Deployment Guide**

</div>

---

## 🎯 Overview

This guide provides comprehensive instructions for setting up, deploying, and maintaining the Sergas Super Account Manager system in various environments. From local development to production deployment, we cover all aspects of infrastructure, configuration, and operational procedures.

### ✨ Key Features

- **🐳 Containerized Deployment**: Docker and Kubernetes ready
- **🔄 Automated CI/CD**: GitHub Actions pipeline
- **🛡️ Security-First**: Secrets management and compliance
- **📊 Monitoring**: Comprehensive observability stack
- **🔄 Zero-Downtime**: Blue-green deployment strategy

---

## 🏗️ Architecture Overview

<div align="center">

```mermaid
graph TB
    subgraph "🌐 Production Environment"
        LB[Load Balancer]
        K8S[Kubernetes Cluster]
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        COGNEE[Cognee Services]
    end
    
    subgraph "🔧 CI/CD Pipeline"
        GH[GitHub Actions]
        REG[Container Registry]
        STAGE[Staging Environment]
        PROD[Production Environment]
    end
    
    subgraph "🛡️ Security Layer"
        SM[Secrets Manager]
        VAULT[HashiCorp Vault]
        MON[Monitoring]
        ALERT[Alerting]
    end
    
    LB --> K8S
    K8S --> DB
    K8S --> REDIS
    K8S --> COGNEE
    
    GH --> REG
    REG --> STAGE
    STAGE --> PROD
    
    K8S --> SM
    SM --> VAULT
    K8S --> MON
    MON --> ALERT
```

</div>

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**
- **Python 3.14+**
- **Git**
- **Zoho CRM Account** with API access
- **Anthropic API Key**

### Local Development Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/mohammadabdelrahman/sergas-agents.git
   cd sergas-agents
   ```

2. **Environment Setup**
   ```bash
   # Create virtual environment
   python3.14 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

4. **Start Services**
   ```bash
   # Start supporting services
   docker-compose up -d postgres redis cognee
   
   # Run database migrations
   alembic upgrade head
   
   # Start the application
   python src/main.py
   ```

---

## 🔧 Environment Configuration

### Development Environment

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/sergas_dev
REDIS_URL=redis://localhost:6379/0

# APIs
ANTHROPIC_API_KEY=sk-ant-dev-xxx
ZOHO_CLIENT_ID=1000.dev.xxx
ZOHO_CLIENT_SECRET=dev_secret
ZOHO_REFRESH_TOKEN=1000.dev.refresh

# Cognee
COGNEE_API_URL=http://localhost:8000
COGNEE_API_KEY=dev_cognee_key
COGNEE_WORKSPACE_ID=sergas_dev
```

### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@staging-db:5432/sergas_staging
REDIS_URL=redis://staging-redis:6379/0

# APIs
ANTHROPIC_API_KEY=sk-ant-staging-xxx
ZOHO_CLIENT_ID=1000.staging.xxx
ZOHO_CLIENT_SECRET=staging_secret
ZOHO_REFRESH_TOKEN=1000.staging.refresh

# Cognee
COGNEE_API_URL=http://staging-cognee:8000
COGNEE_API_KEY=staging_cognee_key
COGNEE_WORKSPACE_ID=sergas_staging
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Database (from secrets manager)
DATABASE_URL=${VAULT_DATABASE_URL}
REDIS_URL=${VAULT_REDIS_URL}

# APIs (from secrets manager)
ANTHROPIC_API_KEY=${VAULT_ANTHROPIC_API_KEY}
ZOHO_CLIENT_ID=${VAULT_ZOHO_CLIENT_ID}
ZOHO_CLIENT_SECRET=${VAULT_ZOHO_CLIENT_SECRET}
ZOHO_REFRESH_TOKEN=${VAULT_ZOHO_REFRESH_TOKEN}

# Cognee (from secrets manager)
COGNEE_API_URL=${VAULT_COGNEE_API_URL}
COGNEE_API_KEY=${VAULT_COGNEE_API_KEY}
COGNEE_WORKSPACE_ID=sergas_production
```

---

## 🐳 Docker Deployment

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
      - cognee
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: sergas
      POSTGRES_USER: sergas
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  cognee:
    build: ./docker/cognee
    ports:
      - "8001:8000"
    environment:
      - COGNEE_DB_URL=postgresql://sergas:${POSTGRES_PASSWORD}@postgres:5432/cognee
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-core.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1000 sergas && chown -R sergas:sergas /app
USER sergas

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "src/main.py"]
```

### Build and Deploy

```bash
# Build image
docker build -t sergas-agents:latest .

# Run with docker-compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

---

## ☸️ Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sergas-agents
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sergas-config
  namespace: sergas-agents
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  COGNEE_API_URL: "http://cognee-service:8000"
  COGNEE_WORKSPACE_ID: "sergas_production"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: sergas-secrets
  namespace: sergas-agents
type: Opaque
data:
  DATABASE_URL: <base64-encoded-url>
  REDIS_URL: <base64-encoded-url>
  ANTHROPIC_API_KEY: <base64-encoded-key>
  ZOHO_CLIENT_ID: <base64-encoded-id>
  ZOHO_CLIENT_SECRET: <base64-encoded-secret>
  ZOHO_REFRESH_TOKEN: <base64-encoded-token>
  COGNEE_API_KEY: <base64-encoded-key>
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sergas-agents
  namespace: sergas-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sergas-agents
  template:
    metadata:
      labels:
        app: sergas-agents
    spec:
      containers:
      - name: sergas-agents
        image: sergas-agents:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: sergas-config
        - secretRef:
            name: sergas-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service and Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sergas-service
  namespace: sergas-agents
spec:
  selector:
    app: sergas-agents
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sergas-ingress
  namespace: sergas-agents
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - sergas-agents.company.com
    secretName: sergas-tls
  rules:
  - host: sergas-agents.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sergas-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n sergas-agents

# Check logs
kubectl logs -f deployment/sergas-agents -n sergas-agents

# Scale deployment
kubectl scale deployment sergas-agents --replicas=5 -n sergas-agents
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=80
      - name: Security scan
        run: bandit -r src/ -ll

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: |
          docker build -t sergas-agents:${{ github.sha }} .
          docker tag sergas-agents:${{ github.sha }} sergas-agents:latest
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push sergas-agents:${{ github.sha }}
          docker push sergas-agents:latest

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          kubectl config use-context staging
          kubectl set image deployment/sergas-agents sergas-agents=sergas-agents:${{ github.sha }} -n sergas-agents
          kubectl rollout status deployment/sergas-agents -n sergas-agents

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          kubectl config use-context production
          kubectl set image deployment/sergas-agents sergas-agents=sergas-agents:${{ github.sha }} -n sergas-agents
          kubectl rollout status deployment/sergas-agents -n sergas-agents
```

### Blue-Green Deployment

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

NEW_VERSION=$1
CURRENT_VERSION=$(kubectl get deployment sergas-agents -n sergas-agents -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)

echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"

# Deploy new version to green environment
kubectl set image deployment/sergas-agents-green sergas-agents=sergas-agents:$NEW_VERSION -n sergas-agents
kubectl rollout status deployment/sergas-agents-green -n sergas-agents

# Run health checks
kubectl exec -it deployment/sergas-agents-green -n sergas-agents -- python scripts/health-check.py

# Switch traffic to green
kubectl patch service sergas-service -n sergas-agents -p '{"spec":{"selector":{"version":"green"}}}'

# Wait for traffic to stabilize
sleep 30

# Verify green is healthy
kubectl exec -it deployment/sergas-agents-green -n sergas-agents -- python scripts/health-check.py

# Scale down blue
kubectl scale deployment sergas-agents-blue --replicas=0 -n sergas-agents

echo "Deployment completed successfully"
```

---

## 📊 Monitoring & Observability

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sergas-agents'
    static_configs:
      - targets: ['sergas-service:80']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Sergas Agents Dashboard",
    "panels": [
      {
        "title": "Agent Sessions",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(agent_sessions_total[5m])",
            "legendFormat": "Sessions/sec"
          }
        ]
      },
      {
        "title": "Tool Call Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(agent_tool_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(agent_errors_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
# monitoring/alerts.yml
groups:
- name: sergas-agents
  rules:
  - alert: HighErrorRate
    expr: rate(agent_errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(agent_tool_duration_seconds_bucket[5m])) > 5
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High latency detected"
      description: "95th percentile latency is {{ $value }} seconds"

  - alert: ServiceDown
    expr: up{job="sergas-agents"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "Sergas Agents service is not responding"
```

---

## 🛡️ Security & Compliance

### Secrets Management

```bash
# Store secrets in HashiCorp Vault
vault kv put secret/sergas-agents \
  database_url="postgresql://user:pass@db:5432/sergas" \
  anthropic_api_key="sk-ant-xxx" \
  zoho_client_secret="secret" \
  cognee_api_key="cognee_key"

# Configure Kubernetes secret
kubectl create secret generic sergas-secrets \
  --from-literal=database_url="$(vault kv get -field=database_url secret/sergas-agents)" \
  --from-literal=anthropic_api_key="$(vault kv get -field=anthropic_api_key secret/sergas-agents)" \
  -n sergas-agents
```

### Network Policies

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sergas-network-policy
  namespace: sergas-agents
spec:
  podSelector:
    matchLabels:
      app: sergas-agents
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Policy

```yaml
# k8s/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: sergas-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

---

## 🔧 Maintenance & Operations

### Health Checks

```python
# scripts/health-check.py
import requests
import sys

def check_health():
    """Comprehensive health check for the application."""
    checks = [
        check_api_health(),
        check_database_connection(),
        check_redis_connection(),
        check_cognee_connection(),
        check_zoho_api()
    ]
    
    if all(checks):
        print("All health checks passed")
        sys.exit(0)
    else:
        print("Health checks failed")
        sys.exit(1)

def check_api_health():
    """Check if the API is responding."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_database_connection():
    """Check database connectivity."""
    # Implementation details...
    return True

# Run health check
if __name__ == "__main__":
    check_health()
```

### Backup Scripts

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump $DATABASE_URL > $BACKUP_DIR/postgres_backup.sql

# Backup Redis
redis-cli --rdb $BACKUP_DIR/redis_backup.rdb

# Backup application logs
tar -czf $BACKUP_DIR/logs.tar.gz /app/logs/

# Upload to S3
aws s3 cp $BACKUP_DIR s3://sergas-backups/ --recursive

# Cleanup old backups (keep 30 days)
find /backups -type d -mtime +30 -exec rm -rf {} \;
```

### Log Management

```yaml
# k8s/logging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: sergas-agents
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/sergas-agents*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name sergas-agents
    </match>
```

---

## 📚 Documentation

- **[Environment Setup](ENVIRONMENT_SETUP.md)** - Detailed environment configuration
- **[Testing Guide](TESTING_GUIDE.md)** - Testing and validation procedures
- **[Monitoring Guide](MONITORING_GUIDE.md)** - Observability and alerting setup
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🔗 Related Documentation

- [Main README](../../README.md) - Project overview
- [Agent Architecture](../agents/README.md) - Agent system design
- [Zoho Integration](../integrations/README.md) - CRM integration guide
- [Cognee Integration](../memory/README.md) - Memory system integration

---

<div align="center">

**Part of the Sergas Super Account Manager System**

[← Back to Main README](../../README.md) • [Agent Architecture →](../agents/README.md)

</div>