"""
Comprehensive Integration Tests for SERGAS Agents System

This module provides full system integration testing covering:
- Workflow engine with real scenarios
- GLM integration with model selection
- Self-modification system with rollback validation
- Zoho evolution system with learning scenarios
- Monitoring system with metrics collection
- End-to-end workflow testing
- Performance benchmarks and validation
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
import pytest
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from agents.orchestrator import EnhancedOrchestratorAgent
from agents.intent_detection import EnhancedIntentEngine
from monitoring.enhanced_monitoring import EnhancedMonitoringSystem
from monitoring.metrics_collector import MetricsCollector
from self_modification.engine import SelfModificationEngine
from zoho.evolution_system import ZohoEvolutionSystem
from workflow.enhanced_engine import EnhancedWorkflowEngine
from api.routers.health_monitor import HealthMonitor
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class TestConfig:
    """Test configuration settings"""

    # Test Data
    TEST_ACCOUNT_ID = "test_account_001"
    TEST_CONTACT_ID = "test_contact_001"
    TEST_DEAL_ID = "test_deal_001"

    # GLM Configuration
    GLM_API_KEY = os.getenv("GLM_API_KEY", "test_key")
    GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

    # Zoho Configuration
    ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "test_client_id")
    ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "test_client_secret")
    ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "test_refresh_token")

    # Monitoring
    METRICS_RETENTION_DAYS = 7
    ALERT_THRESHOLDS = {
        "error_rate": 0.1,
        "response_time": 5000,
        "memory_usage": 0.8
    }

    # Performance
    PERFORMANCE_THRESHOLDS = {
        "workflow_completion_time": 30.0,  # seconds
        "api_response_time": 2.0,  # seconds
        "memory_usage_mb": 512,  # MB
        "cpu_usage_percent": 80  # %
    }


class MockGLMClient:
    """Mock GLM client for testing"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.models = ["glm-4-flash", "glm-4-air", "glm-4-airx", "glm-4-long"]
        self.call_count = 0
        self.response_times = []

    async def chat_completion(self, model: str, messages: List[Dict], **kwargs):
        """Mock chat completion"""
        start_time = time.time()
        self.call_count += 1

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Mock response
        response = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Mock response from {model} for message: {messages[-1]['content'][:100]}..."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 30,
                "total_tokens": 80
            }
        }

        response_time = time.time() - start_time
        self.response_times.append(response_time)

        return response

    def get_available_models(self):
        """Get available models"""
        return self.models


class MockZohoClient:
    """Mock Zoho client for testing"""

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = f"mock_access_token_{uuid.uuid4()}"
        self.call_count = 0
        self.data_store = {}
        self.learning_data = []

    async def get_account(self, account_id: str):
        """Mock get account"""
        self.call_count += 1
        return {
            "id": account_id,
            "name": f"Test Account {account_id}",
            "email": f"test{account_id}@example.com",
            "phone": "+1234567890",
            "website": "https://example.com",
            "industry": "Technology",
            "annual_revenue": 1000000,
            "employee_count": 50,
            "created_time": "2024-01-01T00:00:00Z",
            "modified_time": datetime.utcnow().isoformat() + "Z"
        }

    async def update_account(self, account_id: str, data: Dict):
        """Mock update account"""
        self.call_count += 1
        account = await self.get_account(account_id)
        account.update(data)
        account["modified_time"] = datetime.utcnow().isoformat() + "Z"

        # Store learning data
        self.learning_data.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "update_account",
            "account_id": account_id,
            "data": data,
            "success": True
        })

        return account

    async def get_contacts(self, account_id: str):
        """Mock get contacts"""
        self.call_count += 1
        return [
            {
                "id": f"contact_{i}",
                "first_name": f"Test{i}",
                "last_name": f"Contact{i}",
                "email": f"test{i}@example.com",
                "account_id": account_id
            }
            for i in range(1, 4)
        ]

    def get_learning_insights(self):
        """Get learning insights"""
        return {
            "total_actions": len(self.learning_data),
            "success_rate": 0.95,
            "common_patterns": ["account_updates", "contact_retrieval"],
            "optimization_suggestions": [
                "Batch account operations",
                "Cache frequently accessed data"
            ]
        }


@pytest.fixture
async def test_config():
    """Test configuration fixture"""
    return TestConfig()


@pytest.fixture
async def mock_glm_client():
    """Mock GLM client fixture"""
    return MockGLMClient(
        api_key=TestConfig.GLM_API_KEY,
        base_url=TestConfig.GLM_BASE_URL
    )


@pytest.fixture
async def mock_zoho_client():
    """Mock Zoho client fixture"""
    return MockZohoClient(
        client_id=TestConfig.ZOHO_CLIENT_ID,
        client_secret=TestConfig.ZOHO_CLIENT_SECRET,
        refresh_token=TestConfig.ZOHO_REFRESH_TOKEN
    )


