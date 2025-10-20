#!/bin/bash
# Sergas Super Account Manager - Decommission Environment Script
# Safely shut down and remove old deployment environment

set -euo pipefail

ENVIRONMENT="${1:-staging}"
COLOR="${2:-blue}"

AWS_REGION="${AWS_REGION:-us-east-1}"
ECS_CLUSTER="sergas-${ENVIRONMENT}-cluster"
SERVICE_NAME="sergas-agent-service-${ENVIRONMENT}-${COLOR}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

decommission() {
    log_info "Decommissioning $COLOR environment for $ENVIRONMENT..."

    # Scale service to 0
    log_info "Scaling service to 0 tasks..."
    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$SERVICE_NAME" \
        --desired-count 0 \
        --region "$AWS_REGION" \
        --output json > /dev/null

    # Wait for tasks to stop
    log_info "Waiting for tasks to stop..."
    aws ecs wait services-stable \
        --cluster "$ECS_CLUSTER" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION"

    # Delete service
    log_info "Deleting service..."
    aws ecs delete-service \
        --cluster "$ECS_CLUSTER" \
        --service "$SERVICE_NAME" \
        --force \
        --region "$AWS_REGION" \
        --output json > /dev/null

    # Deregister target group (optional - keep for reuse)
    log_warning "Target group retained for potential reuse"

    log_success "Environment $COLOR decommissioned successfully"
}

decommission
