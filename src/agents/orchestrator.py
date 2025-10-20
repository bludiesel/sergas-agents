"""OrchestratorAgent - Multi-Agent Coordination with AG UI Protocol.

Week 6 Critical Implementation - Orchestrates specialist agents with event streaming.

Architecture Alignment:
- SPARC V3 Refinement Phase (Week 8, Days 11-13, lines 822-946)
- Coordinates ZohoDataScout, MemoryAnalyst, RecommendationAuthor
- AG UI Protocol event streaming for UI integration
- Approval workflow integration

Specialist Agents:
1. ZohoDataScout: Fetches and analyzes Zoho CRM data
2. MemoryAnalyst: Retrieves historical context and patterns
3. RecommendationAuthor: Generates actionable recommendations

Event Flow:
1. RUN_STARTED -> Begin orchestration
2. agent_started -> Start each specialist
3. agent_stream -> Stream specialist progress
4. agent_completed -> Specialist finished
5. approval_required -> Request user approval
6. RUN_FINISHED/RUN_ERROR -> Complete orchestration
"""

import asyncio
import uuid
import traceback
from typing import Dict, Any, AsyncGenerator, Optional, List
from datetime import datetime
import structlog

from src.events.ag_ui_emitter import AGUIEventEmitter
from src.events.approval_manager import ApprovalManager
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst

logger = structlog.get_logger(__name__)


class OrchestratorAgent:
    """Multi-agent orchestrator with AG UI Protocol streaming.

    Coordinates execution of specialist agents in sequence:
    1. ZohoDataScout - Fetch and analyze Zoho CRM data
    2. MemoryAnalyst - Retrieve historical context and patterns
    3. RecommendationAuthor - Generate actionable recommendations (Week 7)

    Emits AG UI Protocol events for real-time UI updates and approval workflows.

    Example:
        >>> orchestrator = OrchestratorAgent(
        ...     session_id="session_123",
        ...     zoho_scout=zoho_scout,
        ...     memory_analyst=memory_analyst,
        ...     approval_manager=approval_manager
        ... )
        >>> async for event in orchestrator.execute_with_events(context):
        ...     print(event)  # Stream to UI via SSE
    """

    def __init__(
        self,
        session_id: str,
        zoho_scout: ZohoDataScout,
        memory_analyst: MemoryAnalyst,
        approval_manager: ApprovalManager,
        recommendation_author: Optional[Any] = None
    ):
        """Initialize orchestrator with specialist agents.

        Args:
            session_id: Unique session identifier
            zoho_scout: ZohoDataScout agent instance
            memory_analyst: MemoryAnalyst agent instance
            approval_manager: Approval workflow manager
            recommendation_author: RecommendationAuthor (optional, Week 7)
        """
        self.session_id = session_id
        self.agent_id = "orchestrator"

        # Specialist agents
        self.zoho_scout = zoho_scout
        self.memory_analyst = memory_analyst
        self.recommendation_author = recommendation_author

        # Approval manager
        self.approval_manager = approval_manager

        # Logging
        self.logger = logger.bind(
            component="orchestrator",
            session_id=session_id
        )

        self.logger.info(
            "orchestrator_initialized",
            has_zoho_scout=zoho_scout is not None,
            has_memory_analyst=memory_analyst is not None,
            has_recommendation_author=recommendation_author is not None
        )

    async def execute_with_events(
        self,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute orchestration with AG UI Protocol event streaming.

        Workflow Steps:
        1. Start workflow (emit workflow_started)
        2. Execute ZohoDataScout (fetch account data)
        3. Execute MemoryAnalyst (retrieve historical context)
        4. Execute RecommendationAuthor (generate recommendations) - Week 7
        5. Request approval (emit approval_required)
        6. Handle approval response
        7. Complete workflow (emit workflow_completed)

        Args:
            context: Execution context containing:
                - account_id: Account to analyze (required)
                - workflow: Workflow type (default: "account_analysis")
                - timeout_seconds: Approval timeout (default: 300)
                - owner_id: Account owner for filtering (optional)

        Yields:
            AG UI Protocol events for streaming to frontend

        Example context:
            {
                "account_id": "ACC-001",
                "workflow": "account_analysis",
                "timeout_seconds": 300,
                "owner_id": "owner_123"
            }
        """
        account_id = context.get("account_id")
        if not account_id:
            raise ValueError("account_id is required in context")

        workflow = context.get("workflow", "account_analysis")
        timeout_seconds = context.get("timeout_seconds", 300)

        emitter = AGUIEventEmitter(session_id=self.session_id)

        self.logger.info(
            "orchestration_started",
            account_id=account_id,
            workflow=workflow
        )

        # Shared execution context (accumulates data between agents)
        execution_context: Dict[str, Any] = {
            "account_id": account_id,
            "workflow": workflow,
            "session_id": self.session_id,
            "start_time": datetime.utcnow()
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
                                "sentiment_trend": execution_context["historical_context"]["sentiment_trend"]
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
                        "recommendations_generated": 0
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
                "orchestration_completed",
                account_id=account_id,
                workflow=workflow,
                status=final_output.get("status"),
                duration_seconds=(datetime.utcnow() - execution_context["start_time"]).total_seconds()
            )

        except Exception as e:
            # Critical error handling
            self.logger.error(
                "orchestration_failed",
                account_id=account_id,
                workflow=workflow,
                error=str(e),
                stack_trace=traceback.format_exc()
            )

            yield emitter.emit_agent_error(
                agent="orchestrator",
                step=0,
                error_type="orchestration_error",
                error_message=f"Orchestration failed: {str(e)}",
                stack_trace=traceback.format_exc()
            )

            # Emit workflow error as final event
            error_output = {
                "status": "error",
                "account_id": account_id,
                "workflow": workflow,
                "error": str(e),
                "error_type": type(e).__name__
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

        async for event in self.execute_with_events(context):
            # Capture final output from workflow_completed event
            if event.get("event") == "workflow_completed":
                final_output = event.get("data", {}).get("final_output")

        if not final_output:
            raise RuntimeError("Orchestration did not complete successfully")

        return final_output

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<OrchestratorAgent "
            f"session_id={self.session_id} "
            f"agents=[zoho_scout, memory_analyst, recommendation_author]>"
        )
