#!/usr/bin/env python3
"""
Test Claude SDK with Max Subscription OAuth
Demonstrates how to use Claude Agent SDK with your Max subscription instead of API billing
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 80)
print("CLAUDE SDK - MAX SUBSCRIPTION OAUTH TEST")
print("=" * 80)
print()

# CRITICAL: Remove ANTHROPIC_API_KEY from environment to use OAuth
if "ANTHROPIC_API_KEY" in os.environ:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    if api_key and api_key != "your-anthropic-api-key-here":
        print("⚠️  WARNING: ANTHROPIC_API_KEY is set in environment")
        print(f"   Value: {api_key[:15]}...")
        print()
        print("   When ANTHROPIC_API_KEY is set, the SDK will use API billing")
        print("   instead of your Max subscription.")
        print()
        choice = input("   Remove API key and use Max subscription OAuth? (y/N): ")
        if choice.lower() == 'y':
            del os.environ["ANTHROPIC_API_KEY"]
            print("   ✓ API key removed, will use OAuth")
        else:
            print("   Continuing with API key (will use API billing)...")
    else:
        # Empty or placeholder key, safe to remove
        del os.environ["ANTHROPIC_API_KEY"]
        print("✓ Empty API key removed, will use OAuth")
else:
    print("✓ No ANTHROPIC_API_KEY in environment")
    print("  SDK will use OAuth authentication with your Max subscription")

print()
print("-" * 80)
print("AUTHENTICATION METHOD")
print("-" * 80)
print()

if "ANTHROPIC_API_KEY" not in os.environ:
    print("✓ OAuth Mode (Max Subscription)")
    print("  - Uses your Claude Pro/Max subscription")
    print("  - No per-token charges")
    print("  - Usage counts against subscription limits")
    print("  - Browser authentication required on first run")
else:
    print("⚠️  API Key Mode")
    print("  - Uses Anthropic API with pay-per-token billing")
    print("  - Does NOT use your Max subscription")
    print("  - May incur API charges")

print()
print("-" * 80)
print("TESTING CLAUDE SDK")
print("-" * 80)

try:
    from claude_agent_sdk import query, TextBlock, AssistantMessage
    import asyncio
    print("\n✓ claude-agent-sdk imported successfully")
except ImportError as e:
    print(f"\n✗ Failed to import claude-agent-sdk: {e}")
    print("  Install with: pip install claude-agent-sdk")
    sys.exit(1)

print("\n[TEST 1] Testing Claude SDK query...")


async def test_query():
    """Test Claude SDK with OAuth"""

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("\n📝 OAuth Authentication:")
        print("  - A browser window may open for authentication")
        print("  - Log in with your Claude Max account")
        print("  - Grant permissions to the SDK")
        print("  - Return to this terminal after authentication")
        print()

    print("\n[TEST 2] Sending simple test message...")

    # Simple test using query() which supports OAuth
    response_text = ""
    async for message in query(prompt="Say 'Hello from Claude SDK!' in exactly those words."):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    print("✓ Message sent successfully")
    print("\nClaude's response:")
    print(f"  {response_text}")

    return response_text


try:
    # Run async test
    result = asyncio.run(test_query())

    print("\n" + "=" * 80)
    print("✅ CLAUDE SDK IS WORKING WITH MAX SUBSCRIPTION!")
    print("=" * 80)

    print("\n📊 Usage Info:")
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("  ✓ Using: Claude Max subscription (OAuth)")
        print("  ✓ Billing: No additional charges (counts against subscription)")
        print("  ✓ Limits: Subject to Max plan limits (resets every 5 hours)")
    else:
        print("  ⚠️  Using: Anthropic API (API Key)")
        print("  ⚠️  Billing: Pay-per-token charges apply")
        print("  ⚠️  Limits: API rate limits apply")

    print("\n📝 Next Steps:")
    print("1. Your Claude SDK is configured correctly")
    print("2. Test with agents: python -m src.orchestrator.main_orchestrator")
    print("3. Agents will use your Max subscription automatically")

except Exception as e:
    print(f"\n✗ Claude SDK test failed: {e}")
    import traceback
    traceback.print_exc()

    if "authentication" in str(e).lower() or "oauth" in str(e).lower():
        print("\n⚠️  OAuth Authentication Issue")
        print("   Make sure you have:")
        print("   1. Active Claude Pro/Max subscription")
        print("   2. Browser access for OAuth login")
        print("   3. Network connection")
    elif "api key" in str(e).lower():
        print("\n⚠️  API Key Issue")
        print("   The SDK is trying to use API key but it's invalid.")
        print("   Remove ANTHROPIC_API_KEY from environment to use OAuth.")

    sys.exit(1)

print()
