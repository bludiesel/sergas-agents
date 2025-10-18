"""
Comprehensive test fixtures for Zoho SDK integration testing.

Provides:
- Mock Zoho API responses
- Test account data (10-100 samples)
- Mock OAuth token responses
- Mock API error responses
- Database test fixtures
- Configuration fixtures
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock

import pytest


# ============================================================================
# Mock OAuth Token Responses
# ============================================================================

@pytest.fixture
def mock_oauth_token_response() -> Dict[str, Any]:
    """Mock successful OAuth token response."""
    return {
        "access_token": "1000.a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.q7r8s9t0u1v2w3x4y5z6",
        "refresh_token": "1000.z6y5x4w3v2u1t0s9r8q7p6o5n4m3l2k1.j0i9h8g7f6e5d4c3b2a1",
        "token_type": "Bearer",
        "expires_in": 3600,
        "api_domain": "https://www.zohoapis.com"
    }


@pytest.fixture
def mock_expired_token_response() -> Dict[str, Any]:
    """Mock expired token response."""
    return {
        "access_token": "1000.expired_token_abc123",
        "refresh_token": "1000.expired_refresh_xyz789",
        "token_type": "Bearer",
        "expires_in": -3600,  # Already expired
        "api_domain": "https://www.zohoapis.com"
    }


@pytest.fixture
def mock_invalid_token_error() -> Dict[str, Any]:
    """Mock invalid token error response."""
    return {
        "code": "INVALID_TOKEN",
        "details": {},
        "message": "Invalid access token",
        "status": "error"
    }


@pytest.fixture
def mock_refresh_token_response() -> Dict[str, Any]:
    """Mock token refresh response."""
    return {
        "access_token": "1000.refreshed_token_new_abc456",
        "token_type": "Bearer",
        "expires_in": 3600,
        "api_domain": "https://www.zohoapis.com"
    }


# ============================================================================
# Mock Zoho Account Data (10-100 samples)
# ============================================================================

class ZohoAccountFactory:
    """Factory for generating test Zoho account data."""

    ACCOUNT_NAMES = [
        "Acme Corporation", "Global Tech Solutions", "Enterprise Dynamics",
        "Digital Innovations Inc", "Strategic Partners LLC", "Future Systems",
        "Advanced Analytics Corp", "Cloud Services Group", "Data Solutions Ltd",
        "Smart Technologies", "Integrated Systems", "Precision Manufacturing",
        "Quality Assurance Inc", "Reliable Services", "Premier Solutions",
        "Elite Enterprises", "Superior Products", "Optimal Systems",
        "Dynamic Industries", "Progressive Tech", "Innovative Solutions",
        "NextGen Corporation", "Visionary Systems", "Apex Technologies",
        "Quantum Solutions", "Zenith Enterprises"
    ]

    INDUSTRIES = [
        "Technology", "Healthcare", "Finance", "Manufacturing", "Retail",
        "Education", "Consulting", "Real Estate", "Transportation", "Energy"
    ]

    ACCOUNT_TYPES = ["Customer", "Prospect", "Partner", "Investor", "Vendor"]

    RATINGS = ["Hot", "Warm", "Cold"]

    @classmethod
    def create_account(
        cls,
        account_id: Optional[str] = None,
        name: Optional[str] = None,
        revenue: Optional[int] = None,
        rating: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a single test account."""
        account_id = account_id or f"acc_{random.randint(100000, 999999)}"
        name = name or random.choice(cls.ACCOUNT_NAMES)

        return {
            "id": account_id,
            "Account_Name": name,
            "Annual_Revenue": revenue or random.randint(100000, 50000000),
            "Industry": random.choice(cls.INDUSTRIES),
            "Account_Type": random.choice(cls.ACCOUNT_TYPES),
            "Rating": rating or random.choice(cls.RATINGS),
            "Owner": {
                "name": f"Owner {random.randint(1, 100)}",
                "id": f"user_{random.randint(1000, 9999)}"
            },
            "Created_Time": (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
            "Modified_Time": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            **kwargs
        }

    @classmethod
    def create_batch(cls, count: int) -> List[Dict[str, Any]]:
        """Create a batch of test accounts."""
        return [cls.create_account() for _ in range(count)]


@pytest.fixture
def mock_account_data() -> Dict[str, Any]:
    """Single mock account for basic tests."""
    return ZohoAccountFactory.create_account(
        account_id="acc_123456",
        name="Acme Corporation",
        revenue=5000000,
        rating="Hot"
    )


@pytest.fixture
def mock_account_batch_10() -> List[Dict[str, Any]]:
    """Batch of 10 test accounts."""
    return ZohoAccountFactory.create_batch(10)


@pytest.fixture
def mock_account_batch_100() -> List[Dict[str, Any]]:
    """Batch of 100 test accounts."""
    return ZohoAccountFactory.create_batch(100)


@pytest.fixture
def mock_account_batch_500() -> List[Dict[str, Any]]:
    """Batch of 500 test accounts for performance testing."""
    return ZohoAccountFactory.create_batch(500)


# ============================================================================
# Mock API Error Responses
# ============================================================================

@pytest.fixture
def mock_rate_limit_error() -> Dict[str, Any]:
    """Mock rate limit error (429)."""
    return {
        "code": "RATE_LIMIT_EXCEEDED",
        "details": {
            "limit": "100 requests per minute",
            "retry_after": 60
        },
        "message": "API rate limit exceeded. Please retry after 60 seconds.",
        "status": "error"
    }


@pytest.fixture
def mock_network_timeout_error() -> Exception:
    """Mock network timeout exception."""
    import requests
    return requests.exceptions.Timeout("Connection timeout after 30 seconds")


@pytest.fixture
def mock_connection_error() -> Exception:
    """Mock connection error exception."""
    import requests
    return requests.exceptions.ConnectionError("Failed to establish connection")


@pytest.fixture
def mock_invalid_record_error() -> Dict[str, Any]:
    """Mock invalid record ID error."""
    return {
        "code": "INVALID_DATA",
        "details": {
            "api_name": "id"
        },
        "message": "The given record ID is invalid",
        "status": "error"
    }


@pytest.fixture
def mock_malformed_response_error() -> str:
    """Mock malformed JSON response."""
    return "<!DOCTYPE html><html><body>Unexpected HTML response</body></html>"


@pytest.fixture
def mock_unauthorized_error() -> Dict[str, Any]:
    """Mock unauthorized error (401)."""
    return {
        "code": "AUTHENTICATION_FAILURE",
        "details": {},
        "message": "Authentication failed. Invalid access token.",
        "status": "error"
    }


@pytest.fixture
def mock_forbidden_error() -> Dict[str, Any]:
    """Mock forbidden error (403)."""
    return {
        "code": "OAUTH_SCOPE_MISMATCH",
        "details": {},
        "message": "Insufficient permissions to access this resource",
        "status": "error"
    }


# ============================================================================
# Mock Zoho SDK Responses
# ============================================================================

@pytest.fixture
def mock_sdk_get_account_response(mock_account_data) -> Dict[str, Any]:
    """Mock SDK get_account response."""
    return {
        "data": [mock_account_data],
        "info": {
            "per_page": 1,
            "count": 1,
            "page": 1,
            "more_records": False
        }
    }


@pytest.fixture
def mock_sdk_bulk_read_response(mock_account_batch_100) -> Dict[str, Any]:
    """Mock SDK bulk read response."""
    return {
        "data": mock_account_batch_100,
        "info": {
            "per_page": 100,
            "count": 100,
            "page": 1,
            "more_records": False
        }
    }


@pytest.fixture
def mock_sdk_update_response() -> Dict[str, Any]:
    """Mock SDK update account response."""
    return {
        "data": [{
            "code": "SUCCESS",
            "details": {
                "Modified_Time": datetime.now().isoformat(),
                "Modified_By": {
                    "name": "Test User",
                    "id": "user_123"
                }
            },
            "message": "record updated",
            "status": "success"
        }]
    }


@pytest.fixture
def mock_sdk_bulk_write_response() -> Dict[str, Any]:
    """Mock SDK bulk write response."""
    return {
        "data": [
            {
                "code": "SUCCESS",
                "details": {"id": f"acc_{i}"},
                "message": "record added",
                "status": "success"
            }
            for i in range(1, 101)
        ]
    }


# ============================================================================
# Database Test Fixtures
# ============================================================================

@pytest.fixture
def mock_token_db_record() -> Dict[str, Any]:
    """Mock token database record."""
    return {
        "id": 1,
        "access_token": "1000.test_access_token_abc123",
        "refresh_token": "1000.test_refresh_token_xyz789",
        "token_type": "Bearer",
        "expires_at": datetime.now() + timedelta(hours=1),
        "created_at": datetime.now() - timedelta(days=1),
        "updated_at": datetime.now()
    }


@pytest.fixture
def mock_expired_token_db_record() -> Dict[str, Any]:
    """Mock expired token database record."""
    return {
        "id": 2,
        "access_token": "1000.expired_access_token",
        "refresh_token": "1000.expired_refresh_token",
        "token_type": "Bearer",
        "expires_at": datetime.now() - timedelta(hours=1),
        "created_at": datetime.now() - timedelta(days=2),
        "updated_at": datetime.now() - timedelta(hours=1)
    }


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_zoho_config() -> Dict[str, Any]:
    """Mock Zoho SDK configuration."""
    return {
        "client_id": "1000.TEST_CLIENT_ID",
        "client_secret": "test_client_secret_abc123xyz789",
        "redirect_uri": "https://localhost:8000/oauth/callback",
        "scope": "ZohoCRM.modules.ALL,ZohoCRM.settings.ALL",
        "environment": "sandbox",
        "api_base_url": "https://www.zohoapis.com",
        "accounts_url": "https://accounts.zoho.com"
    }


@pytest.fixture
def mock_invalid_zoho_config() -> Dict[str, Any]:
    """Mock invalid Zoho configuration."""
    return {
        "client_id": "",  # Invalid: empty
        "client_secret": "short",  # Invalid: too short
        "redirect_uri": "not-a-url",  # Invalid: malformed URL
        "scope": "",  # Invalid: missing scope
    }


@pytest.fixture
def mock_db_config() -> Dict[str, Any]:
    """Mock database configuration."""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "sergas_test",
        "user": "test_user",
        "password": "test_password",
        "pool_size": 5,
        "max_overflow": 10
    }


