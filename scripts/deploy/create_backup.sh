#!/bin/bash
# Sergas Super Account Manager - Create Backup Script
# Create comprehensive backup before deployment

set -euo pipefail

ENVIRONMENT="${1:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_PREFIX="backup-${ENVIRONMENT}-${TIMESTAMP}"

create_backup() {
    log_info "Creating backup for $ENVIRONMENT environment..."

    # Database snapshot
    log_info "Creating database snapshot..."
    DB_INSTANCE="sergas-${ENVIRONMENT}-db"
    DB_SNAPSHOT="${BACKUP_PREFIX}-db"

    aws rds create-db-snapshot \
        --db-instance-identifier "$DB_INSTANCE" \
        --db-snapshot-identifier "$DB_SNAPSHOT" \
        --region "$AWS_REGION" \
        --output json > /dev/null

    log_success "Database snapshot created: $DB_SNAPSHOT"

    # Redis snapshot (automatic with AOF)
    log_info "Redis uses AOF persistence - automatic backup"

    # Export current task definition
    log_info "Exporting task definition..."
    TASK_FAMILY="sergas-agent-task-${ENVIRONMENT}"

    aws ecs describe-task-definition \
        --task-definition "$TASK_FAMILY" \
        --region "$AWS_REGION" \
        --query 'taskDefinition' > "${BACKUP_PREFIX}-task-definition.json"

    log_success "Task definition exported: ${BACKUP_PREFIX}-task-definition.json"

    # Upload to S3
    log_info "Uploading backup metadata to S3..."
    S3_BUCKET="sergas-backups-${ENVIRONMENT}"

    aws s3 cp "${BACKUP_PREFIX}-task-definition.json" \
        "s3://${S3_BUCKET}/${BACKUP_PREFIX}/" \
        --region "$AWS_REGION"

    log_success "Backup completed: $BACKUP_PREFIX"
    echo "$BACKUP_PREFIX"
}

create_backup
