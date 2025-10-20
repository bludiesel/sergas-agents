#!/bin/bash
# Sergas Super Account Manager - Traffic Switching Script
# Gradual traffic migration for blue-green deployment

set -euo pipefail

# ===================================
# Configuration
# ===================================
ENVIRONMENT="${1:-staging}"
TRAFFIC_PERCENTAGE="${2:-50}"

AWS_REGION="${AWS_REGION:-us-east-1}"
ALB_NAME="sergas-${ENVIRONMENT}-alb"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# ===================================
# Get Load Balancer ARN
# ===================================
get_alb_arn() {
    aws elbv2 describe-load-balancers \
        --names "$ALB_NAME" \
        --region "$AWS_REGION" \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text
}

# ===================================
# Get Target Groups
# ===================================
get_target_groups() {
    local ALB_ARN=$1

    aws elbv2 describe-listeners \
        --load-balancer-arn "$ALB_ARN" \
        --region "$AWS_REGION" \
        --query 'Listeners[0].DefaultActions[0].ForwardConfig.TargetGroups' \
        --output json
}

# ===================================
# Switch Traffic
# ===================================
switch_traffic() {
    log_info "Switching traffic to $TRAFFIC_PERCENTAGE% on green environment..."

    ALB_ARN=$(get_alb_arn)
    LISTENER_ARN=$(aws elbv2 describe-listeners \
        --load-balancer-arn "$ALB_ARN" \
        --region "$AWS_REGION" \
        --query 'Listeners[0].ListenerArn' \
        --output text)

    BLUE_TG_ARN=$(aws elbv2 describe-target-groups \
        --names "sergas-${ENVIRONMENT}-blue-tg" \
        --region "$AWS_REGION" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)

    GREEN_TG_ARN=$(aws elbv2 describe-target-groups \
        --names "sergas-${ENVIRONMENT}-green-tg" \
        --region "$AWS_REGION" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)

    BLUE_WEIGHT=$((100 - TRAFFIC_PERCENTAGE))
    GREEN_WEIGHT=$TRAFFIC_PERCENTAGE

    aws elbv2 modify-listener \
        --listener-arn "$LISTENER_ARN" \
        --default-actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=$BLUE_TG_ARN,Weight=$BLUE_WEIGHT},{TargetGroupArn=$GREEN_TG_ARN,Weight=$GREEN_WEIGHT}]}" \
        --region "$AWS_REGION" \
        --output json > /dev/null

    log_success "Traffic switched: Blue=$BLUE_WEIGHT%, Green=$GREEN_WEIGHT%"
}

switch_traffic
