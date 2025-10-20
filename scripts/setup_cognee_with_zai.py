#!/usr/bin/env python3
"""
Setup Cognee with Z.ai GLM-4.6 (Coding Plan)
Uses the proven LiteLLM + Z.ai Anthropic endpoint approach
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

print("=" * 80)
print("COGNEE + Z.AI GLM-4.6 SETUP")
print("Using your existing Z.ai coding plan quota!")
print("=" * 80)
print()

# Load environment
env_file = ".env" if os.path.exists(".env") else ".env.real"
load_dotenv(env_file)
print(f"✓ Loaded environment from: {env_file}")
print()

# Check for Z.ai API key
zai_api_key = os.getenv("ZAI_API_KEY")
if not zai_api_key:
    print("❌ ZAI_API_KEY not found in environment")
    print()
    print("Setup instructions:")
    print("1. Add to .env or .env.real:")
    print("   ZAI_API_KEY=your-z-ai-api-key")
    print()
    print("2. Get your Z.ai API key from your coding plan subscription")
    print("   (Same key you use for Claude Code, Cline, etc.)")
    print()
    sys.exit(1)

print(f"✓ Z.ai API key found: {zai_api_key[:15]}...")
print()

# Import cognee
try:
    import cognee
    print(f"✓ Cognee imported successfully")
except ImportError as e:
    print(f"✗ Failed to import cognee: {e}")
    print("  Install with: pip install cognee")
    sys.exit(1)

# Import litellm
try:
    import litellm
    print(f"✓ LiteLLM imported successfully")
except ImportError as e:
    print(f"✗ Failed to import litellm: {e}")
    print("  Install with: pip install litellm")
    sys.exit(1)

print()
print("-" * 80)
print("CONFIGURING COGNEE WITH Z.AI GLM-4.6")
print("-" * 80)
print()

# Configure Cognee to use LiteLLM with Z.ai
print("Configuration:")
print("  Provider: anthropic (via LiteLLM)")
print("  Model: glm-4.6")
print("  Endpoint: https://api.z.ai/api/anthropic")
print("  Auth: Z.ai API key")
print()

# Set up LiteLLM configuration for Cognee
# IMPORTANT: Set these ONLY in this script's context, not globally!
# This prevents interference with Claude Code's Max subscription OAuth

# Temporarily set environment variables for Cognee only
original_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
original_anthropic_base = os.environ.get("ANTHROPIC_BASE_URL")

os.environ["ANTHROPIC_API_KEY"] = zai_api_key  # For Cognee only
os.environ["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic"  # For Cognee only
os.environ["LITELLM_LOG"] = "DEBUG"  # Enable debug logging

# Configure Cognee
try:
    # Cognee uses LiteLLM under the hood
    # We need to configure it to use Z.ai's Anthropic endpoint

    # Set LiteLLM config for Cognee
    cognee.config.set_llm_provider("anthropic")  # Use Anthropic provider format
    cognee.config.set_llm_model("glm-4.6")  # Z.ai model
    cognee.config.set_llm_api_key(zai_api_key)  # Z.ai API key

    print("✓ Cognee configured with Z.ai GLM-4.6")
    print("  (Environment variables set for this script only)")

except Exception as e:
    print(f"⚠️  Configuration note: {e}")
    print("   Proceeding with environment-based config...")

print()
print("-" * 80)
print("TESTING COGNEE WITH Z.AI")
print("-" * 80)


async def test_cognee_with_zai():
    """Test Cognee with Z.ai GLM-4.6"""

    try:
        print("\n[TEST 1] Adding sample data to Cognee...")

        sample_text = """
        The Sergas Super Account Manager is an intelligent multi-agent system.
        It uses Claude Agent SDK for orchestration.
        The system has three specialized subagents:
        1. Zoho Data Scout - Retrieves account data from Zoho CRM
        2. Memory Analyst - Analyzes patterns using Cognee knowledge graphs
        3. Recommendation Author - Generates actionable recommendations

        The system integrates with Z.ai GLM-4.6 for cost-effective AI processing.
        """

        await cognee.add(sample_text, dataset_name="sergas-zai-test")
        print("✓ Data added to Cognee")

        print("\n[TEST 2] Creating knowledge graph (using Z.ai GLM-4.6)...")
        print("  This will use your Z.ai coding plan quota!")
        await cognee.cognify()
        print("✓ Knowledge graph created successfully")

        print("\n[TEST 3] Querying knowledge graph...")
        from cognee.api.v1.search import SearchType

        results = await cognee.search(
            query_text="What are the three subagents in the Sergas system?",
            query_type=SearchType.INSIGHTS
        )

        print("✓ Query successful")
        print("\n📊 Results from Z.ai GLM-4.6:")
        print("-" * 60)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result}")
        print("-" * 60)

        print("\n" + "=" * 80)
        print("✅ COGNEE IS WORKING WITH Z.AI GLM-4.6!")
        print("=" * 80)
        print()
        print("💰 Cost Savings:")
        print("  • Using your existing Z.ai coding plan quota")
        print("  • No additional API charges")
        print("  • Same quota as Claude Code, Cline, etc.")
        print()
        print("📊 Performance:")
        print("  • Model: GLM-4.6 (latest version)")
        print("  • Endpoint: Z.ai Anthropic-compatible")
        print("  • Provider: LiteLLM translation layer")

        return True

    except Exception as e:
        print(f"\n✗ Cognee test failed: {e}")
        import traceback
        traceback.print_exc()

        print("\n⚠️  Troubleshooting:")
        print("1. Verify Z.ai API key is correct:")
        print(f"   Current: {zai_api_key[:15]}...")
        print()
        print("2. Check if you have Z.ai coding plan subscription active")
        print()
        print("3. Test Z.ai connection directly:")
        print("   curl -X POST https://api.z.ai/api/anthropic/v1/messages \\")
        print("     -H 'x-api-key: $ZAI_API_KEY' \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"model\":\"glm-4.6\",\"max_tokens\":100,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}'")

        return False


async def main():
    """Main test function"""

    success = await test_cognee_with_zai()

    if success:
        print("\n📝 Next Steps:")
        print("1. Your Cognee is now configured to use Z.ai GLM-4.6")
        print("2. Update .env to disable mock mode:")
        print("   COGNEE_MOCK_MODE=false")
        print("3. Run full orchestration:")
        print("   python -m src.orchestrator.main_orchestrator")
        print()
        print("💡 Tip: All Cognee operations now use your Z.ai coding plan quota!")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
