"""OrchestratorAgent - Multi-Agent Coordination with AG UI Protocol.

Week 6 Critical Implementation - Orchestrates specialist agents with event streaming.
Phase 1 Transformation: General-Purpose Agent with Intent Detection.

Architecture Alignment:
- SPARC V3 Refinement Phase (Week 8, Days 11-13, lines 822-946)
- Coordinates ZohoDataScout, MemoryAnalyst, RecommendationAuthor
- AG UI Protocol event streaming for UI integration
- Approval workflow integration
- General conversation mode for non-account-specific queries

Dual Mode Operation:
1. Account Analysis Mode: When account_id provided, uses specialist agents
2. General Conversation Mode: When no account_id, provides direct assistance

Specialist Agents (Account Analysis Mode):
1. ZohoDataScout: Fetches and analyzes Zoho CRM data
2. MemoryAnalyst: Retrieves historical context and patterns
3. RecommendationAuthor: Generates actionable recommendations

Intent Detection:
- Analyzes user messages to determine routing
- Account-specific queries -> Specialist agents
- General questions -> Direct conversation mode

Event Flow:
1. RUN_STARTED -> Begin orchestration
2. Intent Detection -> Determine execution path
3. agent_started -> Start each specialist (account mode) OR direct response (general mode)
4. agent_stream -> Stream progress or response
5. agent_completed -> Task finished
6. approval_required -> Request user approval (account mode only)
7. RUN_FINISHED/RUN_ERROR -> Complete orchestration
"""

import asyncio
import uuid
import traceback
import re
from typing import Dict, Any, AsyncGenerator, Optional, List
from datetime import datetime
import structlog

from src.events.ag_ui_emitter import AGUIEventEmitter
from src.events.approval_manager import ApprovalManager
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.agents.base_agent import BaseAgent
from src.agents.intent_detection import IntentDetectionEngine

logger = structlog.get_logger(__name__)


class OrchestratorAgent:
    """Multi-agent orchestrator with AG UI Protocol streaming and dual-mode operation.

    Phase 1 Transformation: Now supports both account analysis and general conversation modes.

    Dual Operation Modes:
    1. Account Analysis Mode (when account_id provided):
       - Coordinates execution of specialist agents in sequence
       - ZohoDataScout - Fetch and analyze Zoho CRM data
       - MemoryAnalyst - Retrieve historical context and patterns
       - RecommendationAuthor - Generate actionable recommendations (Week 7)
       - Emits approval workflows for recommendations

    2. General Conversation Mode (when no account_id):
       - Direct conversation using Claude SDK
       - Intent detection for intelligent routing
       - General assistance and information retrieval
       - No approval workflows required

    Intent Detection:
    - Account-specific keywords: "account", "customer", "client", "ACC-", "analyze", "review"
    - General conversation indicators: questions, help requests, general topics
    - Automatic routing based on message content and context

    Emits AG UI Protocol events for real-time UI updates and approval workflows.

    Examples:
        # Account Analysis Mode
        >>> context = {"account_id": "ACC-001", "message": "Analyze this customer"}
        >>> async for event in orchestrator.execute_with_events(context):
        ...     print(event)  # Stream to UI via SSE

        # General Conversation Mode
        >>> context = {"message": "How can I improve customer retention?"}
        >>> async for event in orchestrator.execute_with_events(context):
        ...     print(event)  # Stream to UI via SSE
    """

    def __init__(
        self,
        session_id: str,
        zoho_scout: ZohoDataScout,
        memory_analyst: MemoryAnalyst,
        approval_manager: ApprovalManager,
        recommendation_author: Optional[Any] = None,
        system_prompt: Optional[str] = None
    ):
        """Initialize orchestrator with specialist agents and general conversation capability.

        Args:
            session_id: Unique session identifier
            zoho_scout: ZohoDataScout agent instance (for account analysis mode)
            memory_analyst: MemoryAnalyst agent instance (for account analysis mode)
            approval_manager: Approval workflow manager (for account analysis mode)
            recommendation_author: RecommendationAuthor (optional, Week 7)
            system_prompt: Custom system prompt for general conversation mode
        """
        self.session_id = session_id
        self.agent_id = "orchestrator"

        # Specialist agents (account analysis mode)
        self.zoho_scout = zoho_scout
        self.memory_analyst = memory_analyst
        self.recommendation_author = recommendation_author

        # Approval manager (account analysis mode)
        self.approval_manager = approval_manager

        # General conversation mode setup
        self.system_prompt = system_prompt or self._get_default_system_prompt()

        # Intent detection engine for intelligent routing
        self.intent_engine = IntentDetectionEngine(confidence_threshold=0.5)

        # Logging
        self.logger = logger.bind(
            component="orchestrator",
            session_id=session_id
        )

        self.logger.info(
            "orchestrator_initialized_dual_mode",
            has_zoho_scout=zoho_scout is not None,
            has_memory_analyst=memory_analyst is not None,
            has_recommendation_author=recommendation_author is not None,
            supports_general_conversation=True
        )

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for general conversation mode.

        Returns:
            Default system prompt for the orchestrator in general conversation mode
        """
        return """You are a helpful AI assistant for the Sergas Account Management System.

