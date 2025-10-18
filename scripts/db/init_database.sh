#!/bin/bash
# Initialize PostgreSQL database and user for Sergas Super Account Manager

set -e  # Exit on error

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default values
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-sergas_agent_db}"
DB_USER="${DATABASE_USER:-sergas_user}"
DB_PASSWORD="${DATABASE_PASSWORD}"

echo "🚀 Initializing database..."
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on $DB_HOST:$DB_PORT"
    echo "   Start PostgreSQL first: brew services start postgresql@14"
    exit 1
fi

# Create database user if not exists
echo "📝 Creating database user..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc \
    "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c \
    "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

echo "✅ User '$DB_USER' ready"

# Create database if not exists
echo "📝 Creating database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c \
    "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "✅ Database '$DB_NAME' ready"

# Grant privileges
echo "📝 Granting privileges..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c \
    "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Enable required extensions
echo "📝 Enabling extensions..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d "$DB_NAME" -c \
    "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

echo "✅ Extensions enabled"

# Test connection
echo "🧪 Testing connection..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Connection test successful"
else
    echo "❌ Connection test failed"
    exit 1
fi

echo ""
echo "🎉 Database initialization complete!"
echo ""
echo "Next steps:"
echo "  1. Run migrations: ./scripts/db/run_migrations.sh"
echo "  2. Check health: python scripts/db/check_db_health.py"
