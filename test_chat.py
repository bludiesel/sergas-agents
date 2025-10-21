#!/usr/bin/env python3
"""
Quick test script to demonstrate chatting with your SERGAS agents
"""

import subprocess
import time
import sys

def test_agent_chat():
    """Test the agent chat functionality"""
    print("🤖 Testing SERGAS Agent Chat Interface")
    print("=" * 50)

    # Test messages to send to the agents
    test_messages = [
        "Hello, can you help me with account analysis?",
        "What is the GLM-4.6 model capable of?",
        "Can you analyze a sample account for me?",
        "Show me how the workflow engine works"
    ]

    print("💬 You can chat with your agents using:")
    print()
    print("1. TERMINAL CHAT:")
    print("   python3 chat_with_backend.py")
    print()
    print("2. WEB INTERFACE:")
    print("   cd frontend && npm run dev")
    print("   Then visit http://localhost:3000")
    print()
    print("3. DIRECT API CALL:")
    print("   curl -X POST http://localhost:8008/api/copilotkit \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'")
    print()

    print("💡 Sample conversations you can try:")
    print()

    for i, message in enumerate(test_messages, 1):
        print(f"   {i}. '{message}'")

    print()
    print("🎯 Account Analysis Examples:")
    print("   • 'Analyze account ACC-12345 for risk factors'")
    print("   • 'Show me the health score for account ACC-67890'")
    print("   • 'Generate recommendations for premium accounts'")
    print()

    print("🧠 GLM-4.6 Examples:")
    print("   • 'Write a Python function to analyze financial data'")
    print("   • 'Explain the difference between revenue and profit'")
    print("   • 'Create a summary of business performance metrics'")
    print()

    print("🔄 Workflow Examples:")
    print("   • 'Run complete account analysis workflow'")
    print("   • 'Coordinate multiple agents for comprehensive review'")
    print("   • 'Execute parallel analysis tasks'")
    print()

    # Test if backend is running
    try:
        import urllib.request
        import json

        response = urllib.request.urlopen("http://localhost:8008/health", timeout=5)
        health_data = json.loads(response.read().decode())

        print("✅ Backend Status: HEALTHY")
        print(f"   Server: {health_data.get('server', 'Unknown')}")
        print(f"   Status: {health_data.get('status', 'Unknown')}")

    except Exception as e:
        print("⚠️  Backend Status: NOT RUNNING")
        print(f"   Error: {e}")
        print()
        print("🔧 To start the backend:")
        print("   python src/main.py")
        print()
        return False

    print()
    print("🚀 Your agents are ready! Start chatting now!")
    return True

if __name__ == "__main__":
    test_agent_chat()