@pytest.fixture
async def temp_dir():
    """Temporary directory fixture"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def monitoring_system(temp_dir):
    """Monitoring system fixture"""
    return EnhancedMonitoringSystem(
        metrics_dir=temp_dir,
        retention_days=TestConfig.METRICS_RETENTION_DAYS
    )


@pytest.fixture
async def workflow_engine():
    """Workflow engine fixture"""
    return EnhancedWorkflowEngine()


@pytest.fixture
async def intent_engine():
    """Intent engine fixture"""
    return EnhancedIntentEngine()


@pytest.fixture
async def self_modification_engine(temp_dir):
    """Self-modification engine fixture"""
    return SelfModificationEngine(
        workspace_dir=temp_dir,
        backup_dir=os.path.join(temp_dir, "backups")
    )


@pytest.fixture
async def zoho_evolution_system(mock_zoho_client):
    """Zoho evolution system fixture"""
    return ZohoEvolutionSystem(
        zoho_client=mock_zoho_client
    )


@pytest.fixture
async def orchestrator_agent():
    """Orchestrator agent fixture"""
    return EnhancedOrchestratorAgent()


class TestGLMIntegration:
    """Test GLM integration functionality"""

    @pytest.mark.asyncio
    async def test_model_selection_and_chat_completion(self, mock_glm_client):
        """Test GLM model selection and chat completion"""
        logger.info("Testing GLM model selection and chat completion")

        # Test available models
        models = mock_glm_client.get_available_models()
        assert len(models) > 0
        assert "glm-4-flash" in models

        # Test chat completion with different models
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]

        for model in models[:2]:  # Test first 2 models
            response = await mock_glm_client.chat_completion(
                model=model,
                messages=test_messages
            )

            assert response["model"] == model
            assert "choices" in response
            assert len(response["choices"]) > 0
            assert "content" in response["choices"][0]["message"]
            assert "usage" in response

        # Verify performance metrics
        assert mock_glm_client.call_count > 0
        assert len(mock_glm_client.response_times) > 0
        avg_response_time = sum(mock_glm_client.response_times) / len(mock_glm_client.response_times)
        assert avg_response_time < 1.0  # Should be fast for mock

        logger.info(f"GLM integration test passed. {mock_glm_client.call_count} calls made.")

    @pytest.mark.asyncio
    async def test_glm_error_handling(self, mock_glm_client):
        """Test GLM error handling"""
        logger.info("Testing GLM error handling")

        # Test with invalid model
        with pytest.raises(Exception):
            await mock_glm_client.chat_completion(
                model="invalid-model",
                messages=[{"role": "user", "content": "test"}]
            )

        # Test with empty messages
        with pytest.raises(Exception):
            await mock_glm_client.chat_completion(
                model="glm-4-flash",
                messages=[]
            )

        logger.info("GLM error handling test passed")


class TestWorkflowEngine:
    """Test workflow engine functionality"""

    @pytest.mark.asyncio
    async def test_workflow_creation_and_execution(self, workflow_engine):
        """Test workflow creation and execution"""
        logger.info("Testing workflow creation and execution")

        # Define test workflow
        workflow_def = {
            "id": "test_workflow",
            "name": "Test Workflow",
            "description": "A test workflow for integration testing",
            "steps": [
                {
                    "id": "step1",
                    "name": "Initialize",
                    "type": "task",
                    "action": "initialize_workflow",
                    "inputs": {"param1": "value1"}
                },
                {
                    "id": "step2",
                    "name": "Process Data",
                    "type": "task",
                    "action": "process_data",
                    "inputs": {"data": "test_data"},
                    "depends_on": ["step1"]
                },
                {
                    "id": "step3",
                    "name": "Finalize",
                    "type": "task",
                    "action": "finalize_workflow",
                    "depends_on": ["step2"]
                }
            ]
        }

        # Create workflow
        workflow_id = await workflow_engine.create_workflow(workflow_def)
        assert workflow_id is not None

        # Execute workflow
        execution_id = await workflow_engine.execute_workflow(
            workflow_id,
            inputs={"test_input": "test_value"}
        )
        assert execution_id is not None

        # Wait for completion
        max_wait_time = 30  # seconds
        wait_interval = 1
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            status = await workflow_engine.get_execution_status(execution_id)
            if status["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval

        # Verify completion
        final_status = await workflow_engine.get_execution_status(execution_id)
        assert final_status["status"] == "completed"
        assert "results" in final_status

        logger.info(f"Workflow execution test passed. Status: {final_status['status']}")

    @pytest.mark.asyncio
    async def test_workflow_with_conditions(self, workflow_engine):
        """Test workflow with conditional logic"""
        logger.info("Testing workflow with conditional logic")

        workflow_def = {
            "id": "conditional_workflow",
            "name": "Conditional Workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "Check Condition",
                    "type": "condition",
                    "condition": "input.value > 10",
                    "true_branch": "step2a",
                    "false_branch": "step2b"
                },
                {
                    "id": "step2a",
                    "name": "Process High Value",
                    "type": "task",
                    "action": "process_high_value"
                },
                {
                    "id": "step2b",
                    "name": "Process Low Value",
                    "type": "task",
                    "action": "process_low_value"
                }
            ]
        }

        # Test with high value
        workflow_id = await workflow_engine.create_workflow(workflow_def)
        execution_id = await workflow_engine.execute_workflow(
            workflow_id,
            inputs={"value": 15}
        )

        # Wait for completion
        await asyncio.sleep(2)
        status = await workflow_engine.get_execution_status(execution_id)
        assert status["status"] == "completed"

        # Test with low value
        execution_id = await workflow_engine.execute_workflow(
            workflow_id,
            inputs={"value": 5}
        )

        # Wait for completion
        await asyncio.sleep(2)
        status = await workflow_engine.get_execution_status(execution_id)
        assert status["status"] == "completed"

        logger.info("Conditional workflow test passed")

    @pytest.mark.asyncio
    async def test_workflow_parallel_execution(self, workflow_engine):
        """Test workflow parallel execution"""
        logger.info("Testing workflow parallel execution")

        workflow_def = {
            "id": "parallel_workflow",
            "name": "Parallel Workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "Initialize",
                    "type": "task",
                    "action": "initialize"
                },
                {
                    "id": "step2a",
                    "name": "Parallel Task A",
                    "type": "task",
                    "action": "parallel_task_a",
                    "parallel_group": "group1",
                    "depends_on": ["step1"]
                },
                {
                    "id": "step2b",
                    "name": "Parallel Task B",
                    "type": "task",
                    "action": "parallel_task_b",
                    "parallel_group": "group1",
                    "depends_on": ["step1"]
                },
                {
                    "id": "step3",
                    "name": "Finalize",
                    "type": "task",
                    "action": "finalize",
                    "depends_on": ["step2a", "step2b"]
                }
            ]
        }

        workflow_id = await workflow_engine.create_workflow(workflow_def)
        start_time = time.time()

        execution_id = await workflow_engine.execute_workflow(
            workflow_id,
            inputs={}
        )

        # Wait for completion
        max_wait_time = 30
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            status = await workflow_engine.get_execution_status(execution_id)
            if status["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(1)
            elapsed_time += 1

        execution_time = time.time() - start_time
        final_status = await workflow_engine.get_execution_status(execution_id)

        assert final_status["status"] == "completed"
        assert execution_time < TestConfig.PERFORMANCE_THRESHOLDS["workflow_completion_time"]

        logger.info(f"Parallel workflow test passed. Execution time: {execution_time:.2f}s")


class TestSelfModificationSystem:
    """Test self-modification system functionality"""

    @pytest.mark.asyncio
    async def test_code_modification_with_rollback(self, self_modification_engine, temp_dir):
        """Test code modification with rollback functionality"""
        logger.info("Testing code modification with rollback")

        # Create a test Python file
        test_file = os.path.join(temp_dir, "test_module.py")
        original_content = '''
def test_function():
    """Original function"""
    return "original_value"

def another_function():
    """Another function"""
    return 42
'''
        with open(test_file, 'w') as f:
            f.write(original_content)

        # Create modification request
        modification_request = {
            "target_file": test_file,
            "modification_type": "function_enhancement",
            "target_function": "test_function",
            "modification": {
                "add_parameter": "name",
                "add_logging": True,
                "add_error_handling": True
            },
            "description": "Enhance test_function with parameter and logging"
        }

        # Apply modification
        modification_id = await self_modification_engine.apply_modification(modification_request)
        assert modification_id is not None

        # Verify modification was applied
        with open(test_file, 'r') as f:
            modified_content = f.read()

        assert "name" in modified_content
        assert "logging" in modified_content.lower() or "print" in modified_content.lower()
        assert "try:" in modified_content or "except" in modified_content

        # Test rollback
        rollback_success = await self_modification_engine.rollback_modification(modification_id)
        assert rollback_success

        # Verify rollback
        with open(test_file, 'r') as f:
            rollback_content = f.read()

        assert rollback_content == original_content

        logger.info("Code modification with rollback test passed")

    @pytest.mark.asyncio
    async def test_safe_modification_validation(self, self_modification_engine, temp_dir):
        """Test safe modification validation"""
        logger.info("Testing safe modification validation")

        # Create test file
        test_file = os.path.join(temp_dir, "safety_test.py")
        safe_content = '''
def safe_function():
    """A safe function"""
    return "safe"

# Important constant
API_KEY = "secret_key"
'''
        with open(test_file, 'w') as f:
            f.write(safe_content)

        # Test unsafe modification (trying to modify API_KEY)
        unsafe_request = {
            "target_file": test_file,
            "modification_type": "constant_change",
            "target": "API_KEY",
            "modification": {"new_value": "hacked_key"},
            "description": "Try to modify sensitive constant"
        }

        # Should reject unsafe modification
        with pytest.raises(Exception, match="Safety check failed"):
            await self_modification_engine.apply_modification(unsafe_request)

        # Verify file wasn't modified
        with open(test_file, 'r') as f:
            content = f.read()

        assert "secret_key" in content
        assert "hacked_key" not in content

        logger.info("Safe modification validation test passed")

    @pytest.mark.asyncio
    async def test_modification_history_tracking(self, self_modification_engine, temp_dir):
        """Test modification history tracking"""
        logger.info("Testing modification history tracking")

        test_file = os.path.join(temp_dir, "history_test.py")
        with open(test_file, 'w') as f:
            f.write("def test(): pass\n")

        # Apply multiple modifications
        modifications = []
        for i in range(3):
            request = {
                "target_file": test_file,
                "modification_type": "function_addition",
                "modification": {
                    "function_name": f"new_function_{i}",
                    "function_body": f"return {i}"
                }
            }
            mod_id = await self_modification_engine.apply_modification(request)
            modifications.append(mod_id)

        # Get history
        history = await self_modification_engine.get_modification_history(test_file)
        assert len(history) >= 3

        # Verify history contains our modifications
        for mod_id in modifications:
            assert any(h["id"] == mod_id for h in history)

        # Verify each history entry has required fields
        for entry in history:
            assert "id" in entry
            assert "timestamp" in entry
            assert "description" in entry
            assert "changes" in entry

        logger.info("Modification history tracking test passed")


class TestZohoEvolutionSystem:
    """Test Zoho evolution system functionality"""

    @pytest.mark.asyncio
    async def test_adaptive_api_calls(self, zoho_evolution_system):
        """Test adaptive API calls with learning"""
        logger.info("Testing adaptive API calls with learning")

        # Make several API calls to generate learning data
        account_id = TestConfig.TEST_ACCOUNT_ID

        for i in range(5):
            # Get account
            account = await zoho_evolution_system.get_account(account_id)
            assert account["id"] == account_id

            # Update account with different data
            update_data = {
                "custom_field": f"value_{i}",
                "last_activity": datetime.utcnow().isoformat()
            }
            updated_account = await zoho_evolution_system.update_account(account_id, update_data)
            assert updated_account["custom_field"] == f"value_{i}"

            # Small delay to simulate real usage
            await asyncio.sleep(0.1)

        # Get learning insights
        insights = await zoho_evolution_system.get_learning_insights()
        assert insights["total_actions"] >= 10  # 5 gets + 5 updates
        assert insights["success_rate"] > 0.9
        assert len(insights["common_patterns"]) > 0
        assert len(insights["optimization_suggestions"]) > 0

        logger.info(f"Adaptive API calls test passed. {insights['total_actions']} actions recorded")

    @pytest.mark.asyncio
    async def test_intelligent_field_selection(self, zoho_evolution_system):
        """Test intelligent field selection based on usage patterns"""
        logger.info("Testing intelligent field selection")

        # Simulate usage patterns
        account_id = TestConfig.TEST_ACCOUNT_ID

        # Make multiple calls with different field requirements
        scenarios = [
            {"fields": ["name", "email"], "frequency": 3},
            {"fields": ["name", "email", "phone"], "frequency": 2},
            {"fields": ["annual_revenue", "employee_count"], "frequency": 4}
        ]

        for scenario in scenarios:
            for _ in range(scenario["frequency"]):
                await zoho_evolution_system.get_account(
                    account_id,
                    fields=scenario["fields"]
                )
                await asyncio.sleep(0.05)

        # Get field recommendations
        recommendations = await zoho_evolution_system.get_field_recommendations(account_id)
        assert len(recommendations) > 0

        # Most frequently used fields should be recommended
        top_fields = [rec["field"] for rec in recommendations[:3]]
        assert "annual_revenue" in top_fields  # Most frequently used
        assert "employee_count" in top_fields

        logger.info("Intelligent field selection test passed")

    @pytest.mark.asyncio
    async def test_error_recovery_and_adaptation(self, zoho_evolution_system):
        """Test error recovery and adaptation"""
        logger.info("Testing error recovery and adaptation")

        # Simulate API errors and recovery
        account_id = TestConfig.TEST_ACCOUNT_ID

        # Configure mock to simulate errors
        original_get_account = zoho_evolution_system.zoho_client.get_account
        call_count = 0

        async def failing_get_account(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 calls
                raise Exception("Simulated API error")
            return await original_get_account(*args, **kwargs)

        zoho_evolution_system.zoho_client.get_account = failing_get_account

        # Should recover from errors
        start_time = time.time()
        account = await zoho_evolution_system.get_account(account_id)
        recovery_time = time.time() - start_time

        assert account["id"] == account_id
        assert recovery_time < 10.0  # Should recover reasonably fast

        # Check error handling metrics
        error_stats = await zoho_evolution_system.get_error_statistics()
        assert error_stats["total_errors"] > 0
        assert error_stats["recovery_rate"] > 0.8

        logger.info("Error recovery and adaptation test passed")


class TestMonitoringSystem:
    """Test monitoring system functionality"""

    @pytest.mark.asyncio
    async def test_metrics_collection(self, monitoring_system):
        """Test metrics collection and aggregation"""
        logger.info("Testing metrics collection")

        # Record various metrics
        test_metrics = [
            {
                "name": "api_response_time",
                "value": 150.5,
                "tags": {"endpoint": "/accounts", "method": "GET"}
            },
            {
                "name": "api_response_time",
                "value": 200.3,
                "tags": {"endpoint": "/accounts", "method": "POST"}
            },
            {
                "name": "error_rate",
                "value": 0.02,
                "tags": {"service": "zoho_api"}
            },
            {
                "name": "memory_usage",
                "value": 256.7,
                "tags": {"component": "orchestrator"}
            }
        ]

        # Record metrics
        for metric in test_metrics:
            await monitoring_system.record_metric(
                name=metric["name"],
                value=metric["value"],
                tags=metric.get("tags", {})
            )

        # Wait for metrics processing
        await asyncio.sleep(1)

        # Query metrics back
        api_metrics = await monitoring_system.get_metrics(
            name="api_response_time",
            time_range="1h"
        )

        assert len(api_metrics) >= 2

        # Check aggregation
        aggregated = await monitoring_system.get_aggregated_metrics(
            name="api_response_time",
            aggregation="avg",
            time_range="1h"
        )

        assert "value" in aggregated
        assert aggregated["value"] > 0

        logger.info(f"Metrics collection test passed. {len(api_metrics)} metrics recorded")

    @pytest.mark.asyncio
    async def test_alert_system(self, monitoring_system):
        """Test alert system functionality"""
        logger.info("Testing alert system")

        # Configure alert rules
        alert_rules = [
            {
                "name": "high_error_rate",
                "condition": "error_rate > 0.1",
                "threshold": 0.1,
                "severity": "critical"
            },
            {
                "name": "slow_response",
                "condition": "api_response_time > 5000",
                "threshold": 5000,
                "severity": "warning"
            }
        ]

        for rule in alert_rules:
            await monitoring_system.add_alert_rule(rule)

        # Trigger alerts
        await monitoring_system.record_metric(
            name="error_rate",
            value=0.15,  # Above threshold
            tags={"service": "test"}
        )

        await monitoring_system.record_metric(
            name="api_response_time",
            value=6000,  # Above threshold
            tags={"endpoint": "/test"}
        )

        # Wait for alert processing
        await asyncio.sleep(2)

        # Check alerts
        alerts = await monitoring_system.get_active_alerts()
        assert len(alerts) >= 2

        # Verify alert details
        error_alert = next((a for a in alerts if a["rule_name"] == "high_error_rate"), None)
        assert error_alert is not None
        assert error_alert["severity"] == "critical"
        assert error_alert["triggered_value"] == 0.15

        response_alert = next((a for a in alerts if a["rule_name"] == "slow_response"), None)
        assert response_alert is not None
        assert response_alert["severity"] == "warning"
        assert response_alert["triggered_value"] == 6000

        logger.info(f"Alert system test passed. {len(alerts)} alerts triggered")

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, monitoring_system):
        """Test performance monitoring capabilities"""
        logger.info("Testing performance monitoring")

        # Simulate system performance data
        performance_data = [
            {
                "timestamp": datetime.utcnow(),
                "cpu_usage": 45.2,
                "memory_usage": 512.3,
                "disk_usage": 67.8,
                "network_io": 1024.5
            },
            {
                "timestamp": datetime.utcnow(),
                "cpu_usage": 78.9,
                "memory_usage": 678.1,
                "disk_usage": 68.0,
                "network_io": 2048.7
            }
        ]

        # Record performance data
        for data in performance_data:
            await monitoring_system.record_performance_metrics(data)

        # Get performance summary
        summary = await monitoring_system.get_performance_summary(
            time_range="1h"
        )

        assert "cpu_usage" in summary
        assert "memory_usage" in summary
        assert "disk_usage" in summary

        # Check statistics
        cpu_stats = summary["cpu_usage"]
        assert "avg" in cpu_stats
        assert "max" in cpu_stats
        assert "min" in cpu_stats
        assert cpu_stats["max"] > cpu_stats["avg"]

        logger.info("Performance monitoring test passed")


class TestOrchestratorIntegration:
    """Test orchestrator integration with all components"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, orchestrator_agent, workflow_engine, mock_zoho_client):
        """Test complete end-to-end workflow"""
        logger.info("Testing end-to-end workflow")

        # Create a complete workflow scenario
        scenario = {
            "intent": "analyze_account_health",
            "account_id": TestConfig.TEST_ACCOUNT_ID,
            "parameters": {
                "include_contacts": True,
                "include_deals": True,
                "analysis_depth": "comprehensive"
            }
        }

        start_time = time.time()

        # Execute through orchestrator
        result = await orchestrator_agent.process_request(scenario)

        execution_time = time.time() - start_time

        # Verify results
        assert result["status"] == "success"
        assert "account_analysis" in result
        assert "health_score" in result["account_analysis"]
        assert "recommendations" in result["account_analysis"]
        assert execution_time < TestConfig.PERFORMANCE_THRESHOLDS["workflow_completion_time"]

        # Verify data quality
        analysis = result["account_analysis"]
        assert 0 <= analysis["health_score"] <= 100
        assert isinstance(analysis["recommendations"], list)
        assert len(analysis["recommendations"]) > 0

        logger.info(f"End-to-end workflow test passed. Execution time: {execution_time:.2f}s")

    @pytest.mark.asyncio
    async def test_component_coordination(self, orchestrator_agent, monitoring_system, mock_glm_client):
        """Test coordination between different components"""
        logger.info("Testing component coordination")

        # Simulate complex request requiring multiple components
        request = {
            "intent": "multi_component_analysis",
            "components": ["intent_detection", "glm_processing", "zoho_integration", "monitoring"],
            "data": {
                "text": "Analyze customer satisfaction trends",
                "account_id": TestConfig.TEST_ACCOUNT_ID
            }
        }

        # Execute with monitoring
        with monitoring_system.measure_operation("component_coordination"):
            result = await orchestrator_agent.coordinate_components(request)

        # Verify all components participated
        assert result["status"] == "success"
        assert "component_results" in result
        assert len(result["component_results"]) >= 4

        # Check component-specific results
        components = result["component_results"]
        assert any(c["component"] == "intent_detection" for c in components)
        assert any(c["component"] == "glm_processing" for c in components)

        # Verify monitoring captured the operation
        metrics = await monitoring_system.get_metrics(
            name="operation_duration",
            tags={"operation": "component_coordination"}
        )
        assert len(metrics) > 0

        logger.info("Component coordination test passed")

    @pytest.mark.asyncio
    async def test_error_propagation_and_recovery(self, orchestrator_agent):
        """Test error propagation and recovery mechanisms"""
        logger.info("Testing error propagation and recovery")

        # Create scenario that will trigger errors
        error_scenarios = [
            {
                "name": "invalid_account",
                "request": {
                    "intent": "analyze_account",
                    "account_id": "invalid_account_id"
                }
            },
            {
                "name": "missing_required_field",
                "request": {
                    "intent": "analyze_account"
                    # Missing account_id
                }
            },
            {
                "name": "invalid_intent",
                "request": {
                    "intent": "invalid_intent_type",
                    "account_id": TestConfig.TEST_ACCOUNT_ID
                }
            }
        ]

        for scenario in error_scenarios:
            result = await orchestrator_agent.process_request(scenario["request"])

            # Should handle errors gracefully
            assert result["status"] == "error"
            assert "error" in result
            assert "error_code" in result["error"]
            assert "message" in result["error"]

            # Error should be informative
            assert len(result["error"]["message"]) > 0
            assert result["error"]["error_code"] is not None

        logger.info("Error propagation and recovery test passed")


