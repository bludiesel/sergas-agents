# Runbook: Horizontal Scaling

**Service**: Sergas Super Account Manager
**Component**: Application Infrastructure
**Severity**: Medium
**Last Updated**: 2025-10-19

## Overview

This runbook covers procedures for horizontal scaling of the Sergas Super Account Manager system to handle increased load.

## When to Scale

### Scale Up Triggers

- **CPU Utilization** >70% sustained for 10+ minutes
- **Memory Utilization** >80% sustained for 10+ minutes
- **Request Latency** p95 >2 seconds
- **Queue Depth** >100 pending tasks
- **Error Rate** >1% due to resource exhaustion

### Scale Down Triggers

- **CPU Utilization** <30% for 30+ minutes
- **Memory Utilization** <50% for 30+ minutes
- **Request Latency** p95 <500ms
- **Low Traffic** during off-peak hours

## Scaling Procedures

### Manual Scaling (Immediate)

#### Scale Application Instances

```bash
# Check current instance count
kubectl get deployment sergas-app -o jsonpath='{.spec.replicas}'

# Scale up to 5 instances
kubectl scale deployment sergas-app --replicas=5

# Verify scaling
kubectl rollout status deployment/sergas-app

# Check pod distribution
kubectl get pods -l app=sergas-app -o wide
```

#### Scale Database Connections

```bash
# Increase PostgreSQL max_connections
psql -U postgres -c "ALTER SYSTEM SET max_connections = 300;"
psql -U postgres -c "SELECT pg_reload_conf();"

# Update application connection pool
kubectl edit configmap sergas-config
# Change: DATABASE_POOL_SIZE: "50"

# Restart application to pick up new config
kubectl rollout restart deployment/sergas-app
```

#### Scale Redis

```bash
# For Redis Cluster: Add nodes
redis-cli --cluster add-node new-node-ip:6379 existing-node-ip:6379

# For Redis Sentinel: Add replica
redis-cli -h sentinel-host SENTINEL MONITOR mymaster redis-master-ip 6379 2

# Verify cluster status
redis-cli --cluster check redis-master-ip:6379
```

### Auto-Scaling Configuration

#### Horizontal Pod Autoscaler (HPA)

```yaml
# k8s/hpa-sergas-app.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sergas-app-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sergas-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    # CPU-based scaling
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Memory-based scaling
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Custom metric: Request latency
    - type: Pods
      pods:
        metric:
          name: http_request_duration_p95
        target:
          type: AverageValue
          averageValue: "2000m"  # 2 seconds

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
        - type: Pods
          value: 2
          periodSeconds: 60
      selectPolicy: Max

    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 25
          periodSeconds: 60
        - type: Pods
          value: 1
          periodSeconds: 60
      selectPolicy: Min
```

Deploy HPA:

```bash
kubectl apply -f k8s/hpa-sergas-app.yml

# Verify HPA status
kubectl get hpa sergas-app-hpa

# Watch HPA behavior
kubectl get hpa sergas-app-hpa --watch
```

### Database Scaling

#### Read Replicas (PostgreSQL)

```bash
# Create read replica (AWS RDS)
aws rds create-db-instance-read-replica \
  --db-instance-identifier sergas-db-replica-1 \
  --source-db-instance-identifier sergas-db-primary \
  --db-instance-class db.r6g.large \
  --publicly-accessible false \
  --region us-east-1

# Wait for replica to be available
aws rds wait db-instance-available \
  --db-instance-identifier sergas-db-replica-1

# Update application to use replica for read queries
kubectl edit configmap sergas-config
# Add: DATABASE_READ_URL: "postgresql://sergas-db-replica-1:5432/sergas_agent_db"

# Restart application
kubectl rollout restart deployment/sergas-app
```

#### Connection Pooling (PgBouncer)

```yaml
# k8s/pgbouncer-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
        - name: pgbouncer
          image: pgbouncer/pgbouncer:latest
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRESQL_HOST
              value: "postgres-primary"
            - name: POSTGRESQL_PORT
              value: "5432"
            - name: POSTGRESQL_DATABASE
              value: "sergas_agent_db"
            - name: PGBOUNCER_POOL_MODE
              value: "transaction"
            - name: PGBOUNCER_MAX_CLIENT_CONN
              value: "1000"
            - name: PGBOUNCER_DEFAULT_POOL_SIZE
              value: "25"
---
apiVersion: v1
kind: Service
metadata:
  name: pgbouncer
spec:
  selector:
    app: pgbouncer
  ports:
    - port: 5432
      targetPort: 5432
```

Deploy PgBouncer:

```bash
kubectl apply -f k8s/pgbouncer-deployment.yml

# Update application database URL
kubectl edit configmap sergas-config
# Change: DATABASE_URL: "postgresql://pgbouncer:5432/sergas_agent_db"

kubectl rollout restart deployment/sergas-app
```

### Load Balancer Scaling

#### Application Load Balancer (ALB)

```bash
# Check current ALB capacity
aws elbv2 describe-load-balancers \
  --load-balancer-arns arn:aws:elasticloadbalancing:...

# ALB automatically scales, but verify target group health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# Increase target group deregistration delay for graceful scaling
aws elbv2 modify-target-group-attribute \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --attributes Key=deregistration_delay.timeout_seconds,Value=300
```

## Scaling Validation

### Test Scaled Infrastructure

