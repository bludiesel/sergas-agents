# Scaling Runbook

## Overview

This runbook provides procedures for scaling the Sergas Agents system to handle increased load, both proactively and reactively.

## Scaling Dimensions

### Vertical Scaling (Scale Up)
Increasing resources for existing instances

### Horizontal Scaling (Scale Out)
Adding more instances of services

### Data Scaling
Expanding database and storage capacity

---

## Load Indicators

### When to Scale

#### CPU Utilization
- **Warning**: > 70% sustained for 15+ minutes
- **Critical**: > 85% sustained for 5+ minutes
- **Action**: Scale horizontally or vertically

#### Memory Utilization
- **Warning**: > 80% sustained
- **Critical**: > 90% sustained
- **Action**: Scale vertically or optimize

#### Request Queue Depth
- **Warning**: > 100 requests queued
- **Critical**: > 500 requests queued
- **Action**: Scale horizontally

#### Response Time
- **Warning**: p95 > 1000ms
- **Critical**: p95 > 2000ms
- **Action**: Scale or optimize

#### Error Rate
- **Warning**: > 1% errors
- **Critical**: > 5% errors
- **Action**: Scale or fix bugs

---

## Monitoring Commands

### Check Current Load
```bash
# System metrics
python scripts/monitoring/system_metrics.py

# Service metrics
kubectl top pods -n production

# Database load
psql -c "
  SELECT
    count(*) as active_connections,
    max(now() - query_start) as longest_query
  FROM pg_stat_activity
  WHERE state = 'active';"

# Queue depths
python -m src.reliability.rate_limiting queue-metrics

# Circuit breaker status
python scripts/reliability/check_circuit_breakers.py
```

### Predict Future Load
```bash
# Analyze trends
python scripts/monitoring/predict_load.py \
  --metric=request_rate \
  --horizon=24h

# Capacity planning
python scripts/capacity/forecast_needs.py \
  --lookback=7d \
  --lookahead=30d
```

---

## Horizontal Scaling Procedures

### Application Services

#### Manual Scaling
```bash
# Scale specific service
kubectl scale deployment api-server --replicas=10 -n production

# Verify scaling
kubectl get deployment api-server -n production
kubectl get pods -l app=api-server -n production

# Monitor rollout
kubectl rollout status deployment api-server -n production

# Check load distribution
python scripts/monitoring/check_load_distribution.py --service=api-server
```

#### Automated Horizontal Pod Autoscaling (HPA)
```bash
# Create HPA
kubectl autoscale deployment api-server \
  --cpu-percent=70 \
  --min=3 \
  --max=20 \
  -n production

# View HPA status
kubectl get hpa -n production

# Detailed HPA metrics
kubectl describe hpa api-server -n production

# Update HPA configuration
kubectl patch hpa api-server -n production -p '{"spec":{"maxReplicas":30}}'
```

#### HPA Configuration File
```yaml
# hpa-config.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 5
        periodSeconds: 30
      selectPolicy: Max
```

Apply configuration:
```bash
kubectl apply -f hpa-config.yaml
```

### Database Scaling

#### Read Replicas
```bash
# Add read replica (AWS RDS)
aws rds create-db-instance-read-replica \
  --db-instance-identifier sergas-db-replica-3 \
  --source-db-instance-identifier sergas-db-primary \
  --db-instance-class db.r5.2xlarge \
  --publicly-accessible false

# Wait for replica to be available
aws rds wait db-instance-available \
  --db-instance-identifier sergas-db-replica-3

# Add to application load balancer
python scripts/db/add_replica_to_pool.py \
  --replica=sergas-db-replica-3.us-east-1.rds.amazonaws.com

# Verify read distribution
python scripts/db/check_read_distribution.py
```

#### Connection Pool Scaling
```python
# Update connection pool configuration
from src.db.connection_pool import ConnectionPoolManager

pool_manager = ConnectionPoolManager()

# Increase pool size
pool_manager.resize_pool(
    min_connections=10,
    max_connections=100
)

# Monitor pool utilization
metrics = pool_manager.get_metrics()
print(f"Pool utilization: {metrics['utilization_percent']}%")
```

### Cache Scaling

