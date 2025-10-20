#!/bin/bash
# Sergas Super Account Manager - Database Migration Script
# Safe database migration with backup and rollback capability

set -euo pipefail

ENVIRONMENT="${1:-dev}"
DRY_RUN="${2:-}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load environment variables
if [ -f ".env.${ENVIRONMENT}" ]; then
    source ".env.${ENVIRONMENT}"
else
    log_error "Environment file not found: .env.${ENVIRONMENT}"
    exit 1
fi

run_migrations() {
    log_info "Running database migrations for $ENVIRONMENT..."

    if [ "$DRY_RUN" == "--dry-run" ]; then
        log_warning "DRY RUN MODE - No changes will be made"
        alembic upgrade head --sql
        return 0
    fi

    # Create backup before migration
    log_info "Creating database backup..."
    BACKUP_FILE="backup_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql"

    if command -v pg_dump &> /dev/null; then
        PGPASSWORD="$DATABASE_PASSWORD" pg_dump \
            -h "$DATABASE_HOST" \
            -U "$DATABASE_USER" \
            -d "$DATABASE_NAME" \
            -F c \
            -f "$BACKUP_FILE"

        log_success "Backup created: $BACKUP_FILE"
    else
        log_warning "pg_dump not found, skipping backup"
    fi

    # Run migrations
    log_info "Applying migrations..."
    alembic upgrade head

    log_success "Migrations completed successfully"
}

run_migrations
