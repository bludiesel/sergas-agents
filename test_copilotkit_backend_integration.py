#!/usr/bin/env python3
"""
Test script for CopilotKit Backend Integration with GLM-4.6 Agents

This script tests the enhanced CopilotKit backend integration:
- Server-Sent Events streaming
- Real OrchestratorAgent execution
- GraphQL operation handling
- Agent orchestration workflow

Usage:
    python test_copilotkit_backend_integration.py

Requirements:
    - Backend server running on localhost:8000
    - ANTHROPIC_API_KEY configured
    - GLM-4.6 model access via Z.ai
"""

import asyncio
import json
import structlog
import aiohttp
from datetime import datetime
from typing import Dict, Any, AsyncGenerator

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_ACCOUNT_ID = "ACC-TEST001"
TEST_USER_MESSAGE = "Analyze account ACC-TEST001 for risks and opportunities"


class CopilotKitBackendTester:
    """Test suite for CopilotKit backend integration."""

    def __init__(self):
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def log_test_result(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test result with details."""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)

        logger.info(
            "test_completed",
            test_name=test_name,
            status=status,
            details=details
        )

        if status == "passed":
            logger.info(f"✅ {test_name}: PASSED")
        else:
            logger.error(f"❌ {test_name}: FAILED")
            if details:
                logger.error(f"   Details: {json.dumps(details, indent=2)}")

    async def test_health_endpoint(self):
        """Test backend health endpoint."""
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "health_check",
                        "passed",
                        {
                            "response_data": data,
                            "status": data.get("status"),
                            "copilotkit_configured": data.get("copilotkit_configured")
                        }
                    )
                    return True
                else:
                    await self.log_test_result(
                        "health_check",
                        "failed",
                        {"status_code": response.status}
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "health_check",
                "failed",
                {"error": str(e)}
            )
            return False

    async def test_copilotkit_health(self):
        """Test CopilotKit specific health endpoint."""
        try:
            async with self.session.get(f"{BASE_URL}/api/copilotkit/health") as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "copilotkit_health_check",
                        "passed",
                        {
                            "response_data": data,
                            "service": data.get("service"),
                            "model": data.get("model"),
                            "provider": data.get("provider"),
                            "orchestrator": data.get("orchestrator")
                        }
                    )
                    return True
                else:
                    await self.log_test_result(
                        "copilotkit_health_check",
                        "failed",
                        {"status_code": response.status}
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "copilotkit_health_check",
                "failed",
                {"error": str(e)}
            )
            return False

    async def test_load_agent_state(self):
        """Test loadAgentState GraphQL operation."""
        try:
            payload = {
                "operationName": "loadAgentState",
                "variables": {
                    "data": {
                        "threadId": f"thread_test_{datetime.utcnow().timestamp()}"
                    }
                }
            }

            async with self.session.post(
                f"{BASE_URL}/api/copilotkit",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "load_agent_state",
                        "passed" if "data" in data else "failed",
                        {
                            "response_data": data,
                            "has_data": "data" in data,
                            "load_agent_state_present": "loadAgentState" in data.get("data", {}),
                            "messages_count": len(
                                data.get("data", {}).get("loadAgentState", {}).get("messages", [])
                            )
                        }
                    )
                    return "data" in data
                else:
                    await self.log_test_result(
                        "load_agent_state",
                        "failed",
                        {"status_code": response.status}
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "load_agent_state",
                "failed",
                {"error": str(e)}
            )
            return False

    async def test_generate_response_json(self):
        """Test generateCopilotResponse with JSON response (non-streaming)."""
        try:
            payload = {
                "operationName": "generateCopilotResponse",
                "variables": {
                    "messages": [
                        {
                            "role": "user",
                            "content": TEST_USER_MESSAGE
                        }
                    ],
                    "accountId": TEST_ACCOUNT_ID
                },
                "agent": "orchestrator",
                "workflow": "account_analysis",
                "stream": False
            }

            async with self.session.post(
                f"{BASE_URL}/api/copilotkit",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "generate_response_json",
                        "passed" if "data" in data else "failed",
                        {
                            "response_data": data,
                            "has_data": "data" in data,
                            "generate_response_present": "generateCopilotResponse" in data.get("data", {}),
                            "agent": data.get("data", {}).get("generateCopilotResponse", {}).get("agent"),
                            "execution_status": data.get("data", {}).get("generateCopilotResponse", {}).get("executionStatus")
                        }
                    )
                    return "data" in data
                else:
                    await self.log_test_result(
                        "generate_response_json",
                        "failed",
                        {"status_code": response.status}
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "generate_response_json",
                "failed",
                {"error": str(e)}
            )
            return False

    async def test_generate_response_streaming(self):
        """Test generateCopilotResponse with Server-Sent Events streaming."""
        try:
            payload = {
                "operationName": "generateCopilotResponse",
                "variables": {
                    "messages": [
                        {
                            "role": "user",
                            "content": TEST_USER_MESSAGE
                        }
                    ],
                    "accountId": TEST_ACCOUNT_ID
                },
                "agent": "orchestrator",
                "workflow": "account_analysis",
                "stream": True
            }

            events_received = []

            async with self.session.post(
                f"{BASE_URL}/api/copilotkit/stream",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as response:
                if response.status != 200:
                    await self.log_test_result(
                        "generate_response_streaming",
                        "failed",
                        {"status_code": response.status}
                    )
                    return False

                # Process SSE stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])
                            events_received.append(event_data)
                        except json.JSONDecodeError:
                            pass  # Skip malformed JSON

                await self.log_test_result(
                    "generate_response_streaming",
                    "passed" if len(events_received) > 0 else "failed",
                    {
                        "events_received_count": len(events_received),
                        "events_sample": events_received[:3] if events_received else [],
                        "has_connection_event": any(
                            event.get("event") == "connection_established"
                            for event in events_received
                        ),
                        "has_orchestration_events": any(
                            "agent" in event.get("event", "").lower()
                            for event in events_received
                        )
                    }
                )
                return len(events_received) > 0

        except Exception as e:
            await self.log_test_result(
                "generate_response_streaming",
                "failed",
                {"error": str(e)}
            )
            return False

    async def test_agents_listing(self):
        """Test agents listing endpoint."""
        try:
            async with self.session.get(f"{BASE_URL}/agents") as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "agents_listing",
                        "passed" if "agents" in data else "failed",
                        {
                            "response_data": data,
                            "has_agents": "agents" in data,
                            "total_agents": data.get("total_agents", 0),
                            "agent_names": [agent.get("name") for agent in data.get("agents", [])]
                        }
                    )
                    return "agents" in data
                else:
                    await self.log_test_result(
                        "agents_listing",
                        "failed",
                        {"status_code": response.status}
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "agents_listing",
                "failed",
                {"error": str(e)}
            )
            return False

    async def run_all_tests(self):
        """Run complete test suite."""
        logger.info("starting_copilotkit_backend_test_suite")

        tests = [
            ("Health Check", self.test_health_endpoint),
            ("CopilotKit Health", self.test_copilotkit_health),
            ("Load Agent State", self.test_load_agent_state),
            ("Generate Response (JSON)", self.test_generate_response_json),
            ("Generate Response (Streaming)", self.test_generate_response_streaming),
            ("Agents Listing", self.test_agents_listing)
        ]

        for test_name, test_func in tests:
            logger.info(f"running_test", test_name=test_name)
            await test_func()
            await asyncio.sleep(0.5)  # Brief pause between tests

        # Print final results
        await self.print_test_summary()

    async def print_test_summary(self):
        """Print comprehensive test results summary."""
        passed_tests = sum(1 for result in self.test_results if result["status"] == "passed")
        total_tests = len(self.test_results)

        logger.info("test_suite_completed", passed=passed_tests, total=total_tests)

        print("\n" + "="*60)
        print("COPILOTKIT BACKEND INTEGRATION TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("")

        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "passed" else "❌"
            print(f"{status_symbol} {result['test_name']}")
            if result["status"] == "failed" and result["details"]:
                print(f"   Details: {json.dumps(result['details'], indent=4)}")

        print("\n" + "="*60)

        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - CopilotKit Backend Integration is Working!")
        else:
            print("⚠️  Some tests failed - Check the details above for troubleshooting")

        print("="*60)


async def main():
    """Main test execution function."""
    print("🧪 CopilotKit Backend Integration Test Suite")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Account: {TEST_ACCOUNT_ID}")
    print(f"Test Message: {TEST_USER_MESSAGE}")
    print("=" * 60)
    print()

    async with CopilotKitBackendTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())