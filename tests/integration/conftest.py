"""
Integration Test Configuration and Fixtures

This module provides shared fixtures and configuration for integration tests.
"""

import asyncio
import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        "test_data": {
            "account_id": "test_account_001",
            "contact_id": "test_contact_001",
            "deal_id": "test_deal_001"
        },
        "glm": {
            "api_key": os.getenv("GLM_API_KEY", "test_key"),
            "base_url": os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            "models": ["glm-4-flash", "glm-4-air", "glm-4-airx", "glm-4-long"]
        },
        "zoho": {
            "client_id": os.getenv("ZOHO_CLIENT_ID", "test_client_id"),
            "client_secret": os.getenv("ZOHO_CLIENT_SECRET", "test_client_secret"),
            "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN", "test_refresh_token")
        },
        "performance": {
            "workflow_completion_time": 30.0,
            "api_response_time": 2.0,
            "memory_usage_mb": 512,
            "cpu_usage_percent": 80
        },
        "monitoring": {
            "metrics_retention_days": 7,
            "alert_thresholds": {
                "error_rate": 0.1,
                "response_time": 5000,
                "memory_usage": 0.8
            }
        }
    }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def mock_responses():
    """Mock HTTP responses for testing"""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.text = json.dumps(json_data)

        async def json(self):
            return self.json_data

        async def text(self):
            return self.text

    return MockResponse


@pytest.fixture
def mock_file_system():
    """Mock file system operations"""
    class MockFileSystem:
        def __init__(self):
            self.files = {}
            self.directories = set()

        def write_file(self, path, content):
            self.files[path] = content

        def read_file(self, path):
            return self.files.get(path)

        def exists(self, path):
            return path in self.files or path in self.directories

        def create_dir(self, path):
            self.directories.add(path)

        def list_files(self, path):
            return [f for f in self.files.keys() if f.startswith(path)]

    return MockFileSystem()


# Test data fixtures
@pytest.fixture
def sample_account_data():
    """Sample account data for testing"""
    return {
        "id": "test_account_001",
        "name": "Test Company Inc.",
        "email": "contact@testcompany.com",
        "phone": "+1234567890",
        "website": "https://testcompany.com",
        "industry": "Technology",
        "annual_revenue": 1000000,
        "employee_count": 50,
        "created_time": "2024-01-01T00:00:00Z",
        "modified_time": "2024-01-15T00:00:00Z",
        "custom_fields": {
            "account_health_score": 85,
            "last_activity_date": "2024-01-14",
            "risk_level": "Low"
        }
    }


@pytest.fixture
def sample_contact_data():
    """Sample contact data for testing"""
    return [
        {
            "id": "test_contact_001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@testcompany.com",
            "phone": "+1234567890",
            "account_id": "test_account_001",
            "title": "CEO",
            "department": "Executive"
        },
        {
            "id": "test_contact_002",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@testcompany.com",
            "phone": "+1234567891",
            "account_id": "test_account_001",
            "title": "CTO",
            "department": "Technology"
        }
    ]


@pytest.fixture
def sample_deal_data():
    """Sample deal data for testing"""
    return [
        {
            "id": "test_deal_001",
            "name": "Enterprise Software License",
            "account_id": "test_account_001",
            "amount": 50000,
            "stage": "Negotiation",
            "probability": 75,
            "expected_close_date": "2024-03-01",
            "created_time": "2024-01-01T00:00:00Z"
        },
        {
            "id": "test_deal_002",
            "name": "Support Contract Renewal",
            "account_id": "test_account_001",
            "amount": 15000,
            "stage": "Proposal",
            "probability": 90,
            "expected_close_date": "2024-02-15",
            "created_time": "2024-01-05T00:00:00Z"
        }
    ]


@pytest.fixture
def sample_workflow_definitions():
    """Sample workflow definitions for testing"""
    return {
        "account_analysis": {
            "id": "account_analysis_workflow",
            "name": "Account Health Analysis",
            "description": "Comprehensive analysis of account health and risk",
            "steps": [
                {
                    "id": "fetch_account",
                    "name": "Fetch Account Data",
                    "type": "task",
                    "action": "zoho_get_account",
                    "inputs": {"account_id": "${account_id}"}
                },
                {
                    "id": "fetch_contacts",
                    "name": "Fetch Related Contacts",
                    "type": "task",
                    "action": "zoho_get_contacts",
                    "inputs": {"account_id": "${account_id}"},
                    "depends_on": ["fetch_account"]
                },
                {
                    "id": "analyze_health",
                    "name": "Analyze Account Health",
                    "type": "task",
                    "action": "health_analysis",
                    "inputs": {
                        "account": "${fetch_account.result}",
                        "contacts": "${fetch_contacts.result}"
                    },
                    "depends_on": ["fetch_contacts"]
                },
                {
                    "id": "generate_recommendations",
                    "name": "Generate Recommendations",
                    "type": "task",
                    "action": "recommendation_engine",
                    "inputs": {"health_analysis": "${analyze_health.result}"},
                    "depends_on": ["analyze_health"]
                }
            ]
        },
        "customer_onboarding": {
            "id": "customer_onboarding_workflow",
            "name": "Customer Onboarding",
            "description": "Automated customer onboarding process",
            "steps": [
                {
                    "id": "validate_account",
                    "name": "Validate Account Information",
                    "type": "task",
                    "action": "validate_account_data",
                    "inputs": {"account_id": "${account_id}"}
                },
                {
                    "id": "assign_account_manager",
                    "name": "Assign Account Manager",
                    "type": "task",
                    "action": "assign_manager",
                    "inputs": {"account_id": "${account_id}"},
                    "depends_on": ["validate_account"]
                },
                {
                    "id": "send_welcome_email",
                    "name": "Send Welcome Email",
                    "type": "task",
                    "action": "send_email",
                    "inputs": {
                        "template": "welcome",
                        "account_id": "${account_id}"
                    },
                    "depends_on": ["assign_account_manager"]
                },
                {
                    "id": "schedule_onboarding_call",
                    "name": "Schedule Onboarding Call",
                    "type": "task",
                    "action": "schedule_call",
                    "inputs": {"account_id": "${account_id}"},
                    "depends_on": ["send_welcome_email"]
                }
            ]
        }
    }


