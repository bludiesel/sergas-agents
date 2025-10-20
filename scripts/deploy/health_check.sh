#!/bin/bash
# Sergas Super Account Manager - Health Check Script
# Comprehensive health verification for deployed services

set -euo pipefail

URL="${1:-http://localhost:8000}"
COMPREHENSIVE="${2:-false}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# ===================================
# Basic Health Check
# ===================================
check_basic_health() {
    log_info "Checking basic health endpoint..."

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health" || echo "000")

    if [ "$HTTP_CODE" == "200" ]; then
        log_success "Health check passed (HTTP $HTTP_CODE)"
        return 0
    else
        log_error "Health check failed (HTTP $HTTP_CODE)"
        return 1
    fi
}

# ===================================
# Database Connectivity
# ===================================
check_database() {
    log_info "Checking database connectivity..."

    RESPONSE=$(curl -s "$URL/health/database" || echo "{\"status\":\"error\"}")
    STATUS=$(echo "$RESPONSE" | jq -r '.status // "error"')

    if [ "$STATUS" == "healthy" ]; then
        log_success "Database connection OK"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

# ===================================
# Redis Connectivity
# ===================================
check_redis() {
    log_info "Checking Redis connectivity..."

    RESPONSE=$(curl -s "$URL/health/redis" || echo "{\"status\":\"error\"}")
    STATUS=$(echo "$RESPONSE" | jq -r '.status // "error"')

    if [ "$STATUS" == "healthy" ]; then
        log_success "Redis connection OK"
        return 0
    else
        log_error "Redis connection failed"
        return 1
    fi
}

# ===================================
# API Endpoints
# ===================================
check_api_endpoints() {
    log_info "Checking API endpoints..."

    ENDPOINTS=("/api/v1/accounts" "/api/v1/health" "/metrics")
    FAILED=0

    for ENDPOINT in "${ENDPOINTS[@]}"; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL$ENDPOINT" || echo "000")

        if [[ "$HTTP_CODE" =~ ^(200|401|403)$ ]]; then
            log_success "Endpoint $ENDPOINT OK (HTTP $HTTP_CODE)"
        else
            log_error "Endpoint $ENDPOINT failed (HTTP $HTTP_CODE)"
            FAILED=$((FAILED + 1))
        fi
    done

    return $FAILED
}

# ===================================
# Performance Check
# ===================================
check_performance() {
    log_info "Checking response times..."

    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$URL/health")

    if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
        log_success "Response time OK: ${RESPONSE_TIME}s"
        return 0
    else
        log_warning "Slow response time: ${RESPONSE_TIME}s"
        return 1
    fi
}

# ===================================
# Main Health Check
# ===================================
main() {
    log_info "Starting health checks for: $URL"
    FAILED_CHECKS=0

    check_basic_health || FAILED_CHECKS=$((FAILED_CHECKS + 1))

    if [ "$COMPREHENSIVE" == "--comprehensive" ]; then
        log_info "Running comprehensive health checks..."

        check_database || FAILED_CHECKS=$((FAILED_CHECKS + 1))
        check_redis || FAILED_CHECKS=$((FAILED_CHECKS + 1))
        check_api_endpoints || FAILED_CHECKS=$((FAILED_CHECKS + 1))
        check_performance || FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi

    if [ $FAILED_CHECKS -eq 0 ]; then
        log_success "All health checks passed!"
        exit 0
    else
        log_error "$FAILED_CHECKS health check(s) failed"
        exit 1
    fi
}

main
