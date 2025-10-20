# Database Configuration Analysis Report

**Date**: 2025-10-19
**Analyst**: Code Quality Analyzer
**Status**: ⚠️ CRITICAL ISSUES FOUND

## Executive Summary

Analysis of the database configuration reveals **critical PostgreSQL-specific type usage in SQLAlchemy models** that will cause failures when using SQLite. The current setup has multiple inconsistencies between schema definitions and adapter implementations.

## Critical Issues Found

### 🔴 Issue 1: PostgreSQL-Specific Types in Models (HIGH SEVERITY)

**Location**: `src/db/models.py`
**Problem**: Uses PostgreSQL-specific types that are incompatible with SQLite

```python
# Lines 8, 175, 178, 339 in src/db/models.py
from sqlalchemy.dialects.postgresql import JSONB, UUID

# AgentSession model - Line 175
context_snapshot: Mapped[dict] = mapped_column(
    JSONB, nullable=False, default=dict  # ❌ JSONB is PostgreSQL-only
)

# AgentSession model - Line 178
account_ids: Mapped[Optional[List[str]]] = mapped_column(
    ARRAY(String), nullable=True  # ❌ ARRAY is PostgreSQL-only
)

# AuditEvent model - Line 339
event_metadata: Mapped[Optional[dict]] = mapped_column(
    JSONB, nullable=True, default=dict  # ❌ JSONB is PostgreSQL-only
)
```

**Impact**:
- SQLAlchemy will fail to create tables with SQLite
- Any queries using these models will raise `OperationalError`
- Database initialization will fail silently or with cryptic errors

**Solution Required**: Use SQLAlchemy's type coercion to map JSONB→JSON and ARRAY→JSON for SQLite

---

### 🔴 Issue 2: Schema Mismatch Between Implementations (MEDIUM SEVERITY)

**Problem**: Three different token table schemas exist in the codebase

#### Schema A: Migration (zoho_tokens)
**File**: `migrations/versions/20241018_0100_create_zoho_tokens.py`
```python
sa.Column('id', sa.Integer(), autoincrement=True, nullable=False)
sa.Column('token_type', sa.String(length=50), nullable=False)
sa.Column('access_token', sa.Text(), nullable=False)
sa.Column('refresh_token', sa.Text(), nullable=False)
sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False)
sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
```

#### Schema B: SQLAlchemy Model (zoho_tokens)
**File**: `src/db/models.py` (ZohoToken class)
```python
# Matches Schema A perfectly ✅
id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
token_type: Mapped[str] = mapped_column(String(50), nullable=False)
access_token: Mapped[str] = mapped_column(Text, nullable=False)
refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

#### Schema C: SQLiteAdapter (oauth_tokens) ❌
**File**: `src/database/sqlite_adapter.py` (Line 72-83)
```python
CREATE TABLE IF NOT EXISTS oauth_tokens (
    token_id TEXT PRIMARY KEY,              # ❌ Different name and type
    service_name TEXT NOT NULL,             # ❌ Extra field
    access_token TEXT NOT NULL,             # ✅ Matches
    refresh_token TEXT,                     # ⚠️ Nullable vs NOT NULL
    expires_at TEXT NOT NULL,               # ⚠️ TEXT vs DateTime
    scope TEXT,                             # ❌ Extra field
    created_at TEXT NOT NULL,               # ⚠️ TEXT vs DateTime
    updated_at TEXT NOT NULL                # ⚠️ TEXT vs DateTime
)
```

**Impact**:
- SQLiteAdapter creates incompatible `oauth_tokens` table
- Alembic migrations create `zoho_tokens` table
- Two token tables will exist with different schemas
- Token persistence will fail due to table name mismatch

---

### 🟡 Issue 3: DATABASE_URL Configuration Inconsistency (MEDIUM SEVERITY)

**Current .env configuration** (Line 132):
```bash
DATABASE_URL=sqlite:///./data/sergas_agent.db
```

**src/db/config.py validator** (Lines 94-104):
```python
@field_validator("database_url")
@classmethod
def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return None

    # Normalizes sqlite:// to sqlite+aiosqlite://
    if v.startswith("sqlite://"):
        if v.startswith("sqlite:///"):
            path = v[10:]  # Remove 'sqlite:///'
            return f"sqlite+aiosqlite:///{path}"
        else:
            path = v[9:]  # Remove 'sqlite://'
            return f"sqlite+aiosqlite:///{path}"

    return v
