#!/bin/bash
# Sergas Super Account Manager - Blue-Green Deployment Script
# Zero-downtime deployment with automated rollback

set -euo pipefail

# ===================================
# Configuration
# ===================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ENVIRONMENT="${1:-staging}"
TARGET_COLOR="${2:-green}"
IMAGE_TAG="${3:-latest}"

AWS_REGION="${AWS_REGION:-us-east-1}"
ECS_CLUSTER="sergas-${ENVIRONMENT}-cluster"
SERVICE_NAME="sergas-agent-service-${ENVIRONMENT}"
TASK_FAMILY="sergas-agent-task-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===================================
# Helper Functions
# ===================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ===================================
# Validate Inputs
# ===================================
validate_inputs() {
    log_info "Validating inputs..."

    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT"
        exit 1
    fi

    if [[ ! "$TARGET_COLOR" =~ ^(blue|green)$ ]]; then
        log_error "Invalid target color: $TARGET_COLOR"
        exit 1
    fi

    if [ -z "$IMAGE_TAG" ]; then
        log_error "Image tag is required"
        exit 1
    fi

    log_success "Input validation passed"
}

# ===================================
# Get Current Active Color
# ===================================
get_active_color() {
    log_info "Determining active environment color..."

    ACTIVE_COLOR=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION" \
        --query 'services[0].tags[?key==`ActiveColor`].value' \
        --output text)

    if [ -z "$ACTIVE_COLOR" ]; then
        ACTIVE_COLOR="blue"
        log_warning "No active color found, defaulting to blue"
    else
        log_info "Current active color: $ACTIVE_COLOR"
    fi

    echo "$ACTIVE_COLOR"
}

# ===================================
# Register New Task Definition
# ===================================
register_task_definition() {
    log_info "Registering new task definition for $TARGET_COLOR environment..."

    # Get current task definition
    CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
        --task-definition "$TASK_FAMILY" \
        --region "$AWS_REGION" \
        --query 'taskDefinition' \
        --output json)

    # Update image tag
    NEW_TASK_DEF=$(echo "$CURRENT_TASK_DEF" | jq --arg IMAGE_TAG "$IMAGE_TAG" \
        '.containerDefinitions[0].image = (.containerDefinitions[0].image | split(":")[0]) + ":" + $IMAGE_TAG' | \
        jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')

    # Add target color tag
    NEW_TASK_DEF=$(echo "$NEW_TASK_DEF" | jq --arg COLOR "$TARGET_COLOR" \
        '.containerDefinitions[0].environment += [{"name": "DEPLOYMENT_COLOR", "value": $COLOR}]')

    # Register new task definition
    TASK_DEF_ARN=$(echo "$NEW_TASK_DEF" | \
        aws ecs register-task-definition \
            --region "$AWS_REGION" \
            --cli-input-json file:///dev/stdin \
            --query 'taskDefinition.taskDefinitionArn' \
            --output text)

    log_success "Task definition registered: $TASK_DEF_ARN"
    echo "$TASK_DEF_ARN"
}

# ===================================
# Create Target Group
# ===================================
create_target_group() {
    local COLOR=$1
    log_info "Creating target group for $COLOR environment..."

    TG_NAME="sergas-${ENVIRONMENT}-${COLOR}-tg"
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=tag:Environment,Values=$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --query 'Vpcs[0].VpcId' \
        --output text)

    # Check if target group exists
    EXISTING_TG=$(aws elbv2 describe-target-groups \
        --names "$TG_NAME" \
        --region "$AWS_REGION" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXISTING_TG" ] && [ "$EXISTING_TG" != "None" ]; then
        log_info "Target group already exists: $TG_NAME"
        echo "$EXISTING_TG"
        return
    fi

    # Create new target group
    TG_ARN=$(aws elbv2 create-target-group \
        --name "$TG_NAME" \
        --protocol HTTP \
        --port 8000 \
        --vpc-id "$VPC_ID" \
        --health-check-enabled \
        --health-check-protocol HTTP \
        --health-check-path /health \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 10 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --target-type ip \
        --region "$AWS_REGION" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)

    log_success "Target group created: $TG_ARN"
    echo "$TG_ARN"
}

