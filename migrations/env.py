"""Alembic environment configuration for async migrations.

Supports both PostgreSQL and SQLite via DATABASE_URL environment variable:
- PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
- SQLite: DATABASE_URL=sqlite+aiosqlite:///./data/sergas.db
"""

import asyncio
from logging.config import fileConfig
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import models for autogenerate
from src.db.models import Base
from src.db.config import DatabaseConfig

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# Get database URL from environment using DatabaseConfig
db_config = DatabaseConfig()
database_url = db_config.get_connection_string(use_async=True)

# Detect database type for SQLite-specific handling
is_sqlite = database_url.startswith("sqlite")

# Override sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")

    # SQLite-specific configuration
    context_config = {
        "url": url,
        "target_metadata": target_metadata,
        "literal_binds": True,
        "dialect_opts": {"paramstyle": "named"},
        "compare_type": True,
        "compare_server_default": True,
    }

    # For SQLite, disable server default comparison (not fully supported)
    if is_sqlite:
        context_config["compare_server_default"] = False

    context.configure(**context_config)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection.

    Handles both PostgreSQL and SQLite with appropriate settings.
    """
    context_config = {
        "connection": connection,
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
    }

    # SQLite-specific adjustments
    if is_sqlite:
        # Disable server default comparison for SQLite
        context_config["compare_server_default"] = False
        # SQLite doesn't support concurrent transactions
        context_config["transaction_per_migration"] = True

    context.configure(**context_config)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite).
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    # Use NullPool to avoid connection pool issues during migrations
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
