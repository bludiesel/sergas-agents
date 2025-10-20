#!/usr/bin/env python3
"""Test script to verify GLM-4.6 agents are working correctly."""

import requests
import json
import sys

def test_agents_endpoint():
    """Test the /agents endpoint to verify GLM-4.6 configuration."""
    print("Testing /agents endpoint...")

    try:
        response = requests.get("http://localhost:8008/agents")
        response.raise_for_status()

        data = response.json()

        print(f"✅ Model: {data.get('model')}")
        print(f"✅ Total Agents: {data.get('total_agents')}")
        print("✅ Registered Agents:")
        for agent in data.get('agents', []):
            print(f"   - {agent['name']}: {', '.join(agent['capabilities'][:2])}")

        # Verify GLM-4.6
        if data.get('model') == 'glm-4.6':
            print("\n✅ SUCCESS: GLM-4.6 is active!")
            return True
        else:
            print(f"\n❌ FAILED: Expected glm-4.6, got {data.get('model')}")
            return False

    except Exception as e:
        print(f"❌ Error testing agents endpoint: {e}")
        return False

def test_health_endpoint():
    """Test the /health endpoint."""
    print("\nTesting /health endpoint...")

    try:
        response = requests.get("http://localhost:8008/health")
        response.raise_for_status()

        data = response.json()

        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Service: {data.get('service')}")
        print(f"✅ CopilotKit Configured: {data.get('copilotkit_configured')}")
        print(f"✅ Agents Registered: {data.get('agents_registered')}")

        return data.get('status') == 'healthy'

    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("GLM-4.6 Backend Agent Verification")
    print("=" * 60)
    print()

    agents_ok = test_agents_endpoint()
    health_ok = test_health_endpoint()

    print("\n" + "=" * 60)
    if agents_ok and health_ok:
        print("✅ ALL TESTS PASSED - GLM-4.6 agents are working!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Check backend configuration")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
