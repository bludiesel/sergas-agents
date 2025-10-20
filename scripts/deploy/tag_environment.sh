#!/bin/bash
# Sergas Super Account Manager - Tag Environment Script
# Update environment color tags after successful deployment

set -euo pipefail

ENVIRONMENT="${1:-staging}"
SOURCE_COLOR="${2:-green}"
TARGET_COLOR="${3:-blue}"

AWS_REGION="${AWS_REGION:-us-east-1}"
ECS_CLUSTER="sergas-${ENVIRONMENT}-cluster"
SERVICE_NAME="sergas-agent-service-${ENVIRONMENT}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

tag_environment() {
    log_info "Tagging $SOURCE_COLOR as $TARGET_COLOR..."

    # Get service ARN
    SERVICE_ARN=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION" \
        --query 'services[0].serviceArn' \
        --output text)

    # Update tags
    aws ecs tag-resource \
        --resource-arn "$SERVICE_ARN" \
        --tags key=ActiveColor,value="$TARGET_COLOR" \
        --region "$AWS_REGION"

    log_success "Environment tagged: ActiveColor=$TARGET_COLOR"
}

tag_environment
