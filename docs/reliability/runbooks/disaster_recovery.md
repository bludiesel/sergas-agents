# Disaster Recovery Runbook

## Overview

This runbook provides procedures for recovering from catastrophic failures including data loss, infrastructure failure, and complete system outages.

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

### Service Tiers

| Service Tier | RTO | RPO | Priority |
|-------------|-----|-----|----------|
| Critical (Auth, API) | 1 hour | 5 minutes | P0 |
| High (Database, Core Services) | 4 hours | 15 minutes | P1 |
| Medium (Analytics, Reporting) | 24 hours | 1 hour | P2 |
| Low (Batch Jobs, Archive) | 72 hours | 24 hours | P3 |

## Disaster Scenarios

### Scenario 1: Complete Database Loss

**Impact:** All database data inaccessible or corrupted

**Recovery Steps:**

#### 1. Assess Damage (0-15 minutes)
```bash
# Check database connectivity
psql -h db-primary -U sergas -c "SELECT version();"

# Check replication status
psql -h db-replica -U sergas -c "SELECT pg_is_in_recovery();"

# Verify backup availability
python -m src.reliability.disaster_recovery list-backups --type=database
```

#### 2. Activate Disaster Recovery Mode (15-20 minutes)
```python
# Enable maintenance mode
from src.reliability.graceful_degradation import DegradationManager, DegradationLevel

manager = DegradationManager()
manager.set_degradation_level(DegradationLevel.MAINTENANCE)

# Update status page
python scripts/status/update_status.py \
  --status=major_outage \
  --message="Database recovery in progress. All services temporarily unavailable."
```

#### 3. Identify Recovery Point (20-30 minutes)
```bash
# List available backups
python -m src.reliability.disaster_recovery list-backups \
  --type=database \
  --status=completed

# Select most recent backup
BACKUP_ID="database_20251019_140000"

# Verify backup integrity
python -m src.reliability.disaster_recovery verify-backup \
  --backup-id=$BACKUP_ID
```

#### 4. Restore from Backup (30 minutes - 2 hours)
```bash
# Stop all application services
kubectl scale deployment --all --replicas=0 -n production

# Prepare new database instance
# (Provision new RDS instance or repair existing)

# Restore backup
python -m src.reliability.disaster_recovery restore-backup \
  --backup-id=$BACKUP_ID \
  --target-host=db-recovery.internal \
  --verify-checksum

# Monitor restoration progress
tail -f /var/log/recovery/database_restore.log
```

#### 5. Apply Point-in-Time Recovery (If Available)
```bash
# Apply WAL logs for PITR
python -m src.reliability.disaster_recovery pitr-restore \
  --backup-id=$BACKUP_ID \
  --target-time="2025-10-19 14:25:00 UTC" \
  --wal-archive-path=s3://backups/wal-archive

# Verify data consistency
python scripts/db/verify_data_integrity.py
```

#### 6. Validate Restoration
```bash
# Run data integrity checks
python scripts/db/check_referential_integrity.py
python scripts/db/check_data_counts.py

# Test critical queries
psql -h db-recovery.internal -U sergas -f scripts/db/validation_queries.sql

# Compare with pre-disaster metrics
python scripts/db/compare_metrics.py \
  --baseline=s3://backups/metrics/pre_disaster.json \
  --current=db-recovery.internal
```

#### 7. Switch to Recovered Database
```bash
# Update application configuration
kubectl set env deployment/api-server \
  DATABASE_HOST=db-recovery.internal \
  -n production

# Gradually scale up services
kubectl scale deployment api-server --replicas=3 -n production
kubectl scale deployment auth-service --replicas=2 -n production

# Monitor for errors
kubectl logs -f deployment/api-server -n production | grep ERROR
```

#### 8. Resume Normal Operations
```python
# Exit maintenance mode
from src.reliability.graceful_degradation import DegradationManager, DegradationLevel

manager = DegradationManager()
manager.set_degradation_level(DegradationLevel.FULL)

# Update status page
python scripts/status/update_status.py \
  --status=operational \
  --message="All systems recovered and operational."
```

**Estimated Total Recovery Time:** 2-4 hours

---

### Scenario 2: Complete Infrastructure Failure (AWS Region Down)

**Impact:** All services in primary region unavailable

**Recovery Steps:**

