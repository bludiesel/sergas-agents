#!/bin/bash
# Validation Script for Data Scout Test Suite
# Week 8 Deliverable Verification

set -e

echo "=================================================="
echo "Data Scout Test Suite Validation"
echo "Week 8 Comprehensive Testing Coverage"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Run: source venv/bin/activate"
    echo ""
fi

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 missing"
        return 1
    fi
}

# Function to count tests in file
count_tests() {
    local file=$1
    local count=$(grep -c "def test_" "$file" 2>/dev/null || echo "0")
    echo "$count"
}

echo "1. Checking Test Files..."
echo "-----------------------------------"

check_file "tests/unit/agents/test_zoho_data_scout.py"
check_file "tests/unit/agents/test_data_scout_models.py"
check_file "tests/unit/agents/test_data_scout_utils.py"
check_file "tests/integration/test_data_scout_integration.py"
check_file "tests/pytest.ini"
check_file "tests/requirements-test.txt"

echo ""
echo "2. Counting Tests..."
echo "-----------------------------------"

total_tests=0

for file in tests/unit/agents/test_*data_scout*.py tests/integration/test_data_scout*.py; do
    if [ -f "$file" ]; then
        count=$(count_tests "$file")
        echo "$(basename $file): $count tests"
        total_tests=$((total_tests + count))
    fi
done

echo ""
echo -e "${GREEN}Total Tests: $total_tests${NC}"
echo ""

echo "3. Checking Implementation Files..."
echo "-----------------------------------"

check_file "src/agents/zoho_data_scout.py"
check_file "src/agents/models.py"
check_file "src/agents/utils.py"
check_file "src/agents/config.py"

echo ""
echo "4. Test Dependencies..."
echo "-----------------------------------"

if command -v pip &> /dev/null; then
    echo "Checking installed packages..."

    packages=("pytest" "pytest-asyncio" "pytest-mock" "pytest-cov")
    missing=0

    for pkg in "${packages[@]}"; do
        if pip show "$pkg" &> /dev/null; then
            echo -e "${GREEN}✓${NC} $pkg installed"
        else
            echo -e "${RED}✗${NC} $pkg missing"
            missing=$((missing + 1))
        fi
    done

    if [ $missing -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Install missing packages:${NC}"
        echo "pip install -r tests/requirements-test.txt"
    fi
else
    echo -e "${YELLOW}pip not found - skipping dependency check${NC}"
fi

echo ""
echo "5. Running Quick Test Discovery..."
echo "-----------------------------------"

if command -v pytest &> /dev/null; then
    echo "Discovering tests with pytest..."
    pytest tests/unit/agents/test_*data_scout*.py tests/integration/test_data_scout*.py --collect-only -q 2>/dev/null || echo "Pytest collection failed - install dependencies"
else
    echo -e "${YELLOW}pytest not installed - skipping test discovery${NC}"
    echo "Install: pip install -r tests/requirements-test.txt"
fi

echo ""
echo "=================================================="
echo "Validation Summary"
echo "=================================================="

if [ $total_tests -ge 200 ]; then
    echo -e "${GREEN}✓${NC} Test Count: $total_tests (Target: 200+) - ${GREEN}PASSED${NC}"
else
    echo -e "${RED}✗${NC} Test Count: $total_tests (Target: 200+) - ${RED}FAILED${NC}"
fi

echo ""
echo "Next Steps:"
echo "-----------------------------------"
echo "1. Install test dependencies:"
echo "   pip install -r tests/requirements-test.txt"
echo ""
echo "2. Run unit tests:"
echo "   pytest tests/unit/agents/test_*data_scout*.py -v"
echo ""
echo "3. Run integration tests:"
echo "   pytest tests/integration/test_data_scout*.py -v"
echo ""
echo "4. Run with coverage:"
echo "   pytest tests/ --cov=src/agents --cov-report=html"
echo ""
echo "5. View coverage report:"
echo "   open tests/coverage_html/index.html"
echo ""
echo "=================================================="
echo -e "${GREEN}Data Scout Test Suite Validation Complete${NC}"
echo "=================================================="
