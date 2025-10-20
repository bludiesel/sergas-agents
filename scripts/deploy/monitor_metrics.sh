#!/bin/bash
# Sergas Super Account Manager - Metrics Monitoring Script
# Monitor key metrics during deployment

set -euo pipefail

ENVIRONMENT="${1:-staging}"
DURATION="${2:-300}"
ERROR_THRESHOLD="${3:---threshold-error-rate=0.05}"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Extract threshold
THRESHOLD=$(echo "$ERROR_THRESHOLD" | sed 's/--threshold-error-rate=//')

log_info "Monitoring metrics for $DURATION seconds..."
log_info "Error rate threshold: $THRESHOLD"

NAMESPACE="Sergas/Application"
START_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)
INTERVAL=30
ITERATIONS=$((DURATION / INTERVAL))

for i in $(seq 1 $ITERATIONS); do
    log_info "Iteration $i/$ITERATIONS"

    # Get error rate
    ERROR_RATE=$(aws cloudwatch get-metric-statistics \
        --namespace "$NAMESPACE" \
        --metric-name ErrorRate \
        --dimensions Name=Environment,Value="$ENVIRONMENT" \
        --statistics Average \
        --start-time "$START_TIME" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 60 \
        --query 'Datapoints[-1].Average' \
        --output text)

    # Get response time
    RESPONSE_TIME=$(aws cloudwatch get-metric-statistics \
        --namespace "$NAMESPACE" \
        --metric-name ResponseTime \
        --dimensions Name=Environment,Value="$ENVIRONMENT" \
        --statistics Average \
        --start-time "$START_TIME" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 60 \
        --query 'Datapoints[-1].Average' \
        --output text)

    if [ "$ERROR_RATE" != "None" ]; then
        if (( $(echo "$ERROR_RATE > $THRESHOLD" | bc -l) )); then
            log_error "Error rate too high: $ERROR_RATE (threshold: $THRESHOLD)"
            exit 1
        else
            log_success "Error rate OK: $ERROR_RATE"
        fi
    fi

    if [ "$RESPONSE_TIME" != "None" ]; then
        log_info "Response time: ${RESPONSE_TIME}ms"
    fi

    sleep $INTERVAL
done

log_success "Monitoring completed successfully"
