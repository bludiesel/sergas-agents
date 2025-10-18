#!/bin/bash
# Sergas Super Account Manager - Environment Setup Script
# This script sets up the complete development environment

set -e  # Exit on error

echo "=========================================="
echo "Sergas Super Account Manager Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Found Python $python_version${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "\n${GREEN}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Install dependencies
echo -e "\n${YELLOW}Installing core dependencies...${NC}"
pip install -r requirements-core.txt

# Install pre-commit hooks
echo -e "\n${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install

# Create necessary directories
echo -e "\n${YELLOW}Creating project directories...${NC}"
mkdir -p src/{agents,zoho,cognee,api,database,security,monitoring}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs/{api,architecture,deployment}
mkdir -p logs
mkdir -p config
mkdir -p scripts
echo -e "${GREEN}Directories created${NC}"

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "\n${YELLOW}Creating .env file...${NC}"
        cp .env.example .env
        echo -e "${GREEN}.env file created${NC}"
        echo -e "${YELLOW}Please update .env with your configuration${NC}"
    fi
fi

# Run validation tests
echo -e "\n${YELLOW}Running environment validation tests...${NC}"
pytest tests/test_environment.py -v

echo -e "\n${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo -e "\nTo activate the virtual environment:"
echo -e "  ${GREEN}source venv/bin/activate${NC}"
echo -e "\nTo run tests:"
echo -e "  ${GREEN}pytest${NC}"
echo -e "\nTo start development:"
echo -e "  ${GREEN}./scripts/dev_server.sh${NC}"
