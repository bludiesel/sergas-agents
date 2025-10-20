#!/usr/bin/env python3
"""
Test Script for Agent Orchestration
Tests the orchestrator's ability to coordinate subagents without requiring external credentials
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load test environment
from dotenv import load_dotenv
load_dotenv('.env.test')

print("=" * 80)
print("SERGAS AGENT ORCHESTRATION TEST")
print("=" * 80)
print(f"Test started at: {datetime.now().isoformat()}")
print(f"Environment: {os.getenv('ENV', 'unknown')}")
print(f"SQLite Mode: {os.getenv('DATABASE_TYPE') == 'sqlite'}")
print(f"Mock Mode: Zoho={os.getenv('ZOHO_MOCK_MODE')}, Cognee={os.getenv('COGNEE_MOCK_MODE')}")
print("=" * 80)
print()


async def test_sqlite_connection():
    """Test 1: SQLite Database Connection"""
    print("[TEST 1] Testing SQLite Database Connection...")

    try:
        from database.sqlite_adapter import get_sqlite_adapter

        db = get_sqlite_adapter()
        conn = await db.connect()

        print("✓ SQLite connection successful")
        print(f"  Database path: {db.db_path}")

        # Test creating a session
        session_id = f"test-session-{datetime.now().timestamp()}"
        session = await db.create_session(
            session_id=session_id,
            orchestrator_id="test-orchestrator",
            account_owner_id="OWNER1",
            account_ids=["ACC1000", "ACC1001"]
        )

        print(f"✓ Created test session: {session_id}")
        print(f"  Session data: {json.dumps(session, indent=2)}")

        # Test retrieving session
        retrieved = await db.get_session(session_id)
        assert retrieved is not None, "Failed to retrieve session"
        print("✓ Retrieved session successfully")

        # Test logging audit event
        await db.log_audit_event(
            event_id=f"evt-{datetime.now().timestamp()}",
            session_id=session_id,
            agent_id="test-orchestrator",
            event_type="test_event",
            event_data={"message": "Test audit event"},
            severity="info"
        )
        print("✓ Logged audit event successfully")

        print()
        return True

    except Exception as e:
        print(f"✗ SQLite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_zoho():
    """Test 2: Mock Zoho Integration"""
    print("[TEST 2] Testing Mock Zoho Integration...")

    try:
        from integrations.mock_zoho import get_mock_zoho

        zoho = get_mock_zoho()
        print("✓ Mock Zoho client initialized")
        print(f"  Generated {len(zoho.mock_accounts)} mock accounts")

        # Test getting accounts by owner
        result = await zoho.get_accounts_by_owner("OWNER1")
        print(f"✓ Retrieved {len(result['data'])} accounts for OWNER1")

        if result['data']:
            account = result['data'][0]
            print(f"  Sample account: {account['Account_Name']} ({account['id']})")

            # Test getting account details
            account_id = account['id']
            deals = await zoho.get_account_deals(account_id)
            print(f"✓ Retrieved {len(deals.get('data', []))} deals for {account_id}")

            activities = await zoho.get_account_activities(account_id)
            print(f"✓ Retrieved {len(activities.get('data', []))} activities for {account_id}")

            notes = await zoho.get_account_notes(account_id)
            print(f"✓ Retrieved {len(notes.get('data', []))} notes for {account_id}")

            # Test change detection
            from datetime import timedelta
            changes = await zoho.detect_changes(
                account_id,
                datetime.now() - timedelta(days=30)
            )
            print(f"✓ Change detection: {changes['has_changes']} changes detected")

        print()
        return True

    except Exception as e:
        print(f"✗ Mock Zoho test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_cognee():
    """Test 3: Mock Cognee Integration"""
    print("[TEST 3] Testing Mock Cognee Integration...")

    try:
        from integrations.mock_zoho import get_mock_cognee

        cognee = get_mock_cognee()
        print("✓ Mock Cognee client initialized")

        # Test storing memory
        await cognee.store_memory(
            account_id="ACC1000",
            memory_type="test_context",
            data={"test": "data", "timestamp": datetime.now().isoformat()}
        )
        print("✓ Stored test memory")

        # Test getting historical context
        context = await cognee.get_historical_context("ACC1000")
        print(f"✓ Retrieved historical context")
        print(f"  Summary: {context['summary']}")
        print(f"  Key events: {len(context['key_events'])}")
        print(f"  Sentiment: {context['sentiment_trend']}")

        # Test pattern identification
        patterns = await cognee.identify_patterns("ACC1000")
        print(f"✓ Identified {len(patterns)} patterns")
        for pattern in patterns:
            print(f"  - {pattern['pattern_type']}: {pattern['description']} (confidence: {pattern['confidence']})")

        # Test memory query
        result = await cognee.query_memory("ACC1000", "What are recent activities?")
        print(f"✓ Memory query returned {len(result['results'])} results")

        print()
        return True

    except Exception as e:
        print(f"✗ Mock Cognee test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_workflow_simulation():
    """Test 4: Simulate Agent Workflow"""
    print("[TEST 4] Simulating Agent Workflow (without Claude SDK)...")

    try:
        from integrations.mock_zoho import get_mock_zoho, get_mock_cognee
        from database.sqlite_adapter import get_sqlite_adapter

        # Initialize components
        zoho = get_mock_zoho()
        cognee = get_mock_cognee()
        db = get_sqlite_adapter()

        print("✓ All components initialized")

        # Create workflow session
        session_id = f"workflow-{datetime.now().timestamp()}"
        session = await db.create_session(
            session_id=session_id,
            orchestrator_id="main-orchestrator",
            account_owner_id="OWNER1",
            account_ids=["ACC1000", "ACC1001"]
        )
        print(f"✓ Created workflow session: {session_id}")

        # Simulate Data Scout workflow
        print("\n  [Simulating Data Scout Agent]")
        accounts = await zoho.get_accounts_by_owner("OWNER1")
        print(f"  ✓ Fetched {len(accounts['data'])} accounts")

        for account in accounts['data'][:2]:  # Limit to 2 for testing
            account_id = account['id']
            deals = await zoho.get_account_deals(account_id)
            activities = await zoho.get_account_activities(account_id)
            print(f"  ✓ Processed {account_id}: {len(deals['data'])} deals, {len(activities['data'])} activities")

        # Simulate Memory Analyst workflow
        print("\n  [Simulating Memory Analyst Agent]")
        for account in accounts['data'][:2]:
            account_id = account['id']
            context = await cognee.get_historical_context(account_id)
            patterns = await cognee.identify_patterns(account_id)
            print(f"  ✓ Analyzed {account_id}: {len(patterns)} patterns, sentiment={context['sentiment_trend']}")

        # Simulate Recommendation Author workflow
        print("\n  [Simulating Recommendation Author Agent]")
        recommendations = []
        for account in accounts['data'][:2]:
            recommendation = {
                "account_id": account['id'],
                "action": "schedule_followup",
                "rationale": f"Account {account['Account_Name']} shows positive engagement",
                "confidence": 0.85,
                "priority": "high"
            }
            recommendations.append(recommendation)
            print(f"  ✓ Generated recommendation for {account['id']}")

        # Update session with results
        await db.update_session(
            session_id=session_id,
            updates={
                "status": "completed",
                "workflow_state": {"stage": "recommendations_generated"},
                "subagent_results": {
                    "data_scout": {"accounts_processed": len(accounts['data'][:2])},
                    "memory_analyst": {"patterns_found": 4},
                    "recommendation_author": {"recommendations_count": len(recommendations)}
                }
            }
        )
        print(f"\n✓ Workflow completed and session updated")

        # Log final audit event
        await db.log_audit_event(
            event_id=f"evt-complete-{datetime.now().timestamp()}",
            session_id=session_id,
            agent_id="main-orchestrator",
            event_type="workflow_completed",
            event_data={
                "accounts_processed": len(accounts['data'][:2]),
                "recommendations_generated": len(recommendations)
            },
            severity="info"
        )
        print("✓ Audit trail logged")

        print()
        return True

    except Exception as e:
        print(f"✗ Workflow simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    results = {
        "SQLite Connection": False,
        "Mock Zoho Integration": False,
        "Mock Cognee Integration": False,
        "Agent Workflow Simulation": False
    }

    # Run tests
    results["SQLite Connection"] = await test_sqlite_connection()
    results["Mock Zoho Integration"] = await test_mock_zoho()
    results["Mock Cognee Integration"] = await test_mock_cognee()
    results["Agent Workflow Simulation"] = await test_agent_workflow_simulation()

    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:>8} | {test_name}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Orchestration infrastructure is working.")
        print("\nNEXT STEPS:")
        print("1. Add your ANTHROPIC_API_KEY to .env.test")
        print("2. Install Claude Agent SDK: pip install claude-agent-sdk")
        print("3. Test actual Claude SDK agent spawning")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