```

**Analysis**:
- ✅ Configuration is correct
- ✅ Validator properly converts `sqlite://` to `sqlite+aiosqlite://`
- ⚠️ However, multiple database path variables exist:
  - `DATABASE_URL` (Line 132): `sqlite:///./data/sergas_agent.db`
  - `DATABASE_PATH` (Line 82): `./data/sergas.db`
  - Different filenames will create separate database files

---

### 🟡 Issue 4: SQLiteAdapter Independence from Main Schema (LOW SEVERITY)

**Problem**: `sqlite_adapter.py` creates its own schema independently

**File**: `src/database/sqlite_adapter.py` (Lines 35-106)
```python
async def _initialize_schema(self):
    """Initialize database schema"""
    # Creates: agent_sessions, audit_events, oauth_tokens
    # Does NOT use Alembic migrations
    # Does NOT use src/db/models.py definitions
```

**Impact**:
- Schema drift between SQLiteAdapter and Alembic migrations
- No migration tracking for SQLiteAdapter tables
- Manual schema updates required in two places
- Testing databases differ from production schema

---

## Environment Configuration Issues

### Current .env Settings

```bash
# Line 81-83 (.env file)
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/sergas.db

# Line 132 (.env file)
DATABASE_URL=sqlite:///./data/sergas_agent.db
```

**Problems**:
1. **Database filename mismatch**: `sergas.db` vs `sergas_agent.db`
2. **Unused variable**: `DATABASE_TYPE=sqlite` (not referenced in code)
3. **Path inconsistency**: `DATABASE_PATH` used by SQLiteAdapter, `DATABASE_URL` used by SQLAlchemy

---

## Code Quality Assessment

### Positive Findings ✅

1. **Well-documented models**: Clear docstrings and type hints in `src/db/models.py`
2. **Proper async support**: Correct use of `AsyncEngine` and `async_sessionmaker`
3. **Connection pooling**: Appropriate pool configuration for PostgreSQL
4. **WAL mode optimization**: SQLite configured with WAL journal mode
5. **Type safety**: Proper use of SQLAlchemy 2.0 `Mapped[]` types
6. **Error handling**: Comprehensive exception handling in config.py

### Code Smells Detected ⚠️

1. **Duplicate schema definitions**: Token schema defined in 3 places
2. **Hardcoded defaults**: Database paths hardcoded in multiple files
3. **No type fallback**: PostgreSQL types don't degrade gracefully to SQLite
4. **Global singletons**: Multiple global variables in config.py
5. **Mixed sync/async**: SQLiteAdapter uses async, TokenStore uses sync SQLAlchemy

---

## Recommended Fixes

### Priority 1: Fix PostgreSQL Type Incompatibility

**Create**: `src/db/types.py`

```python
"""Database type adapters for cross-database compatibility."""

from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.asyncio import AsyncEngine
import json


class JSONType(TypeDecorator):
    """JSON type that uses JSONB for PostgreSQL, JSON for SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class ArrayType(TypeDecorator):
    """Array type that uses ARRAY for PostgreSQL, JSON-encoded for SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if dialect.name != 'postgresql' and value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != 'postgresql' and value is not None:
            return json.loads(value) if isinstance(value, str) else value
        return value
```

**Update**: `src/db/models.py`

```python
# Replace imports
from sqlalchemy.dialects.postgresql import JSONB, UUID
# With:
from src.db.types import JSONType, ArrayType

# Update models
class AgentSession(Base):
    context_snapshot: Mapped[dict] = mapped_column(
        JSONType, nullable=False, default=dict  # ✅ Cross-compatible
    )
    account_ids: Mapped[Optional[List[str]]] = mapped_column(
        ArrayType, nullable=True  # ✅ Cross-compatible
    )

class AuditEvent(Base):
    event_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONType, nullable=True, default=dict  # ✅ Cross-compatible
    )
```

