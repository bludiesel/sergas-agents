"""Tests for database migrations."""

import pytest
from sqlalchemy import text, inspect


@pytest.mark.asyncio
class TestMigrations:
    """Test database migrations."""

    async def test_zoho_tokens_table_exists(self, db_session):
        """Test zoho_tokens table exists."""
        result = await db_session.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'zoho_tokens')"
            )
        )
        exists = result.scalar()
        assert exists is True

    async def test_token_refresh_audit_table_exists(self, db_session):
        """Test token_refresh_audit table exists."""
        result = await db_session.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'token_refresh_audit')"
            )
        )
        exists = result.scalar()
        assert exists is True

    async def test_zoho_tokens_columns(self, db_session):
        """Test zoho_tokens has required columns."""
        result = await db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'zoho_tokens'"
            )
        )
        columns = {row[0] for row in result.fetchall()}

        required_columns = {
            "id",
            "token_type",
            "access_token",
            "refresh_token",
            "expires_at",
            "created_at",
            "updated_at",
        }
        assert required_columns.issubset(columns)

    async def test_unique_constraint_exists(self, db_session):
        """Test unique constraint on token_type exists."""
        result = await db_session.execute(
            text(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_name = 'zoho_tokens' AND constraint_type = 'UNIQUE'"
            )
        )
        constraints = [row[0] for row in result.fetchall()]

        assert any("token_type" in c.lower() for c in constraints)

    async def test_indexes_exist(self, db_session):
        """Test required indexes exist."""
        result = await db_session.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename IN ('zoho_tokens', 'token_refresh_audit')"
            )
        )
        indexes = {row[0] for row in result.fetchall()}

        required_indexes = {
            "idx_zoho_tokens_expires_at",
            "idx_zoho_tokens_updated_at",
            "idx_token_refresh_audit_refreshed_at",
            "idx_token_refresh_audit_success",
        }

        assert required_indexes.issubset(indexes)

    async def test_audit_table_columns(self, db_session):
        """Test token_refresh_audit has required columns."""
        result = await db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'token_refresh_audit'"
            )
        )
        columns = {row[0] for row in result.fetchall()}

        required_columns = {
            "id",
            "token_id",
            "token_type",
            "refreshed_at",
            "previous_expires_at",
            "new_expires_at",
            "success",
            "error_message",
        }
        assert required_columns.issubset(columns)

    async def test_not_null_constraints(self, db_session):
        """Test NOT NULL constraints on critical fields."""
        result = await db_session.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'zoho_tokens' AND column_name IN "
                "('token_type', 'access_token', 'refresh_token', 'expires_at')"
            )
        )
        columns = {row[0]: row[1] for row in result.fetchall()}

        # All should be NOT NULL (is_nullable = 'NO')
        for column in ["token_type", "access_token", "refresh_token", "expires_at"]:
            assert columns.get(column) == "NO", f"{column} should be NOT NULL"

    async def test_primary_keys(self, db_session):
        """Test primary key constraints exist."""
        result = await db_session.execute(
            text(
                "SELECT table_name FROM information_schema.table_constraints "
                "WHERE constraint_type = 'PRIMARY KEY' AND "
                "table_name IN ('zoho_tokens', 'token_refresh_audit')"
            )
        )
        tables = {row[0] for row in result.fetchall()}

        assert "zoho_tokens" in tables
        assert "token_refresh_audit" in tables