class TestPerformanceBenchmarks:
    """Test performance benchmarks and validation"""

    @pytest.mark.asyncio
    async def test_system_performance_benchmarks(self, orchestrator_agent, monitoring_system):
        """Test system performance against benchmarks"""
        logger.info("Testing system performance benchmarks")

        # Define performance test scenarios
        scenarios = [
            {
                "name": "simple_account_lookup",
                "request": {
                    "intent": "get_account",
                    "account_id": TestConfig.TEST_ACCOUNT_ID
                },
                "max_response_time": 2.0
            },
            {
                "name": "comprehensive_analysis",
                "request": {
                    "intent": "analyze_account_health",
                    "account_id": TestConfig.TEST_ACCOUNT_ID,
                    "parameters": {"analysis_depth": "comprehensive"}
                },
                "max_response_time": 10.0
            }
        ]

        performance_results = []

        for scenario in scenarios:
            # Run multiple iterations
            iteration_times = []

            for i in range(5):
                start_time = time.time()
                result = await orchestrator_agent.process_request(scenario["request"])
                execution_time = time.time() - start_time

                iteration_times.append(execution_time)
                assert result["status"] == "success"

                # Small delay between iterations
                await asyncio.sleep(0.1)

            # Calculate statistics
            avg_time = sum(iteration_times) / len(iteration_times)
            max_time = max(iteration_times)
            min_time = min(iteration_times)

            performance_results.append({
                "scenario": scenario["name"],
                "avg_time": avg_time,
                "max_time": max_time,
                "min_time": min_time,
                "max_allowed": scenario["max_response_time"],
                "passed": avg_time <= scenario["max_response_time"]
            })

            # Verify performance meets requirements
            assert avg_time <= scenario["max_response_time"], \
                f"Performance test failed for {scenario['name']}: {avg_time:.2f}s > {scenario['max_response_time']}s"

        # Log performance summary
        logger.info("Performance Benchmark Results:")
        for result in performance_results:
            logger.info(f"  {result['scenario']}: avg={result['avg_time']:.2f}s, "
                       f"max={result['max_time']:.2f}s, passed={result['passed']}")

        # Record performance metrics
        for result in performance_results:
            await monitoring_system.record_metric(
                name="performance_benchmark",
                value=result["avg_time"],
                tags={
                    "scenario": result["scenario"],
                    "passed": str(result["passed"])
                }
            )

        logger.info("System performance benchmarks test passed")

    @pytest.mark.asyncio
    async def test_load_handling(self, orchestrator_agent, monitoring_system):
        """Test system performance under load"""
        logger.info("Testing load handling")

        # Define load test parameters
        concurrent_requests = 10
        requests_per_second = 5

        # Create test requests
        test_requests = [
            {
                "intent": "get_account",
                "account_id": f"test_account_{i % 3 + 1}"  # Rotate between 3 accounts
            }
            for i in range(concurrent_requests)
        ]

        # Execute concurrent requests
        start_time = time.time()

        async def execute_request(request):
            request_start = time.time()
            result = await orchestrator_agent.process_request(request)
            request_time = time.time() - request_start
            return {
                "result": result,
                "execution_time": request_time
            }

        # Run requests concurrently
        tasks = [execute_request(req) for req in test_requests]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Analyze results
        successful_requests = sum(1 for r in results if r["result"]["status"] == "success")
        failed_requests = len(results) - successful_requests
        avg_response_time = sum(r["execution_time"] for r in results) / len(results)
        max_response_time = max(r["execution_time"] for r in results)

        # Verify load handling
        success_rate = successful_requests / len(results)
        assert success_rate >= 0.9, f"Success rate too low: {success_rate:.2%}"
        assert avg_response_time < 5.0, f"Average response time too high: {avg_response_time:.2f}s"
        assert max_response_time < 10.0, f"Max response time too high: {max_response_time:.2f}s"

        # Calculate requests per second
        actual_rps = concurrent_requests / total_time
        assert actual_rps >= requests_per_second * 0.8, \
            f"RPS too low: {actual_rps:.2f} < {requests_per_second}"

        # Record load test metrics
        await monitoring_system.record_metric(
            name="load_test_success_rate",
            value=success_rate,
            tags={"test_type": "concurrent_requests"}
        )

        await monitoring_system.record_metric(
            name="load_test_avg_response_time",
            value=avg_response_time,
            tags={"test_type": "concurrent_requests"}
        )

        await monitoring_system.record_metric(
            name="load_test_rps",
            value=actual_rps,
            tags={"test_type": "concurrent_requests"}
        )

        logger.info(f"Load handling test passed. Success rate: {success_rate:.2%}, "
                   f"Avg response time: {avg_response_time:.2f}s, RPS: {actual_rps:.2f}")

    @pytest.mark.asyncio
    async def test_memory_usage_validation(self, orchestrator_agent, monitoring_system):
        """Test memory usage stays within acceptable limits"""
        logger.info("Testing memory usage validation")

        import psutil
        import gc

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Execute memory-intensive operations
        operations = []
        for i in range(50):
            request = {
                "intent": "analyze_account_health",
                "account_id": f"test_account_{i % 5 + 1}",
                "parameters": {
                    "include_contacts": True,
                    "include_deals": True,
                    "analysis_depth": "comprehensive"
                }
            }
            operations.append(orchestrator_agent.process_request(request))

        # Execute operations
        results = await asyncio.gather(*operations)

        # Force garbage collection
        gc.collect()

        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory usage
        assert final_memory < TestConfig.PERFORMANCE_THRESHOLDS["memory_usage_mb"], \
            f"Memory usage too high: {final_memory:.2f}MB"
        assert memory_increase < 200, \
            f"Memory increase too high: {memory_increase:.2f}MB"

        # Record memory metrics
        await monitoring_system.record_metric(
            name="memory_usage_test",
            value=final_memory,
            tags={
                "initial": str(initial_memory),
                "increase": str(memory_increase)
            }
        )

        logger.info(f"Memory usage validation passed. Initial: {initial_memory:.2f}MB, "
                   f"Final: {final_memory:.2f}MB, Increase: {memory_increase:.2f}MB")


