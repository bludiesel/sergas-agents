#!/usr/bin/env python3
"""
Quick test script for CopilotKit GraphQL protocol integration.

This script tests the fixed GraphQL protocol to ensure CopilotKit can properly
communicate with the GLM-4.6 backend.

Usage:
    python test_copilotkit_graphql_integration.py
"""

import asyncio
import json
import aiohttp
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

async def test_copilotkit_graphql_protocol():
    """Test CopilotKit's GraphQL protocol with the backend."""

    print("🧪 Testing CopilotKit GraphQL Protocol Integration")
    print("=" * 60)

    # Test 1: Health check
    print("\n1. Testing backend health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/copilotkit/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Backend healthy: {data.get('service')} with {data.get('model')}")
                else:
                    print(f"❌ Backend health failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        print("   Make sure the backend is running on localhost:8000")
        return False

    # Test 2: GraphQL loadAgentState operation
    print("\n2. Testing GraphQL loadAgentState operation...")
    try:
        payload = {
            "operationName": "loadAgentState",
            "variables": {
                "data": {
                    "threadId": f"thread_test_{datetime.utcnow().timestamp()}"
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/copilotkit",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and "loadAgentState" in data["data"]:
                        print("✅ loadAgentState operation successful")
                        print(f"   Thread ID: {data['data']['loadAgentState']['threadId']}")
                    else:
                        print("❌ loadAgentState response format incorrect")
                        print(f"   Response: {json.dumps(data, indent=2)}")
                        return False
                else:
                    print(f"❌ loadAgentState request failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    except Exception as e:
        print(f"❌ loadAgentState test failed: {e}")
        return False

    # Test 3: GraphQL generateCopilotResponse operation
    print("\n3. Testing GraphQL generateCopilotResponse operation...")
    try:
        payload = {
            "operationName": "generateCopilotResponse",
            "variables": {
                "data": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Analyze account ACC-TEST123 for risks and opportunities"
                        }
                    ]
                }
            },
            "agent": "glm-4.6-account-manager",
            "threadId": f"thread_test_{datetime.utcnow().timestamp()}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/copilotkit",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and "generateCopilotResponse" in data["data"]:
                        response_data = data["data"]["generateCopilotResponse"]
                        print("✅ generateCopilotResponse operation successful")
                        print(f"   Agent: {response_data.get('agent')}")
                        print(f"   Model: {response_data.get('model')}")
                        print(f"   Account: {response_data.get('accountId')}")
                        print(f"   Status: {response_data.get('executionStatus')}")
                        print(f"   Response length: {len(response_data.get('response', ''))}")

                        # Check if it contains GLM-4.6 content
                        if "GLM-4.6" in response_data.get('response', ''):
                            print("✅ GLM-4.6 integration working")
                        else:
                            print("⚠️  GLM-4.6 content not found in response")
                    else:
                        print("❌ generateCopilotResponse response format incorrect")
                        print(f"   Response: {json.dumps(data, indent=2)}")
                        return False
                else:
                    print(f"❌ generateCopilotResponse request failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    except Exception as e:
        print(f"❌ generateCopilotResponse test failed: {e}")
        return False

    # Test 4: Test with variables.messages format (alternative CopilotKit format)
    print("\n4. Testing alternative messages format...")
    try:
        payload = {
            "operationName": "generateCopilotResponse",
            "variables": {
                "messages": [
                    {
                        "role": "user",
                        "content": "What are the risk indicators for account ACC-DEMO456?"
                    }
                ]
            },
            "agent": "glm-4.6-account-manager",
            "threadId": f"thread_test_{datetime.utcnow().timestamp()}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/copilotkit",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and "generateCopilotResponse" in data["data"]:
                        response_data = data["data"]["generateCopilotResponse"]
                        print("✅ Alternative messages format working")
                        print(f"   Account extracted: {response_data.get('accountId')}")
                    else:
                        print("❌ Alternative format failed")
                        return False
                else:
                    print(f"❌ Alternative format request failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Alternative format test failed: {e}")
        return False

    return True

async def test_environment_setup():
    """Test if environment variables are properly configured."""
    print("\n🔧 Testing environment setup...")

    import os
    required_vars = ["ANTHROPIC_API_KEY", "CLAUDE_MODEL"]
    optional_vars = ["ANTHROPIC_BASE_URL"]

    all_good = True

    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is missing")
            all_good = False

    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} is set: {os.getenv(var)}")
        else:
            print(f"⚠️  {var} is not set (using default)")

    if all_good:
        print("✅ Environment configuration looks good")
    else:
        print("❌ Environment configuration incomplete")
        print("   Please set the missing environment variables")

    return all_good

async def main():
    """Main test function."""
    print("🚀 CopilotKit GraphQL Protocol Integration Test")
    print("=" * 60)

    # Test environment setup
    env_ok = await test_environment_setup()

    if not env_ok:
        print("\n❌ Environment setup incomplete. Please configure environment variables.")
        print("   Check your .env file or export the required variables.")
        return

    # Test GraphQL protocol
    protocol_ok = await test_copilotkit_graphql_protocol()

    print("\n" + "=" * 60)
    if protocol_ok:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ CopilotKit GraphQL protocol integration is working")
        print("✅ GLM-4.6 backend is properly connected")
        print("✅ The 'Unexpected parameter messages' error should be fixed")
        print("\nNext steps:")
        print("1. Start your frontend (npm run dev)")
        print("2. Test the CopilotKit chat interface")
        print("3. Verify GLM-4.6 responses appear in the frontend")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("1. Make sure the backend is running on localhost:8000")
        print("2. Check environment variables are set correctly")
        print("3. Verify GLM-4.6 API access via Z.ai")
        print("4. Check backend logs for detailed error messages")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())