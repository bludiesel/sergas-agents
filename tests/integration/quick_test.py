#!/usr/bin/env python3
"""
Quick Integration Test Validation

This script provides a quick way to validate that the integration tests
can run and that the basic functionality is working.
"""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

async def test_basic_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")

    try:
        from agents.orchestrator import EnhancedOrchestratorAgent
        from agents.intent_detection import EnhancedIntentEngine
        from monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        from workflow.enhanced_engine import EnhancedWorkflowEngine
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality of key components"""
    print("🔧 Testing basic functionality...")

    try:
        # Test intent engine
        from agents.intent_detection import EnhancedIntentEngine
        intent_engine = EnhancedIntentEngine()

        # Test workflow engine
        from workflow.enhanced_engine import EnhancedWorkflowEngine
        workflow_engine = EnhancedWorkflowEngine()

        # Test monitoring system
        from monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        temp_dir = tempfile.mkdtemp()
        monitoring_system = EnhancedMonitoringSystem(metrics_dir=temp_dir)

        # Test orchestrator
        from agents.orchestrator import EnhancedOrchestratorAgent
        orchestrator = EnhancedOrchestratorAgent()

        # Cleanup
        shutil.rmtree(temp_dir)

        print("✅ All components initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

async def test_mock_services():
    """Test that mock services work correctly"""
    print("🎭 Testing mock services...")

    try:
        # Import mock services from integration test
        sys.path.insert(0, str(Path(__file__).parent))
        from full_system_integration_test import MockGLMClient, MockZohoClient

        # Test GLM mock
        glm_client = MockGLMClient("test_key", "https://test.com")
        models = glm_client.get_available_models()
        assert len(models) > 0

        # Test Zoho mock
        zoho_client = MockZohoClient("client_id", "client_secret", "refresh_token")
        account = await zoho_client.get_account("test_account")
        assert account["id"] == "test_account"

        print("✅ Mock services working correctly")
        return True
    except Exception as e:
        print(f"❌ Mock services test failed: {e}")
        return False

async def test_basic_workflow():
    """Test a basic workflow execution"""
    print("🔄 Testing basic workflow...")

    try:
        from workflow.enhanced_engine import EnhancedWorkflowEngine

        workflow_engine = EnhancedWorkflowEngine()

        # Define a simple workflow
        workflow_def = {
            "id": "test_basic_workflow",
            "name": "Basic Test Workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "Initialize",
                    "type": "task",
                    "action": "initialize"
                },
                {
                    "id": "step2",
                    "name": "Process",
                    "type": "task",
                    "action": "process",
                    "depends_on": ["step1"]
                }
            ]
        }

        # Create and execute workflow
        workflow_id = await workflow_engine.create_workflow(workflow_def)
        assert workflow_id is not None

        print("✅ Basic workflow test passed")
        return True
    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}")
        return False

async def test_monitoring_basic():
    """Test basic monitoring functionality"""
    print("📊 Testing monitoring system...")

    try:
        from monitoring.enhanced_monitoring import EnhancedMonitoringSystem

        temp_dir = tempfile.mkdtemp()
        monitoring_system = EnhancedMonitoringSystem(metrics_dir=temp_dir)

        # Record a test metric
        await monitoring_system.record_metric(
            name="test_metric",
            value=42.0,
            tags={"test": "true"}
        )

        # Query the metric back
        metrics = await monitoring_system.get_metrics(name="test_metric")
        assert len(metrics) > 0

        # Cleanup
        shutil.rmtree(temp_dir)

        print("✅ Monitoring system test passed")
        return True
    except Exception as e:
        print(f"❌ Monitoring system test failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("🚀 Running Quick Integration Test Validation")
    print("=" * 50)

    tests = [
        ("Module Imports", test_basic_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Mock Services", test_mock_services),
        ("Basic Workflow", test_basic_workflow),
        ("Monitoring System", test_monitoring_basic),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All quick tests passed! System is ready for full integration testing.")
        print("\nNext steps:")
        print("1. Run: python tests/integration/run_integration_tests.py")
        print("2. Or run: pytest tests/integration/full_system_integration_test.py")
        return 0
    else:
        print("❌ Some quick tests failed. Please fix issues before running full integration tests.")
        print("\nCommon fixes:")
        print("1. Check that all dependencies are installed")
        print("2. Verify the Python path includes src/")
        print("3. Check environment variables are set")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)