### Priority 2: Standardize Token Table Schema

**Option A**: Update SQLiteAdapter to match main schema
```python
# src/database/sqlite_adapter.py - Line 72
await conn.execute("""
    CREATE TABLE IF NOT EXISTS zoho_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_type TEXT NOT NULL UNIQUE,
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
""")
```

**Option B**: Remove SQLiteAdapter entirely, use main models
- Delete `src/database/sqlite_adapter.py`
- Use `src/db/models.py` for all database operations
- Run Alembic migrations for schema creation

### Priority 3: Consolidate Database Configuration

**Update**: `.env`

```bash
# Remove DATABASE_TYPE (unused)
# Remove DATABASE_PATH (redundant)

# Single source of truth
DATABASE_URL=sqlite+aiosqlite:///./data/sergas_agent.db
```

**Ensure**: All code references `DATABASE_URL` via `get_database_config()`

---

## Migration Strategy

### Step 1: Create Type Adapters (15 min)
1. Create `src/db/types.py` with JSONType and ArrayType
2. Update imports in `src/db/models.py`
3. Test type conversion with both SQLite and PostgreSQL

### Step 2: Schema Consolidation (30 min)
1. Choose Option A or B for token table
2. Update SQLiteAdapter or remove it
3. Verify Alembic migrations run successfully
4. Test token persistence operations

### Step 3: Configuration Cleanup (10 min)
1. Update `.env` and `.env.example`
2. Remove unused `DATABASE_TYPE` variable
3. Standardize on single `DATABASE_URL`
4. Update documentation

### Step 4: Testing (20 min)
1. Run migrations on clean SQLite database
2. Test all CRUD operations
3. Verify schema matches between SQLite and PostgreSQL modes
4. Validate token refresh workflow

---

## Testing Checklist

- [ ] SQLite database initialization completes without errors
- [ ] All tables created with correct schema (zoho_tokens, not oauth_tokens)
- [ ] JSONB fields serialize/deserialize correctly in SQLite
- [ ] ARRAY fields store/retrieve lists properly in SQLite
- [ ] Token persistence saves and retrieves tokens
- [ ] Alembic migrations apply cleanly
- [ ] No schema version mismatches between adapters
- [ ] Database URL detection works for both sqlite:// and postgresql://
- [ ] WAL mode enabled for SQLite
- [ ] Connection pooling configured appropriately per database type

---

## Files Requiring Changes

### Must Change (Critical)
1. `src/db/models.py` - Replace PostgreSQL types with cross-compatible types
2. `src/database/sqlite_adapter.py` - Fix token table schema or remove

### Should Change (Important)
3. `.env` - Consolidate database configuration variables
4. `.env.example` - Update template with correct configuration

### Nice to Have (Optimization)
5. `src/db/config.py` - Add database type detection logging
6. `src/integrations/zoho/token_store.py` - Migrate to async if using SQLite

---

## Technical Debt Assessment

**Debt Level**: Medium
**Estimated Resolution Time**: 1.5-2 hours
**Risk if Unresolved**: High (application will fail with SQLite in production)

### Debt Items
1. Multiple schema definitions for same table (3 locations)
2. Mixed sync/async database operations
3. Hardcoded database paths in multiple files
4. No database type detection in SQLiteAdapter
5. PostgreSQL-specific optimizations applied to all engines

---

## Conclusion

The database configuration has solid foundations with good async support and proper connection pooling. However, **critical PostgreSQL-specific type usage will prevent SQLite from functioning**. The recommended fixes are straightforward and should take approximately 2 hours to implement and test.

**Next Actions**:
1. Implement cross-database type adapters (Priority 1)
2. Consolidate token table schema (Priority 2)
3. Clean up environment configuration (Priority 3)
4. Run comprehensive testing suite

**Risk Assessment**:
- **Without fixes**: 🔴 Application will fail on SQLite
- **With fixes**: 🟢 Full SQLite/PostgreSQL compatibility
- **Code Quality Score**: 6/10 (current) → 9/10 (after fixes)
