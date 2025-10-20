#!/bin/bash
# Sergas Super Account Manager - Smoke Tests
# Quick validation of critical functionality

set -euo pipefail

URL="${1:-http://localhost:8000}"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

FAILED=0

# Test 1: Health endpoint
log_info "Testing health endpoint..."
if curl -f -s "$URL/health" > /dev/null; then
    log_success "Health endpoint OK"
else
    log_error "Health endpoint failed"
    FAILED=$((FAILED + 1))
fi

# Test 2: Metrics endpoint
log_info "Testing metrics endpoint..."
if curl -f -s "$URL/metrics" | grep -q "# HELP"; then
    log_success "Metrics endpoint OK"
else
    log_error "Metrics endpoint failed"
    FAILED=$((FAILED + 1))
fi

# Test 3: API documentation
log_info "Testing API docs..."
if curl -f -s "$URL/docs" | grep -q "swagger"; then
    log_success "API documentation OK"
else
    log_error "API documentation failed"
    FAILED=$((FAILED + 1))
fi

# Test 4: Database connectivity
log_info "Testing database connectivity..."
if curl -f -s "$URL/health/database" | grep -q "healthy"; then
    log_success "Database connectivity OK"
else
    log_error "Database connectivity failed"
    FAILED=$((FAILED + 1))
fi

# Test 5: Redis connectivity
log_info "Testing Redis connectivity..."
if curl -f -s "$URL/health/redis" | grep -q "healthy"; then
    log_success "Redis connectivity OK"
else
    log_error "Redis connectivity failed"
    FAILED=$((FAILED + 1))
fi

if [ $FAILED -eq 0 ]; then
    log_success "All smoke tests passed!"
    exit 0
else
    log_error "$FAILED smoke test(s) failed"
    exit 1
fi
