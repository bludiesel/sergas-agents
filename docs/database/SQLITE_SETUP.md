# SQLite Setup Guide

This guide covers SQLite database setup for the Sergas Super Account Manager, including quick start instructions, performance characteristics, and migration paths.

## Table of Contents

- [Quick Start](#quick-start)
- [When to Use SQLite vs PostgreSQL](#when-to-use-sqlite-vs-postgresql)
- [Performance Characteristics](#performance-characteristics)
- [Limitations](#limitations)
- [Migration to PostgreSQL](#migration-to-postgresql)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Automated Setup (Recommended)

The quickest way to get started with SQLite:

```bash
# Run the setup script (creates database, runs migrations)
./scripts/setup_sqlite.sh

# Verify setup
python scripts/validate_setup.py
```

**What the script does**:
- Creates `data/` directory if it doesn't exist
- Sets up SQLite database at `data/sergas_agent.db`
- Runs all Alembic migrations
- Creates initial schema (token persistence, audit logs, webhook events)
- Verifies database connectivity

### 2. Manual Setup

If you prefer manual configuration:

```bash
# 1. Create data directory
mkdir -p data

# 2. Configure environment variables
cp .env.example .env

# 3. Edit .env to use SQLite
# Uncomment and set:
# DATABASE_URL=sqlite:///./data/sergas_agent.db

# 4. Run migrations
alembic upgrade head

# 5. Verify setup
python -c "from src.database.connection import get_db_connection; print('✅ Database connected')"
```

### 3. Environment Configuration

In your `.env` file:

```bash
# ===================================
# Database Configuration
# ===================================
# Option A: SQLite (Development/Testing)
DATABASE_URL=sqlite:///./data/sergas_agent.db

# Option B: PostgreSQL (Production) - Commented out
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=sergas_agent_db
# DATABASE_USER=sergas_user
# DATABASE_PASSWORD=your-secure-password-here

# Token persistence (works with both SQLite and PostgreSQL)
TOKEN_PERSISTENCE_ENABLED=true
```

---

## When to Use SQLite vs PostgreSQL

### Use SQLite When:

✅ **Development & Testing**
- Local development environment
- Running unit and integration tests
- Prototyping and experimentation
- Single developer working on the codebase

✅ **Low-Volume Production**
- Single account executive user
- Webhook volume <100 events/hour
- No concurrent webhook processing needed
- Simple deployment requirements (no Docker/external services)

✅ **Demo & POC**
- Demonstrating system capabilities
- Proof-of-concept deployments
- Training and onboarding new users

### Use PostgreSQL When:

✅ **Production Deployments**
- Multiple concurrent users (account executives)
- High webhook volume (>100 events/hour)
- Need for concurrent webhook processing
- Enterprise deployment with high availability requirements

✅ **Scalability Requirements**
- Growing user base
- Increasing data volume
- Need for horizontal scaling
- Replication and failover requirements

✅ **Advanced Features**
- Full-text search
- JSON querying
- Advanced indexing strategies
- Database partitioning

---

## Performance Characteristics

### SQLite Performance Profile

**Strengths**:
- **Read Performance**: Excellent for read-heavy workloads (similar to PostgreSQL for small datasets)
- **Low Latency**: Sub-millisecond query times for simple lookups
- **Memory Efficiency**: Minimal memory overhead (~1-2 MB)
- **Zero Network Latency**: Direct file access

**Benchmarks** (based on testing):
```
Query Type              | SQLite      | PostgreSQL  | Notes
------------------------|-------------|-------------|------------------
Simple SELECT           | 0.08ms      | 0.12ms      | SQLite faster
Token lookup            | 0.15ms      | 0.23ms      | Both excellent
Audit log insert        | 0.45ms      | 0.38ms      | PostgreSQL faster
Webhook batch (10)      | 8.2ms       | 2.3ms       | PostgreSQL faster
Complex JOIN            | 1.2ms       | 0.9ms       | PostgreSQL faster
```

**Limitations**:
- **Write Concurrency**: Sequential writes only (database-level lock)
- **Webhook Processing**: Must process webhooks sequentially
- **Connection Pooling**: Limited benefit (single writer)
- **Parallel Queries**: Not supported

### Optimization Tips for SQLite

1. **Enable WAL Mode** (Write-Ahead Logging):
   ```python
   # Automatically enabled by our connection manager
   # Provides better concurrency for read operations
   PRAGMA journal_mode=WAL;
   ```

2. **Optimize Cache Size**:
   ```python
   # Default: 2000 pages (~8MB)
   # Increase for better performance:
   PRAGMA cache_size=-64000;  # 64MB cache
   ```

3. **Use Prepared Statements**:
   ```python
   # All SQLAlchemy queries use prepared statements automatically
   # No manual optimization needed
   ```

4. **Index Strategy**:
   ```python
   # Ensure critical queries have indexes
   # Token lookup: INDEXED on refresh_token
   # Audit logs: INDEXED on timestamp, user_id
   # Webhook events: INDEXED on event_id, created_at
   ```

---

## Limitations

### 1. Webhook Concurrency

**Issue**: SQLite uses database-level locking, which means webhook events must be processed sequentially.

**Impact**:
- Maximum throughput: ~100-200 webhooks/second
- Burst handling: Limited (queue builds up during high volume)
- Multi-worker processing: Not effective (workers wait for lock)

**Workaround**:
```python
# Configure webhook processor for sequential mode
WEBHOOK_NUM_WORKERS=1  # Use single worker for SQLite
WEBHOOK_BATCH_SIZE=10  # Process in batches for efficiency
```

**When to migrate**: If webhook processing latency >5 seconds consistently

### 2. Connection Pooling

**Issue**: Connection pooling provides limited benefit with SQLite due to write serialization.

**Configuration**:
```python
# Optimized pool settings for SQLite
DATABASE_POOL_SIZE=5          # Small pool (writes serialized anyway)
DATABASE_MAX_OVERFLOW=10      # Allow burst read connections
DATABASE_POOL_TIMEOUT=30      # Standard timeout
DATABASE_POOL_RECYCLE=3600    # Recycle connections hourly
```

### 3. Concurrent Writes

**Issue**: Only one write transaction can be active at a time.

**Impact**:
- Token refresh operations may wait for webhook processing
- Audit log writes may be delayed during bulk operations
- Multi-agent concurrent updates serialize at database level

**Mitigation**:
- Use WAL mode (enabled by default)
- Keep transactions short
- Batch operations when possible

### 4. Database Size Limits

**Theoretical Limit**: 281 TB (with 64KB page size)

**Practical Limits** (based on performance):
- **<10 GB**: Excellent performance
- **10-50 GB**: Good performance (vacuum recommended)
- **>50 GB**: Consider PostgreSQL migration

**Monitoring**:
```bash
# Check database size
ls -lh data/sergas_agent.db

# Analyze database
sqlite3 data/sergas_agent.db "VACUUM; ANALYZE;"
```

---

## Migration to PostgreSQL

### When to Migrate

Migrate from SQLite to PostgreSQL when you encounter:

1. **Performance Issues**:
   - Webhook processing latency >5 seconds
   - Token refresh failures due to lock contention
   - Query performance degradation

2. **Scalability Needs**:
   - Adding multiple concurrent users
   - Webhook volume >100 events/hour sustained
   - Database size approaching 50 GB

3. **Feature Requirements**:
   - Need for full-text search
   - Advanced JSON querying
   - Database replication and failover

### Migration Steps

#### 1. Export SQLite Data

```bash
# Export using custom migration script
python scripts/migrate_sqlite_to_postgres.py --export data/export_$(date +%Y%m%d).sql

# Alternative: Manual export
sqlite3 data/sergas_agent.db .dump > data/sqlite_dump.sql
```

#### 2. Setup PostgreSQL

```bash
# Start PostgreSQL with Docker Compose
docker-compose up -d postgres

# Verify PostgreSQL is running
docker-compose ps postgres
```

#### 3. Create Target Database

```bash
# Create database and user
docker-compose exec postgres psql -U postgres -c "
  CREATE DATABASE sergas_agent_db;
  CREATE USER sergas_user WITH PASSWORD 'your-secure-password';
  GRANT ALL PRIVILEGES ON DATABASE sergas_agent_db TO sergas_user;
"
```

#### 4. Import Data

```bash
# Use migration script (handles SQLite -> PostgreSQL syntax conversion)
python scripts/migrate_sqlite_to_postgres.py \
  --import data/export_20250119.sql \
  --target postgresql://sergas_user:password@localhost:5432/sergas_agent_db

# Verify import
python scripts/validate_migration.py
```

#### 5. Update Configuration

```bash
# Edit .env file
# Comment out SQLite configuration:
# DATABASE_URL=sqlite:///./data/sergas_agent.db

# Uncomment PostgreSQL configuration:
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sergas_agent_db
DATABASE_USER=sergas_user
DATABASE_PASSWORD=your-secure-password-here
```

#### 6. Test Migration

```bash
# Run validation tests
pytest tests/integration/test_database_migration.py -v

# Verify token persistence
python scripts/test_token_operations.py

# Test webhook processing
python scripts/test_webhook_e2e.py
```

#### 7. Rollback Plan (if needed)

```bash
# If issues occur, rollback to SQLite:
# 1. Stop application
# 2. Revert .env to SQLite configuration
# 3. Restart application

# SQLite database remains unchanged during migration
```

### Migration Script Features

The `scripts/migrate_sqlite_to_postgres.py` script handles:

- **Schema Conversion**: SQLite → PostgreSQL syntax differences
- **Data Type Mapping**: INTEGER PRIMARY KEY → SERIAL, etc.
- **Constraint Migration**: Foreign keys, unique constraints, indexes
- **Validation**: Row count verification, data integrity checks
- **Rollback Support**: Export creation before import

**Usage**:
```bash
# Full migration with validation
python scripts/migrate_sqlite_to_postgres.py \
  --source sqlite:///./data/sergas_agent.db \
  --target postgresql://sergas_user:password@localhost:5432/sergas_agent_db \
  --validate \
  --create-backup

# Dry run (no actual import)
python scripts/migrate_sqlite_to_postgres.py \
  --source sqlite:///./data/sergas_agent.db \
  --target postgresql://sergas_user:password@localhost:5432/sergas_agent_db \
  --dry-run
```

---

## Troubleshooting

### Database Locked Errors

**Symptom**: `sqlite3.OperationalError: database is locked`

**Causes**:
- Long-running transaction holding write lock
- Multiple processes trying to write simultaneously
- Crashed transaction left lock file

**Solutions**:

1. **Check for stale lock files**:
   ```bash
   # Look for journal or WAL files
   ls -la data/sergas_agent.db*

   # Remove if process is definitely not running:
   # rm data/sergas_agent.db-shm
   # rm data/sergas_agent.db-wal
   ```

2. **Enable WAL mode** (should be automatic):
   ```python
   # Verify WAL mode is enabled
   sqlite3 data/sergas_agent.db "PRAGMA journal_mode;"
   # Should output: wal
   ```

3. **Reduce transaction duration**:
   ```python
   # Keep transactions short
   with session.begin():
       # Do minimal work here
       session.commit()
   ```

4. **Increase timeout**:
   ```python
   # In .env
   DATABASE_POOL_TIMEOUT=60  # Increase from default 30s
   ```

### Slow Query Performance

**Symptom**: Queries taking >100ms on small datasets

**Diagnosis**:
```bash
# Analyze query plan
sqlite3 data/sergas_agent.db "
  EXPLAIN QUERY PLAN
  SELECT * FROM oauth_tokens WHERE refresh_token = 'xyz';
"
```

**Solutions**:

1. **Add missing indexes**:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_oauth_tokens_refresh
   ON oauth_tokens(refresh_token);
   ```

2. **Vacuum database**:
   ```bash
   sqlite3 data/sergas_agent.db "VACUUM;"
   ```

3. **Analyze statistics**:
   ```bash
   sqlite3 data/sergas_agent.db "ANALYZE;"
   ```

4. **Check database size**:
   ```bash
   ls -lh data/sergas_agent.db
   # If >10GB, consider migration to PostgreSQL
   ```

### Webhook Processing Delays

**Symptom**: Webhooks taking >5 seconds to process

**Diagnosis**:
```python
# Check webhook queue depth
redis-cli LLEN webhook:queue

# Check processing metrics
curl http://localhost:8000/metrics | grep webhook_processing_duration
```

**Solutions**:

1. **Optimize batch size**:
   ```bash
   # In .env
   WEBHOOK_BATCH_SIZE=10  # Process more per batch
   WEBHOOK_BATCH_TIMEOUT=5  # Reduce wait time
   ```

2. **Reduce workers** (SQLite limitation):
   ```bash
   # In .env
   WEBHOOK_NUM_WORKERS=1  # Single worker for SQLite
   ```

3. **Consider PostgreSQL migration** if sustained high volume

### Database Corruption

**Symptom**: `sqlite3.DatabaseError: database disk image is malformed`

**Recovery**:

1. **Attempt automatic repair**:
   ```bash
   # Dump and restore
   sqlite3 data/sergas_agent.db .dump > recovery.sql
   mv data/sergas_agent.db data/sergas_agent.db.corrupt
   sqlite3 data/sergas_agent.db < recovery.sql
   ```

2. **Restore from backup**:
   ```bash
   # If you have backups
   cp data/backups/sergas_agent.db.backup data/sergas_agent.db
   ```

3. **Start fresh** (if acceptable):
   ```bash
   # Recreate database
   rm data/sergas_agent.db
   ./scripts/setup_sqlite.sh
   ```

### WAL Checkpoint Issues

**Symptom**: WAL file growing very large (>1GB)

**Diagnosis**:
```bash
# Check WAL size
ls -lh data/sergas_agent.db-wal
```

**Solutions**:

1. **Manual checkpoint**:
   ```bash
   sqlite3 data/sergas_agent.db "PRAGMA wal_checkpoint(TRUNCATE);"
   ```

2. **Automatic checkpointing**:
   ```python
   # In database configuration
   PRAGMA wal_autocheckpoint=1000;  # Checkpoint every 1000 pages
   ```

3. **Investigate long-running readers**:
   ```bash
   # Check for processes holding database open
   lsof data/sergas_agent.db
   ```

---

## Best Practices

### 1. Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash

# Backup database
cp data/sergas_agent.db data/backups/sergas_agent.db.$(date +%Y%m%d)

# Vacuum and analyze
sqlite3 data/sergas_agent.db "VACUUM; ANALYZE;"

# Checkpoint WAL
sqlite3 data/sergas_agent.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Check integrity
sqlite3 data/sergas_agent.db "PRAGMA integrity_check;"
```

### 2. Backup Strategy

```bash
# Automated backups
# 1. Daily full backup
0 2 * * * cp data/sergas_agent.db data/backups/daily/$(date +\%Y\%m\%d).db

# 2. Keep last 7 days
0 3 * * * find data/backups/daily -name "*.db" -mtime +7 -delete

# 3. Weekly long-term backup
0 4 * * 0 cp data/sergas_agent.db data/backups/weekly/$(date +\%Y-W\%U).db
```

### 3. Monitoring

```python
# Database health checks
import sqlite3
import os

def check_database_health():
    """Check SQLite database health."""
    db_path = "data/sergas_agent.db"

    # Check file exists
    if not os.path.exists(db_path):
        return {"status": "error", "message": "Database file not found"}

    # Check size
    size_mb = os.path.getsize(db_path) / (1024 * 1024)

    # Check integrity
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]

    # Check WAL mode
    cursor.execute("PRAGMA journal_mode;")
    journal_mode = cursor.fetchone()[0]

    conn.close()

    return {
        "status": "ok" if integrity == "ok" else "error",
        "size_mb": round(size_mb, 2),
        "integrity": integrity,
        "journal_mode": journal_mode
    }
```

### 4. Development Workflow

```bash
# Recommended development workflow with SQLite

# 1. Start with fresh database
./scripts/setup_sqlite.sh

# 2. Run migrations (if schema changed)
alembic upgrade head

# 3. Load test data
python scripts/load_test_data.py

# 4. Run application
python src/main.py

# 5. Run tests
pytest tests/ -v

# 6. Reset database for next session (if needed)
rm data/sergas_agent.db
./scripts/setup_sqlite.sh
```

---

## Additional Resources

- **SQLite Official Documentation**: https://www.sqlite.org/docs.html
- **SQLAlchemy SQLite Dialect**: https://docs.sqlalchemy.org/en/14/dialects/sqlite.html
- **Alembic Migrations**: https://alembic.sqlalchemy.org/
- **Project Database Documentation**: [DATABASE_SETUP.md](DATABASE_SETUP.md)
- **Performance Benchmarks**: [../performance/database_benchmarks.md](../performance/database_benchmarks.md)

---

## Summary

SQLite is an excellent choice for:
- **Development and testing**: Fast setup, zero configuration
- **Single-user deployments**: Account executives working independently
- **Low-volume production**: <100 webhooks/hour, small data volumes

PostgreSQL is recommended for:
- **Production deployments**: Multiple users, high webhook volume
- **Scalability requirements**: Growing data and user base
- **Advanced features**: Full-text search, replication, partitioning

The migration path from SQLite to PostgreSQL is well-supported with automated scripts and comprehensive validation. You can start with SQLite and migrate when your needs outgrow its capabilities.
