#!/bin/bash

# Circuit Breaker Implementation Verification Script
# Week 3 Deliverables Check

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Circuit Breaker Pattern Implementation Verification"
echo "  Week 3 Milestone - Sergas Super Account Manager"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0

check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $2"
        ((FAIL++))
    fi
}

echo -e "${BLUE}1. Checking Core Implementation Files${NC}"
echo "───────────────────────────────────────────────────────────"

[ -f "src/resilience/__init__.py" ]
check $? "Module __init__.py exists"

[ -f "src/resilience/circuit_breaker.py" ]
check $? "circuit_breaker.py exists"

[ -f "src/resilience/circuit_breaker_manager.py" ]
check $? "circuit_breaker_manager.py exists"

[ -f "src/resilience/retry_policy.py" ]
check $? "retry_policy.py exists"

[ -f "src/resilience/fallback_handler.py" ]
check $? "fallback_handler.py exists"

[ -f "src/resilience/health_monitor.py" ]
check $? "health_monitor.py exists"

[ -f "src/resilience/exceptions.py" ]
check $? "exceptions.py exists"

echo ""
echo -e "${BLUE}2. Checking Test Files${NC}"
echo "───────────────────────────────────────────────────────────"

[ -f "tests/unit/resilience/test_circuit_breaker.py" ]
check $? "test_circuit_breaker.py exists"

[ -f "tests/unit/resilience/test_circuit_breaker_manager.py" ]
check $? "test_circuit_breaker_manager.py exists"

[ -f "tests/unit/resilience/test_retry_policy.py" ]
check $? "test_retry_policy.py exists"

[ -f "tests/unit/resilience/test_fallback_handler.py" ]
check $? "test_fallback_handler.py exists"

[ -f "tests/integration/test_resilience.py" ]
check $? "test_resilience.py exists"

echo ""
echo -e "${BLUE}3. Checking Documentation${NC}"
echo "───────────────────────────────────────────────────────────"

[ -f "docs/resilience/README.md" ]
check $? "README.md exists"

[ -f "docs/resilience/CIRCUIT_BREAKER_GUIDE.md" ]
check $? "CIRCUIT_BREAKER_GUIDE.md exists"

[ -f "docs/resilience/IMPLEMENTATION_SUMMARY.md" ]
check $? "IMPLEMENTATION_SUMMARY.md exists"

[ -f "docs/WEEK3_CIRCUIT_BREAKER_COMPLETE.md" ]
check $? "WEEK3_CIRCUIT_BREAKER_COMPLETE.md exists"

echo ""
echo -e "${BLUE}4. Checking Examples${NC}"
echo "───────────────────────────────────────────────────────────"

[ -f "examples/resilience_example.py" ]
check $? "resilience_example.py exists"

echo ""
echo -e "${BLUE}5. Checking Configuration${NC}"
echo "───────────────────────────────────────────────────────────"

grep -q "CIRCUIT_BREAKER_FAILURE_THRESHOLD" .env.example
check $? ".env.example contains circuit breaker config"

grep -q "MAX_RETRY_ATTEMPTS" .env.example
check $? ".env.example contains retry policy config"

grep -q "HEALTH_CHECK_INTERVAL" .env.example
check $? ".env.example contains health monitoring config"

echo ""
echo -e "${BLUE}6. Code Quality Checks${NC}"
echo "───────────────────────────────────────────────────────────"

# Check for type hints in circuit_breaker.py
grep -q "def __init__(" src/resilience/circuit_breaker.py
check $? "Functions defined in circuit_breaker.py"

# Check for docstrings
grep -q '"""' src/resilience/circuit_breaker.py
check $? "Docstrings present in circuit_breaker.py"

# Check for async/await
grep -q "async def" src/resilience/circuit_breaker.py
check $? "Async functions in circuit_breaker.py"

# Check for logging
grep -q "logger" src/resilience/circuit_breaker.py
check $? "Logging implemented in circuit_breaker.py"

echo ""
echo -e "${BLUE}7. File Statistics${NC}"
echo "───────────────────────────────────────────────────────────"

IMPL_FILES=$(find src/resilience -name "*.py" | wc -l | tr -d ' ')
TEST_FILES=$(find tests -name "*resilience*.py" | wc -l | tr -d ' ')
DOC_FILES=$(find docs/resilience -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

echo "Implementation files: $IMPL_FILES"
echo "Test files: $TEST_FILES"
echo "Documentation files: $DOC_FILES"

[ "$IMPL_FILES" -ge 6 ]
check $? "Implementation files count (expected ≥6)"

[ "$TEST_FILES" -ge 5 ]
check $? "Test files count (expected ≥5)"

[ "$DOC_FILES" -ge 3 ]
check $? "Documentation files count (expected ≥3)"

echo ""
echo -e "${BLUE}8. Line Count Verification${NC}"
echo "───────────────────────────────────────────────────────────"

TOTAL_LINES=$(wc -l src/resilience/*.py tests/unit/resilience/*.py tests/integration/test_resilience.py 2>/dev/null | tail -1 | awk '{print $1}')
echo "Total lines of code: $TOTAL_LINES"

[ "$TOTAL_LINES" -gt 2000 ]
check $? "Total lines of code (expected >2000)"

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}  Verification Summary${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Implementation is complete.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review.${NC}"
    exit 1
fi
