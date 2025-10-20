#!/bin/bash

# SQLite Development Database Setup Script
# This script sets up a local SQLite database for development
# Safe to run multiple times (idempotent)

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================="
echo "SQLite Development Database Setup"
echo "=================================="
echo ""

# Step 1: Create data directory
print_info "Step 1: Creating data directory..."
if [ ! -d "data" ]; then
    mkdir -p data
    print_success "Created data/ directory"
else
    print_success "data/ directory already exists"
fi

# Step 2: Check and setup .env file
print_info "Step 2: Checking .env configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
    else
        print_error ".env.example not found!"
        exit 1
    fi
else
    print_success ".env file already exists"
fi

# Step 3: Configure DATABASE_URL
print_info "Step 3: Configuring DATABASE_URL..."
DATABASE_URL="sqlite:///./data/sergas_agent.db"

if grep -q "^DATABASE_URL=" .env; then
    # Update existing DATABASE_URL
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed syntax
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=${DATABASE_URL}|" .env
    else
        # Linux sed syntax
        sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${DATABASE_URL}|" .env
    fi
    print_success "Updated DATABASE_URL in .env"
else
    # Add DATABASE_URL if it doesn't exist
    echo "DATABASE_URL=${DATABASE_URL}" >> .env
    print_success "Added DATABASE_URL to .env"
fi

# Step 4: Check for required dependencies
print_info "Step 4: Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    print_error "python3 not found! Please install Python 3.8+"
    exit 1
fi
print_success "Python 3 found"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
elif [ -d ".venv" ]; then
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    print_success "Virtual environment activated"
else
    print_info "No virtual environment found. Using system Python."
fi

# Step 5: Check if required packages are installed
print_info "Step 5: Checking for required dependencies..."
MISSING_DEPS=()

if ! python3 -c "import sqlalchemy" 2>/dev/null; then
    MISSING_DEPS+=("sqlalchemy")
fi

if ! python3 -c "import alembic" 2>/dev/null; then
    MISSING_DEPS+=("alembic")
fi

if ! python3 -c "import greenlet" 2>/dev/null; then
    MISSING_DEPS+=("greenlet")
fi

if ! python3 -c "import aiosqlite" 2>/dev/null; then
    MISSING_DEPS+=("aiosqlite")
fi

if ! python3 -c "import dotenv" 2>/dev/null; then
    MISSING_DEPS+=("python-dotenv")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    print_error "Missing dependencies: ${MISSING_DEPS[*]}"
    print_info "Installing dependencies..."
    pip install -q alembic sqlalchemy python-dotenv greenlet aiosqlite
    print_success "Installed required dependencies"
else
    print_success "All dependencies installed"
fi

# Step 6: Run database migrations
print_info "Step 6: Running database migrations..."
if [ -d "migrations" ]; then
    alembic upgrade head
    print_success "Database migrations completed"
else
    print_error "migrations/ directory not found!"
    print_info "You may need to initialize Alembic first with: alembic init migrations"
    exit 1
fi

# Step 7: Create initial test data
print_info "Step 7: Creating initial test data..."
python3 << 'EOF'
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv

    # Load environment variables with explicit path (required for heredoc)
    load_dotenv('.env')

    # Get database URL, fallback to default if not set
    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/sergas_agent.db")

    # Create engine with echo for debugging
    engine = create_engine(database_url, echo=False)

    # Use begin() for automatic transaction management
    with engine.begin() as conn:
        # Check if zoho_tokens table exists and has data
        result = conn.execute(text(
            "SELECT COUNT(*) as count FROM zoho_tokens"
        )).fetchone()

        if result[0] == 0:
            # Insert sample Zoho token
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=1)
            conn.execute(text("""
                INSERT INTO zoho_tokens (
                    token_type, access_token, refresh_token, expires_at,
                    created_at, updated_at
                ) VALUES (
                    :token_type, :access_token, :refresh_token, :expires_at,
                    :created_at, :updated_at
                )
            """), {
                "token_type": "Bearer",
                "access_token": "sample_access_token_for_development",
                "refresh_token": "sample_refresh_token_for_development",
                "expires_at": expires_at,
                "created_at": now,
                "updated_at": now
            })
            print("✓ Created sample Zoho token record")
        else:
            print("✓ Zoho tokens table already has data")

    print("✓ Database initialization complete")

except Exception as e:
    import traceback
    print(f"✗ Error creating test data: {e}", file=sys.stderr)
    print("\nFull traceback:", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    print_success "Initial test data created"
else
    print_error "Failed to create test data"
    exit 1
fi

# Final success message
echo ""
echo "=================================="
print_success "SQLite Database Setup Complete!"
echo "=================================="
echo ""
echo "Database location: ./data/sergas_agent.db"
echo "Configuration: .env"
echo ""
echo "Next steps:"
echo "  1. Review your .env configuration"
echo "  2. Update OAuth credentials with real values"
echo "  3. Start the application: python -m src.main"
echo "  4. Run tests: pytest tests/"
echo ""