@pytest.mark.asyncio
async def test_full_system_integration():
    """Complete full system integration test"""
    logger.info("Starting full system integration test")

    # Initialize all components
    test_dir = tempfile.mkdtemp()

    try:
        # Setup components
        monitoring_system = EnhancedMonitoringSystem(metrics_dir=test_dir)
        workflow_engine = EnhancedWorkflowEngine()
        intent_engine = EnhancedIntentEngine()

        mock_glm = MockGLMClient(TestConfig.GLM_API_KEY, TestConfig.GLM_BASE_URL)
        mock_zoho = MockZohoClient(
            TestConfig.ZOHO_CLIENT_ID,
            TestConfig.ZOHO_CLIENT_SECRET,
            TestConfig.ZOHO_REFRESH_TOKEN
        )

        orchestrator = EnhancedOrchestratorAgent()

        # Define comprehensive test scenario
        test_scenarios = [
            {
                "name": "account_analysis_workflow",
                "request": {
                    "intent": "analyze_account_health",
                    "account_id": TestConfig.TEST_ACCOUNT_ID,
                    "parameters": {
                        "include_contacts": True,
                        "include_deals": True,
                        "analysis_depth": "comprehensive"
                    }
                },
                "expected_components": ["intent_detection", "zoho_integration", "analysis_engine"]
            },
            {
                "name": "customer_recommendation_workflow",
                "request": {
                    "intent": "generate_recommendations",
                    "account_id": TestConfig.TEST_ACCOUNT_ID,
                    "parameters": {
                        "recommendation_type": "growth",
                        "priority": "high"
                    }
                },
                "expected_components": ["intent_detection", "zoho_integration", "recommendation_engine"]
            }
        ]

        # Execute all scenarios
        all_results = []
        total_start_time = time.time()

        for scenario in test_scenarios:
            logger.info(f"Executing scenario: {scenario['name']}")

            with monitoring_system.measure_operation(f"scenario_{scenario['name']}"):
                result = await orchestrator.process_request(scenario["request"])

                # Verify scenario success
                assert result["status"] == "success", \
                    f"Scenario {scenario['name']} failed: {result}"

                # Verify expected components participated
                if "components_used" in result:
                    for component in scenario["expected_components"]:
                        assert component in result["components_used"], \
                            f"Expected component {component} not found in results"

                all_results.append({
                    "scenario": scenario["name"],
                    "result": result,
                    "execution_time": result.get("execution_time", 0)
                })

        total_execution_time = time.time() - total_start_time

        # Verify overall performance
        avg_scenario_time = sum(r["execution_time"] for r in all_results) / len(all_results)
        assert avg_scenario_time < TestConfig.PERFORMANCE_THRESHOLDS["workflow_completion_time"]

        # Verify system health
        system_health = await monitoring_system.get_system_health()
        assert system_health["overall_status"] == "healthy"

        # Generate integration test report
        integration_report = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "total_scenarios": len(test_scenarios),
            "successful_scenarios": len(all_results),
            "total_execution_time": total_execution_time,
            "average_scenario_time": avg_scenario_time,
            "system_health": system_health,
            "performance_summary": {
                "all_scenarios_passed": True,
                "within_time_thresholds": True,
                "system_stable": True
            }
        }

        # Save integration report
        report_path = os.path.join(test_dir, "integration_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(integration_report, f, indent=2)

        logger.info(f"Full system integration test passed successfully!")
        logger.info(f"Integration report saved to: {report_path}")
        logger.info(f"Total execution time: {total_execution_time:.2f}s")
        logger.info(f"Average scenario time: {avg_scenario_time:.2f}s")

        # Verify system is production-ready
        production_readiness_checks = [
            avg_scenario_time < TestConfig.PERFORMANCE_THRESHOLDS["workflow_completion_time"],
            system_health["overall_status"] == "healthy",
            len(all_results) == len(test_scenarios),
            all(r["result"]["status"] == "success" for r in all_results)
        ]

        assert all(production_readiness_checks), \
            "System is not production-ready - some checks failed"

        logger.info("✅ System verified as production-ready!")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    # Run the integration tests
    import pytest

    # Configure pytest
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ]

    # Run tests
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)