#### Redis Cluster Scaling
```bash
# Add Redis nodes
redis-cli --cluster add-node \
  new-node-ip:6379 \
  existing-node-ip:6379

# Rebalance cluster
redis-cli --cluster rebalance existing-node-ip:6379 --cluster-use-empty-masters

# Verify cluster status
redis-cli --cluster check existing-node-ip:6379
```

#### Cache Memory Scaling
```bash
# Increase Redis memory (AWS ElastiCache)
aws elasticache modify-cache-cluster \
  --cache-cluster-id sergas-redis \
  --cache-node-type cache.r5.xlarge \
  --apply-immediately

# Monitor memory usage
redis-cli INFO memory
```

---

## Vertical Scaling Procedures

### Increase Pod Resources

#### Update Deployment Resources
```yaml
# Update deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  template:
    spec:
      containers:
      - name: api-server
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

Apply changes:
```bash
kubectl apply -f api-server-deployment.yaml

# Rolling update will automatically apply
kubectl rollout status deployment api-server -n production

# Verify new resources
kubectl describe pod -l app=api-server -n production | grep -A 5 "Limits:"
```

### Database Instance Scaling

#### Increase RDS Instance Size
```bash
# Modify DB instance class
aws rds modify-db-instance \
  --db-instance-identifier sergas-db-primary \
  --db-instance-class db.r5.4xlarge \
  --apply-immediately

# Monitor modification
aws rds describe-db-instances \
  --db-instance-identifier sergas-db-primary \
  --query 'DBInstances[0].DBInstanceStatus'

# Wait for completion
aws rds wait db-instance-available \
  --db-instance-identifier sergas-db-primary
```

Note: This causes brief downtime (typically 1-2 minutes)

#### Increase Database Storage
```bash
# Increase storage size
aws rds modify-db-instance \
  --db-instance-identifier sergas-db-primary \
  --allocated-storage 1000 \
  --apply-immediately

# Storage scaling is online, no downtime
```

---

## Rate Limiting Adjustments

### Increase Rate Limits During High Load

```python
from src.reliability.rate_limiting import RateLimiter, RateLimitConfig

# Get current rate limiter
limiter = RateLimiter.get_instance("api_rate_limiter")

# Temporarily increase limits
new_config = RateLimitConfig(
    name="api_rate_limiter",
    max_requests=2000,  # Increased from 1000
    window_seconds=60,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)

limiter.update_config(new_config)

# Monitor impact
metrics = limiter.get_metrics()
print(f"Current utilization: {metrics['utilization_percent']}%")
```

### Adjust Queue Capacity

```python
from src.reliability.rate_limiting import QueueManager

# Increase queue size
queue = QueueManager.get_instance("request_queue")

# Scale workers
await queue.scale_workers(new_worker_count=20)

# Increase queue capacity
queue.resize_queue(new_max_size=5000)

# Check queue metrics
metrics = queue.get_metrics()
print(f"Queue size: {metrics['queue_size']}/{metrics['max_size']}")
```

---

## Graceful Degradation During Scaling

### Enable Degradation Mode

```python
from src.reliability.graceful_degradation import DegradationManager, DegradationLevel

manager = DegradationManager()

# Reduce to essential services during scaling
manager.set_degradation_level(DegradationLevel.DEGRADED)

# Disable non-critical features
manager.feature_flags.disable("recommendations")
manager.feature_flags.disable("analytics")
manager.feature_flags.disable("notifications")

# Perform scaling operations
# ... scaling commands ...

# Restore full functionality
manager.set_degradation_level(DegradationLevel.FULL)
manager.feature_flags.enable("recommendations")
manager.feature_flags.enable("analytics")
manager.feature_flags.enable("notifications")
```

---

## Scaling Validation

### Post-Scaling Health Checks

```bash
# Verify all services healthy
python scripts/reliability/health_check_all.py

# Check load distribution
python scripts/monitoring/check_load_distribution.py

# Verify performance improvements
python scripts/monitoring/check_response_times.py --before-scaling --after-scaling

# Monitor error rates
python scripts/monitoring/check_error_rates.py --duration=30m

# Verify database performance
python scripts/db/check_db_performance.py

