# Disaster Recovery Plan

## Overview

This document outlines comprehensive disaster recovery (DR) procedures for the Sergas Super Account Manager system, ensuring business continuity in the event of system failures, data loss, or catastrophic events.

## Table of Contents

1. [DR Objectives](#dr-objectives)
2. [Backup Strategy](#backup-strategy)
3. [Recovery Procedures](#recovery-procedures)
4. [Failover Procedures](#failover-procedures)
5. [Testing & Validation](#testing--validation)
6. [Communication Plan](#communication-plan)

---

## DR Objectives

### Recovery Metrics

| Metric | Target | Maximum Acceptable |
|--------|--------|-------------------|
| **RTO** (Recovery Time Objective) | 15 minutes | 1 hour |
| **RPO** (Recovery Point Objective) | 15 minutes | 1 hour |
| **Data Loss** | 0% for critical data | <0.1% |
| **Availability** | 99.9% | 99.5% |

### Critical Components

**Priority 1 (Restore within 15 minutes):**
- Application servers
- Load balancer
- PostgreSQL database
- Redis cache
- Authentication service

**Priority 2 (Restore within 1 hour):**
- Monitoring stack
- Cognee memory service
- Background job processors

**Priority 3 (Restore within 4 hours):**
- Analytics services
- Reporting tools
- Historical data archives

---

## Backup Strategy

### Automated Backups

#### Database Backups

```bash
#!/bin/bash
# /usr/local/bin/backup-database.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/sergas/database"
S3_BUCKET="s3://sergas-backups-prod/database"
RETENTION_DAYS=30
RETENTION_S3_DAYS=90

# Database connection details
DB_HOST="${DATABASE_HOST}"
DB_PORT="${DATABASE_PORT}"
DB_NAME="${DATABASE_NAME}"
DB_USER="${DATABASE_USER}"
export PGPASSWORD="${DATABASE_PASSWORD}"

# Backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sergas_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "[$(date)] Starting database backup..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -F custom \
  --verbose \
  --compress=9 \
  | gzip > "$BACKUP_FILE"

# Verify backup
if [ ! -f "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file not created!"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3
echo "[$(date)] Uploading to S3..."
aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/" \
  --storage-class STANDARD_IA \
  --server-side-encryption AES256

# Verify S3 upload
if aws s3 ls "$S3_BUCKET/$(basename $BACKUP_FILE)" > /dev/null; then
    echo "[$(date)] S3 upload successful"
else
    echo "[$(date)] ERROR: S3 upload failed!"
    exit 1
fi

# Cleanup old local backups
echo "[$(date)] Cleaning up old local backups..."
find "$BACKUP_DIR" -name "sergas_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Cleanup old S3 backups
echo "[$(date)] Cleaning up old S3 backups..."
aws s3 ls "$S3_BUCKET/" | \
  awk '{print $4}' | \
  grep "sergas_.*\.sql\.gz" | \
  while read file; do
    file_date=$(echo "$file" | sed -E 's/sergas_([0-9]{8})_.*/ \1/')
    file_age_days=$(( ($(date +%s) - $(date -d "$file_date" +%s)) / 86400 ))
    if [ $file_age_days -gt $RETENTION_S3_DAYS ]; then
        echo "Deleting old backup: $file (age: $file_age_days days)"
        aws s3 rm "$S3_BUCKET/$file"
    fi
done

echo "[$(date)] Backup completed successfully"

# Send notification
python /usr/local/bin/send_notification.py \
  --type success \
  --message "Database backup completed: $BACKUP_FILE ($BACKUP_SIZE)"
```

**Schedule:**
```bash
# crontab -e
# Full backup every 6 hours
0 */6 * * * /usr/local/bin/backup-database.sh >> /var/log/sergas/backup.log 2>&1

# Incremental backup every hour (WAL archiving)
0 * * * * /usr/local/bin/archive-wal.sh >> /var/log/sergas/wal-archive.log 2>&1
```

#### Configuration Backups

```bash
#!/bin/bash
# /usr/local/bin/backup-config.sh

BACKUP_DIR="/var/backups/sergas/config"
S3_BUCKET="s3://sergas-backups-prod/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/config_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

# Backup configuration files
tar -czf "$BACKUP_FILE" \
  /etc/systemd/system/sergas-app.service \
  /etc/nginx/sites-available/sergas \
  /etc/prometheus/prometheus.yml \
  /etc/prometheus/alerts.yml \
  /etc/alertmanager/config.yml \
  /home/sergas/super-account-manager/.env.example \
  /home/sergas/super-account-manager/alembic.ini \
  /home/sergas/super-account-manager/pyproject.toml

# Upload to S3
aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/"

# Cleanup old backups (keep 90 days)
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +90 -delete

echo "Configuration backup completed: $BACKUP_FILE"
```

**Schedule:**
```bash
# Daily at 1 AM
0 1 * * * /usr/local/bin/backup-config.sh >> /var/log/sergas/config-backup.log 2>&1
```

#### Application Code Backups

```bash
#!/bin/bash
# /usr/local/bin/backup-code.sh

BACKUP_DIR="/var/backups/sergas/code"
S3_BUCKET="s3://sergas-backups-prod/code"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CODE_DIR="/home/sergas/super-account-manager"

cd "$CODE_DIR"

# Get current git commit
GIT_COMMIT=$(git rev-parse HEAD)
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create backup
tar -czf "$BACKUP_DIR/code_${GIT_COMMIT}_${TIMESTAMP}.tar.gz" \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  .

# Upload to S3
aws s3 cp "$BACKUP_DIR/code_${GIT_COMMIT}_${TIMESTAMP}.tar.gz" "$S3_BUCKET/"

# Tag in Git
git tag -a "backup-${TIMESTAMP}" -m "Automated backup tag"

echo "Code backup completed: ${GIT_COMMIT} (${GIT_BRANCH})"
```

#### Redis Backup

```bash
#!/bin/bash
# /usr/local/bin/backup-redis.sh

BACKUP_DIR="/var/backups/sergas/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Trigger Redis save
redis-cli BGSAVE

# Wait for save to complete
while redis-cli LASTSAVE | grep -q "$(redis-cli LASTSAVE)"; do
    sleep 1
done

# Copy RDB file
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/dump_${TIMESTAMP}.rdb"

# Upload to S3
aws s3 cp "$BACKUP_DIR/dump_${TIMESTAMP}.rdb" \
  s3://sergas-backups-prod/redis/

echo "Redis backup completed"
```

---

## Recovery Procedures

### Complete System Recovery

#### Prerequisites

- Access to S3 backup bucket
- Fresh server/VM/container
- Database restored
- DNS updated (if needed)

#### Step 1: Provision Infrastructure

```bash
# Launch new EC2 instance (or equivalent)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.large \
  --key-name sergas-prod \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=sergas-recovery}]'

# Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=sergas-recovery" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "New instance: $INSTANCE_ID ($PUBLIC_IP)"
```

#### Step 2: Restore Database

```bash
# SSH to new instance
ssh -i sergas-prod.pem ubuntu@$PUBLIC_IP

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql-14

# Download latest backup from S3
LATEST_BACKUP=$(aws s3 ls s3://sergas-backups-prod/database/ | \
  sort | tail -1 | awk '{print $4}')

aws s3 cp "s3://sergas-backups-prod/database/$LATEST_BACKUP" /tmp/

# Create database
sudo -u postgres psql << EOF
CREATE DATABASE sergas_prod;
CREATE USER sergas_prod_user WITH PASSWORD '<password>';
GRANT ALL PRIVILEGES ON DATABASE sergas_prod TO sergas_prod_user;
EOF

# Restore backup
gunzip < "/tmp/$LATEST_BACKUP" | \
  pg_restore -U sergas_prod_user -d sergas_prod --verbose

# Verify restoration
psql -U sergas_prod_user -d sergas_prod -c "SELECT count(*) FROM accounts;"

echo "Database restored successfully"
```

#### Step 3: Restore Application

```bash
# Install dependencies
sudo apt install -y python3.14 python3.14-venv git redis-server nginx

# Clone repository (or restore from backup)
git clone https://github.com/sergas/super-account-manager.git
cd super-account-manager

# Checkout production tag
git checkout $(git describe --tags --abbrev=0)

# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Restore configuration
aws s3 cp s3://sergas-backups-prod/config/latest/config.tar.gz /tmp/
tar -xzf /tmp/config.tar.gz -C /

# Restore environment variables
aws secretsmanager get-secret-value \
  --secret-id sergas/production/app-secrets \
  --query SecretString \
  --output text > .env

# Run migrations
alembic upgrade head

# Start application
sudo systemctl start sergas-app
sudo systemctl enable sergas-app

# Verify application
curl http://localhost:8000/health
```

#### Step 4: Restore Redis

```bash
# Stop Redis
sudo systemctl stop redis-server

# Download backup
LATEST_REDIS=$(aws s3 ls s3://sergas-backups-prod/redis/ | \
  sort | tail -1 | awk '{print $4}')

aws s3 cp "s3://sergas-backups-prod/redis/$LATEST_REDIS" \
  /var/lib/redis/dump.rdb

# Set permissions
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo chmod 640 /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis-server

# Verify data
redis-cli DBSIZE
```

#### Step 5: Update DNS

```bash
# Update Route53 (or your DNS provider)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.sergas.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "'$PUBLIC_IP'"}]
      }
    }]
  }'

# Wait for propagation
dig api.sergas.com +short
```

#### Step 6: Verify Recovery

```bash
# Run health checks
curl https://api.sergas.com/health | jq

# Test account query
curl https://api.sergas.com/v1/accounts/ACC-123 \
  -H "Authorization: Bearer $TOKEN" | jq

# Check metrics
curl https://api.sergas.com/metrics | grep sergas_

# Verify database connectivity
psql -h localhost -U sergas_prod_user -d sergas_prod -c "SELECT NOW();"

# Check logs for errors
journalctl -u sergas-app -n 100 --no-pager
```

#### Step 7: Resume Services

```bash
# Enable monitoring
sudo systemctl start prometheus grafana alertmanager

# Resume background jobs
sudo systemctl start sergas-worker

# Verify all services
sudo systemctl status sergas-app sergas-worker prometheus grafana

# Notify stakeholders
python scripts/send_recovery_notification.py \
  --status complete \
  --downtime "45 minutes" \
  --rto "15 minutes"
```

---

### Database Point-in-Time Recovery

For WAL-enabled PostgreSQL:

```bash
#!/bin/bash
# Point-in-time recovery to specific timestamp

# Target recovery point
RECOVERY_TARGET="2024-10-19 14:30:00"

# Stop application
sudo systemctl stop sergas-app

# Restore base backup
gunzip < /path/to/base_backup.sql.gz | \
  pg_restore -U postgres -d sergas_prod

# Create recovery configuration
cat > /var/lib/postgresql/14/main/recovery.conf << EOF
restore_command = 'aws s3 cp s3://sergas-backups-prod/wal/%f %p'
recovery_target_time = '$RECOVERY_TARGET'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL
sudo systemctl start postgresql

# Wait for recovery to complete
tail -f /var/log/postgresql/postgresql-14-main.log

# Verify recovery point
psql -U sergas_prod_user -d sergas_prod -c "SELECT pg_last_xact_replay_timestamp();"

# Start application
sudo systemctl start sergas-app
```

---

## Failover Procedures

### Active-Passive Database Failover

#### Monitor Primary

```bash
#!/bin/bash
# /usr/local/bin/monitor-primary.sh

PRIMARY_HOST="primary-db.sergas.internal"
REPLICA_HOST="replica-db.sergas.internal"

while true; do
    if ! pg_isready -h $PRIMARY_HOST -U postgres > /dev/null 2>&1; then
        echo "[$(date)] Primary database is down! Initiating failover..."

        # Promote replica
        ssh $REPLICA_HOST "sudo -u postgres pg_ctl promote -D /var/lib/postgresql/14/main"

        # Update DNS
        aws route53 change-resource-record-sets \
          --hosted-zone-id Z1234567890ABC \
          --change-batch '{
            "Changes": [{
              "Action": "UPSERT",
              "ResourceRecordSet": {
                "Name": "db.sergas.internal",
                "Type": "CNAME",
                "TTL": 60,
                "ResourceRecords": [{"Value": "'$REPLICA_HOST'"}]
              }
            }]
          }'

        # Update application configuration
        ssh app-server "sudo sed -i 's/$PRIMARY_HOST/$REPLICA_HOST/g' /home/sergas/.env && sudo systemctl restart sergas-app"

        # Send alert
        python /usr/local/bin/send_alert.py \
          --severity critical \
          --message "Database failover completed to $REPLICA_HOST"

        break
    fi

    sleep 30
done
```

### Multi-Region Failover

For geographic redundancy:

```bash
#!/bin/bash
# Failover to DR region

PRIMARY_REGION="us-east-1"
DR_REGION="us-west-2"

# Update Route53 to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.sergas.com",
        "Type": "A",
        "SetIdentifier": "DR-Region",
        "Failover": "PRIMARY",
        "TTL": 60,
        "ResourceRecords": [{"Value": "dr-lb-ip"}]
      }
    }]
  }'

# Activate DR database
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier sergas-prod-dr \
  --db-snapshot-identifier latest-snapshot \
  --region $DR_REGION

# Update application configuration
aws ssm put-parameter \
  --name /sergas/production/database_host \
  --value "sergas-prod-dr.$DR_REGION.rds.amazonaws.com" \
  --overwrite \
  --region $DR_REGION

echo "Failover to $DR_REGION completed"
```

---

## Testing & Validation

### DR Testing Schedule

| Test Type | Frequency | Duration | Success Criteria |
|-----------|-----------|----------|------------------|
| **Backup Verification** | Daily | 15 min | Restore test succeeds |
| **Database Recovery** | Weekly | 1 hour | Data integrity verified |
| **Full System Recovery** | Monthly | 4 hours | RTO/RPO met |
| **Failover Drill** | Quarterly | 2 hours | Zero data loss |
| **Disaster Simulation** | Annually | 8 hours | All systems recovered |

### DR Test Procedure

```bash
#!/bin/bash
# /usr/local/bin/dr-test.sh

TEST_DATE=$(date +%Y%m%d)
TEST_REPORT="/var/log/sergas/dr-test-${TEST_DATE}.log"

echo "=== DR Test Started at $(date) ===" | tee $TEST_REPORT

# 1. Backup verification
echo "\n1. Verifying latest backup..." | tee -a $TEST_REPORT
LATEST_BACKUP=$(aws s3 ls s3://sergas-backups-prod/database/ | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://sergas-backups-prod/database/$LATEST_BACKUP" /tmp/test-restore.sql.gz

if [ -f /tmp/test-restore.sql.gz ]; then
    echo "✓ Backup file retrieved successfully" | tee -a $TEST_REPORT
else
    echo "✗ Backup file retrieval failed" | tee -a $TEST_REPORT
    exit 1
fi

# 2. Test database restoration (to test database)
echo "\n2. Testing database restoration..." | tee -a $TEST_REPORT
psql -U postgres -c "DROP DATABASE IF EXISTS sergas_test;"
psql -U postgres -c "CREATE DATABASE sergas_test;"

gunzip < /tmp/test-restore.sql.gz | \
  pg_restore -U postgres -d sergas_test 2>&1 | tee -a $TEST_REPORT

# Verify row count
ACCOUNT_COUNT=$(psql -U postgres -d sergas_test -t -c "SELECT count(*) FROM accounts;")
echo "Restored account count: $ACCOUNT_COUNT" | tee -a $TEST_REPORT

# 3. Test application startup
echo "\n3. Testing application startup..." | tee -a $TEST_REPORT
# Test in Docker container with test database
docker run --rm \
  -e DATABASE_NAME=sergas_test \
  sergas/super-account-manager:latest \
  python -c "from src.main import app; print('✓ Application starts successfully')" \
  2>&1 | tee -a $TEST_REPORT

# 4. Calculate RTO/RPO
echo "\n4. Performance Metrics:" | tee -a $TEST_REPORT
echo "Estimated RTO: 15 minutes" | tee -a $TEST_REPORT
echo "Estimated RPO: $(redis-cli GET last_backup_timestamp)" | tee -a $TEST_REPORT

# 5. Cleanup
psql -U postgres -c "DROP DATABASE sergas_test;"
rm /tmp/test-restore.sql.gz

echo "\n=== DR Test Completed at $(date) ===" | tee -a $TEST_REPORT

# Send report
python /usr/local/bin/send_dr_report.py --report-file $TEST_REPORT
```

---

## Communication Plan

### Incident Notification

**Severity Levels:**

| Level | Description | Response Time | Notification |
|-------|-------------|---------------|--------------|
| **P0 - Critical** | Complete outage | Immediate | Page all, Slack #incident, Email executives |
| **P1 - High** | Degraded service | 15 minutes | Slack #incident, Email team |
| **P2 - Medium** | Partial impact | 1 hour | Slack #operations |
| **P3 - Low** | Minor impact | 4 hours | Ticket system |

### Notification Templates

**P0 - Critical Outage:**
```
🚨 CRITICAL INCIDENT ALERT 🚨

Incident: [INCIDENT-ID]
Severity: P0 - Critical
Status: Investigating

Issue: Complete service outage detected at [TIME]
Impact: All users unable to access system
ETA: Investigating
Next Update: 15 minutes

Incident Commander: [NAME]
Status Page: https://status.sergas.com
```

**Recovery Complete:**
```
✅ INCIDENT RESOLVED

Incident: [INCIDENT-ID]
Severity: P0
Status: Resolved

Recovery completed at [TIME]
Total Downtime: [DURATION]
Root Cause: [BRIEF DESCRIPTION]

Next Steps:
- Post-mortem scheduled for [DATE]
- Preventive measures being implemented

Thank you for your patience.
```

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas DevOps Team
