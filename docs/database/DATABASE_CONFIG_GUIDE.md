# Database Configuration Guide

## Overview

The `src/db/config.py` module provides a unified database configuration system that automatically detects and configures either PostgreSQL or SQLite based on environment variables.

## Features

### Automatic Database Detection
- Detects database type from `DATABASE_URL` environment variable
- Falls back to SQLite if no configuration is provided
- Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite) drivers

### PostgreSQL Support
- Connection pooling with configurable parameters
- Automatic connection health checks (pre-ping)
- Async support via asyncpg driver
- Configurable pool size, overflow, timeout, and recycling

### SQLite Support
- WAL (Write-Ahead Logging) mode for better concurrency
- Foreign key enforcement
- Optimized pragmas for performance
- Automatic directory creation for database files
- StaticPool for single-connection async operations

### Production Features
- Proper error handling and logging
- Session management with automatic commit/rollback
- Health check endpoints
- Compatible with Alembic migrations
- Graceful connection cleanup

## Configuration

### Environment Variables

#### PostgreSQL Configuration
```bash
# Option 1: Using DATABASE_URL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Option 2: Using individual parameters
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sergas_agent_db
DATABASE_USER=sergas_user
DATABASE_PASSWORD=your_password

# Connection pooling
POOL_SIZE=20              # Default: 20
MAX_OVERFLOW=10           # Default: 10
POOL_TIMEOUT=30           # Default: 30 seconds
POOL_RECYCLE=3600         # Default: 3600 seconds (1 hour)
```

#### SQLite Configuration
```bash
# Option 1: Using DATABASE_URL
DATABASE_URL=sqlite:///./data/sergas.db

# Option 2: Using database path
DATABASE_PATH=./data/sergas.db
```

#### Feature Flags
```bash
TOKEN_PERSISTENCE_ENABLED=true  # Enable connection pooling (PostgreSQL)
SQL_ECHO=false                  # Log SQL queries (debugging)
```

## Usage Examples

### Basic Usage

```python
from src.db.config import get_engine, get_db_session

# Get configured engine
engine = get_engine()

# Use database session
async with get_db_session() as session:
    result = await session.execute(query)
    await session.commit()
```

### Health Check

```python
from src.db.config import check_database_health

is_healthy = await check_database_health()
if is_healthy:
    print("Database is accessible")
```

### Initialize Schema (Development Only)

```python
from src.db.config import init_database

# WARNING: Only use in development
# Use Alembic migrations in production
await init_database()
```

### Connection Management

```python
from src.db.config import close_database_connections

# Gracefully close all connections
await close_database_connections()
```

## Auto-Detection Logic

The configuration automatically detects the database type using the following logic:

1. **DATABASE_URL provided?**
   - Starts with `postgresql://` or `postgresql+asyncpg://` → PostgreSQL
   - Starts with `sqlite://` or `sqlite+aiosqlite://` → SQLite
   - Unknown scheme → SQLite (with warning)

2. **No DATABASE_URL?**
   - `DATABASE_PASSWORD` set → PostgreSQL (builds URL from individual params)
   - No password → SQLite (default to `./data/sergas.db`)

## Database-Specific Optimizations

### PostgreSQL
- **QueuePool**: Maintains pool of reusable connections
- **pool_pre_ping**: Verifies connections before use
- **pool_recycle**: Recycles connections after timeout
- **max_overflow**: Additional connections during high load

### SQLite
- **WAL mode**: Better concurrency for read/write operations
- **Foreign keys**: Enforced referential integrity
- **Synchronous=NORMAL**: Balanced performance and safety
- **Cache size**: 64MB for improved performance
- **Temp store=MEMORY**: Fast temporary table operations

## Migration Compatibility

The configuration is fully compatible with Alembic migrations:

```python
# migrations/env.py
from src.db.config import DatabaseConfig

db_config = DatabaseConfig()
database_url = db_config.get_connection_string(use_async=True)

config.set_main_option("sqlalchemy.url", database_url)
```

## Testing

Comprehensive test suite available in `tests/unit/test_db_config.py`:

```bash
# Run tests
pytest tests/unit/test_db_config.py -v

# Test coverage
pytest tests/unit/test_db_config.py --cov=src.db.config
```