@pytest.fixture
def sample_intent_examples():
    """Sample intent examples for testing"""
    return [
        {
            "text": "Analyze the health of account XYZ123",
            "intent": "analyze_account_health",
            "entities": {"account_id": "XYZ123"},
            "confidence": 0.95
        },
        {
            "text": "Show me all contacts for company ABC Corp",
            "intent": "get_contacts",
            "entities": {"company_name": "ABC Corp"},
            "confidence": 0.92
        },
        {
            "text": "Generate growth recommendations for customer 456",
            "intent": "generate_recommendations",
            "entities": {"customer_id": "456", "recommendation_type": "growth"},
            "confidence": 0.88
        },
        {
            "text": "What's the status of deal with Acme Inc?",
            "intent": "get_deal_status",
            "entities": {"company_name": "Acme Inc"},
            "confidence": 0.90
        }
    ]


# Performance testing fixtures
@pytest.fixture
def performance_test_config():
    """Configuration for performance testing"""
    return {
        "load_test": {
            "concurrent_users": 10,
            "requests_per_user": 5,
            "ramp_up_time": 30,  # seconds
            "test_duration": 120  # seconds
        },
        "stress_test": {
            "max_concurrent_users": 50,
            "step_increment": 5,
            "step_duration": 30,  # seconds
            "max_steps": 10
        },
        "endurance_test": {
            "duration": 3600,  # 1 hour
            "constant_load": 5,  # concurrent users
            "measurement_interval": 60  # seconds
        }
    }


# Mock services
@pytest.fixture
def mock_zoho_service():
    """Mock Zoho service"""
    class MockZohoService:
        def __init__(self):
            self.accounts = {}
            self.contacts = {}
            self.deals = {}
            self.call_count = 0

        async def get_account(self, account_id):
            self.call_count += 1
            await asyncio.sleep(0.1)  # Simulate API call
            return self.accounts.get(account_id, {
                "id": account_id,
                "name": f"Account {account_id}",
                "status": "active"
            })

        async def update_account(self, account_id, data):
            self.call_count += 1
            await asyncio.sleep(0.2)  # Simulate API call
            if account_id in self.accounts:
                self.accounts[account_id].update(data)
                return self.accounts[account_id]
            return None

        async def get_contacts(self, account_id):
            self.call_count += 1
            await asyncio.sleep(0.1)  # Simulate API call
            return self.contacts.get(account_id, [])

        async def create_account(self, data):
            self.call_count += 1
            await asyncio.sleep(0.2)  # Simulate API call
            account_id = f"account_{len(self.accounts) + 1}"
            account = {"id": account_id, **data}
            self.accounts[account_id] = account
            return account

    return MockZohoService()


@pytest.fixture
def mock_glm_service():
    """Mock GLM service"""
    class MockGLMService:
        def __init__(self):
            self.models = ["glm-4-flash", "glm-4-air", "glm-4-airx", "glm-4-long"]
            self.call_count = 0
            self.response_times = []

        async def chat_completion(self, model, messages, **kwargs):
            self.call_count += 1
            start_time = time.time()

            await asyncio.sleep(0.1)  # Simulate processing time

            response_time = time.time() - start_time
            self.response_times.append(response_time)

            return {
                "id": f"chatcmpl_{self.call_count}",
                "model": model,
                "choices": [{
                    "message": {
                        "content": f"Mock response from {model} for: {messages[-1]['content'][:50]}..."
                    }
                }],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 30,
                    "total_tokens": 80
                }
            }

        def get_available_models(self):
            return self.models

    return MockGLMService()


# Test utilities
@pytest.fixture
def test_utils():
    """Utility functions for testing"""
    class TestUtils:
        @staticmethod
        async def wait_for_condition(condition, timeout=30, interval=1):
            """Wait for a condition to become true"""
            elapsed = 0
            while elapsed < timeout:
                if await condition():
                    return True
                await asyncio.sleep(interval)
                elapsed += interval
            return False

        @staticmethod
        def assert_close(value1, value2, tolerance=0.1):
            """Assert that two values are close within tolerance"""
            assert abs(value1 - value2) <= tolerance, \
                f"{value1} and {value2} are not close within {tolerance}"

        @staticmethod
        def generate_test_data(count, factory):
            """Generate test data using a factory function"""
            return [factory(i) for i in range(count)]

        @staticmethod
        async def measure_async_function(func, *args, **kwargs):
            """Measure execution time of an async function"""
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time

    return TestUtils()


# Environment setup
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_external: mark test as requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Add performance marker to performance tests
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.performance)

        # Add slow marker to potentially slow tests
        if any(keyword in item.nodeid for keyword in ["load", "stress", "endurance"]):
            item.add_marker(pytest.mark.slow)