#### 1. Confirm Regional Outage (0-10 minutes)
```bash
# Check AWS health dashboard
curl https://status.aws.amazon.com/

# Verify services in primary region
aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Environment,Values=production"

# Check if failover region healthy
aws ec2 describe-instances --region us-west-2 --filters "Name=tag:Environment,Values=production"
```

#### 2. Initiate Failover to DR Region (10-30 minutes)
```bash
# Update DNS to point to DR region
python scripts/dr/failover_dns.py \
  --from-region=us-east-1 \
  --to-region=us-west-2 \
  --services=all

# Verify DNS propagation
dig api.sergas.com +short

# Update load balancer targets
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:... \
  --region us-west-2
```

#### 3. Promote DR Database to Primary
```bash
# Promote read replica to master
aws rds promote-read-replica \
  --db-instance-identifier sergas-db-dr \
  --region us-west-2

# Wait for promotion
aws rds wait db-instance-available \
  --db-instance-identifier sergas-db-dr \
  --region us-west-2

# Update connection strings
kubectl set env deployment/api-server \
  DATABASE_HOST=sergas-db-dr.us-west-2.rds.amazonaws.com \
  -n production
```

#### 4. Scale Services in DR Region
```bash
# Scale up DR services to production capacity
kubectl scale deployment --all --replicas=3 -n production --context=dr-cluster

# Verify pod health
kubectl get pods -n production --context=dr-cluster
kubectl top pods -n production --context=dr-cluster
```

#### 5. Validate DR Services
```bash
# Run smoke tests
python scripts/testing/smoke_test.py --environment=dr

# Check health endpoints
curl https://api.sergas.com/health
curl https://api.sergas.com/ready

# Monitor error rates
python scripts/monitoring/check_error_rates.py --region=us-west-2
```

**Estimated Total Recovery Time:** 30-60 minutes

---

### Scenario 3: Data Corruption

**Impact:** Database contains corrupted or invalid data

**Recovery Steps:**

#### 1. Identify Corruption Scope (0-20 minutes)
```bash
# Check data integrity
python scripts/db/check_data_integrity.py --full-scan

# Identify affected tables
psql -c "
  SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(tablename::regclass) DESC;"

# Check for constraint violations
python scripts/db/check_constraints.py
```

#### 2. Determine Recovery Point
```bash
# List recent backups
python -m src.reliability.disaster_recovery list-backups \
  --type=database \
  --since="2025-10-18"

# Identify last known good state
# Review application logs for when corruption started
kubectl logs deployment/api-server -n production --since=24h | grep "data.*corrupt"
```

#### 3. Selective Data Restoration
```bash
# Restore specific tables from backup
python -m src.reliability.disaster_recovery restore-tables \
  --backup-id=$BACKUP_ID \
  --tables=accounts,transactions,users \
  --target-schema=recovery

# Compare corrupted vs restored data
python scripts/db/compare_table_data.py \
  --schema1=public \
  --schema2=recovery \
  --table=accounts
```

#### 4. Data Reconciliation
```bash
# Identify differences
python scripts/db/reconcile_data.py \
  --corrupted-schema=public \
  --clean-schema=recovery \
  --output=reconciliation_report.json

# Manual review of differences
cat reconciliation_report.json | jq '.differences[] | select(.severity == "high")'
```

#### 5. Apply Corrections
```sql
-- Begin transaction for safety
BEGIN;

-- Backup current state
CREATE TABLE accounts_before_fix AS SELECT * FROM accounts;

-- Apply corrections from clean backup
UPDATE accounts a
SET
  balance = r.balance,
  updated_at = r.updated_at
FROM recovery.accounts r
WHERE a.id = r.id
  AND a.balance != r.balance;

-- Verify corrections
SELECT count(*) FROM accounts WHERE balance < 0;

-- If satisfied, commit
COMMIT;
-- If issues, rollback
-- ROLLBACK;
```

#### 6. Validation
```bash
# Run full data validation
python scripts/db/validate_all_data.py

# Check application functionality
python scripts/testing/integration_test.py

# Monitor for errors
python scripts/monitoring/check_error_rates.py --duration=30m
```

**Estimated Total Recovery Time:** 2-6 hours (depending on data volume)

---

### Scenario 4: Complete Application Code Loss

**Impact:** Source code repository and CI/CD destroyed

**Recovery Steps:**

#### 1. Recover Source Code
```bash
# Restore from backup repository
git clone https://github.com/sergas-backup/sergas-agents.git

# Verify commit history
cd sergas-agents
git log --oneline | head -20

# Check out production branch
git checkout production
git log -1
```

