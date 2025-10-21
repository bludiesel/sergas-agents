"""Test suite for OrchestratorAgent Phase 1 Transformation.

Tests the dual-mode operation:
1. Account Analysis Mode - when account_id provided or account intent detected
2. General Conversation Mode - when no account_id and general intent detected

This test verifies that the orchestrator can handle both specialized account
analysis workflows and general conversation without requiring account_id.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agents.orchestrator import OrchestratorAgent
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.events.approval_manager import ApprovalManager
from src.events.ag_ui_emitter import AGUIEventEmitter


class TestOrchestratorTransformation:
    """Test OrchestratorAgent dual-mode transformation."""

    @pytest.fixture
    def mock_zoho_scout(self):
        """Create mock ZohoDataScout."""
        scout = AsyncMock(spec=ZohoDataScout)
        return scout

    @pytest.fixture
    def mock_memory_analyst(self):
        """Create mock MemoryAnalyst."""
        analyst = AsyncMock(spec=MemoryAnalyst)
        return analyst

    @pytest.fixture
    def mock_approval_manager(self):
        """Create mock ApprovalManager."""
        manager = AsyncMock(spec=ApprovalManager)

        # Mock approval request
        mock_approval_request = AsyncMock()
        mock_approval_request.approval_id = "test_approval_123"
        mock_approval_request.status.value = "approved"
        mock_approval_request.approved_by = "test_user"
        mock_approval_request.wait_for_response.return_value = True
        mock_approval_request.to_dict.return_value = {
            "approval_id": "test_approval_123",
            "status": "approved",
            "approved_by": "test_user"
        }

        manager.create_approval_request.return_value = mock_approval_request
        return manager

    @pytest.fixture
    def orchestrator(self, mock_zoho_scout, mock_memory_analyst, mock_approval_manager):
        """Create OrchestratorAgent instance for testing."""
        return OrchestratorAgent(
            session_id="test_session_123",
            zoho_scout=mock_zoho_scout,
            memory_analyst=mock_memory_analyst,
            approval_manager=mock_approval_manager,
            recommendation_author=None
        )

    @pytest.mark.asyncio
    async def test_general_conversation_mode(self, orchestrator):
        """Test general conversation mode without account_id."""

        # Mock Claude SDK for general conversation
        with patch('src.agents.orchestrator.ClaudeSDKClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock response chunks
            mock_client.query.side_effect = [
                {"type": "text", "content": "Hello! I'm here to help"},
                {"type": "text", "content": " you with customer retention strategies."}
            ]

            # Test general conversation context
            context = {
                "message": "How can I improve customer retention?",
                "workflow": "general_conversation"
            }

            # Collect events
            events = []
            async for event in orchestrator.execute_with_events(context):
                events.append(event)

            # Verify workflow started
            workflow_started_events = [e for e in events if e.get("event") == "workflow_started"]
            assert len(workflow_started_events) == 1
            assert workflow_started_events[0]["data"]["workflow"] == "general_conversation"

            # Verify agent started
            agent_started_events = [e for e in events if e.get("event") == "agent_started"]
            assert len(agent_started_events) == 1
            assert agent_started_events[0]["data"]["agent"] == "orchestrator"

            # Verify streaming content
            stream_events = [e for e in events if e.get("event") == "agent_stream"]
            assert len(stream_events) >= 2  # At least thinking + response

            # Verify workflow completed
            workflow_completed_events = [e for e in events if e.get("event") == "workflow_completed"]
            assert len(workflow_completed_events) == 1
            assert workflow_completed_events[0]["data"]["final_output"]["mode"] == "general_conversation"

    @pytest.mark.asyncio
    async def test_account_analysis_mode_with_account_id(self, orchestrator, mock_zoho_scout, mock_memory_analyst):
        """Test account analysis mode when account_id is provided."""

        # Mock account snapshot
        mock_account_snapshot = MagicMock()
        mock_account_snapshot.snapshot_id = "test_snapshot_123"
        mock_account_snapshot.account.account_name = "Test Customer"
        mock_account_snapshot.account.model_dump.return_value = {"name": "Test Customer"}
        mock_account_snapshot.aggregated_data.model_dump.return_value = {"revenue": 100000}
        mock_account_snapshot.changes.model_dump.return_value = {"changes": []}
        mock_account_snapshot.risk_signals = []
        mock_account_snapshot.risk_level.value = "low"
        mock_account_snapshot.priority_score = 0.3
        mock_account_snapshot.needs_review = False

        mock_zoho_scout.get_account_snapshot.return_value = mock_account_snapshot

        # Mock historical context
        mock_historical_context = MagicMock()
        mock_historical_context.timeline = []
        mock_historical_context.patterns = []
        mock_historical_context.sentiment_trend.value = "stable"
        mock_historical_context.relationship_strength.value = "strong"
        mock_historical_context.risk_level.value = "low"
        mock_historical_context.model_dump.return_value = {"sentiment": "stable"}

        mock_memory_analyst.get_historical_context.return_value = mock_historical_context

        # Test account analysis context
        context = {
            "account_id": "ACC-123",
            "message": "Analyze this customer account",
            "workflow": "account_analysis",
            "timeout_seconds": 300
        }

        # Collect events
        events = []
        async for event in orchestrator.execute_with_events(context):
            events.append(event)

        # Verify workflow started
        workflow_started_events = [e for e in events if e.get("event") == "workflow_started"]
        assert len(workflow_started_events) == 1
        assert workflow_started_events[0]["data"]["workflow"] == "account_analysis"

        # Verify ZohoDataScout was called
        mock_zoho_scout.get_account_snapshot.assert_called_once_with("ACC-123")

        # Verify MemoryAnalyst was called
        mock_memory_analyst.get_historical_context.assert_called_once_with(
            account_id="ACC-123",
            lookback_days=365,
            include_patterns=True
        )

        # Verify agent started events for specialist agents
        agent_started_events = [e for e in events if e.get("event") == "agent_started"]
        assert len(agent_started_events) >= 2  # At least zoho_scout and memory_analyst

        # Verify workflow completed
        workflow_completed_events = [e for e in events if e.get("event") == "workflow_completed"]
        assert len(workflow_completed_events) == 1
        final_output = workflow_completed_events[0]["data"]["final_output"]
        assert final_output["account_id"] == "ACC-123"
        assert final_output["workflow"] == "account_analysis"

    @pytest.mark.asyncio
    async def test_account_analysis_guidance_when_no_account_id(self, orchestrator):
        """Test guidance when account analysis intent detected but no account_id provided."""

        # Test context with account-related message but no account_id
        context = {
            "message": "I want to analyze account risks and health metrics",
            "workflow": "account_analysis"
        }

        # Collect events
        events = []
        async for event in orchestrator.execute_with_events(context):
            events.append(event)

        # Verify guidance workflow
        workflow_started_events = [e for e in events if e.get("event") == "workflow_started"]
        assert len(workflow_started_events) == 1
        assert workflow_started_events[0]["data"]["workflow"] == "account_analysis_guidance"

        # Verify helpful guidance message
        stream_events = [e for e in events if e.get("event") == "agent_stream"]
        guidance_messages = [e["data"]["content"] for e in stream_events]
        assert any("provide an account ID" in msg for msg in guidance_messages)

        # Verify workflow completed with guidance
        workflow_completed_events = [e for e in events if e.get("event") == "workflow_completed"]
        assert len(workflow_completed_events) == 1
        final_output = workflow_completed_events[0]["data"]["final_output"]
        assert final_output["status"] == "guidance_provided"

    @pytest.mark.asyncio
    async def test_intent_detection_for_account_analysis(self, orchestrator):
        """Test intent detection routing for account analysis."""

        # Mock Claude SDK for general conversation (should not be called)
        with patch('src.agents.orchestrator.ClaudeSDKClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Test account-related message
            context = {
                "message": "Analyze account ACC-456 for risk factors",
                "workflow": "auto"  # Let intent detection decide
            }

            # Collect events
            events = []
            async for event in orchestrator.execute_with_events(context):
                events.append(event)

            # Should NOT route to general conversation (Claude SDK not called)
            mock_client.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_intent_detection_for_general_conversation(self, orchestrator):
        """Test intent detection routing for general conversation."""

        # Mock Claude SDK for general conversation
        with patch('src.agents.orchestrator.ClaudeSDKClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock response
            mock_client.query.side_effect = [
                {"type": "text", "content": "I can help with general questions"}
            ]

            # Test general message
            context = {
                "message": "Hello, how are you today?",
                "workflow": "auto"  # Let intent detection decide
            }

            # Collect events
            events = []
            async for event in orchestrator.execute_with_events(context):
                events.append(event)

            # Should route to general conversation
            mock_client.query.assert_called_once_with("Hello, how are you today?")

            # Verify general conversation workflow
            workflow_completed_events = [e for e in events if e.get("event") == "workflow_completed"]
            assert len(workflow_completed_events) == 1
            final_output = workflow_completed_events[0]["data"]["final_output"]
            assert final_output["mode"] == "general_conversation"

    @pytest.mark.asyncio
    async def test_force_mode_override(self, orchestrator):
        """Test force_mode parameter to override intent detection."""

        # Mock Claude SDK for general conversation
        with patch('src.agents.orchestrator.ClaudeSDKClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock response
            mock_client.query.side_effect = [
                {"type": "text", "content": "Forced general conversation"}
            ]

            # Test account-related message but force general conversation
            context = {
                "message": "Analyze account ACC-789 for risks",
                "force_mode": "general_conversation"
            }

            # Collect events
            events = []
            async for event in orchestrator.execute_with_events(context):
                events.append(event)

            # Should route to general conversation despite account keywords
            mock_client.query.assert_called_once_with("Analyze account ACC-789 for risks")

    @pytest.mark.asyncio
    async def test_backward_compatibility_with_existing_workflows(self, orchestrator, mock_zoho_scout, mock_memory_analyst):
        """Test backward compatibility with existing account analysis workflows."""

        # Mock account snapshot
        mock_account_snapshot = MagicMock()
        mock_account_snapshot.snapshot_id = "legacy_snapshot_123"
        mock_account_snapshot.account.account_name = "Legacy Customer"
        mock_account_snapshot.account.model_dump.return_value = {"name": "Legacy Customer"}
        mock_account_snapshot.aggregated_data.model_dump.return_value = {"revenue": 200000}
        mock_account_snapshot.changes.model_dump.return_value = {"changes": []}
        mock_account_snapshot.risk_signals = []
        mock_account_snapshot.risk_level.value = "medium"
        mock_account_snapshot.priority_score = 0.6
        mock_account_snapshot.needs_review = True

        mock_zoho_scout.get_account_snapshot.return_value = mock_account_snapshot

        # Mock historical context
        mock_historical_context = MagicMock()
        mock_historical_context.timeline = []
        mock_historical_context.patterns = []
        mock_historical_context.sentiment_trend.value = "improving"
        mock_historical_context.relationship_strength.value = "moderate"
        mock_historical_context.risk_level.value = "medium"
        mock_historical_context.model_dump.return_value = {"sentiment": "improving"}

        mock_memory_analyst.get_historical_context.return_value = mock_historical_context

        # Test legacy context format (no message, only account_id)
        context = {
            "account_id": "ACC-999",
            "workflow": "account_analysis",
            "timeout_seconds": 300,
            "owner_id": "owner_456"
        }

        # Collect events
        events = []
        async for event in orchestrator.execute_with_events(context):
            events.append(event)

        # Should work exactly like before
        mock_zoho_scout.get_account_snapshot.assert_called_once_with("ACC-999")
        mock_memory_analyst.get_historical_context.assert_called_once_with(
            account_id="ACC-999",
            lookback_days=365,
            include_patterns=True
        )

        # Verify workflow completed successfully
        workflow_completed_events = [e for e in events if e.get("event") == "workflow_completed"]
        assert len(workflow_completed_events) == 1
        final_output = workflow_completed_events[0]["data"]["final_output"]
        assert final_output["account_id"] == "ACC-999"
        assert final_output["status"] == "completed"

    @pytest.mark.asyncio
    async def test_error_handling_in_general_conversation(self, orchestrator):
        """Test error handling in general conversation mode."""

        # Mock Claude SDK to raise an error
        with patch('src.agents.orchestrator.ClaudeSDKClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.query.side_effect = Exception("Claude SDK error")

            # Test general conversation context
            context = {
                "message": "This will cause an error",
                "workflow": "general_conversation"
            }

            # Collect events
            events = []
            with pytest.raises(Exception):
                async for event in orchestrator.execute_with_events(context):
                    events.append(event)

            # Verify error event was emitted
            error_events = [e for e in events if e.get("event") == "agent_error"]
            assert len(error_events) == 1
            assert error_events[0]["data"]["agent"] == "orchestrator"
            assert "Claude SDK error" in error_events[0]["data"]["error_message"]

    @pytest.mark.asyncio
    async def test_missing_environment_variable(self, orchestrator):
        """Test handling of missing ANTHROPIC_API_KEY."""

        # Mock os.getenv to return None for API key
        with patch('src.agents.orchestrator.os.getenv', return_value=None):
            # Test general conversation context
            context = {
                "message": "Test message",
                "workflow": "general_conversation"
            }

            # Should raise ValueError for missing API key
            events = []
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                async for event in orchestrator.execute_with_events(context):
                    events.append(event)

    @pytest.mark.asyncio
    async def test_intent_detection_engine_integration(self, orchestrator):
        """Test that intent detection engine is properly integrated."""

        # Test the intent engine directly
        message = "Analyze account ACC-123 for performance metrics"
        intent_result = orchestrator.intent_engine.analyze_intent(message)

        # Verify intent detection results
        assert intent_result is not None
        assert intent_result.primary_intent in [
            "account_analysis", "zoho_specific", "memory_history",
            "help_assistance", "general_conversation"
        ]
        assert 0 <= intent_result.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_dual_mode_routing_logic(self, orchestrator):
        """Test the dual-mode routing logic."""

        # Mock Claude SDK
        with patch('src.agents.orchestrator.ClaudeSDKClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Test cases for routing decisions
            test_cases = [
                {
                    "context": {"message": "Hello there", "workflow": "general"},
                    "expected_general": True,
                    "description": "General greeting should route to general conversation"
                },
                {
                    "context": {"account_id": "ACC-123", "workflow": "account_analysis"},
                    "expected_general": False,
                    "description": "Explicit account_id should route to account analysis"
                },
                {
                    "context": {"message": "Analyze account risks", "workflow": "auto"},
                    "expected_general": False,
                    "description": "Account analysis intent should route to account analysis"
                },
                {
                    "context": {"message": "What can you help me with?", "workflow": "auto"},
                    "expected_general": True,
                    "description": "Help request should route to general conversation"
                }
            ]

            for test_case in test_cases:
                with self.subTest(test_case["description"]):
                    # Reset mock
                    mock_client.query.reset_mock()

                    # Execute routing
                    events = []
                    try:
                        async for event in orchestrator.execute_with_events(test_case["context"]):
                            events.append(event)

                        # Check if Claude SDK was called (indicates general conversation)
                        was_general = mock_client.query.called

                        assert was_general == test_case["expected_general"], \
                            f"Failed: {test_case['description']}"

                    except Exception as e:
                        # Account analysis without account_id should complete with guidance
                        if not test_case["expected_general"] and not test_case["context"].get("account_id"):
                            # Should have completed with guidance, not an error
                            workflow_completed = [e for e in events if e.get("event") == "workflow_completed"]
                            assert len(workflow_completed) == 1
                            final_output = workflow_completed[0]["data"]["final_output"]
                            assert final_output["status"] == "guidance_provided"
                        else:
                            raise e

    def test_orchestrator_initialization(self, mock_zoho_scout, mock_memory_analyst, mock_approval_manager):
        """Test orchestrator initialization with dual-mode support."""

        orchestrator = OrchestratorAgent(
            session_id="test_session",
            zoho_scout=mock_zoho_scout,
            memory_analyst=mock_memory_analyst,
            approval_manager=mock_approval_manager,
            system_prompt="Custom test prompt"
        )

        # Verify dual-mode setup
        assert hasattr(orchestrator, 'intent_engine')
        assert hasattr(orchestrator, 'system_prompt')
        assert orchestrator.system_prompt == "Custom test prompt"

        # Verify string representation includes dual mode
        repr_str = repr(orchestrator)
        assert "dual_mode=True" in repr_str

    def test_default_system_prompt(self, mock_zoho_scout, mock_memory_analyst, mock_approval_manager):
        """Test default system prompt generation."""

        orchestrator = OrchestratorAgent(
            session_id="test_session",
            zoho_scout=mock_zoho_scout,
            memory_analyst=mock_memory_analyst,
            approval_manager=mock_approval_manager
        )

        # Should have default system prompt
        assert hasattr(orchestrator, 'system_prompt')
        assert len(orchestrator.system_prompt) > 0
        assert "Sergas Account Management System" in orchestrator.system_prompt


if __name__ == "__main__":
    # Run tests with detailed output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=src.agents.orchestrator",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])