# Check circuit breakers
python scripts/reliability/check_circuit_breakers.py
```

### Scaling Validation Checklist

- [ ] All pods running and healthy
- [ ] Load evenly distributed
- [ ] Response times improved
- [ ] Error rates normal or improved
- [ ] Database connections stable
- [ ] Cache hit rates maintained
- [ ] No circuit breakers open
- [ ] Queue depths reduced
- [ ] Memory utilization acceptable
- [ ] CPU utilization acceptable

---

## Capacity Planning

### Daily Capacity Review

```bash
# Generate capacity report
python scripts/capacity/daily_report.py \
  --output=docs/capacity/daily_$(date +%Y%m%d).md

# Analyze trends
python scripts/capacity/analyze_trends.py \
  --period=7d \
  --metrics=cpu,memory,requests,database
```

### Weekly Capacity Planning

```bash
# Forecast needs
python scripts/capacity/forecast_weekly.py \
  --lookback=30d \
  --lookahead=14d \
  --output=capacity_forecast.json

# Generate recommendations
python scripts/capacity/generate_recommendations.py \
  --forecast=capacity_forecast.json \
  --output=scaling_recommendations.md
```

### Capacity Thresholds

| Metric | Warning | Critical | Recommended Scaling |
|--------|---------|----------|---------------------|
| CPU | 70% | 85% | +50% instances |
| Memory | 80% | 90% | +2x memory or +50% instances |
| Request Rate | 80% capacity | 95% capacity | +100% instances |
| Database Connections | 80% max | 90% max | Add read replica or increase pool |
| Queue Depth | 100 | 500 | +50% workers |
| Error Rate | 1% | 5% | Scale and investigate |

---

## Pre-emptive Scaling

### Scheduled High-Load Events

```bash
# Scale before known traffic spike
# Example: Product launch at 10 AM

# At 9:30 AM - Pre-scale
kubectl scale deployment api-server --replicas=20 -n production
kubectl scale deployment auth-service --replicas=10 -n production

# Increase rate limits
python scripts/scaling/increase_rate_limits.py --multiplier=2

# Add database read replicas
python scripts/db/add_temporary_replicas.py --count=2

# Monitor during event
python scripts/monitoring/real_time_monitor.py --alert-on=anomalies

# After event (e.g., 2 PM) - Scale down
kubectl scale deployment api-server --replicas=5 -n production
kubectl scale deployment auth-service --replicas=3 -n production

# Remove temporary replicas
python scripts/db/remove_temporary_replicas.py
```

### Automated Pre-emptive Scaling

```yaml
# scheduled-scaling.yaml
apiVersion: autoscaling.k8s.io/v1
kind: ScheduledScaling
metadata:
  name: business-hours-scaling
spec:
  deployments:
    - name: api-server
      namespace: production
  schedules:
    - name: morning-scale-up
      cron: "0 8 * * 1-5"  # 8 AM weekdays
      replicas: 10
    - name: evening-scale-down
      cron: "0 20 * * 1-5"  # 8 PM weekdays
      replicas: 3
    - name: weekend-minimal
      cron: "0 0 * * 6,0"  # Midnight weekends
      replicas: 2
```

---

## Emergency Scaling

### Rapid Scale-Out Procedure

When experiencing sudden traffic spike:

```bash
# 1. Immediate scale-out
kubectl scale deployment api-server --replicas=30 -n production
kubectl scale deployment auth-service --replicas=15 -n production
kubectl scale deployment worker --replicas=20 -n production

# 2. Increase resource limits temporarily
kubectl set resources deployment api-server \
  --limits=cpu=4,memory=8Gi \
  -n production

# 3. Add database read capacity
python scripts/db/emergency_scale_reads.py

# 4. Increase cache memory
python scripts/cache/increase_memory.py --target=16GB

# 5. Raise rate limits
python scripts/scaling/emergency_rate_limits.py

# 6. Enable aggressive caching
python scripts/cache/aggressive_mode.py --ttl=300

# 7. Monitor continuously
watch -n 5 'kubectl top pods -n production'
```

### Scale-Out Validation

```bash
# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=api-server \
  -n production \
  --timeout=300s

# Check health
curl https://api.sergas.com/health

# Verify load distribution
python scripts/monitoring/check_load_distribution.py --services=all