```bash
# 1. Verify all instances are healthy
kubectl get pods -l app=sergas-app
kubectl describe deployment sergas-app

# 2. Run load test
./scripts/performance/load_test.sh --users=100 --duration=300

# Expected results:
# - Response time p95 <2s
# - Error rate <0.1%
# - All instances serving traffic

# 3. Check metrics
curl http://prometheus:9090/api/v1/query?query=rate(http_requests_total[5m])

# 4. Verify database connections
psql -h postgres -U sergas_user -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Should be: (instance_count * pool_size) ± 20%
```

### Monitor After Scaling

```bash
# Watch key metrics for 15 minutes
watch -n 10 './scripts/monitoring/check_health.sh'

# Key metrics to monitor:
# - CPU utilization (should be <70%)
# - Memory utilization (should be <80%)
# - Request latency p95 (should be <2s)
# - Error rate (should be <0.5%)
# - Database connection count (should be stable)
```

## Capacity Planning

### Current Capacity Baseline

```bash
# Document current capacity
cat > docs/capacity/baseline.md <<EOF
# Capacity Baseline - $(date +%Y-%m-%d)

## Infrastructure
- Application instances: 2
- Instance type: t3.medium (2 vCPU, 4GB RAM)
- Database: db.r6g.large (2 vCPU, 16GB RAM)
- Redis: cache.r6g.large (2 vCPU, 13GB RAM)

## Performance Metrics
- Requests per second: 100
- Average response time: 800ms
- P95 response time: 1.5s
- P99 response time: 2.8s
- Error rate: 0.05%

## Resource Utilization
- CPU: 45% average
- Memory: 60% average
- Database connections: 25 active
- Redis memory: 40% used

## Cost
- Monthly infrastructure: \$500
- Cost per 1M requests: \$2.50
EOF
```

### Growth Projections

```bash
# Calculate capacity for user growth
cat > docs/capacity/projections.md <<EOF
# Capacity Projections - 2025

## User Growth Scenarios

### Scenario 1: Linear Growth (10% monthly)
- Month 3: 65 users → 3 instances
- Month 6: 85 users → 4 instances
- Month 12: 140 users → 6 instances

### Scenario 2: Hockey Stick Growth (30% monthly)
- Month 3: 85 users → 4 instances
- Month 6: 180 users → 8 instances
- Month 12: 520 users → 20 instances

## Scaling Actions Required

### At 75 users (Month 4)
- [ ] Add 1 application instance
- [ ] Add PostgreSQL read replica
- [ ] Increase Redis memory to 26GB

### At 100 users (Month 6)
- [ ] Upgrade to t3.large instances
- [ ] Add 2 more application instances
- [ ] Consider Redis cluster (3 nodes)

### At 200 users (Month 10)
- [ ] Upgrade database to db.r6g.xlarge
- [ ] Implement application-level caching
- [ ] Add CDN for static assets
EOF
```

## Rollback Procedures

### Scale Down

```bash
# 1. Gradually reduce instance count
kubectl scale deployment sergas-app --replicas=3

# 2. Wait 10 minutes, monitor metrics
sleep 600
./scripts/monitoring/check_health.sh

# 3. If stable, continue scaling down
kubectl scale deployment sergas-app --replicas=2

# 4. Update HPA min replicas if needed
kubectl patch hpa sergas-app-hpa -p '{"spec":{"minReplicas":2}}'
```

### Emergency Scale-Up

```bash
# If system is overwhelmed, scale up immediately
kubectl scale deployment sergas-app --replicas=10

# Add database connections
psql -U postgres -c "ALTER SYSTEM SET max_connections = 500;"

# Disable HPA to prevent interference
kubectl delete hpa sergas-app-hpa

# After incident, re-enable HPA
kubectl apply -f k8s/hpa-sergas-app.yml
```

## Monitoring & Alerts

### Scaling Metrics

```promql
# Instance count
count(kube_pod_status_ready{pod=~"sergas-app-.*"})

# CPU utilization
avg(rate(container_cpu_usage_seconds_total{pod=~"sergas-app-.*"}[5m])) * 100

# Memory utilization
avg(container_memory_working_set_bytes{pod=~"sergas-app-.*"} / container_spec_memory_limit_bytes) * 100

# Request rate per instance
sum(rate(http_requests_total[5m])) / count(kube_pod_status_ready{pod=~"sergas-app-.*"})
```

### Capacity Alerts

```yaml
# config/alerts/capacity_alerts.yml
groups:
  - name: capacity_planning
    rules:
      - alert: ApproachingMaxCapacity
        expr: (kube_deployment_status_replicas{deployment="sergas-app"} / kube_deployment_spec_replicas_max) > 0.8
        for: 10m
        severity: warning
        annotations:
          summary: "Approaching maximum scaling capacity"

      - alert: HighInstanceUtilization
        expr: avg(rate(container_cpu_usage_seconds_total{pod=~"sergas-app-.*"}[5m])) > 0.8
        for: 10m
        severity: warning
        annotations:
          summary: "Consider scaling up or optimizing application"
```

## Cost Optimization

### Right-Sizing

```bash
# Analyze instance utilization over 7 days
aws ce get-cost-and-usage \
  --time-period Start=2025-10-12,End=2025-10-19 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=INSTANCE_TYPE

# Consider Savings Plans or Reserved Instances for baseline capacity
# Use Spot Instances for burst capacity
```

## Related Runbooks

- `/docs/runbooks/DATABASE_ISSUES.md`
- `/docs/runbooks/incident_response.md`

## References

- Kubernetes HPA: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- AWS Auto Scaling: https://aws.amazon.com/autoscaling/

---

**Last Capacity Review**: 2025-10-19
**Next Review**: 2025-11-19
