"""Unit tests for Zoho token store."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.integrations.zoho.token_store import TokenStore, ZohoTokenModel
from src.integrations.zoho.exceptions import ZohoDatabaseError


@pytest.fixture
def mock_engine():
    """Mock SQLAlchemy engine."""
    with patch("src.integrations.zoho.token_store.create_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield mock


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter_by.return_value = session
    return session


@pytest.fixture
def token_store(mock_engine):
    """Create token store instance with mocked engine."""
    with patch("src.integrations.zoho.token_store.sessionmaker"):
        store = TokenStore("postgresql://test:test@localhost/test")
        return store


class TestZohoTokenModel:
    """Test ZohoTokenModel SQLAlchemy model."""

    def test_to_dict_converts_model_to_dictionary(self):
        """Test model to dictionary conversion."""
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)

        token = ZohoTokenModel(
            id=1,
            token_type="oauth",
            access_token="access123",
            refresh_token="refresh456",
            expires_at=expires,
            created_at=now,
            updated_at=now,
        )

        result = token.to_dict()

        assert result["id"] == 1
        assert result["token_type"] == "oauth"
        assert result["access_token"] == "access123"
        assert result["refresh_token"] == "refresh456"
        assert result["expires_at"] == expires.isoformat()
        assert result["created_at"] == now.isoformat()
        assert result["updated_at"] == now.isoformat()

    def test_is_expired_returns_true_for_expired_token(self):
        """Test token expiration check for expired token."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        token = ZohoTokenModel(
            access_token="test",
            refresh_token="test",
            expires_at=past_time,
        )

        assert token.is_expired() is True

    def test_is_expired_returns_true_within_buffer_period(self):
        """Test token expiration check within 5-minute buffer."""
        near_expiry = datetime.utcnow() + timedelta(minutes=3)
        token = ZohoTokenModel(
            access_token="test",
            refresh_token="test",
            expires_at=near_expiry,
        )

        assert token.is_expired() is True

    def test_is_expired_returns_false_for_valid_token(self):
        """Test token expiration check for valid token."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        token = ZohoTokenModel(
            access_token="test",
            refresh_token="test",
            expires_at=future_time,
        )

        assert token.is_expired() is False


class TestTokenStoreInit:
    """Test TokenStore initialization."""

    def test_init_creates_engine_with_correct_params(self, mock_engine):
        """Test engine creation with proper configuration."""
        database_url = "postgresql://user:pass@localhost/dbname"

        TokenStore(database_url)

        mock_engine.assert_called_once()
        call_args = mock_engine.call_args
        assert call_args[0][0] == database_url
        assert call_args[1]["pool_pre_ping"] is True
        assert call_args[1]["pool_size"] == 5
        assert call_args[1]["max_overflow"] == 10

    def test_init_raises_error_on_connection_failure(self):
        """Test initialization error handling."""
        with patch("src.integrations.zoho.token_store.create_engine") as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")

            with pytest.raises(ZohoDatabaseError) as exc_info:
                TokenStore("postgresql://invalid")

            assert "Failed to initialize token store" in str(exc_info.value)
            assert exc_info.value.details["database_url"] == "postgresql://invalid"


class TestTokenStoreSave:
    """Test token save operations."""

    def test_save_token_creates_new_token(self, token_store, mock_session):
        """Test creating new token in database."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = token_store.save_token(
            access_token="new_access",
            refresh_token="new_refresh",
            expires_in=3600,
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert "access_token" in result
        assert "refresh_token" in result

    def test_save_token_updates_existing_token(self, token_store, mock_session):
        """Test updating existing token in database."""
        token_store.SessionLocal = lambda: mock_session
        existing_token = ZohoTokenModel(
            id=1,
            token_type="oauth",
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            existing_token
        )

        result = token_store.save_token(
            access_token="new_access",
            refresh_token="new_refresh",
            expires_in=3600,
        )

        assert existing_token.access_token == "new_access"
        assert existing_token.refresh_token == "new_refresh"
        mock_session.commit.assert_called_once()
        assert "access_token" in result

    def test_save_token_calculates_expiry_correctly(self, token_store, mock_session):
        """Test token expiry calculation."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        before_save = datetime.utcnow()
        token_store.save_token(
            access_token="test",
            refresh_token="test",
            expires_in=3600,
        )
        after_save = datetime.utcnow()

        # Verify token was added
        assert mock_session.add.called
        saved_token = mock_session.add.call_args[0][0]

        # Check expiry is approximately 1 hour from now
        expected_expiry = before_save + timedelta(seconds=3600)
        time_diff = abs((saved_token.expires_at - expected_expiry).total_seconds())
        assert time_diff < 2  # Within 2 seconds tolerance

    def test_save_token_handles_database_error(self, token_store, mock_session):
        """Test error handling during save operation."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(ZohoDatabaseError) as exc_info:
            token_store.save_token(
                access_token="test",
                refresh_token="test",
                expires_in=3600,
            )

        assert "Failed to save token" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_save_token_is_thread_safe(self, token_store, mock_session):
        """Test thread safety of save operation."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Verify lock is used
        with patch.object(token_store._lock, "acquire") as mock_acquire:
            with patch.object(token_store._lock, "release") as mock_release:
                # Use context manager behavior
                mock_acquire.return_value = True

                token_store.save_token("test", "test", 3600)

                # Lock should be acquired and released
                assert mock_acquire.called or mock_release.called


class TestTokenStoreGet:
    """Test token retrieval operations."""

    def test_get_token_retrieves_existing_token(self, token_store, mock_session):
        """Test retrieving existing token."""
        token_store.SessionLocal = lambda: mock_session
        expected_token = ZohoTokenModel(
            id=1,
            token_type="oauth",
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            expected_token
        )

        result = token_store.get_token()

        assert result is not None
        assert result["access_token"] == "test_access"
        assert result["refresh_token"] == "test_refresh"
        mock_session.close.assert_called_once()

    def test_get_token_returns_none_when_not_found(self, token_store, mock_session):
        """Test returning None for missing token."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = token_store.get_token()

        assert result is None
        mock_session.close.assert_called_once()

    def test_get_token_handles_database_error(self, token_store, mock_session):
        """Test error handling during get operation."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.side_effect = SQLAlchemyError("Query error")

        with pytest.raises(ZohoDatabaseError) as exc_info:
            token_store.get_token()

        assert "Failed to retrieve token" in str(exc_info.value)

    def test_get_token_with_custom_type(self, token_store, mock_session):
        """Test retrieving token with custom type."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        token_store.get_token(token_type="custom")

        mock_session.query.return_value.filter_by.assert_called_with(
            token_type="custom"
        )


