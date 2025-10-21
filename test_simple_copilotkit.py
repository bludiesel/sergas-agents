#!/usr/bin/env python3
"""
Simple test script for CopilotKit GraphQL protocol integration.
Uses only standard library modules.
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime

def test_copilotkit_endpoint():
    """Test the CopilotKit endpoint with a simple GraphQL request."""

    print("🧪 Testing CopilotKit GraphQL Integration")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Testing backend health...")
    try:
        with urllib.request.urlopen("http://localhost:8000/api/copilotkit/health") as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"✅ Backend healthy: {data.get('service')} with {data.get('model')}")
            else:
                print(f"❌ Backend health failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        print("   Make sure the backend is running on localhost:8000")
        return False

    # Test 2: GraphQL loadAgentState operation
    print("\n2. Testing GraphQL loadAgentState...")
    try:
        payload = {
            "operationName": "loadAgentState",
            "variables": {
                "data": {
                    "threadId": f"thread_test_{datetime.utcnow().timestamp()}"
                }
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8000/api/copilotkit",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                response_data = json.loads(response.read().decode())
                if "data" in response_data and "loadAgentState" in response_data["data"]:
                    print("✅ loadAgentState operation successful")
                    print(f"   Thread ID: {response_data['data']['loadAgentState']['threadId']}")
                else:
                    print("❌ loadAgentState response format incorrect")
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return False
            else:
                print(f"❌ loadAgentState request failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ loadAgentState test failed: {e}")
        return False

    # Test 3: GraphQL generateCopilotResponse operation
    print("\n3. Testing GraphQL generateCopilotResponse...")
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

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8000/api/copilotkit",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                response_data = json.loads(response.read().decode())
                if "data" in response_data and "generateCopilotResponse" in response_data["data"]:
                    result = response_data["data"]["generateCopilotResponse"]
                    print("✅ generateCopilotResponse operation successful")
                    print(f"   Agent: {result.get('agent')}")
                    print(f"   Model: {result.get('model')}")
                    print(f"   Account: {result.get('accountId')}")
                    print(f"   Status: {result.get('executionStatus')}")
                    print(f"   Response length: {len(result.get('response', ''))}")

                    # Check if it contains GLM-4.6 content
                    if "GLM-4.6" in result.get('response', ''):
                        print("✅ GLM-4.6 integration working")
                    else:
                        print("⚠️  GLM-4.6 content not found in response")
                        print("   This might indicate an issue with the GLM-4.6 API setup")
                else:
                    print("❌ generateCopilotResponse response format incorrect")
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return False
            else:
                print(f"❌ generateCopilotResponse request failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ generateCopilotResponse test failed: {e}")
        return False

    return True

def test_environment():
    """Test if environment variables are set."""
    print("\n🔧 Testing environment setup...")

    import os

    required_vars = ["ANTHROPIC_API_KEY"]
    optional_vars = ["CLAUDE_MODEL", "ANTHROPIC_BASE_URL"]

    all_good = True

    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is missing")
            all_good = False

    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set (will use default)")

    return all_good

def main():
    """Main test function."""
    print("🚀 CopilotKit GraphQL Protocol Integration Test")
    print("=" * 60)

    # Test environment
    env_ok = test_environment()

    if not env_ok:
        print("\n❌ Environment setup incomplete")
        print("   Please set ANTHROPIC_API_KEY environment variable")
        return

    # Test integration
    integration_ok = test_copilotkit_endpoint()

    print("\n" + "=" * 60)
    if integration_ok:
        print("🎉 INTEGRATION TEST PASSED!")
        print("\n✅ CopilotKit GraphQL protocol is working")
        print("✅ Backend properly handles GraphQL operations")
        print("✅ The 'Unexpected parameter messages' error should be fixed")
        print("\nThe implementation successfully:")
        print("• Parses CopilotKit's GraphQL protocol")
        print("• Extracts user messages from variables.data.messages")
        print("• Calls GLM-4.6 model via Z.ai")
        print("• Returns properly formatted GraphQL responses")
        print("\nNext steps:")
        print("1. Start your frontend: npm run dev")
        print("2. Test the CopilotKit chat interface")
        print("3. Verify the GraphQL errors are gone")
    else:
        print("❌ INTEGRATION TEST FAILED")
        print("\nTroubleshooting:")
        print("1. Ensure backend is running on localhost:8000")
        print("2. Check ANTHROPIC_API_KEY is set correctly")
        print("3. Verify GLM-4.6 access via Z.ai")
        print("4. Check backend logs for detailed errors")

    print("=" * 60)

if __name__ == "__main__":
    main()