Your capabilities include:
1. General conversation and assistance
2. Answering questions about customer relationship management
3. Providing business insights and recommendations
4. Helping with account management best practices
5. Assisting with data analysis and reporting

When users ask about specific accounts or need account analysis, guide them to provide account identifiers so you can use specialized analysis tools.

Be helpful, professional, and concise. Focus on providing actionable insights and clear explanations."""

    def _detect_intent(self, message: str, context: Dict[str, Any]) -> Any:
        """Detect user intent using the comprehensive IntentDetectionEngine.

        Args:
            message: User message to analyze
            context: Additional context for intent detection

        Returns:
            IntentResult from the IntentDetectionEngine
        """
        return self.intent_engine.analyze_intent(message)

    def _get_intent_recommendation(self, intent_type: str, confidence: float) -> str:
        """Get recommendation based on intent analysis.

        Args:
            intent_type: Detected intent type
            confidence: Confidence score (0-1)

        Returns:
            Recommendation string
        """
        if intent_type == "account_analysis":
            return "Proceeding with account analysis using specialist agents."
        elif intent_type == "account_analysis_suggested":
            if confidence > 0.7:
                return "Account analysis detected. Please provide an account ID for detailed analysis."
            else:
                return "Account-related query detected. Would you like to analyze a specific account?"
        else:
            return "Engaging in general conversation mode."

    async def _execute_general_conversation(
        self,
        message: str,
        context: Dict[str, Any],
        emitter: AGUIEventEmitter
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute general conversation mode.

        Args:
            message: User message to respond to
            context: Execution context
            emitter: Event emitter for streaming

        Yields:
            AG UI Protocol events for general conversation
        """
        workflow = "general_conversation"

        # Emit workflow started
        yield emitter.emit_workflow_started(workflow, "general_assistance")

        # Emit agent started
        yield emitter.emit_agent_started(
            agent="orchestrator",
            step=1,
            task="Processing general conversation"
        )

        try:
            # Initialize Anthropic client for general conversation
            from anthropic import Anthropic
            import os

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable must be set for general conversation mode")

            base_url = os.getenv("ANTHROPIC_BASE_URL")
            model = os.getenv("CLAUDE_MODEL", "glm-4.6")

            client = Anthropic(api_key=api_key, base_url=base_url)

            # Emit thinking stream
            yield emitter.emit_agent_stream(
                agent="orchestrator",
                content="Thinking about your question...",
                content_type="text"
            )

            # Get response from Claude/GLM-4.6 - use simple prompt to avoid API issues
            simple_prompt = "You are a helpful AI assistant. Please respond helpfully to the user's message."
            combined_message = f"{simple_prompt}\n\nUser message: {message}"

            response = client.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": combined_message}]
            )

            full_response = response.content[0].text

            # Stream the response
            yield emitter.emit_agent_stream(
                agent="orchestrator",
                content=full_response,
                content_type="text"
            )

            # Emit agent completed
            yield emitter.emit_agent_completed(
                agent="orchestrator",
                step=1,
                output={
                    "status": "success",
                    "message": full_response,
                    "mode": "general_conversation"
                }
            )

            # Emit workflow completed
            final_output = {
                "status": "completed",
                "workflow": workflow,
                "mode": "general_conversation",
                "message": full_response,
                "execution_summary": {
                    "intent_detected": "general_conversation",
                    "response_length": len(full_response),
                    "specialist_agents_used": False
                }
            }

            yield emitter.emit_workflow_completed(
                workflow=workflow,
                account_id="general",
                final_output=final_output
            )

            self.logger.info(
                "general_conversation_completed",
                session_id=self.session_id,
                response_length=len(full_response)
            )

        except Exception as e:
            self.logger.error(
                "general_conversation_failed",
                error=str(e),
                stack_trace=traceback.format_exc()
            )

            yield emitter.emit_agent_error(
                agent="orchestrator",
                step=1,
                error_type="conversation_error",
                error_message=f"Failed to process conversation: {str(e)}",
                stack_trace=traceback.format_exc()
            )

            # Emit workflow error
            error_output = {
                "status": "error",
                "workflow": workflow,
                "mode": "general_conversation",
                "error": str(e),
                "error_type": type(e).__name__
            }

            yield emitter.emit_workflow_completed(
                workflow=workflow,
                account_id="general",
                final_output=error_output
            )

            raise

    async def execute_with_events(
        self,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute orchestration with AG UI Protocol event streaming and dual-mode operation.

        Phase 1 Transformation: Supports both account analysis and general conversation modes.

        Workflow Steps (Intent Detection First):
        1. Extract message and detect user intent
        2. Route to appropriate execution mode:
           - Account Analysis Mode: When account_id provided or account intent detected
           - General Conversation Mode: When no account_id and general intent detected

        Account Analysis Mode Workflow:
        1. Start workflow (emit workflow_started)
        2. Execute ZohoDataScout (fetch account data)
        3. Execute MemoryAnalyst (retrieve historical context)
        4. Execute RecommendationAuthor (generate recommendations) - Week 7
        5. Request approval (emit approval_required)
        6. Handle approval response
        7. Complete workflow (emit workflow_completed)

        General Conversation Mode Workflow:
        1. Start workflow (emit workflow_started)
        2. Process message with Claude SDK
        3. Stream response directly
        4. Complete workflow (emit workflow_completed)

        Args:
            context: Execution context containing:
                - message: User message (optional, used for intent detection)
                - account_id: Account to analyze (optional for account analysis mode)
                - workflow: Workflow type (default: auto-detected)
                - timeout_seconds: Approval timeout (default: 300)
                - owner_id: Account owner for filtering (optional)
                - force_mode: Override intent detection ("account_analysis" or "general_conversation")

        Yields:
            AG UI Protocol events for streaming to frontend

        Examples:
            # Account Analysis Mode
            {
                "account_id": "ACC-001",
                "message": "Analyze this customer",
                "workflow": "account_analysis",
                "timeout_seconds": 300
            }

            # General Conversation Mode
            {
                "message": "How can I improve customer retention?",
                "workflow": "general_conversation"
            }
        """
        # Extract message for intent detection
        message = context.get("message", "")

        # Check for forced mode override
        force_mode = context.get("force_mode")

        # Detect intent unless mode is explicitly forced
        if force_mode:
            intent_result = {
                "primary_intent": force_mode,
                "confidence_score": 1.0,
                "requires_account_data": force_mode == "account_analysis",
                "should_call_zoho_agent": force_mode == "account_analysis",
                "should_call_memory_agent": force_mode == "account_analysis"
            }
        else:
            # Use intent detection engine
            intent_analysis = self.intent_engine.analyze_intent(message)
            intent_result = {
                "primary_intent": intent_analysis.primary_intent,
                "confidence_score": intent_analysis.confidence_score,
                "requires_account_data": intent_analysis.requires_account_data,
                "should_call_zoho_agent": intent_analysis.should_call_zoho_agent,
                "should_call_memory_agent": intent_analysis.should_call_memory_agent
            }

        # Route to appropriate execution mode
        account_id = context.get("account_id")

        # Simple greeting check - bypass intent detection for common greetings
        simple_greetings = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'good morning', 'good afternoon']
        is_simple_greeting = message.lower().strip() in simple_greetings

        # Decision logic for routing
        should_use_account_analysis = (
            not is_simple_greeting and (  # Don't use account analysis for simple greetings
                account_id and  # Must have explicit account_id provided
                self.zoho_scout is not None and  # Must have Zoho agent initialized
                self.memory_analyst is not None and  # Must have Memory agent initialized
                (
                    intent_result["requires_account_data"] or  # Intent requires account data
                    intent_result["should_call_zoho_agent"] or  # Intent calls for Zoho agent
                    intent_result["should_call_memory_agent"]  # Intent calls for Memory agent
                )
            )
        )

        if should_use_account_analysis:
            # Account Analysis Mode - use existing logic but make account_id optional
            async for event in self._execute_account_analysis(context, intent_result):
                yield event
        else:
            # General Conversation Mode
            async for event in self._execute_general_conversation(message, context, AGUIEventEmitter(session_id=self.session_id)):
                yield event

    async def _execute_account_analysis(
        self,
        context: Dict[str, Any],
        intent_result: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute account analysis workflow with specialist agents.

        Args:
            context: Execution context
            intent_result: Intent detection results

        Yields:
            AG UI Protocol events for account analysis workflow
        """
        account_id = context.get("account_id")

        # If no account_id but intent suggests account analysis, emit helpful response
        if not account_id:
            emitter = AGUIEventEmitter(session_id=self.session_id)

            yield emitter.emit_workflow_started("account_analysis_guidance", "guidance")

            yield emitter.emit_agent_started(
                agent="orchestrator",
                step=1,
                task="Providing account analysis guidance"
            )

            guidance_message = "I'd be happy to help with account analysis! To provide detailed insights, please provide an account ID (like ACC-123)."

            yield emitter.emit_agent_stream(
                agent="orchestrator",
                content=guidance_message,
                content_type="text"
            )

            yield emitter.emit_agent_completed(
                agent="orchestrator",
                step=1,
                output={
                    "status": "guidance_provided",
                    "message": guidance_message,
                    "intent_detected": intent_result["primary_intent"],
                    "recommendation": "Provide account_id for detailed analysis"
                }
            )

            yield emitter.emit_workflow_completed(
                workflow="account_analysis_guidance",
                account_id="none_provided",
                final_output={
                    "status": "guidance_provided",
                    "message": guidance_message,
                    "intent_detected": intent_result["primary_intent"],
                    "next_step": "Provide account_id for detailed analysis"
                }
            )
            return

        workflow = context.get("workflow", "account_analysis")
        timeout_seconds = context.get("timeout_seconds", 300)

        emitter = AGUIEventEmitter(session_id=self.session_id)

        self.logger.info(
            "account_analysis_orchestration_started",
            account_id=account_id,
            workflow=workflow,
            intent_detected=intent_result["primary_intent"],
            intent_confidence=intent_result["confidence_score"]
        )

        # Shared execution context (accumulates data between agents)
        execution_context: Dict[str, Any] = {
            "account_id": account_id,
            "workflow": workflow,
            "session_id": self.session_id,
            "start_time": datetime.utcnow(),
            "intent_detection": intent_result
        }

        try:
            # ================================================================
            # Step 1: Workflow Started
            # ================================================================
            yield emitter.emit_workflow_started(workflow, account_id)

            # ================================================================
            # Step 2: ZohoDataScout - Fetch Account Data
            # ================================================================
            yield emitter.emit_agent_started(
                agent="zoho_scout",
                step=1,
                task="Fetching account data from Zoho CRM"
            )

            try:
                # Fetch account snapshot
                account_snapshot = await self.zoho_scout.get_account_snapshot(account_id)

                # Store in execution context
                execution_context["account_data"] = {
                    "snapshot_id": account_snapshot.snapshot_id,
                    "account": account_snapshot.account.model_dump(),
                    "aggregated_data": account_snapshot.aggregated_data.model_dump(),
                    "changes": account_snapshot.changes.model_dump(),
                    "risk_signals": [signal.model_dump() for signal in account_snapshot.risk_signals],
                    "risk_level": account_snapshot.risk_level.value,
                    "priority_score": account_snapshot.priority_score,
                    "needs_review": account_snapshot.needs_review
                }

                # Emit progress stream
                yield emitter.emit_agent_stream(
                    agent="zoho_scout",
                    content=f"Retrieved account snapshot for {account_snapshot.account.account_name}",
                    content_type="text"
                )

                yield emitter.emit_agent_stream(
                    agent="zoho_scout",
                    content=f"Detected {len(account_snapshot.risk_signals)} risk signals",
                    content_type="text"
                )

                yield emitter.emit_agent_completed(
                    agent="zoho_scout",
                    step=1,
                    output={
                        "status": "success",
                        "snapshot_id": account_snapshot.snapshot_id,
                        "risk_level": account_snapshot.risk_level.value,
                        "priority_score": account_snapshot.priority_score
                    }
                )

            except Exception as e:
                self.logger.error(
                    "zoho_scout_failed",
                    account_id=account_id,
                    error=str(e)
                )
                yield emitter.emit_agent_error(
                    agent="zoho_scout",
                    step=1,
                    error_type="data_fetch_error",
                    error_message=f"Failed to fetch account data: {str(e)}",
                    stack_trace=traceback.format_exc()
                )
                raise

            # ================================================================
            # Step 3: MemoryAnalyst - Retrieve Historical Context
            # ================================================================
            yield emitter.emit_agent_started(
                agent="memory_analyst",
                step=2,
                task="Analyzing historical patterns and context"
            )

            try:
                # Get historical context
                historical_context = await self.memory_analyst.get_historical_context(
                    account_id=account_id,
                    lookback_days=365,
                    include_patterns=True
                )

                # Store in execution context
                execution_context["historical_context"] = historical_context.model_dump()

                # Emit progress stream
                yield emitter.emit_agent_stream(
                    agent="memory_analyst",
                    content=f"Analyzed {len(historical_context.timeline)} historical events",
                    content_type="text"
                )

                yield emitter.emit_agent_stream(
                    agent="memory_analyst",
                    content=f"Detected {len(historical_context.patterns)} patterns",
                    content_type="text"
                )

                yield emitter.emit_agent_stream(
                    agent="memory_analyst",
                    content=f"Sentiment trend: {historical_context.sentiment_trend.value}",
                    content_type="text"
                )

                yield emitter.emit_agent_completed(
                    agent="memory_analyst",
                    step=2,
                    output={
                        "status": "success",
                        "patterns_detected": len(historical_context.patterns),
                        "sentiment_trend": historical_context.sentiment_trend.value,
                        "relationship_strength": historical_context.relationship_strength.value,
                        "risk_level": historical_context.risk_level.value
                    }
                )

            except Exception as e:
                self.logger.error(
                    "memory_analyst_failed",
                    account_id=account_id,
                    error=str(e)
                )
                yield emitter.emit_agent_error(
                    agent="memory_analyst",
                    step=2,
                    error_type="memory_retrieval_error",
                    error_message=f"Failed to retrieve historical context: {str(e)}",
                    stack_trace=traceback.format_exc()
                )
                raise

            # ================================================================
            # Step 4: RecommendationAuthor - Generate Recommendations
            # ================================================================
            # TODO: Week 7 implementation
            if self.recommendation_author:
                yield emitter.emit_agent_started(
                    agent="recommendation_author",
                    step=3,
                    task="Generating actionable recommendations"
                )

                # Placeholder for Week 7
                execution_context["recommendations"] = []

                yield emitter.emit_agent_stream(
                    agent="recommendation_author",
                    content="Recommendation generation - Week 7 implementation pending",
                    content_type="text"
                )

                yield emitter.emit_agent_completed(
                    agent="recommendation_author",
                    step=3,
                    output={"status": "pending", "message": "Week 7 implementation"}
                )
            else:
                # Generate basic recommendation structure for approval flow
                execution_context["recommendations"] = [{
                    "recommendation_id": f"rec_{uuid.uuid4().hex[:8]}",
                    "account_id": account_id,
                    "action_type": "review_account",
                    "priority": "high" if execution_context["account_data"]["risk_level"] in ["high", "critical"] else "medium",
                    "recommendation": "Review account based on detected risk signals",
                    "reasoning": f"Risk level: {execution_context['account_data']['risk_level']}",
                    "expected_impact": "Mitigate identified risks"
                }]

            # ================================================================
            # Step 5: Request Approval
            # ================================================================
            recommendations = execution_context.get("recommendations", [])

            if recommendations:
                # Emit approval required event
                approval_data = {
                    "recommendation_id": recommendations[0].get("recommendation_id", f"rec_{uuid.uuid4().hex[:8]}"),
                    "account_id": account_id,
                    "action_type": recommendations[0].get("action_type", "review"),
                    "priority": recommendations[0].get("priority", "medium"),
                    "reasoning": recommendations[0].get("reasoning", ""),
                    "expected_impact": recommendations[0].get("expected_impact", "")
                }

                yield emitter.emit_approval_required(
                    recommendation=approval_data,
                    timeout_hours=int(timeout_seconds / 3600)
                )

                # Create approval request
                approval_request = await self.approval_manager.create_approval_request(
                    recommendation_id=approval_data["recommendation_id"],
                    recommendation=approval_data,
                    run_id=self.session_id,
                    timeout_seconds=timeout_seconds
                )

                self.logger.info(
                    "approval_requested",
                    approval_id=approval_request.approval_id,
                    recommendation_id=approval_data["recommendation_id"]
                )

                # Wait for approval response
                response_received = await approval_request.wait_for_response(timeout=timeout_seconds)

                if response_received:
                    approval_result = approval_request.to_dict()
                    execution_context["approval"] = approval_result

                    if approval_request.status.value == "approved":
                        yield emitter.emit_agent_stream(
                            agent="orchestrator",
                            content=f"Recommendations approved by {approval_request.approved_by or 'user'}",
                            content_type="text"
                        )

                        final_output = {
                            "status": "completed",
                            "account_id": account_id,
                            "workflow": workflow,
                            "approval": approval_result,
                            "recommendations": recommendations,
                            "execution_summary": {
                                "zoho_data_fetched": True,
                                "historical_context_retrieved": True,
                                "recommendations_generated": len(recommendations),
                                "risk_level": execution_context["account_data"]["risk_level"],
                                "sentiment_trend": execution_context["historical_context"]["sentiment_trend"],
                                "intent_detection": intent_result
                            }
                        }
                    else:
                        yield emitter.emit_agent_stream(
                            agent="orchestrator",
                            content=f"Recommendations {approval_request.status.value}: {approval_request.reason or 'No reason provided'}",
                            content_type="text"
                        )

                        final_output = {
                            "status": approval_request.status.value,
                            "account_id": account_id,
                            "workflow": workflow,
                            "approval": approval_result,
                            "message": approval_request.reason or f"Workflow {approval_request.status.value}"
                        }
                else:
                    # Timeout
                    yield emitter.emit_agent_stream(
                        agent="orchestrator",
                        content="Approval request timed out - workflow auto-rejected",
                        content_type="text"
                    )

                    final_output = {
                        "status": "timeout",
                        "account_id": account_id,
                        "workflow": workflow,
                        "message": "Approval request timed out"
                    }
            else:
                # No recommendations - complete without approval
                final_output = {
                    "status": "completed",
                    "account_id": account_id,
                    "workflow": workflow,
                    "message": "No recommendations generated",
                    "execution_summary": {
                        "zoho_data_fetched": True,
                        "historical_context_retrieved": True,
                        "recommendations_generated": 0,
                        "intent_detection": intent_result
                    }
                }

            # ================================================================
            # Step 6: Workflow Completed
            # ================================================================
            execution_context["final_output"] = final_output

            yield emitter.emit_workflow_completed(
                workflow=workflow,
                account_id=account_id,
                final_output=final_output
            )

            self.logger.info(
                "account_analysis_orchestration_completed",
                account_id=account_id,
                workflow=workflow,
                status=final_output.get("status"),
                duration_seconds=(datetime.utcnow() - execution_context["start_time"]).total_seconds()
            )

        except Exception as e:
            # Critical error handling
            self.logger.error(
                "account_analysis_orchestration_failed",
                account_id=account_id,
                workflow=workflow,
                error=str(e),
                stack_trace=traceback.format_exc()
            )

            yield emitter.emit_agent_error(
                agent="orchestrator",
                step=0,
                error_type="orchestration_error",
                error_message=f"Account analysis failed: {str(e)}",
                stack_trace=traceback.format_exc()
            )

            # Emit workflow error as final event
            error_output = {
                "status": "error",
                "account_id": account_id,
                "workflow": workflow,
                "error": str(e),
                "error_type": type(e).__name__,
                "intent_detection": intent_result
            }

            yield emitter.emit_workflow_completed(
                workflow=workflow,
                account_id=account_id,
                final_output=error_output
            )

            raise

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestration without event streaming (legacy interface).

        For compatibility with BaseAgent interface. Use execute_with_events()
        for AG UI Protocol streaming.

        Args:
            context: Execution context

        Returns:
            Final execution output
        """
        final_output = None
        last_error = None

        try:
            async for event in self.execute_with_events(context):
                event_type = event.get("event", "unknown")
                self.logger.info("orchestrator_event_received", event_type=event_type)

                # Capture final output from workflow_completed event
                if event_type == "workflow_completed":
                    final_output = event.get("data", {}).get("final_output")
                    self.logger.info("workflow_completed_found", output=final_output)

                # Check for error events
                elif event_type == "error":
                    last_error = event.get("data", {}).get("error", "Unknown error")
                    self.logger.error("orchestrator_error_event", error=last_error)

        except Exception as e:
            self.logger.error("orchestrator_execute_exception", error=str(e), error_type=type(e).__name__)
            last_error = str(e)

        if not final_output:
            error_msg = last_error or "Orchestration did not complete successfully"
            self.logger.error("orchestrator_no_final_output", error=error_msg)
            raise RuntimeError(error_msg)

        return final_output

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<OrchestratorAgent "
            f"session_id={self.session_id} "
            f"dual_mode=True "
            f"agents=[zoho_scout, memory_analyst, recommendation_author]>"
        )
