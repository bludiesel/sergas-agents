#!/bin/bash
# Quick environment validation script
# Run this anytime to verify environment health

set -e

echo "================================================"
echo "Sergas Environment Validation"
echo "================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found${NC}"
    exit 1
fi

# Check Python version
echo -e "\n${YELLOW}Python Version:${NC}"
python --version

# Check key packages
echo -e "\n${YELLOW}Key Packages:${NC}"
python -c "import pydantic; print(f'✓ Pydantic {pydantic.__version__}')"
python -c "import fastapi; print(f'✓ FastAPI {fastapi.__version__}')"
python -c "import zohocrmsdk; print('✓ Zoho CRM SDK installed')"
python -c "import pytest; print(f'✓ Pytest {pytest.__version__}')"
python -c "import sqlalchemy; print(f'✓ SQLAlchemy {sqlalchemy.__version__}')"

# Run tests
echo -e "\n${YELLOW}Running Tests:${NC}"
pytest tests/test_environment.py -v --tb=short

echo -e "\n${GREEN}================================================"
echo "Validation Complete!"
echo "================================================${NC}"