#### 2. Rebuild CI/CD Pipeline
```bash
# Restore pipeline configurations
aws s3 cp s3://sergas-dr/cicd/buildspec.yml .
aws s3 cp s3://sergas-dr/cicd/deploy.yml .

# Recreate CodePipeline
aws codepipeline create-pipeline \
  --cli-input-json file://pipeline-config.json

# Restore secrets
aws secretsmanager restore-secret --secret-id sergas/production/env
```

#### 3. Deploy from DR Artifacts
```bash
# Pull latest production image from backup registry
docker pull backup-registry.sergas.com/api-server:production-latest

# Tag for deployment
docker tag backup-registry.sergas.com/api-server:production-latest \
  production-registry.sergas.com/api-server:latest

# Deploy to Kubernetes
kubectl set image deployment/api-server \
  api-server=production-registry.sergas.com/api-server:latest \
  -n production
```

**Estimated Total Recovery Time:** 1-2 hours

---

## Backup Verification Procedures

### Daily Backup Verification
```bash
# Run automated backup tests
python -m src.reliability.disaster_recovery test-recovery \
  --backup-type=full \
  --latest

# Check backup integrity
python scripts/backups/verify_all_backups.py --last-24h

# Generate verification report
python scripts/backups/generate_report.py --output=daily_backup_report.html
```

### Monthly Recovery Drill
```bash
# Full disaster recovery drill
python scripts/dr/monthly_drill.py \
  --scenario=database_failure \
  --dry-run=false \
  --notify-team

# Document results
python scripts/dr/drill_report.py \
  --drill-id=$DRILL_ID \
  --output=docs/dr_drills/2025-10-drill.md
```

---

## Backup Automation

### Automated Backup Schedule

```yaml
# Backup schedule configuration
# Location: /config/backup_schedule.yaml

schedules:
  - name: database_full
    type: full
    cron: "0 2 * * *"  # 2 AM daily
    retention_days: 30

  - name: database_incremental
    type: incremental
    cron: "0 */6 * * *"  # Every 6 hours
    retention_days: 7

  - name: application_config
    type: snapshot
    cron: "0 */12 * * *"  # Every 12 hours
    retention_days: 14

  - name: user_data
    type: full
    cron: "0 3 * * 0"  # Sunday 3 AM weekly
    retention_days: 90
```

### Backup Execution
```bash
# Manual backup trigger
python -m src.reliability.disaster_recovery create-backup \
  --name=emergency_backup \
  --type=full \
  --retention-days=90

# Verify backup completed
python -m src.reliability.disaster_recovery list-backups \
  --name=emergency_backup \
  --status=completed
```

---

## Communication Templates

### Internal Alert (Disaster Declared)
```
DISASTER RECOVERY ACTIVATED

Scenario: Complete database failure
Severity: P0 - Critical
RTO: 4 hours
Impact: All services offline

Recovery Lead: [Name]
War Room: #disaster-recovery-20251019
Status Updates: Every 15 minutes

Current Status: Assessing backup integrity
Next Step: Database restoration from backup
ETA: 2 hours to service restoration
```

### Customer Communication
```
We are currently experiencing a major service disruption due to [brief description].

Our disaster recovery procedures have been activated and our team is working to restore service.

Expected Resolution: [Time]
Next Update: [Time]

We apologize for the inconvenience and appreciate your patience.
```

---

## Recovery Validation Checklist

After any disaster recovery procedure:

- [ ] All health checks passing
- [ ] Database integrity verified
- [ ] Data consistency checks passed
- [ ] Critical user flows tested
- [ ] Error rates within normal range
- [ ] Performance metrics acceptable
- [ ] Monitoring and alerting functional
- [ ] Backups resuming normally
- [ ] Team debriefed
- [ ] Post-mortem scheduled
- [ ] DR documentation updated
- [ ] Customers notified of resolution

---

## Contact Information

### Disaster Recovery Team
- **DR Lead**: dr-lead@sergas.com
- **Database Team**: db-team@sergas.com
- **Infrastructure**: infra-team@sergas.com
- **Security**: security@sergas.com

### Escalation
1. Engineering Manager
2. CTO
3. CEO (for catastrophic failures)

### External Contacts
- **AWS Support**: enterprise-support@amazon.com (Priority: Critical)
- **Database Vendor**: support@postgresql.org
- **Backup Vendor**: support@backup-provider.com
