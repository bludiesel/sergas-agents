"""Unit tests for database configuration with auto-detection."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.db.config import (
    DatabaseConfig,
    get_database_config,
    get_database_url,
    DatabaseType,
)


class TestDatabaseConfig:
    """Test DatabaseConfig class functionality."""

    def test_default_sqlite_configuration(self):
        """Test default configuration uses SQLite."""
        # Clear any existing DATABASE_URL
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig()

            assert config.detect_database_type() == "sqlite"
            url = config.get_database_url()
            assert url.startswith("sqlite+aiosqlite:///")
            assert "sergas.db" in url

    def test_postgresql_detection_from_url(self):
        """Test PostgreSQL detection from DATABASE_URL."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db"}):
            config = DatabaseConfig()

            assert config.detect_database_type() == "postgresql"
            assert config.get_database_url() == "postgresql+asyncpg://user:pass@localhost:5432/db"

    def test_sqlite_detection_from_url(self):
        """Test SQLite detection from DATABASE_URL."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}):
            config = DatabaseConfig()

            assert config.detect_database_type() == "sqlite"
            # Should normalize to aiosqlite driver
            assert config.get_database_url() == "sqlite+aiosqlite:///./test.db"

    def test_sqlite_url_normalization(self):
        """Test SQLite URL normalization to aiosqlite."""
        test_cases = [
            ("sqlite:///./data/test.db", "sqlite+aiosqlite:///./data/test.db"),
            ("sqlite://./data/test.db", "sqlite+aiosqlite:///./data/test.db"),
            ("sqlite+aiosqlite:///./test.db", "sqlite+aiosqlite:///./test.db"),
        ]

        for input_url, expected_url in test_cases:
            with patch.dict(os.environ, {"DATABASE_URL": input_url}):
                config = DatabaseConfig()
                assert config.get_database_url() == expected_url

    def test_postgresql_from_individual_params(self):
        """Test PostgreSQL configuration from individual parameters."""
        with patch.dict(os.environ, {
            "DATABASE_HOST": "db.example.com",
            "DATABASE_PORT": "5433",
            "DATABASE_NAME": "mydb",
            "DATABASE_USER": "myuser",
            "DATABASE_PASSWORD": "mypass",
        }):
            config = DatabaseConfig()

            assert config.detect_database_type() == "postgresql"
            url = config.get_database_url()
            assert "postgresql+asyncpg" in url
            assert "myuser:mypass" in url
            assert "db.example.com:5433" in url
            assert "mydb" in url

    def test_sqlite_path_configuration(self):
        """Test SQLite path configuration."""
        with patch.dict(os.environ, {"DATABASE_PATH": "./custom/path/db.sqlite"}):
            config = DatabaseConfig()

            assert config.detect_database_type() == "sqlite"
            url = config.get_database_url()
            assert "custom/path/db.sqlite" in url

    def test_connection_string_backward_compatibility(self):
        """Test get_connection_string method for backward compatibility."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db"}):
            config = DatabaseConfig()

            # get_connection_string should work the same as get_database_url
            assert config.get_connection_string() == config.get_database_url()

    def test_async_vs_sync_drivers(self):
        """Test async vs sync driver selection."""
        with patch.dict(os.environ, {
            "DATABASE_PASSWORD": "test",
            "DATABASE_HOST": "localhost",
            "DATABASE_NAME": "testdb",
            "DATABASE_USER": "testuser",
        }):
            config = DatabaseConfig()

            # Async drivers
            async_url = config.get_database_url(use_async=True)
            assert "postgresql+asyncpg" in async_url

            # Sync drivers
            sync_url = config.get_database_url(use_async=False)
            assert "postgresql+psycopg2" in sync_url

    def test_database_url_precedence(self):
        """Test that DATABASE_URL takes precedence over individual parameters."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///./override.db",
            "DATABASE_HOST": "localhost",
            "DATABASE_PASSWORD": "ignored",
        }):
            config = DatabaseConfig()

            url = config.get_database_url()
            assert "override.db" in url
            assert "localhost" not in url


class TestDatabaseConfigFunctions:
    """Test module-level configuration functions."""

    def test_get_database_config_singleton(self):
        """Test that get_database_config returns singleton."""
        config1 = get_database_config()
        config2 = get_database_config()

        # Should be same instance
        assert config1 is config2

    def test_get_database_url_function(self):
        """Test get_database_url function."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db"}):
            # Reset singleton for test
            from src.db import config as config_module
            config_module._db_config = None

            url = get_database_url()
            assert url == "postgresql+asyncpg://user:pass@localhost/db"


class TestDatabaseTypeDetection:
    """Test database type detection edge cases."""

    def test_unknown_scheme_defaults_to_sqlite(self):
        """Test that unknown URL schemes default to SQLite."""
        with patch.dict(os.environ, {"DATABASE_URL": "mysql://user:pass@localhost/db"}):
            config = DatabaseConfig()

            # Should log warning and default to sqlite
            db_type = config.detect_database_type()
            assert db_type == "sqlite"

    def test_empty_database_url_uses_sqlite(self):
        """Test that empty DATABASE_URL defaults to SQLite."""
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig()

            assert config.detect_database_type() == "sqlite"


class TestConnectionPoolingConfiguration:
    """Test connection pooling configuration."""

    def test_postgresql_pooling_parameters(self):
        """Test PostgreSQL pooling parameters are configurable."""
        with patch.dict(os.environ, {
            "DATABASE_PASSWORD": "test",
            "POOL_SIZE": "50",
            "MAX_OVERFLOW": "20",
            "POOL_TIMEOUT": "60",
            "POOL_RECYCLE": "1800",
        }):
            config = DatabaseConfig()

            assert config.pool_size == 50
            assert config.max_overflow == 20
            assert config.pool_timeout == 60
            assert config.pool_recycle == 1800

    def test_feature_flags(self):
        """Test feature flags configuration."""
        with patch.dict(os.environ, {
            "TOKEN_PERSISTENCE_ENABLED": "false",
            "SQL_ECHO": "true",
        }):
            config = DatabaseConfig()

            assert config.token_persistence_enabled is False
            assert config.enable_sql_echo is True


class TestSQLitePathHandling:
    """Test SQLite path handling and directory creation."""

    def test_sqlite_path_absolute_resolution(self):
        """Test that SQLite paths are resolved to absolute paths."""
        with patch.dict(os.environ, {"DATABASE_PATH": "./relative/path/db.sqlite"}):
            config = DatabaseConfig()
            url = config.get_database_url()

            # URL should contain absolute path
            assert "sqlite+aiosqlite:///" in url
            # Path should be absolute (starts with / on Unix)
            path_part = url.replace("sqlite+aiosqlite:///", "")
            assert Path(path_part).is_absolute()


@pytest.mark.asyncio
class TestAsyncEngineConfiguration:
    """Test async engine configuration (integration-style tests)."""

    async def test_get_engine_postgresql(self):
        """Test engine creation for PostgreSQL."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db"}):
            from src.db import config as config_module

            # Reset singleton
            config_module._engine = None
            config_module._db_config = None

            engine = config_module.get_engine()

            assert engine is not None
            assert str(engine.url).startswith("postgresql+asyncpg")

    async def test_get_engine_sqlite(self):
        """Test engine creation for SQLite."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}, clear=True):
            from src.db import config as config_module

            # Reset singleton
            config_module._engine = None
            config_module._db_config = None

            engine = config_module.get_engine()

            assert engine is not None
            assert str(engine.url).startswith("sqlite+aiosqlite")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
