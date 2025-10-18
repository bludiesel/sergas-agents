#!/bin/bash
# Week 1 Validation Test Runner
# Runs comprehensive validation tests for Week 1 deliverables

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Week 1 Validation Test Suite"
echo "=========================================="
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not detected${NC}"
    echo "Recommend activating virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Install dependencies: pip install -r requirements.txt"
    exit 1
fi

echo "Running Week 1 validation tests..."
echo ""

# Run environment tests first
echo "----------------------------------------"
echo "1. Environment Validation Tests"
echo "----------------------------------------"
pytest tests/test_environment.py -v --tb=short || {
    echo -e "${RED}Environment tests failed!${NC}"
    exit 1
}
echo ""

# Run Week 1 integration tests
echo "----------------------------------------"
echo "2. Week 1 Integration Tests"
echo "----------------------------------------"
pytest tests/integration/test_week1_integration.py -v --tb=short || {
    echo -e "${RED}Integration tests failed!${NC}"
    exit 1
}
echo ""

# Run full test suite with coverage
echo "----------------------------------------"
echo "3. Full Test Suite with Coverage"
echo "----------------------------------------"
pytest tests/ -v \
    --cov=src \
    --cov-report=html \
    --cov-report=term \
    --cov-report=xml \
    -m week1 || {
    echo -e "${RED}Test suite failed!${NC}"
    exit 1
}
echo ""

# Generate summary
echo "=========================================="
echo -e "${GREEN}Week 1 Validation Complete!${NC}"
echo "=========================================="
echo ""
echo "Reports generated:"
echo "  - Coverage: htmlcov/index.html"
echo "  - Validation: docs/setup/WEEK1_VALIDATION.md"
echo ""
echo "Next steps:"
echo "  1. Review validation report"
echo "  2. Address any warnings or failures"
echo "  3. Proceed to Week 2 implementation"
echo ""