### Test Coverage
- ✅ Default SQLite configuration
- ✅ PostgreSQL detection from URL
- ✅ SQLite detection from URL
- ✅ URL normalization (sqlite:// → sqlite+aiosqlite://)
- ✅ Individual parameter configuration
- ✅ Backward compatibility
- ✅ Async vs sync drivers
- ✅ Configuration precedence
- ✅ Singleton pattern
- ✅ Connection pooling
- ✅ Feature flags
- ✅ Path resolution

## API Reference

### Functions

#### `get_database_config() -> DatabaseConfig`
Returns singleton database configuration instance.

#### `get_database_url() -> str`
Returns the configured database URL with async driver.

#### `get_engine(force_recreate: bool = False) -> AsyncEngine`
Returns the configured SQLAlchemy async engine.

#### `get_async_session_maker() -> async_sessionmaker`
Returns the session factory for creating database sessions.

#### `get_db_session() -> AsyncGenerator[AsyncSession, None]`
Context manager for database sessions with automatic transaction management.

#### `check_database_health() -> bool`
Verifies database connection health.

#### `init_database() -> None`
Creates all database tables (development only).

#### `drop_all_tables() -> None`
Drops all database tables (development only, blocked in production).

#### `close_database_connections() -> None`
Gracefully closes all database connections.

### Classes

#### `DatabaseConfig`
Pydantic settings class for database configuration.

**Attributes:**
- `host`: PostgreSQL host (default: "localhost")
- `port`: PostgreSQL port (default: 5432)
- `name`: Database name (default: "sergas_agent_db")
- `user`: Database user (default: "sergas_user")
- `password`: Database password (default: "")
- `database_url`: Connection string override (default: None)
- `sqlite_path`: SQLite database path (default: "./data/sergas.db")
- `pool_size`: Connection pool size (default: 20)
- `max_overflow`: Maximum overflow connections (default: 10)
- `pool_timeout`: Pool checkout timeout (default: 30s)
- `pool_recycle`: Connection recycle time (default: 3600s)
- `token_persistence_enabled`: Enable connection pooling (default: True)
- `enable_sql_echo`: Log SQL queries (default: False)

**Methods:**
- `detect_database_type() -> DatabaseType`: Returns "postgresql" or "sqlite"
- `get_database_url(use_async: bool = True) -> str`: Build connection string
- `get_connection_string(use_async: bool = True) -> str`: Alias for get_database_url

## Troubleshooting

### SQLite Permission Errors
Ensure the directory for the SQLite database exists and has write permissions:
```bash
mkdir -p ./data
chmod 755 ./data
```

### PostgreSQL Connection Issues
Verify PostgreSQL is running and credentials are correct:
```bash
psql -h localhost -U sergas_user -d sergas_agent_db
```

### Migration Errors
Ensure Alembic is using the correct database URL:
```bash
alembic current
alembic upgrade head
```

### Import Errors
If you get `ModuleNotFoundError` for asyncpg or aiosqlite:
```bash
# For PostgreSQL
pip install asyncpg

# For SQLite
pip install aiosqlite
```

## Best Practices

1. **Use Alembic for Migrations**: Never use `init_database()` in production
2. **Set TOKEN_PERSISTENCE_ENABLED=true**: For production PostgreSQL deployments
3. **Configure Pool Settings**: Based on your application's concurrency needs
4. **Use Health Checks**: Implement readiness probes using `check_database_health()`
5. **Graceful Shutdown**: Always call `close_database_connections()` on shutdown
6. **Environment-Specific Config**: Use different `.env` files per environment
7. **Secure Credentials**: Never commit `.env` files with real credentials

## Example Configurations

### Development (SQLite)
```bash
ENV=development
DATABASE_PATH=./data/dev.db
SQL_ECHO=true
```

### Testing (SQLite)
```bash
ENV=testing
DATABASE_URL=sqlite:///./data/test.db
SQL_ECHO=false
```

### Production (PostgreSQL)
```bash
ENV=production
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/production_db
POOL_SIZE=50
MAX_OVERFLOW=20
POOL_RECYCLE=1800
TOKEN_PERSISTENCE_ENABLED=true
SQL_ECHO=false
```

## Related Files

- `/src/db/config.py` - Database configuration implementation
- `/src/db/models.py` - SQLAlchemy ORM models
- `/migrations/env.py` - Alembic migration configuration
- `/tests/unit/test_db_config.py` - Comprehensive test suite
- `/.env.example` - Example environment configuration
