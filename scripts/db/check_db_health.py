#!/usr/bin/env python3
"""Database health check script.

Verifies database connectivity, schema, and basic operations.
"""

import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select, text

# Add project root to path
sys.path.insert(0, ".")

from src.db.config import (
    check_database_health,
    get_db_session,
    db_config,
)
from src.db.models import ZohoToken
import structlog

logger = structlog.get_logger(__name__)


async def check_connection() -> bool:
    """Check basic database connectivity."""
    print("🔍 Checking database connection...")
    try:
        result = await check_database_health()
        if result:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
        return result
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


async def check_tables() -> bool:
    """Check if required tables exist."""
    print("\n🔍 Checking database tables...")
    try:
        async with get_db_session() as session:
            # Check zoho_tokens table
            result = await session.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'zoho_tokens')"
                )
            )
            zoho_tokens_exists = result.scalar()

            # Check token_refresh_audit table
            result = await session.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'token_refresh_audit')"
                )
            )
            audit_exists = result.scalar()

            if zoho_tokens_exists:
                print("✅ Table 'zoho_tokens' exists")
            else:
                print("❌ Table 'zoho_tokens' missing")

            if audit_exists:
                print("✅ Table 'token_refresh_audit' exists")
            else:
                print("❌ Table 'token_refresh_audit' missing")

            return zoho_tokens_exists and audit_exists
    except Exception as e:
        print(f"❌ Table check error: {e}")
        return False


async def check_indexes() -> bool:
    """Check if required indexes exist."""
    print("\n🔍 Checking database indexes...")
    required_indexes = [
        "idx_zoho_tokens_expires_at",
        "idx_zoho_tokens_updated_at",
        "idx_token_refresh_audit_refreshed_at",
        "idx_token_refresh_audit_success",
    ]

    try:
        async with get_db_session() as session:
            all_exist = True
            for index_name in required_indexes:
                result = await session.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM pg_indexes "
                        f"WHERE indexname = '{index_name}')"
                    )
                )
                exists = result.scalar()
                if exists:
                    print(f"✅ Index '{index_name}' exists")
                else:
                    print(f"❌ Index '{index_name}' missing")
                    all_exist = False

            return all_exist
    except Exception as e:
        print(f"❌ Index check error: {e}")
        return False


async def test_crud_operations() -> bool:
    """Test basic CRUD operations."""
    print("\n🔍 Testing CRUD operations...")
    try:
        from src.db.repositories.token_repository import TokenRepository

        repo = TokenRepository()

        # Create test token
        print("  📝 Creating test token...")
        token = await repo.save_token(
            token_type="test",
            access_token="test_access_token_12345",
            refresh_token="test_refresh_token_67890",
            expires_in=3600,
        )
        print(f"  ✅ Token created: ID={token.id}")

        # Read token
        print("  📖 Reading token...")
        retrieved = await repo.get_latest_token("test")
        if retrieved and retrieved.id == token.id:
            print(f"  ✅ Token retrieved: ID={retrieved.id}")
        else:
            print("  ❌ Token retrieval failed")
            return False

        # Update token
        print("  🔄 Updating token...")
        updated = await repo.refresh_token_record(
            token_id=token.id,
            new_access_token="new_access_token_99999",
            new_expires_in=7200,
        )
        print(f"  ✅ Token updated: ID={updated.id}")

        # Delete token
        print("  🗑️  Deleting token...")
        deleted = await repo.delete_token("test")
        if deleted:
            print("  ✅ Token deleted")
        else:
            print("  ❌ Token deletion failed")
            return False

        print("✅ All CRUD operations successful")
        return True

    except Exception as e:
        print(f"❌ CRUD operations error: {e}")
        return False


async def show_config() -> None:
    """Display current database configuration."""
    print("\n📊 Database Configuration:")
    print(f"  Host: {db_config.host}")
    print(f"  Port: {db_config.port}")
    print(f"  Database: {db_config.name}")
    print(f"  User: {db_config.user}")
    print(f"  Pool Size: {db_config.pool_size}")
    print(f"  Max Overflow: {db_config.max_overflow}")
    print(f"  Pool Timeout: {db_config.pool_timeout}s")
    print(f"  Token Persistence: {db_config.token_persistence_enabled}")


async def main() -> int:
    """Run all health checks."""
    print("=" * 60)
    print("🏥 Database Health Check")
    print("=" * 60)

    await show_config()

    checks = [
        ("Connection", check_connection()),
        ("Tables", check_tables()),
        ("Indexes", check_indexes()),
        ("CRUD Operations", test_crud_operations()),
    ]

    results = []
    for name, check in checks:
        result = await check
        results.append((name, result))

    # Summary
    print("\n" + "=" * 60)
    print("📋 Health Check Summary")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All health checks passed!")
        return 0
    else:
        print("\n⚠️  Some health checks failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
