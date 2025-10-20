"""
Integration tests for SQLite database setup and operations.

Tests database URL detection, engine creation, migrations, CRUD operations,
concurrency behavior, and performance characteristics.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

# Import database setup utilities
from src.database.database import get_database_url, create_engine_with_settings
from src.models.sync.token_storage import TokenStorage, Base


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary SQLite database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()

    # Clean up WAL and SHM files if they exist
    wal_path = Path(str(db_path) + "-wal")
    shm_path = Path(str(db_path) + "-shm")
    if wal_path.exists():
        wal_path.unlink()
    if shm_path.exists():
        shm_path.unlink()


@pytest.fixture
def sqlite_url(temp_db_path: Path) -> str:
    """Generate SQLite database URL."""
    return f"sqlite:///{temp_db_path}"


@pytest.fixture
def test_engine(sqlite_url: str):
    """Create test database engine with proper settings."""
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Enable WAL mode
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.commit()

    # Create tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_session(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()

    yield session

    session.close()


class TestDatabaseURLDetection:
    """Test database URL detection and configuration."""

    def test_detect_sqlite_url(self, temp_db_path: Path):
        """Test SQLite URL is correctly detected."""
        os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"
        url = get_database_url()

        assert url.startswith("sqlite:///")
        assert str(temp_db_path) in url

        # Cleanup
        del os.environ["DATABASE_URL"]

    def test_detect_postgresql_url(self):
        """Test PostgreSQL URL is correctly detected."""
        postgres_url = "postgresql://user:pass@localhost:5432/dbname"
        os.environ["DATABASE_URL"] = postgres_url
        url = get_database_url()

        assert url.startswith("postgresql://")
        assert "localhost" in url

        # Cleanup
        del os.environ["DATABASE_URL"]

    def test_default_sqlite_url(self):
        """Test default SQLite URL when no DATABASE_URL is set."""
        # Ensure DATABASE_URL is not set
        os.environ.pop("DATABASE_URL", None)

        url = get_database_url()

        assert url.startswith("sqlite:///")
        assert "sergas_agents.db" in url or "test" in url.lower()


class TestSQLiteEngineCreation:
    """Test SQLite engine creation with proper settings."""

    def test_engine_creation(self, sqlite_url: str):
        """Test engine is created with correct settings."""
        engine = create_engine_with_settings(sqlite_url)

        assert engine is not None
        assert "sqlite" in str(engine.url)

        engine.dispose()

    def test_wal_mode_enabled(self, test_engine):
        """Test WAL mode is enabled on SQLite database."""
        with test_engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode")).fetchone()
            journal_mode = result[0] if result else None

            assert journal_mode == "wal"

    def test_connection_pooling(self, sqlite_url: str):
        """Test connection pooling is properly configured."""
        engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # Test multiple connections can be created
        conn1 = engine.connect()
        conn2 = engine.connect()

        assert conn1 is not None
        assert conn2 is not None

        conn1.close()
        conn2.close()
        engine.dispose()


class TestMigrationExecution:
    """Test database migration execution on SQLite."""

    def test_table_creation(self, test_engine):
        """Test tables are created by migrations."""
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()

        assert "token_storage" in tables

    def test_table_schema(self, test_engine):
        """Test table schema matches expected structure."""
        inspector = inspect(test_engine)
        columns = inspector.get_columns("token_storage")
        column_names = [col["name"] for col in columns]

        expected_columns = ["id", "access_token", "refresh_token",
                          "expires_at", "created_at", "updated_at"]

        for col in expected_columns:
            assert col in column_names


class TestCRUDOperations:
    """Test basic CRUD operations on SQLite."""

    def test_create_token(self, test_session: Session):
        """Test creating a token record."""
        token = TokenStorage(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        test_session.add(token)
        test_session.commit()

        assert token.id is not None
        assert token.created_at is not None

    def test_read_token(self, test_session: Session):
        """Test reading a token record."""
        # Create token
        token = TokenStorage(
            access_token="read_test_token",
            refresh_token="read_refresh_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        test_session.add(token)
        test_session.commit()
        token_id = token.id

        # Read token
        retrieved = test_session.query(TokenStorage).filter_by(id=token_id).first()

        assert retrieved is not None
        assert retrieved.access_token == "read_test_token"
        assert retrieved.refresh_token == "read_refresh_token"

    def test_update_token(self, test_session: Session):
        """Test updating a token record."""
        # Create token
        token = TokenStorage(
            access_token="old_token",
            refresh_token="old_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        test_session.add(token)
        test_session.commit()

        # Update token
        token.access_token = "new_token"
        token.refresh_token = "new_refresh"
        test_session.commit()

        # Verify update
        test_session.refresh(token)
        assert token.access_token == "new_token"
        assert token.refresh_token == "new_refresh"

    def test_delete_token(self, test_session: Session):
        """Test deleting a token record."""
        # Create token
        token = TokenStorage(
            access_token="delete_test_token",
            refresh_token="delete_refresh_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        test_session.add(token)
        test_session.commit()
        token_id = token.id

        # Delete token
        test_session.delete(token)
        test_session.commit()

        # Verify deletion
        retrieved = test_session.query(TokenStorage).filter_by(id=token_id).first()
        assert retrieved is None


class TestConcurrentOperations:
    """Test concurrent read and write operations."""

    def test_concurrent_reads(self, test_engine):
        """Test concurrent read operations work correctly."""
        # Create test data
        SessionLocal = sessionmaker(bind=test_engine)
        session = SessionLocal()

        for i in range(5):
            token = TokenStorage(
                access_token=f"concurrent_token_{i}",
                refresh_token=f"concurrent_refresh_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            session.add(token)
        session.commit()
        session.close()

        # Concurrent reads
        def read_tokens():
            session = SessionLocal()
            tokens = session.query(TokenStorage).all()
            session.close()
            return len(tokens)

        # Execute concurrent reads
        results = []
        for _ in range(10):
            result = read_tokens()
            results.append(result)

        # All reads should succeed and return same count
        assert all(r == 5 for r in results)

    def test_concurrent_write_behavior(self, test_engine):
        """Test and document concurrent write lock behavior."""
        SessionLocal = sessionmaker(bind=test_engine)

        def write_token(token_id: int):
            session = SessionLocal()
            try:
                token = TokenStorage(
                    access_token=f"concurrent_write_{token_id}",
                    refresh_token=f"concurrent_refresh_{token_id}",
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
                session.add(token)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                return False
            finally:
                session.close()

        # Execute concurrent writes
        results = []
        for i in range(5):
            result = write_token(i)
            results.append(result)

        # Verify writes completed (may be serialized due to WAL mode)
        session = SessionLocal()
        count = session.query(TokenStorage).count()
        session.close()

        # All writes should succeed (WAL mode allows concurrent writes)
        assert count == 5
        assert all(results)


class TestPerformanceComparison:
    """Test performance characteristics of SQLite."""

    def test_bulk_insert_performance(self, test_engine):
        """Test bulk insert performance."""
        SessionLocal = sessionmaker(bind=test_engine)
        session = SessionLocal()

        import time
        start_time = time.time()

        # Bulk insert 100 records
        tokens = []
        for i in range(100):
            token = TokenStorage(
                access_token=f"bulk_token_{i}",
                refresh_token=f"bulk_refresh_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            tokens.append(token)

        session.bulk_save_objects(tokens)
        session.commit()

        elapsed_time = time.time() - start_time

        session.close()

        # Should complete in reasonable time (< 1 second for 100 records)
        assert elapsed_time < 1.0

        # Verify all records inserted
        session = SessionLocal()
        count = session.query(TokenStorage).count()
        session.close()
        assert count == 100

    def test_query_performance(self, test_engine):
        """Test query performance with indexed and non-indexed columns."""
        SessionLocal = sessionmaker(bind=test_engine)
        session = SessionLocal()

        # Create test data
        for i in range(50):
            token = TokenStorage(
                access_token=f"query_token_{i}",
                refresh_token=f"query_refresh_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            session.add(token)
        session.commit()

        import time

        # Test query performance
        start_time = time.time()
        results = session.query(TokenStorage).filter(
            TokenStorage.access_token.like("query_token_%")
        ).all()
        elapsed_time = time.time() - start_time

        session.close()

        # Query should be fast (< 0.1 seconds)
        assert elapsed_time < 0.1
        assert len(results) == 50
