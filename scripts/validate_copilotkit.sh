#!/bin/bash
#
# CopilotKit Integration Validation Script
# Validates complete frontend-backend integration
#

set -e

echo "================================================"
echo "CopilotKit Integration Validation"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected="$3"

    echo -n "Testing $name... "

    if curl -s "$url" | grep -q "$expected"; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test JSON endpoint
test_json_endpoint() {
    local name="$1"
    local url="$2"
    local field="$3"
    local expected="$4"

    echo -n "Testing $name... "

    local result=$(curl -s "$url" | jq -r ".$field // empty" 2>/dev/null)
    if [ "$result" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (got: $result, expected: $expected)"
        ((FAILED++))
        return 1
    fi
}

# Test process
test_process() {
    local name="$1"
    local port="$2"

    echo -n "Testing $name process on port $port... "

    if lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1. Process Checks"
echo "=================="
test_process "Frontend" 7007
test_process "Backend" 8008
echo ""

echo "2. Health Checks"
echo "================"
test_json_endpoint "Backend health" "http://localhost:8008/health" "status" "healthy"
test_json_endpoint "API route health" "http://localhost:7007/api/copilotkit" "status" "ok"
echo ""

echo "3. Frontend Rendering"
echo "===================="
test_endpoint "CopilotKit UI presence" "http://localhost:7007" "copilotKitSidebar"
test_endpoint "Page title" "http://localhost:7007" "Sergas Account Manager"
echo ""

echo "4. Backend Configuration"
echo "========================"
test_json_endpoint "CopilotKit configured" "http://localhost:8008/health" "copilotkit_configured" "true"
test_json_endpoint "Agents registered" "http://localhost:8008/health" "agents_registered" "3"
echo ""

echo "5. Environment Variables"
echo "========================"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT/frontend" || { echo -e "${RED}Cannot find frontend directory${NC}"; exit 1; }

if [ -f .env.local ]; then
    echo -n "Checking COPILOTKIT_API_KEY... "
    if grep -q "NEXT_PUBLIC_COPILOTKIT_API_KEY" .env.local; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi

    echo -n "Checking API_URL... "
    if grep -q "NEXT_PUBLIC_API_URL" .env.local; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi

    echo -n "Checking RUNTIME_URL... "
    if grep -q "NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL" .env.local; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}FAIL - .env.local not found${NC}"
    ((FAILED+=3))
fi
echo ""

echo "6. File Structure"
echo "================="

check_file() {
    local file="$1"
    echo -n "Checking $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

FRONTEND_DIR="$PROJECT_ROOT/frontend"
check_file "$FRONTEND_DIR/app/layout.tsx"
check_file "$FRONTEND_DIR/app/page.tsx"
check_file "$FRONTEND_DIR/app/api/copilotkit/route.ts"
check_file "$FRONTEND_DIR/components/copilot/CopilotProvider.tsx"
check_file "$FRONTEND_DIR/components/copilot/index.ts"
echo ""

echo "================================================"
echo "Validation Complete"
echo "================================================"
echo -e "Tests Passed: ${GREEN}$PASSED${NC}"
echo -e "Tests Failed: ${RED}$FAILED${NC}"
echo "Total Tests: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✅${NC}"
    echo "CopilotKit integration is working correctly."
    exit 0
else
    echo -e "${RED}Some tests failed! ❌${NC}"
    echo "Please review the failures above."
    exit 1
fi
