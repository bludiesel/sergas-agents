#!/usr/bin/env python3
"""
Simple Chat Interface for Sergas Agents (No Dependencies Required)

This script lets you chat with your agents without installing any external packages.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

class SimpleAgentChat:
    """Simple chat interface that works with minimal dependencies"""

    def __init__(self, base_url="http://localhost:8008"):
        self.base_url = base_url
        self.session_id = f"session_{int(time.time())}"

    def send_message(self, message: str, account_id: str = "DEFAULT_ACCOUNT") -> dict:
        """Send message to agent backend"""

        payload = {
            "messages": [{"role": "user", "content": message}],
            "account_id": account_id,
            "operationName": "generateCopilotResponse"
        }

        try:
            # Create HTTP request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/api/copilotkit",
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            # Send request and get response
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result

        except urllib.error.URLError as e:
            return {
                "response": f"❌ Connection Error: Cannot reach backend at {self.base_url}",
                "error": str(e),
                "agent_used": "error_handler",
                "confidence": 0.0
            }
        except Exception as e:
            return {
                "response": f"❌ Error: {e}",
                "error": str(e),
                "agent_used": "error_handler",
                "confidence": 0.0
            }

    def check_backend_status(self) -> dict:
        """Check if backend is running"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": self.base_url
            }

def print_welcome():
    """Print welcome message"""
    print("🤖 Sergas Agents - Simple Chat Interface")
    print("=" * 60)
    print("💬 Type your messages and press Enter")
    print("🚪 Type 'quit', 'exit', or Ctrl+C to exit")
    print("❓ Type 'help' for available commands")
    print("📊 Type 'status' to check backend status")
    print("=" * 60)

def print_help():
    """Print help information"""
    print("\n📖 Available Commands:")
    print("  help     - Show this help message")
    print("  status   - Check backend server status")
    print("  quit/exit- Exit the chat")
    print("  agents  - Show available agent types")
    print()
    print("💬 Example Conversations:")
    print("  • Analyze account ACC-12345")
    print("  • Write Python code to analyze revenue")
    print("  • Explain GLM-4.6 model capabilities")
    print("  • Run complete account analysis workflow")
    print("  • Show me agent learning progress")
    print()

def print_agents_info():
    """Print information about available agents"""
    print("\n🤖 Available Agent Capabilities:")
    print("  📊 Account Analysis Agent:")
    print("     • Analyze account health and risk factors")
    print("     • Generate recommendations and insights")
    print("     • Monitor account performance metrics")
    print()
    print("  💻 Code Generation Agent:")
    print("     • Write Python functions for data analysis")
    print("     • Create data visualization code")
    print("     • Generate automation scripts")
    print()
    print("  🔄 Workflow Coordinator:")
    print("     • Coordinate multi-agent workflows")
    print("     • Execute parallel analysis tasks")
    print("     • Handle complex multi-step processes")
    print()
    print("  🧠 GLM-4.6 Enhanced Agent:")
    print("     • Intelligent model selection")
    print("     • Complex reasoning and analysis")
    print("     • Generate sophisticated responses")
    print()
    print("  📈 Learning & Evolution Agent:")
    print("     • Learn from user interactions")
    print("     • Improve response quality over time")
    print("     • Adapt to user preferences")
    print()

def main():
    """Main chat loop"""
    print_welcome()

    # Initialize chat interface
    chat = SimpleAgentChat()

    # Check backend status
    print("🔍 Checking backend status...")
    status = chat.check_backend_status()

    if status.get("status") == "healthy":
        print("✅ Backend is running and ready!")
        print(f"   Server: {status.get('server', 'unknown')}")
        print(f"   Orchestrator: {'✅ Available' if status.get('orchestrator_available') else '❌ Not Available'}")
    else:
        print("⚠️  Backend is not running!")
        print(f"   Error: {status.get('error', 'Unknown error')}")
        print()
        print("🔧 To start the backend:")
        print("   python3 src/main_simple.py")
        print()
        print("💡 You can still chat, but responses will be from mock agents")

    print("\n💬 How can I help you today?")

    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()

            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Thanks for chatting with Sergas Agents!")
                break

            elif user_input.lower() == 'help':
                print_help()
                continue

            elif user_input.lower() == 'status':
                print(f"\n📊 Backend Status:")
                print(json.dumps(status, indent=2))
                continue

            elif user_input.lower() == 'agents':
                print_agents_info()
                continue

            elif not user_input:
                continue

            # Send message to agent
            print("🤖 Agent: ", end="", flush=True)

            # Get response from backend
            start_time = time.time()
            response = chat.send_message(user_input)
            response_time = time.time() - start_time

            # Display response
            print(response.get("response", "I'm not sure how to respond to that."))

            # Show metadata if available
            metadata = response.get("metadata", {})
            if metadata:
                print(f"\n   🤖 Agent: {response.get('agent_used', 'unknown')}")
                print(f"   📊 Confidence: {response.get('confidence', 0):.2f}")
                print(f"   ⏱️  Response Time: {response_time:.2f}s")

                # Show additional metadata
                for key, value in metadata.items():
                    if key not in ['timestamp']:
                        print(f"   📋 {key.replace('_', ' ').title()}: {value}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for chatting with Sergas Agents!")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Thanks for chatting with Sergas Agents!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("💡 Please try again or type 'quit' to exit")

if __name__ == "__main__":
    main()