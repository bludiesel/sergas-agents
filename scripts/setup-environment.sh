#!/bin/bash
# Sergas Super Account Manager - Environment Setup Script
# This script sets up the development environment for the project

set -e  # Exit on error

echo "🚀 Sergas Super Account Manager - Environment Setup"
echo "=================================================="

# Check Python version
echo ""
echo "📌 Checking Python version..."
if command -v python3.14 &> /dev/null; then
    PYTHON_CMD=python3.14
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" < "3.14" ]]; then
        echo "⚠️  Warning: Python 3.14+ recommended, found $PYTHON_VERSION"
    fi
else
    echo "❌ Error: Python 3.14+ is required"
    exit 1
fi

echo "✅ Using: $($PYTHON_CMD --version)"

# Create virtual environment
echo ""
echo "📌 Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "📌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "📌 Upgrading pip..."
pip install --upgrade pip
echo "✅ Pip upgraded"

# Install dependencies
echo ""
echo "📌 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed from requirements.txt"
fi

if [ -f "pyproject.toml" ]; then
    pip install poetry
    poetry install
    echo "✅ Dependencies installed from pyproject.toml"
fi

# Install Claude Agent SDK
echo ""
echo "📌 Installing Claude Agent SDK..."
pip install claude-agent-sdk
echo "✅ Claude Agent SDK installed"

# Install Zoho Python SDK
echo ""
echo "📌 Installing Zoho Python SDK v8..."
pip install zohocrmsdk8-0
echo "✅ Zoho Python SDK v8 installed"

# Install development tools
echo ""
echo "📌 Installing development tools..."
pip install pytest pytest-asyncio pytest-cov pylint mypy black isort bandit pre-commit
echo "✅ Development tools installed"

# Setup pre-commit hooks
echo ""
echo "📌 Setting up pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  No .pre-commit-config.yaml found, skipping"
fi

# Create .env file from example
echo ""
echo "📌 Setting up environment variables..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
    echo "⚠️  Please edit .env and add your actual credentials"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo ""
echo "📌 Creating project directories..."
mkdir -p src/{agents,orchestrator,integrations,utils,models,hooks,services}
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p docs/{sparc,api,guides}
mkdir -p config/environments
mkdir -p logs
mkdir -p scripts
mkdir -p .github/workflows
echo "✅ Project directories created"

# Initialize git if not already initialized
echo ""
echo "📌 Initializing git repository..."
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial commit: Project setup"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Setup PostgreSQL (optional)
echo ""
echo "📌 PostgreSQL setup..."
read -p "Do you want to setup PostgreSQL for token persistence? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Setting up PostgreSQL..."
    # Check if PostgreSQL is installed
    if command -v psql &> /dev/null; then
        echo "✅ PostgreSQL is installed"
        echo "Please create database manually:"
        echo "  CREATE DATABASE sergas_agent_db;"
        echo "  CREATE USER sergas_user WITH PASSWORD 'your-password';"
        echo "  GRANT ALL PRIVILEGES ON DATABASE sergas_agent_db TO sergas_user;"
    else
        echo "⚠️  PostgreSQL not found. Please install it manually."
    fi
fi

# Setup Redis (optional)
echo ""
echo "📌 Redis setup..."
read -p "Do you want to setup Redis for caching? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Setting up Redis..."
    if command -v redis-server &> /dev/null; then
        echo "✅ Redis is installed"
        redis-server --version
    else
        echo "⚠️  Redis not found. Please install it manually."
    fi
fi

# Run initial tests
echo ""
echo "📌 Running initial tests..."
if [ -d "tests" ]; then
    pytest tests/ -v || echo "⚠️  Some tests failed (expected at this stage)"
fi

echo ""
echo "=================================================="
echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your credentials"
echo "  2. Setup PostgreSQL database (if needed)"
echo "  3. Setup Redis cache (if needed)"
echo "  4. Run: source venv/bin/activate"
echo "  5. Run: pytest tests/ -v"
echo ""
echo "Happy coding! 🚀"
