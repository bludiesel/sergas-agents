"""
Environment validation tests for Sergas Super Account Manager.
These tests verify that the development environment is correctly configured.

Test-Driven Development (TDD) - Created before environment setup.
"""

import sys
import os
import pytest


class TestPythonEnvironment:
    """Validate Python version and core setup."""

    def test_python_version(self):
        """Verify Python 3.10+ is installed."""
        assert sys.version_info >= (3, 10), (
            f"Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}"
        )

    def test_python_3_14(self):
        """Verify Python 3.14 is installed (project target)."""
        assert sys.version_info >= (3, 14), (
            f"Python 3.14+ recommended, found {sys.version_info.major}.{sys.version_info.minor}"
        )

    def test_virtual_environment(self):
        """Verify running in virtual environment."""
        # Check if in venv by looking for VIRTUAL_ENV or checking sys.prefix
        in_venv = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None
        )
        assert in_venv, "Not running in virtual environment"


class TestCoreSDKs:
    """Validate core SDK imports."""

    @pytest.mark.skip(reason="Claude Agent SDK not compatible with Python 3.14 yet")
    def test_claude_sdk_import(self):
        """Verify Claude Agent SDK is installed."""
        try:
            import claude_agent_sdk
            assert hasattr(claude_agent_sdk, '__version__') or True
        except ImportError as e:
            pytest.fail(f"Claude Agent SDK not installed: {e}")

    def test_pydantic_import(self):
        """Verify Pydantic is installed."""
        try:
            import pydantic
            # Pydantic uses version strings, compare as strings
            version = pydantic.__version__
            major, minor = int(version.split('.')[0]), int(version.split('.')[1])
            assert major >= 2 and minor >= 5, f"Pydantic 2.5+ required, found {version}"
        except ImportError as e:
            pytest.fail(f"Pydantic not installed: {e}")


class TestZohoIntegration:
    """Validate Zoho integration dependencies."""

    def test_zoho_sdk_import(self):
        """Verify Zoho CRM SDK is installed."""
        try:
            # zohocrmsdk8-0 package imports as 'zohocrmsdk'
            import zohocrmsdk
            assert True
        except ImportError as e:
            pytest.fail(f"Zoho SDK not installed: {e}")

    def test_http_clients(self):
        """Verify HTTP clients for REST API fallback."""
        clients = ['requests', 'aiohttp', 'httpx']
        for client in clients:
            try:
                __import__(client)
            except ImportError as e:
                pytest.fail(f"{client} not installed: {e}")


class TestCogneeMemory:
    """Validate Cognee memory system dependencies."""

    @pytest.mark.skip(reason="Cognee not available on PyPI, install from source if needed")
    def test_cognee_import(self):
        """Verify Cognee is installed."""
        try:
            import cognee
            assert True
        except ImportError as e:
            pytest.fail(f"Cognee not installed: {e}")

    @pytest.mark.skip(reason="LanceDB not compatible with Python 3.14 yet, use ChromaDB alternative")
    def test_lancedb_import(self):
        """Verify LanceDB is installed."""
        try:
            import lancedb
            assert True
        except ImportError as e:
            pytest.fail(f"LanceDB not installed: {e}")


class TestDatabaseSupport:
    """Validate database dependencies."""

    def test_postgresql_driver(self):
        """Verify PostgreSQL driver is installed."""
        try:
            import psycopg2
            assert True
        except ImportError as e:
            pytest.fail(f"psycopg2 not installed: {e}")

    def test_sqlalchemy_import(self):
        """Verify SQLAlchemy is installed."""
        try:
            import sqlalchemy
            assert sqlalchemy.__version__ >= "2.0.0"
        except ImportError as e:
            pytest.fail(f"SQLAlchemy not installed: {e}")

    def test_redis_client(self):
        """Verify Redis client is installed."""
        try:
            import redis
            assert True
        except ImportError as e:
            pytest.fail(f"Redis not installed: {e}")


class TestAPIFramework:
    """Validate API framework dependencies."""

    def test_fastapi_import(self):
        """Verify FastAPI is installed."""
        try:
            import fastapi
            assert True
        except ImportError as e:
            pytest.fail(f"FastAPI not installed: {e}")

    def test_uvicorn_import(self):
        """Verify Uvicorn is installed."""
        try:
            import uvicorn
            assert True
        except ImportError as e:
            pytest.fail(f"Uvicorn not installed: {e}")


class TestSecurityLibraries:
    """Validate security dependencies."""

    def test_authlib_import(self):
        """Verify Authlib is installed."""
        try:
            import authlib
            assert True
        except ImportError as e:
            pytest.fail(f"Authlib not installed: {e}")

    def test_jose_import(self):
        """Verify python-jose is installed."""
        try:
            import jose
            assert True
        except ImportError as e:
            pytest.fail(f"python-jose not installed: {e}")

    def test_passlib_import(self):
        """Verify passlib is installed."""
        try:
            import passlib
            assert True
        except ImportError as e:
            pytest.fail(f"passlib not installed: {e}")


class TestMonitoring:
    """Validate monitoring and observability dependencies."""

    def test_prometheus_client(self):
        """Verify Prometheus client is installed."""
        try:
            import prometheus_client
            assert True
        except ImportError as e:
            pytest.fail(f"prometheus-client not installed: {e}")

    def test_structlog_import(self):
        """Verify structlog is installed."""
        try:
            import structlog
            assert True
        except ImportError as e:
            pytest.fail(f"structlog not installed: {e}")

    def test_opentelemetry_import(self):
        """Verify OpenTelemetry is installed."""
        try:
            import opentelemetry
            assert True
        except ImportError as e:
            pytest.fail(f"OpenTelemetry not installed: {e}")


class TestCodeQuality:
    """Validate code quality tools."""

    def test_pytest_import(self):
        """Verify pytest is installed."""
        try:
            import pytest
            assert True
        except ImportError as e:
            pytest.fail(f"pytest not installed: {e}")

    def test_black_import(self):
        """Verify black is installed."""
        try:
            import black
            assert True
        except ImportError as e:
            pytest.fail(f"black not installed: {e}")

    def test_mypy_import(self):
        """Verify mypy is installed."""
        try:
            import mypy
            assert True
        except ImportError as e:
            pytest.fail(f"mypy not installed: {e}")


class TestProjectStructure:
    """Validate project structure and configuration files."""

    def test_env_example_exists(self):
        """Verify .env.example file exists."""
        env_example = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '.env.example'
        )
        assert os.path.exists(env_example), ".env.example file missing"

    def test_requirements_exists(self):
        """Verify requirements.txt exists."""
        requirements = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        assert os.path.exists(requirements), "requirements.txt missing"

    def test_pyproject_exists(self):
        """Verify pyproject.toml exists."""
        pyproject = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'pyproject.toml'
        )
        assert os.path.exists(pyproject), "pyproject.toml missing"

    def test_git_initialized(self):
        """Verify git repository is initialized."""
        git_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '.git'
        )
        assert os.path.exists(git_dir), "Git repository not initialized"


class TestDevTools:
    """Validate development tools."""

    def test_ipython_import(self):
        """Verify IPython is installed."""
        try:
            import IPython
            assert True
        except ImportError as e:
            pytest.fail(f"IPython not installed: {e}")

    def test_precommit_import(self):
        """Verify pre-commit is installed."""
        try:
            import pre_commit
            assert True
        except ImportError as e:
            pytest.fail(f"pre-commit not installed: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
