# Database Setup Guide

Complete guide for setting up PostgreSQL database for Sergas Super Account Manager.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [PostgreSQL Installation](#postgresql-installation)
3. [Database Creation](#database-creation)
4. [Running Migrations](#running-migrations)
5. [Connection Configuration](#connection-configuration)
6. [Troubleshooting](#troubleshooting)
7. [Backup & Restore](#backup--restore)

---

## Prerequisites

- PostgreSQL 14+ (recommended: 15 or 16)
- Python 3.14+
- Project dependencies installed (`pip install -r requirements.txt`)

---

## PostgreSQL Installation

### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Verify installation
psql --version
```

### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

### Docker (All Platforms)

```bash
# Run PostgreSQL in Docker
docker run -d \
  --name sergas_postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_USER=sergas_user \
  -e POSTGRES_DB=sergas_agent_db \
  -p 5432:5432 \
  postgres:15-alpine

# Verify container is running
docker ps | grep sergas_postgres
```

---

## Database Creation

### Option 1: Automated Script (Recommended)

```bash
# Make script executable
chmod +x scripts/db/init_database.sh

# Run initialization script
./scripts/db/init_database.sh
```

This script will:
- Create database user `sergas_user`
- Create database `sergas_agent_db`
- Grant necessary privileges
- Enable required extensions (pgcrypto)
- Test database connection

### Option 2: Manual Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create user
CREATE USER sergas_user WITH PASSWORD 'your-secure-password';

# Create database
CREATE DATABASE sergas_agent_db OWNER sergas_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sergas_agent_db TO sergas_user;

# Connect to the new database
\c sergas_agent_db

# Enable extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

# Verify
\l  # List databases
\du  # List users
```

---

## Running Migrations

### Initial Migration

```bash
# Make migration scripts executable
chmod +x scripts/db/run_migrations.sh

# Apply all migrations
./scripts/db/run_migrations.sh
```

### Manual Migration Commands

```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Create new migration
alembic revision -m "description of changes"

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"
```

### Verify Migration Success

```bash
# Connect to database
psql -U sergas_user -d sergas_agent_db

# List tables
\dt

# Expected output:
# zoho_tokens
# token_refresh_audit
# alembic_version

# Describe table structure
\d zoho_tokens
\d token_refresh_audit
```

---

## Connection Configuration

### Environment Variables (.env)

```bash
# Copy example file
cp .env.example .env

# Edit database credentials
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sergas_agent_db
DATABASE_USER=sergas_user
DATABASE_PASSWORD=your-secure-password

# Enable token persistence
TOKEN_PERSISTENCE_ENABLED=true
```

### Connection String Format

```
postgresql+asyncpg://user:password@host:port/database
```

Example:
```
postgresql+asyncpg://sergas_user:mypassword@localhost:5432/sergas_agent_db
```

### Test Connection

```bash
# Using psql
psql -U sergas_user -d sergas_agent_db -h localhost -p 5432

# Using Python script
python scripts/db/check_db_health.py
```

---

## Troubleshooting

### Connection Refused

**Error:**
```
psql: error: connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

**Solutions:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL (macOS)
brew services start postgresql@15

# Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Check PostgreSQL status
brew services list  # macOS
sudo systemctl status postgresql  # Linux
```

### Authentication Failed

**Error:**
```
psql: error: FATAL: password authentication failed for user "sergas_user"
```

**Solutions:**
```bash
# Reset user password
psql -U postgres -c "ALTER USER sergas_user WITH PASSWORD 'new_password';"

# Update .env file with new password
DATABASE_PASSWORD=new_password
```

### Database Does Not Exist

**Error:**
```
psql: error: FATAL: database "sergas_agent_db" does not exist
```

**Solutions:**
```bash
# Create database
psql -U postgres -c "CREATE DATABASE sergas_agent_db OWNER sergas_user;"

# Or run init script
./scripts/db/init_database.sh
```

### Migration Conflicts

**Error:**
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Solutions:**
```bash
# Check current version
alembic current

# View migration history
alembic history --verbose

# Stamp database to specific version
alembic stamp head

# Reapply migrations
alembic upgrade head
```

### Permission Denied

**Error:**
```
ERROR: permission denied for table zoho_tokens
```

**Solutions:**
```bash
# Grant table permissions
psql -U postgres -d sergas_agent_db -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO sergas_user;"

# Grant sequence permissions
psql -U postgres -d sergas_agent_db -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO sergas_user;"
```

---

## Backup & Restore

### Create Backup

```bash
# Full database backup
pg_dump -U sergas_user -d sergas_agent_db -F c -f sergas_backup_$(date +%Y%m%d).dump

# Schema only
pg_dump -U sergas_user -d sergas_agent_db --schema-only -f schema_backup.sql

# Data only
pg_dump -U sergas_user -d sergas_agent_db --data-only -f data_backup.sql

# Specific table
pg_dump -U sergas_user -d sergas_agent_db -t zoho_tokens -F c -f tokens_backup.dump
```

### Restore Backup

```bash
# Restore full backup
pg_restore -U sergas_user -d sergas_agent_db -c sergas_backup_20241018.dump

# Restore from SQL file
psql -U sergas_user -d sergas_agent_db < schema_backup.sql
```

### Automated Backup Script

```bash
#!/bin/bash
# Save as scripts/db/backup_database.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sergas_agent_db_$TIMESTAMP.dump"

mkdir -p "$BACKUP_DIR"

pg_dump -U sergas_user -d sergas_agent_db -F c -f "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
```

---

## Health Checks

### Manual Health Check

```bash
# Connect and run simple query
psql -U sergas_user -d sergas_agent_db -c "SELECT 1;"

# Check table counts
psql -U sergas_user -d sergas_agent_db -c "SELECT COUNT(*) FROM zoho_tokens;"
```

### Automated Health Check

```bash
# Run comprehensive health check
python scripts/db/check_db_health.py

# Expected output:
# ✅ Database connection successful
# ✅ Table 'zoho_tokens' exists
# ✅ Table 'token_refresh_audit' exists
# ✅ All indexes exist
# ✅ All CRUD operations successful
```

---

## Development Workflow

### Reset Database (Development Only)

```bash
# WARNING: This deletes all data!
chmod +x scripts/db/reset_database.sh
./scripts/db/reset_database.sh
```

### Quick Reset for Testing

```bash
# Rollback all migrations
alembic downgrade base

# Reapply migrations
alembic upgrade head

# Run health check
python scripts/db/check_db_health.py
```

---

## Production Considerations

### Security

1. **Use strong passwords:**
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

2. **Restrict database user permissions:**
   ```sql
   -- Create read-only user for monitoring
   CREATE USER monitor_user WITH PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE sergas_agent_db TO monitor_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_user;
   ```

3. **Enable SSL connections:**
   ```bash
   # In postgresql.conf
   ssl = on
   ssl_cert_file = 'server.crt'
   ssl_key_file = 'server.key'
   ```

### Performance

1. **Connection pooling:**
   - Already configured in `src/db/config.py`
   - Pool size: 20 connections
   - Max overflow: 10 connections

2. **Index optimization:**
   ```sql
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM zoho_tokens WHERE expires_at < NOW();
   ```

3. **Vacuum and analyze:**
   ```bash
   # Run weekly
   psql -U sergas_user -d sergas_agent_db -c "VACUUM ANALYZE;"
   ```

### Monitoring

```bash
# Active connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'sergas_agent_db';"

# Database size
psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('sergas_agent_db'));"

# Table sizes
psql -U sergas_user -d sergas_agent_db -c "
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Run health check: `python scripts/db/check_db_health.py`
3. Check logs: `tail -f logs/database.log`
4. Open GitHub issue with error details