# Monitor error rates
python scripts/monitoring/check_error_rates.py --real-time
```

---

## Auto-Scaling Configuration

### Cluster Autoscaler

```yaml
# cluster-autoscaler-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*-spot-.*
    20:
      - .*-on-demand-.*
    50:
      - .*-high-memory-.*
```

Enable cluster autoscaler:
```bash
# AWS EKS
eksctl create cluster \
  --name sergas-production \
  --enable-cluster-autoscaler \
  --asg-access

# Configure autoscaler
kubectl set image deployment/cluster-autoscaler \
  cluster-autoscaler=k8s.gcr.io/autoscaling/cluster-autoscaler:v1.24.0 \
  -n kube-system
```

### Vertical Pod Autoscaler (VPA)

```yaml
# vpa-config.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-server-vpa
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: api-server
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: api-server
      minAllowed:
        cpu: 500m
        memory: 1Gi
      maxAllowed:
        cpu: 4
        memory: 16Gi
```

---

## Scaling Rollback

### When Scaling Causes Issues

```bash
# Rollback to previous replica count
kubectl rollout undo deployment api-server -n production

# Or specify exact count
kubectl scale deployment api-server --replicas=5 -n production

# Rollback resource changes
kubectl rollout undo deployment api-server -n production

# Restore rate limits
python scripts/scaling/restore_rate_limits.py --from-backup

# Monitor recovery
python scripts/monitoring/check_all_metrics.py --duration=15m
```

---

## Cost Optimization

### Right-Sizing

```bash
# Analyze actual resource usage
python scripts/capacity/analyze_usage.py --period=30d

# Generate right-sizing recommendations
python scripts/capacity/right_sizing_recommendations.py \
  --output=right_sizing_report.json

# Apply recommendations
python scripts/capacity/apply_right_sizing.py \
  --recommendations=right_sizing_report.json \
  --dry-run
```

### Scheduled Scaling for Cost Savings

```bash
# Scale down during low-traffic periods
# Example: Night hours, weekends

# Configure scheduled scaling
kubectl apply -f scheduled-scaling.yaml

# Verify schedule
kubectl get schedules -n production

# Monitor cost impact
python scripts/cost/analyze_savings.py --period=monthly
```

---

## Scaling Metrics Dashboard

### Key Metrics to Monitor

1. **Request Rate**: Requests per second
2. **Response Time**: p50, p95, p99 latency
3. **Error Rate**: Percentage of failed requests
4. **CPU Utilization**: Per pod and aggregate
5. **Memory Utilization**: Per pod and aggregate
6. **Database Connections**: Active and idle
7. **Queue Depth**: Pending requests
8. **Cache Hit Rate**: Percentage of cache hits
9. **Pod Count**: Current vs desired replicas
10. **Cost**: Estimated hourly/daily cost

### Grafana Dashboard Query Examples

```promql
# Request rate
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Pod count vs desired
kube_deployment_status_replicas{deployment="api-server"}

# HPA current replicas
kube_hpa_status_current_replicas{hpa="api-server"}
```

---

## Troubleshooting Scaling Issues

### Pods Not Scaling

```bash
# Check HPA status
kubectl describe hpa api-server -n production

# Check metrics server
kubectl top nodes
kubectl top pods -n production

# View HPA events
kubectl get events -n production | grep HorizontalPodAutoscaler

# Check resource quotas
kubectl describe resourcequota -n production
```

### Scaling Causing Instability

```bash
# Check pod disruption budget
kubectl get pdb -n production

# Review pod events
kubectl get events -n production --sort-by='.lastTimestamp'

# Check for OOMKilled pods
kubectl get pods -n production | grep OOMKilled

# Review logs for errors
kubectl logs -l app=api-server -n production --tail=100 | grep ERROR
```

### Database Connection Issues After Scaling

```bash
# Check connection pool size
psql -c "SHOW max_connections;"

# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection pool
python scripts/db/increase_connection_pool.py --size=200

# Add pgbouncer for connection pooling
kubectl apply -f pgbouncer-deployment.yaml
```

---

## Contact Information

### Scaling Support Team
- **Platform Team**: platform-team@sergas.com
- **Database Team**: db-team@sergas.com
- **On-Call Engineer**: PagerDuty escalation

### Escalation
For scaling issues requiring executive approval (cost > $10k/month):
1. Engineering Manager
2. CTO
3. CFO (for budget approval)
