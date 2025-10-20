#!/bin/bash

# Performance Benchmark Execution Script
# Week 8 - SPARC Refinement Phase (Day 15)
#
# Runs comprehensive performance benchmarks and generates report.
#
# Usage:
#   ./scripts/run_benchmarks.sh
#   ./scripts/run_benchmarks.sh --with-load-test
#
# Author: Performance Benchmarker Agent
# Date: 2025-10-19

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/docs/performance"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Sergas Performance Benchmark Suite                           ║${NC}"
echo -e "${BLUE}║  Week 8 - SPARC Refinement Phase (Day 15)                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Started: $(date)${NC}"
echo ""

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

# ============================================================================
# Phase 1: Pytest Performance Benchmarks
# ============================================================================

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 1: Running Pytest Performance Benchmarks${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT"

# Run pytest benchmarks with detailed output
echo -e "${YELLOW}Executing comprehensive benchmark suite...${NC}"

python3 -m pytest tests/performance/test_comprehensive_benchmarks.py \
    -v \
    -m performance \
    --tb=short \
    --color=yes \
    --durations=10 \
    -o log_cli=true \
    -o log_cli_level=INFO \
    2>&1 | tee "$RESULTS_DIR/benchmark_results_${TIMESTAMP}.log"

PYTEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Pytest benchmarks PASSED${NC}"
else
    echo -e "${RED}❌ Pytest benchmarks FAILED (exit code: $PYTEST_EXIT_CODE)${NC}"
fi

echo ""

# ============================================================================
# Phase 2: Load Testing (Optional)
# ============================================================================

if [ "$1" == "--with-load-test" ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Phase 2: Running Locust Load Tests${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Check if locust is installed
    if command -v locust &> /dev/null; then
        echo -e "${YELLOW}Running load test (50 users, 10/s spawn rate, 60s duration)...${NC}"

        # Ensure FastAPI server is running (or use mock)
        echo -e "${YELLOW}Note: Ensure FastAPI server is running at http://localhost:8000${NC}"
        echo -e "${YELLOW}Or modify host in command below${NC}"
        echo ""

        # Run load test
        locust -f tests/performance/locust_load_test.py \
            --headless \
            -u 50 \
            -r 10 \
            -t 60s \
            --host http://localhost:8000 \
            --html "$RESULTS_DIR/load_test_report_${TIMESTAMP}.html" \
            --csv "$RESULTS_DIR/load_test_${TIMESTAMP}" \
            2>&1 | tee "$RESULTS_DIR/load_test_${TIMESTAMP}.log"

        LOCUST_EXIT_CODE=${PIPESTATUS[0]}

        if [ $LOCUST_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}✅ Load tests COMPLETED${NC}"
        else
            echo -e "${RED}⚠️  Load tests had issues (exit code: $LOCUST_EXIT_CODE)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Locust not installed. Skipping load tests.${NC}"
        echo -e "${YELLOW}   Install with: pip install locust${NC}"
    fi

    echo ""
else
    echo -e "${YELLOW}ℹ️  Load tests skipped. Run with --with-load-test to include.${NC}"
    echo ""
fi

# ============================================================================
# Phase 3: Generate Performance Report
# ============================================================================

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 3: Generating Performance Report${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

REPORT_FILE="$RESULTS_DIR/benchmark_report_${TIMESTAMP}.md"

cat > "$REPORT_FILE" << 'EOF'
# Performance Benchmark Report

**Date:** $(date)
**SPARC Phase:** Week 8 - Refinement Phase (Day 15)
**NFR Reference:** NFR-P01 (Event streaming latency < 200ms)

---

## Executive Summary

This report summarizes the performance benchmark results for the AG UI Protocol streaming implementation.

### Key Metrics

- **Event Streaming Latency**: See detailed results below
- **Concurrent Stream Handling**: 10+ concurrent streams target
- **Complete Workflow Duration**: < 10s target
- **Memory Usage**: < 500 MB increase target
- **System Throughput**: 100+ events/second target

---

## Benchmark Results

### 1. Event Streaming Latency (NFR-P01)

**Target:** < 200ms average event latency

**Results:**
- See pytest output in benchmark log file

**Validation:**
- ✅ PASS / ❌ FAIL

---

### 2. Concurrent Stream Handling

**Target:** 10+ concurrent streams

**Results:**
- See pytest output in benchmark log file

**Validation:**
- ✅ PASS / ❌ FAIL

---

### 3. Complete Workflow Duration

**Target:** < 10s end-to-end

**Results:**
- See pytest output in benchmark log file

**Validation:**
- ✅ PASS / ❌ FAIL

---

### 4. Memory Usage Under Load

**Target:** < 500 MB memory increase

**Results:**
- See pytest output in benchmark log file

**Validation:**
- ✅ PASS / ❌ FAIL

---

### 5. System Throughput

**Target:** 100+ events/second

**Results:**
- See pytest output in benchmark log file

**Validation:**
- ✅ PASS / ❌ FAIL

---

## Load Test Results (if run)

**Scenario:** 50 concurrent users, 60s duration

**Results:**
- See Locust HTML report and CSV files

---

## Bottleneck Analysis

**Identified Bottlenecks:**
1. [List any identified bottlenecks]
2. [Performance issues discovered]

**Recommendations:**
1. [Optimization recommendations]
2. [Infrastructure improvements]

---

## Compliance Status

| Requirement | Target | Actual | Status |
|------------|--------|--------|--------|
| Event Latency (NFR-P01) | < 200ms | TBD | TBD |
| Concurrent Streams | 10+ | TBD | TBD |
| Workflow Duration | < 10s | TBD | TBD |
| Memory Usage | < 500 MB | TBD | TBD |
| Throughput | 100+ eps | TBD | TBD |

---

## Next Steps

1. Review detailed benchmark logs
2. Address any failed benchmarks
3. Optimize identified bottlenecks
4. Re-run benchmarks to validate improvements

---

## Files Generated

- Benchmark Log: `benchmark_results_${TIMESTAMP}.log`
- Load Test HTML: `load_test_report_${TIMESTAMP}.html` (if applicable)
- Load Test CSV: `load_test_${TIMESTAMP}_*.csv` (if applicable)

EOF

echo -e "${GREEN}✅ Performance report generated: ${REPORT_FILE}${NC}"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Benchmark Execution Complete${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Completed: $(date)${NC}"
echo ""

echo -e "${GREEN}Results Summary:${NC}"
echo -e "  📊 Benchmark Log:     $RESULTS_DIR/benchmark_results_${TIMESTAMP}.log"
echo -e "  📄 Report:            $REPORT_FILE"

if [ "$1" == "--with-load-test" ] && command -v locust &> /dev/null; then
    echo -e "  🌐 Load Test HTML:    $RESULTS_DIR/load_test_report_${TIMESTAMP}.html"
    echo -e "  📈 Load Test CSV:     $RESULTS_DIR/load_test_${TIMESTAMP}_*.csv"
fi

echo ""

if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ All Benchmarks PASSED                                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ Some Benchmarks FAILED - Review logs for details          ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