class TestTokenStoreExpiry:
    """Test token expiry checking."""

    def test_is_token_expired_returns_true_for_expired(self, token_store, mock_session):
        """Test expiry check for expired token."""
        token_store.SessionLocal = lambda: mock_session
        expired_token = ZohoTokenModel(
            access_token="test",
            refresh_token="test",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            expired_token
        )

        result = token_store.is_token_expired()

        assert result is True

    def test_is_token_expired_returns_false_for_valid(self, token_store, mock_session):
        """Test expiry check for valid token."""
        token_store.SessionLocal = lambda: mock_session
        valid_token = ZohoTokenModel(
            access_token="test",
            refresh_token="test",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            valid_token
        )

        result = token_store.is_token_expired()

        assert result is False

    def test_is_token_expired_returns_true_when_not_found(
        self, token_store, mock_session
    ):
        """Test expiry check when token doesn't exist."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = token_store.is_token_expired()

        assert result is True


class TestTokenStoreDelete:
    """Test token deletion operations."""

    def test_delete_token_removes_existing_token(self, token_store, mock_session):
        """Test deleting existing token."""
        token_store.SessionLocal = lambda: mock_session
        token = ZohoTokenModel(id=1, access_token="test", refresh_token="test")
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            token
        )

        result = token_store.delete_token()

        assert result is True
        mock_session.delete.assert_called_once_with(token)
        mock_session.commit.assert_called_once()

    def test_delete_token_returns_false_when_not_found(
        self, token_store, mock_session
    ):
        """Test delete returns False for missing token."""
        token_store.SessionLocal = lambda: mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = token_store.delete_token()

        assert result is False
        mock_session.delete.assert_not_called()

    def test_delete_token_handles_database_error(self, token_store, mock_session):
        """Test error handling during delete."""
        token_store.SessionLocal = lambda: mock_session
        token = ZohoTokenModel(id=1, access_token="test", refresh_token="test")
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            token
        )
        mock_session.commit.side_effect = SQLAlchemyError("Delete failed")

        with pytest.raises(ZohoDatabaseError) as exc_info:
            token_store.delete_token()

        assert "Failed to delete token" in str(exc_info.value)
        mock_session.rollback.assert_called_once()


class TestTokenStoreCleanup:
    """Test expired token cleanup."""

    def test_cleanup_removes_expired_tokens(self, token_store, mock_session):
        """Test cleanup of expired tokens."""
        token_store.SessionLocal = lambda: mock_session
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.delete.return_value = 3

        result = token_store.cleanup_expired_tokens()

        assert result == 3
        mock_session.commit.assert_called_once()

    def test_cleanup_returns_zero_when_none_expired(self, token_store, mock_session):
        """Test cleanup when no tokens are expired."""
        token_store.SessionLocal = lambda: mock_session
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.delete.return_value = 0

        result = token_store.cleanup_expired_tokens()

        assert result == 0

    def test_cleanup_handles_database_error(self, token_store, mock_session):
        """Test error handling during cleanup."""
        token_store.SessionLocal = lambda: mock_session
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.delete.side_effect = SQLAlchemyError(
            "Cleanup failed"
        )

        with pytest.raises(ZohoDatabaseError) as exc_info:
            token_store.cleanup_expired_tokens()

        assert "Failed to cleanup expired tokens" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
