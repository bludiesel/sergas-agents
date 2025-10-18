# Database Migrations

This directory contains Alembic database migrations for the Sergas Super Account Manager.

## Quick Start

```bash
# Create migration
alembic revision -m "description of changes"

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

## Migration Files

- `env.py` - Alembic environment configuration with async support
- `script.py.mako` - Template for generating new migrations
- `versions/` - Migration version files

## Current Migrations

1. **001_create_zoho_tokens** - Initial schema with token tables
   - Creates `zoho_tokens` table for OAuth token storage
   - Creates `token_refresh_audit` table for audit logging
   - Adds indexes for performance

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations** in development before production
3. **Never edit applied migrations** - create new ones instead
4. **Keep migrations atomic** - one logical change per migration
5. **Add comments** to migrations for complex changes
6. **Test rollback** to ensure downgrade works

## Environment Variables

Migrations use database configuration from `.env`:

```
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sergas_agent_db
DATABASE_USER=sergas_user
DATABASE_PASSWORD=your-password
```

## Troubleshooting

**Connection refused:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```

**Migration conflicts:**
```bash
# Check current version
alembic current

# View pending migrations
alembic history
```

**Reset database (development only):**
```bash
# Rollback all migrations
alembic downgrade base

# Reapply all migrations
alembic upgrade head
```