# ============================================================================
# Mock Zoho SDK Client
# ============================================================================

class MockZohoSDKClient:
    """Mock Zoho SDK client for testing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.access_token = None
        self.refresh_token = None
        self.call_count = 0
        self.should_fail = False
        self.failure_mode = None
        self._accounts_db = {}

    def initialize(self, oauth_token: Dict[str, Any]) -> None:
        """Initialize with OAuth token."""
        self.access_token = oauth_token.get("access_token")
        self.refresh_token = oauth_token.get("refresh_token")

    def get_account(self, account_id: str) -> Dict[str, Any]:
        """Mock get account."""
        self.call_count += 1

        if self.should_fail:
            if self.failure_mode == "unauthorized":
                raise PermissionError("INVALID_TOKEN")
            elif self.failure_mode == "rate_limit":
                raise Exception("RATE_LIMIT_EXCEEDED")
            elif self.failure_mode == "timeout":
                raise TimeoutError("Connection timeout")

        if account_id in self._accounts_db:
            return {"data": [self._accounts_db[account_id]]}

        return {"data": [ZohoAccountFactory.create_account(account_id=account_id)]}

    def update_account(self, account_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock update account."""
        self.call_count += 1

        if self.should_fail:
            raise Exception(f"Update failed: {self.failure_mode}")

        if account_id in self._accounts_db:
            self._accounts_db[account_id].update(data)
        else:
            self._accounts_db[account_id] = {**ZohoAccountFactory.create_account(account_id=account_id), **data}

        return {
            "data": [{
                "code": "SUCCESS",
                "details": {"id": account_id},
                "message": "record updated",
                "status": "success"
            }]
        }

    def bulk_read(self, module: str, criteria: Optional[str] = None, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Mock bulk read."""
        self.call_count += 1

        if self.should_fail:
            raise Exception(f"Bulk read failed: {self.failure_mode}")

        # Return batch of accounts
        accounts = ZohoAccountFactory.create_batch(min(per_page, 100))

        return {
            "data": accounts,
            "info": {
                "per_page": per_page,
                "count": len(accounts),
                "page": page,
                "more_records": False
            }
        }

    def bulk_write(self, module: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock bulk write."""
        self.call_count += 1

        if self.should_fail:
            raise Exception(f"Bulk write failed: {self.failure_mode}")

        # Simulate batch processing
        results = []
        for i, record in enumerate(records):
            account_id = record.get("id") or f"acc_{i+1000}"
            self._accounts_db[account_id] = record
            results.append({
                "code": "SUCCESS",
                "details": {"id": account_id},
                "message": "record added",
                "status": "success"
            })

        return {"data": results}

    def refresh_access_token(self) -> str:
        """Mock token refresh."""
        self.call_count += 1

        if self.should_fail and self.failure_mode == "invalid_refresh_token":
            raise PermissionError("INVALID_REFRESH_TOKEN")

        self.access_token = f"1000.refreshed_token_{random.randint(1000, 9999)}"
        return self.access_token


@pytest.fixture
def mock_zoho_sdk_client(mock_zoho_config) -> MockZohoSDKClient:
    """Provide mock Zoho SDK client."""
    return MockZohoSDKClient(mock_zoho_config)


@pytest.fixture
def mock_zoho_sdk_client_with_failure(mock_zoho_sdk_client) -> MockZohoSDKClient:
    """Provide mock Zoho SDK client configured to fail."""
    mock_zoho_sdk_client.should_fail = True
    mock_zoho_sdk_client.failure_mode = "timeout"
    return mock_zoho_sdk_client