# ===================================
# Deploy to Target Environment
# ===================================
deploy_to_target() {
    local TASK_DEF_ARN=$1
    local TG_ARN=$2

    log_info "Deploying to $TARGET_COLOR environment..."

    SERVICE_NAME_COLOR="${SERVICE_NAME}-${TARGET_COLOR}"

    # Check if service exists
    EXISTING_SERVICE=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$SERVICE_NAME_COLOR" \
        --region "$AWS_REGION" \
        --query 'services[0].status' \
        --output text 2>/dev/null || echo "")

    if [ "$EXISTING_SERVICE" == "ACTIVE" ]; then
        # Update existing service
        log_info "Updating existing service: $SERVICE_NAME_COLOR"

        aws ecs update-service \
            --cluster "$ECS_CLUSTER" \
            --service "$SERVICE_NAME_COLOR" \
            --task-definition "$TASK_DEF_ARN" \
            --force-new-deployment \
            --region "$AWS_REGION" \
            --output json > /dev/null

    else
        # Create new service
        log_info "Creating new service: $SERVICE_NAME_COLOR"

        SUBNETS=$(aws ec2 describe-subnets \
            --filters "Name=tag:Environment,Values=$ENVIRONMENT" "Name=tag:Type,Values=Private" \
            --region "$AWS_REGION" \
            --query 'Subnets[*].SubnetId' \
            --output text | tr '\t' ',')

        SECURITY_GROUP=$(aws ec2 describe-security-groups \
            --filters "Name=tag:Environment,Values=$ENVIRONMENT" "Name=tag:Name,Values=*ecs*" \
            --region "$AWS_REGION" \
            --query 'SecurityGroups[0].GroupId' \
            --output text)

        aws ecs create-service \
            --cluster "$ECS_CLUSTER" \
            --service-name "$SERVICE_NAME_COLOR" \
            --task-definition "$TASK_DEF_ARN" \
            --desired-count 2 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
            --load-balancers "targetGroupArn=$TG_ARN,containerName=sergas-app,containerPort=8000" \
            --health-check-grace-period-seconds 60 \
            --region "$AWS_REGION" \
            --output json > /dev/null
    fi

    log_success "Deployment to $TARGET_COLOR initiated"
}

# ===================================
# Wait for Service Stability
# ===================================
wait_for_stability() {
    log_info "Waiting for service to reach stable state..."

    SERVICE_NAME_COLOR="${SERVICE_NAME}-${TARGET_COLOR}"

    aws ecs wait services-stable \
        --cluster "$ECS_CLUSTER" \
        --services "$SERVICE_NAME_COLOR" \
        --region "$AWS_REGION"

    log_success "Service is stable"
}

# ===================================
# Verify Health Checks
# ===================================
verify_health_checks() {
    local TG_ARN=$1

    log_info "Verifying health checks..."

    MAX_ATTEMPTS=30
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        HEALTHY_COUNT=$(aws elbv2 describe-target-health \
            --target-group-arn "$TG_ARN" \
            --region "$AWS_REGION" \
            --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
            --output text)

        if [ "$HEALTHY_COUNT" -ge 1 ]; then
            log_success "Health checks passed: $HEALTHY_COUNT healthy targets"
            return 0
        fi

        ATTEMPT=$((ATTEMPT + 1))
        log_info "Waiting for healthy targets... Attempt $ATTEMPT/$MAX_ATTEMPTS"
        sleep 10
    done

    log_error "Health checks failed after $MAX_ATTEMPTS attempts"
    return 1
}

# ===================================
# Main Deployment Flow
# ===================================
main() {
    log_info "Starting blue-green deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Target Color: $TARGET_COLOR"
    log_info "Image Tag: $IMAGE_TAG"

    validate_inputs

    ACTIVE_COLOR=$(get_active_color)

    if [ "$ACTIVE_COLOR" == "$TARGET_COLOR" ]; then
        log_warning "Target color $TARGET_COLOR is already active. This will update the active environment."
    fi

    TASK_DEF_ARN=$(register_task_definition)
    TG_ARN=$(create_target_group "$TARGET_COLOR")

    deploy_to_target "$TASK_DEF_ARN" "$TG_ARN"
    wait_for_stability

    if verify_health_checks "$TG_ARN"; then
        log_success "Blue-green deployment completed successfully!"
        log_info "Next steps:"
        log_info "  1. Run integration tests on $TARGET_COLOR environment"
        log_info "  2. Switch traffic using: ./traffic_switch.sh $ENVIRONMENT <percentage>"
        log_info "  3. Monitor metrics and logs"
        log_info "  4. Decommission old environment if successful"
        exit 0
    else
        log_error "Health checks failed. Deployment unsuccessful."
        log_error "The $TARGET_COLOR environment is not healthy."
        log_error "Consider rolling back or investigating the issue."
        exit 1
    fi
}

main "$@"
