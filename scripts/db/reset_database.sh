#!/bin/bash
# Reset database (DEVELOPMENT ONLY - DESTRUCTIVE!)

set -e  # Exit on error

# Safety check
ENV="${ENV:-development}"
if [ "$ENV" == "production" ]; then
    echo "❌ CANNOT RESET DATABASE IN PRODUCTION!"
    exit 1
fi

# Confirmation prompt
echo "⚠️  WARNING: This will DELETE ALL DATA in the database!"
echo "   Environment: $ENV"
read -p "   Type 'RESET' to confirm: " confirm

if [ "$confirm" != "RESET" ]; then
    echo "❌ Reset cancelled"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-sergas_agent_db}"
DB_USER="${DATABASE_USER:-sergas_user}"

echo "🗑️  Resetting database..."

# Rollback all migrations
echo "📝 Rolling back migrations..."
alembic downgrade base

# Drop all tables (extra safety)
echo "📝 Dropping all tables..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $DB_USER;"

# Reapply migrations
echo "📝 Reapplying migrations..."
alembic upgrade head

echo "✅ Database reset complete!"
echo ""
echo "Next steps:"
echo "  1. Verify tables: psql -U $DB_USER -d $DB_NAME -c '\\dt'"
echo "  2. Check health: python scripts/db/check_db_health.py"
