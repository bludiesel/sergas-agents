#!/usr/bin/env python3
"""
Simple terminal chat interface for the Sergas GLM-4.6 backend
Bypasses all Next.js/CopilotKit complexity and talks directly to the Python agents
"""

import urllib.request
import urllib.parse
import json
import sys

def chat_with_backend(message, account_id="DEFAULT_ACCOUNT"):
    """Send a message directly to the GLM-4.6 backend"""

    url = "http://localhost:8008/api/copilotkit"

    payload = {
        "messages": [{"role": "user", "content": message}],
        "account_id": account_id,
        "operationName": "generateCopilotResponse"
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Extract the response from different possible formats
            if "data" in result and "generateCopilotResponse" in result["data"]:
                return result["data"]["generateCopilotResponse"]["response"]
            elif "response" in result:
                return result["response"]
            else:
                return f"Received: {json.dumps(result, indent=2)}"

    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        return f"Connection error: {e}"

def main():
    """Interactive chat loop"""
    print("🤖 Sergas GLM-4.6 Backend Direct Chat")
    print("=" * 50)
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'help' for available commands")
    print("⚠️  Note: Use account format ACC-XXX for account analysis")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  help    - Show this help")
                print("  quit    - Exit chat")
                print("  status  - Check backend status")
                print("  agents  - List available agents")
                print()
                continue

            if user_input.lower() == 'status':
                try:
                    response = requests.get("http://localhost:8008/health", timeout=5)
                    if response.status_code == 200:
                        print(f"✅ Backend Status: {response.json()}")
                    else:
                        print(f"❌ Backend Error: {response.status_code}")
                except:
                    print("❌ Backend not reachable")
                print()
                continue

            if user_input.lower() == 'agents':
                print("🤖 Available GLM-4.6 Agents:")
                print("  • orchestrator    - Main coordination agent")
                print("  • zoho_scout     - Zoho CRM data specialist")
                print("  • memory_analyst - Context and memory manager")
                print()
                continue

            if not user_input:
                continue

            print("🤖 GLM-4.6: ", end="", flush=True)
            response = chat_with_backend(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()