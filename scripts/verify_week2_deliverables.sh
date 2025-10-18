#!/bin/bash
# Week 2 Deliverables Verification Script
# Checks that all required files and components are present

echo "=================================================="
echo "Week 2 Deliverables Verification"
echo "Zoho SDK Integration"
echo "=================================================="
echo ""

PROJECT_ROOT="/Users/mohammadabdelrahman/Projects/sergas_agents"
PASSED=0
FAILED=0

check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo "✅ $description"
        ((PASSED++))
    else
        echo "❌ $description - FILE MISSING"
        ((FAILED++))
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo "✅ $description"
        ((PASSED++))
    else
        echo "❌ $description - DIRECTORY MISSING"
        ((FAILED++))
    fi
}

echo "=== Source Code Files ==="
check_file "$PROJECT_ROOT/src/integrations/zoho/exceptions.py" "Custom exceptions"
check_file "$PROJECT_ROOT/src/integrations/zoho/token_store.py" "Token store implementation"
check_file "$PROJECT_ROOT/src/integrations/zoho/sdk_client.py" "SDK client wrapper"
check_file "$PROJECT_ROOT/src/integrations/zoho/__init__.py" "Package initialization"
echo ""

echo "=== Database Migration ==="
check_file "$PROJECT_ROOT/migrations/001_create_zoho_tokens_table.sql" "Token table migration"
echo ""

echo "=== Unit Tests ==="
check_file "$PROJECT_ROOT/tests/unit/integrations/__init__.py" "Test package init"
check_file "$PROJECT_ROOT/tests/unit/integrations/test_token_store.py" "Token store tests"
check_file "$PROJECT_ROOT/tests/unit/integrations/test_zoho_sdk_client.py" "SDK client tests"
echo ""

echo "=== Integration Tests ==="
check_file "$PROJECT_ROOT/tests/integration/test_zoho_sdk.py" "Integration tests"
echo ""

echo "=== Documentation ==="
check_file "$PROJECT_ROOT/docs/integrations/ZOHO_SDK_GUIDE.md" "Zoho SDK guide"
check_file "$PROJECT_ROOT/docs/integrations/TESTING_GUIDE.md" "Testing guide"
check_file "$PROJECT_ROOT/docs/integrations/WEEK2_IMPLEMENTATION_SUMMARY.md" "Implementation summary"
echo ""

echo "=== Configuration ==="
check_file "$PROJECT_ROOT/src/models/config.py" "Configuration models"
check_file "$PROJECT_ROOT/requirements.txt" "Python dependencies"
echo ""

echo "=== Code Statistics ==="
echo ""

if [ -f "$PROJECT_ROOT/src/integrations/zoho/sdk_client.py" ]; then
    SDK_LINES=$(wc -l < "$PROJECT_ROOT/src/integrations/zoho/sdk_client.py" | tr -d ' ')
    echo "SDK Client: $SDK_LINES lines"
fi

if [ -f "$PROJECT_ROOT/src/integrations/zoho/token_store.py" ]; then
    STORE_LINES=$(wc -l < "$PROJECT_ROOT/src/integrations/zoho/token_store.py" | tr -d ' ')
    echo "Token Store: $STORE_LINES lines"
fi

if [ -f "$PROJECT_ROOT/src/integrations/zoho/exceptions.py" ]; then
    EXC_LINES=$(wc -l < "$PROJECT_ROOT/src/integrations/zoho/exceptions.py" | tr -d ' ')
    echo "Exceptions: $EXC_LINES lines"
fi

TOTAL_SOURCE=$((SDK_LINES + STORE_LINES + EXC_LINES))
echo "Total Source Code: $TOTAL_SOURCE lines"
echo ""

if [ -f "$PROJECT_ROOT/tests/unit/integrations/test_token_store.py" ]; then
    TEST1_LINES=$(wc -l < "$PROJECT_ROOT/tests/unit/integrations/test_token_store.py" | tr -d ' ')
    echo "Token Store Tests: $TEST1_LINES lines"
fi

if [ -f "$PROJECT_ROOT/tests/unit/integrations/test_zoho_sdk_client.py" ]; then
    TEST2_LINES=$(wc -l < "$PROJECT_ROOT/tests/unit/integrations/test_zoho_sdk_client.py" | tr -d ' ')
    echo "SDK Client Tests: $TEST2_LINES lines"
fi

if [ -f "$PROJECT_ROOT/tests/integration/test_zoho_sdk.py" ]; then
    TEST3_LINES=$(wc -l < "$PROJECT_ROOT/tests/integration/test_zoho_sdk.py" | tr -d ' ')
    echo "Integration Tests: $TEST3_LINES lines"
fi

TOTAL_TESTS=$((TEST1_LINES + TEST2_LINES + TEST3_LINES))
echo "Total Test Code: $TOTAL_TESTS lines"
echo ""

if [ -f "$PROJECT_ROOT/docs/integrations/ZOHO_SDK_GUIDE.md" ]; then
    DOC1_LINES=$(wc -l < "$PROJECT_ROOT/docs/integrations/ZOHO_SDK_GUIDE.md" | tr -d ' ')
    echo "SDK Guide: $DOC1_LINES lines"
fi

if [ -f "$PROJECT_ROOT/docs/integrations/TESTING_GUIDE.md" ]; then
    DOC2_LINES=$(wc -l < "$PROJECT_ROOT/docs/integrations/TESTING_GUIDE.md" | tr -d ' ')
    echo "Testing Guide: $DOC2_LINES lines"
fi

TOTAL_DOCS=$((DOC1_LINES + DOC2_LINES))
echo "Total Documentation: $TOTAL_DOCS lines"
echo ""

echo "=================================================="
echo "Summary"
echo "=================================================="
echo "Checks Passed: $PASSED"
echo "Checks Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All Week 2 deliverables are present!"
    echo ""
    echo "Next Steps:"
    echo "1. Install dependencies: pip install -r requirements.txt"
    echo "2. Set up database: psql -f migrations/001_create_zoho_tokens_table.sql"
    echo "3. Run tests: pytest tests/unit/integrations/ tests/integration/ -v"
    echo "4. Check coverage: pytest --cov=src/integrations/zoho"
    echo "5. Read documentation: docs/integrations/ZOHO_SDK_GUIDE.md"
    exit 0
else
    echo "❌ Some deliverables are missing!"
    echo "Please review the failed checks above."
    exit 1
fi
