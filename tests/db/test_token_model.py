"""Tests for ZohoToken ORM model."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from src.db.models import ZohoToken, TokenRefreshAudit


@pytest.mark.asyncio
class TestZohoTokenModel:
    """Test ZohoToken model."""

    async def test_create_token(self, db_session, sample_token_data):
        """Test creating a new token record."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=sample_token_data["expires_in"]
        )

        token = ZohoToken(
            token_type=sample_token_data["token_type"],
            access_token=sample_token_data["access_token"],
            refresh_token=sample_token_data["refresh_token"],
            expires_at=expires_at,
        )

        db_session.add(token)
        await db_session.flush()

        assert token.id is not None
        assert token.token_type == "oauth"
        assert token.access_token == sample_token_data["access_token"]
        assert token.created_at is not None
        assert token.updated_at is not None

    async def test_unique_token_type_constraint(self, db_session, sample_token_data):
        """Test unique constraint on token_type."""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)

        # Create first token
        token1 = ZohoToken(
            token_type="oauth",
            access_token="token1",
            refresh_token="refresh1",
            expires_at=expires_at,
        )
        db_session.add(token1)
        await db_session.flush()

        # Try to create duplicate token_type
        token2 = ZohoToken(
            token_type="oauth",
            access_token="token2",
            refresh_token="refresh2",
            expires_at=expires_at,
        )
        db_session.add(token2)

        with pytest.raises(Exception):  # Unique constraint violation
            await db_session.flush()

    async def test_token_expiration_check(self, db_session):
        """Test is_expired() method."""
        # Create expired token
        expired_token = ZohoToken(
            token_type="expired",
            access_token="expired_token",
            refresh_token="refresh_token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(expired_token)
        await db_session.flush()

        assert expired_token.is_expired() is True

        # Create valid token
        valid_token = ZohoToken(
            token_type="valid",
            access_token="valid_token",
            refresh_token="refresh_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(valid_token)
        await db_session.flush()

        assert valid_token.is_expired() is False

    async def test_token_expiration_buffer(self, db_session):
        """Test 5-minute expiration buffer."""
        # Token expiring in 3 minutes (within buffer)
        soon_expiring = ZohoToken(
            token_type="soon",
            access_token="soon_token",
            refresh_token="refresh_token",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=3),
        )
        db_session.add(soon_expiring)
        await db_session.flush()

        # Should be considered expired due to 5-minute buffer
        assert soon_expiring.is_expired() is True

    async def test_updated_at_timestamp(self, db_session, sample_token_data):
        """Test updated_at timestamp updates on modification."""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)

        token = ZohoToken(
            token_type="test",
            access_token="original_token",
            refresh_token="refresh_token",
            expires_at=expires_at,
        )
        db_session.add(token)
        await db_session.flush()

        original_updated_at = token.updated_at

        # Update token
        await asyncio.sleep(0.1)  # Ensure time difference
        token.access_token = "new_token"
        await db_session.flush()

        # updated_at should be newer
        assert token.updated_at > original_updated_at

    async def test_token_repr(self, db_session):
        """Test __repr__ method."""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)

        token = ZohoToken(
            token_type="oauth",
            access_token="test_token",
            refresh_token="refresh_token",
            expires_at=expires_at,
        )
        db_session.add(token)
        await db_session.flush()

        repr_str = repr(token)
        assert "ZohoToken" in repr_str
        assert "oauth" in repr_str
        assert str(token.id) in repr_str


@pytest.mark.asyncio
class TestTokenRefreshAuditModel:
    """Test TokenRefreshAudit model."""

    async def test_create_audit_record(self, db_session):
        """Test creating an audit record."""
        now = datetime.now(timezone.utc)

        audit = TokenRefreshAudit(
            token_id=1,
            token_type="oauth",
            previous_expires_at=now,
            new_expires_at=now + timedelta(hours=1),
            success=True,
        )
        db_session.add(audit)
        await db_session.flush()

        assert audit.id is not None
        assert audit.token_id == 1
        assert audit.success is True
        assert audit.error_message is None

    async def test_audit_failed_refresh(self, db_session):
        """Test audit record for failed refresh."""
        audit = TokenRefreshAudit(
            token_id=1,
            token_type="oauth",
            success=False,
            error_message="Token refresh failed: Invalid refresh token",
        )
        db_session.add(audit)
        await db_session.flush()

        assert audit.success is False
        assert "Invalid refresh token" in audit.error_message

    async def test_audit_repr(self, db_session):
        """Test __repr__ method."""
        audit = TokenRefreshAudit(
            token_id=1,
            token_type="oauth",
            success=True,
        )
        db_session.add(audit)
        await db_session.flush()

        repr_str = repr(audit)
        assert "TokenRefreshAudit" in repr_str
        assert "oauth" in repr_str
        assert "True" in repr_str


# Required for async test sleep
import asyncio
