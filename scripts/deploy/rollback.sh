#!/bin/bash
# Sergas Super Account Manager - Rollback Script
# Emergency rollback to previous stable deployment

set -euo pipefail

ENVIRONMENT="${1:-staging}"
AWS_REGION="${AWS_REGION:-us-east-1}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

rollback() {
    log_warning "Initiating rollback for $ENVIRONMENT environment..."

    # Switch all traffic back to blue (stable)
    log_info "Switching all traffic to blue environment..."
    ./traffic_switch.sh "$ENVIRONMENT" 0

    # Get active services
    ECS_CLUSTER="sergas-${ENVIRONMENT}-cluster"
    GREEN_SERVICE="sergas-agent-service-${ENVIRONMENT}-green"

    # Scale down green environment
    log_info "Scaling down green environment..."
    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$GREEN_SERVICE" \
        --desired-count 0 \
        --region "$AWS_REGION" \
        --output json > /dev/null || true

    # Restore database from backup if needed
    if [ "${RESTORE_DATABASE:-false}" == "true" ]; then
        log_warning "Restoring database from backup..."
        ./restore_database.sh "$ENVIRONMENT"
    fi

    log_info "Rollback completed successfully"
    log_info "All traffic is now on blue (stable) environment"
}

rollback
