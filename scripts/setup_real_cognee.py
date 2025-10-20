#!/usr/bin/env python3
"""
Setup Real Cognee (No Mocks, No Docker)
Configures Cognee to use real LLM with OAuth or API key
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

print("=" * 80)
print("COGNEE REAL SETUP - Using Actual LLM (No Mocks)")
print("=" * 80)
print()

# Load environment
env_file = ".env.real" if os.path.exists(".env.real") else ".env.test"
load_dotenv(env_file)
print(f"✓ Loaded environment from: {env_file}")
print()

# Import cognee
try:
    import cognee
    print(f"✓ Cognee imported successfully (version: {cognee.__version__ if hasattr(cognee, '__version__') else 'unknown'})")
except ImportError as e:
    print(f"✗ Failed to import cognee: {e}")
    print("  Install with: pip install cognee")
    sys.exit(1)

print()
print("-" * 80)
print("COGNEE CONFIGURATION")
print("-" * 80)

# Configure Cognee LLM
llm_provider = os.getenv("LLM_PROVIDER", "anthropic")
llm_model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
llm_api_key = os.getenv("LLM_API_KEY", "")

print(f"LLM Provider: {llm_provider}")
print(f"LLM Model: {llm_model}")

if llm_api_key and llm_api_key != "your-api-key-here":
    print(f"LLM API Key: {llm_api_key[:10]}..." if len(llm_api_key) > 10 else "LLM API Key: (set)")
    cognee.config.set_llm_api_key(llm_api_key)
    cognee.config.set_llm_provider(llm_provider)
    cognee.config.set_llm_model(llm_model)
    print("✓ Cognee configured with API key")
else:
    print("⚠️  No LLM API key provided")
    print("   Cognee may prompt for authentication or use defaults")
    print()
    print("   To use Anthropic API:")
    print("   1. Get API key from: https://console.anthropic.com/")
    print("   2. Add to .env.real: LLM_API_KEY=sk-ant-...")
    print()
    print("   To use OpenAI API:")
    print("   1. Get API key from: https://platform.openai.com/api-keys")
    print("   2. Add to .env.real: LLM_PROVIDER=openai")
    print("   3. Add to .env.real: LLM_API_KEY=sk-...")

print()
print("-" * 80)
print("TESTING COGNEE")
print("-" * 80)


async def test_cognee():
    """Test basic Cognee functionality"""

    try:
        print("\n[TEST 1] Adding sample data to Cognee...")

        sample_text = """
        Sergas Super Account Manager is a multi-agent system built with Claude SDK.
        It automates Zoho CRM account management for account executives.
        The system uses three specialized subagents: Data Scout, Memory Analyst, and Recommendation Author.
        It integrates with Cognee for persistent knowledge graph storage.
        """

        await cognee.add(sample_text, dataset_name="sergas-test")
        print("✓ Data added to Cognee")

        print("\n[TEST 2] Processing data (creating knowledge graph)...")
        await cognee.cognify()
        print("✓ Knowledge graph created")

        print("\n[TEST 3] Querying knowledge...")
        from cognee.api.v1.search import SearchType

        results = await cognee.search(
            SearchType.INSIGHTS,
            query_text="What are the subagents in the system?"
        )

        print("✓ Query successful")
        print("\nResults:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result}")

        print("\n" + "=" * 80)
        print("✅ COGNEE IS WORKING!")
        print("=" * 80)
        print("\nCognee is configured and ready to use.")
        print("Data is stored locally in: venv312/lib/python3.12/site-packages/cognee/.cognee_system/")

        return True

    except Exception as e:
        print(f"\n✗ Cognee test failed: {e}")
        import traceback
        traceback.print_exc()

        if "API key" in str(e) or "authentication" in str(e).lower():
            print("\n⚠️  This looks like an API key issue.")
            print("   Add your LLM API key to .env.real and try again.")

        return False


async def main():
    """Main test function"""

    # Check if LLM is configured
    if not llm_api_key or llm_api_key == "your-api-key-here":
        print("\n" + "=" * 80)
        print("⚠️  SETUP INCOMPLETE")
        print("=" * 80)
        print("\nCognee needs an LLM API key to work.")
        print("\nQuick setup:")
        print("1. Copy .env.real to .env: cp .env.real .env")
        print("2. Add your Anthropic API key: LLM_API_KEY=sk-ant-...")
        print("3. Run this script again")
        print("\nAlternatively, you can use OpenAI:")
        print("  LLM_PROVIDER=openai")
        print("  LLM_API_KEY=sk-...")
        return False

    # Run tests
    success = await test_cognee()

    if success:
        print("\n📝 Next Steps:")
        print("1. Update test scripts to use COGNEE_MOCK_MODE=false")
        print("2. Run: python scripts/test_orchestration.py")
        print("3. Test with real agents: python -m src.orchestrator.main_orchestrator")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
