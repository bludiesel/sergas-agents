#!/bin/bash
# Run Alembic database migrations

set -e  # Exit on error

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Running database migrations..."

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Install it first:"
    echo "   pip install alembic"
    exit 1
fi

# Check database connection
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-sergas_agent_db}"

echo "📝 Checking database connection..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    echo "❌ Cannot connect to PostgreSQL on $DB_HOST:$DB_PORT"
    exit 1
fi

# Show current migration version
echo "📊 Current migration version:"
alembic current

# Show pending migrations
echo ""
echo "📋 Pending migrations:"
alembic history

# Apply migrations
echo ""
echo "🔄 Applying migrations..."
alembic upgrade head

# Show new version
echo ""
echo "✅ Migrations complete!"
echo "📊 New migration version:"
alembic current

echo ""
echo "🎉 Database is up to date!"
