"""
LangGraph Wrapper for RecommendationAuthor Agent

This module wraps the existing RecommendationAuthor (Claude Agent SDK) with
LangGraph to make it compatible with CopilotKit's agent interface.

Integration Pattern:
1. Existing RecommendationAuthor -> LangGraph Node -> CopilotKit
2. Maintains all existing functionality (recommendation generation)
3. Adds CopilotKit streaming and state management
4. Implements HITL approval workflow for recommendations
5. Outputs formatted recommendations for final delivery

Key Capabilities:
- Generate engagement recommendations (follow-ups, EBRs)
- Generate expansion recommendations (upsell, cross-sell)
- Generate retention recommendations (renewal, churn prevention)
- Generate risk mitigation recommendations (health recovery)
- Calculate confidence scores for recommendations
- HITL approval integration for high-priority actions
- Template-based recommendation formatting
"""

from typing import TypedDict, Annotated, Dict, Any, List, Optional
from typing_extensions import NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import structlog
from datetime import datetime

# Import existing Sergas agents and services
from src.agents.recommendation_author import RecommendationAuthor

logger = structlog.get_logger(__name__)


# ============================================================================
# LangGraph State Definition
# ============================================================================

class RecommendationAuthorState(TypedDict):
    """
    State managed by LangGraph for recommendation generation workflow.

    This state is shared across all nodes in the graph and persists
    throughout the recommendation generation process.

    Attributes:
        messages: Conversation history (managed by LangGraph)
        account_id: Account being analyzed
        session_id: Unique session identifier
        account_data: Account metrics and information from ZohoDataScout
        historical_context: Historical insights from MemoryAnalyst
        recommendations: Generated recommendations list
        approval_status: Approval workflow status
        approved_recommendations: Recommendations approved by user
        rejected_recommendations: Recommendations rejected by user
        confidence_scores: Confidence scores per recommendation
        workflow_status: Current workflow status
        error: Error information if generation fails
        event_stream: AG UI Protocol events for streaming
    """

    # Conversation history - automatically managed by LangGraph
    messages: Annotated[List[BaseMessage], add_messages]

    # Input parameters
    account_id: NotRequired[str]
    session_id: NotRequired[str]
    account_data: NotRequired[Dict[str, Any]]
    historical_context: NotRequired[Dict[str, Any]]

    # Recommendation outputs
    recommendations: NotRequired[List[Dict[str, Any]]]
    approved_recommendations: NotRequired[List[Dict[str, Any]]]
    rejected_recommendations: NotRequired[List[Dict[str, Any]]]
    confidence_scores: NotRequired[Dict[str, float]]

    # Workflow tracking
    approval_status: NotRequired[str]
    workflow_status: NotRequired[str]
    error: NotRequired[str]

    # Event streaming for CopilotKit
    event_stream: NotRequired[List[Dict[str, Any]]]


# ============================================================================
# LangGraph Nodes (Agent Wrappers)
# ============================================================================

async def recommendation_author_node(state: RecommendationAuthorState) -> RecommendationAuthorState:
    """
    Main recommendation author node that generates actionable recommendations.

    This wraps the existing RecommendationAuthor and makes it compatible with
    LangGraph's state management.

    Args:
        state: Current LangGraph state

    Returns:
        Updated state with generated recommendations

    Flow:
        1. Extract account_data and historical_context from state
        2. Initialize RecommendationAuthor
        3. Execute recommendation generation via execute_with_events()
        4. Collect AG UI Protocol events for streaming
        5. Update state with recommendations
        6. Add AI message with summary

    Non-invasive Approach:
        - Calls existing RecommendationAuthor.execute_with_events()
        - No modifications to original agent logic
        - Simply wraps with LangGraph state management
    """

    logger.info(
        "recommendation_author_node_executing",
        session_id=state.get("session_id"),
        account_id=state.get("account_id")
    )

    try:
        # Extract input data
        account_data = state.get("account_data")
        historical_context = state.get("historical_context")
        session_id = state.get("session_id", f"rec_session_{datetime.utcnow().timestamp()}")

        if not account_data:
            raise ValueError("account_data is required for recommendation generation")

        # Create RecommendationAuthor instance
        recommendation_author = RecommendationAuthor()

        # Build execution context
        execution_context = {
            "account_data": account_data,
            "historical_insights": _extract_historical_insights(historical_context),
            "session_id": session_id
        }

        # Collect results from streaming execution
        recommendations = []
        event_stream = []

        # Execute with AG UI Protocol event streaming
        async for event in recommendation_author.execute_with_events(execution_context):
            event_type = event.get("event")

            # Store event for CopilotKit streaming
            event_stream.append(event)

            # Capture final recommendations
            if event_type == "agent_completed":
                recommendations = event.get("data", {}).get("output", {}).get("recommendations", [])

        if not recommendations:
            logger.warning(
                "no_recommendations_generated",
                account_id=account_data.get("account_id")
            )

        # Calculate confidence scores
        confidence_scores = _calculate_confidence_scores(recommendations)

        # Create summary message
        summary_parts = [
            f"Recommendation Generation Complete:",
            f"- {len(recommendations)} recommendations generated",
            ""
        ]

        # Group by category
        categories = {}
        for rec in recommendations:
            category = rec.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(rec)

        # Add category summaries
        if categories:
            summary_parts.append("Recommendations by Category:")
            for category, recs in categories.items():
                summary_parts.append(f"  • {category}: {len(recs)} recommendation(s)")

        # Add high-priority recommendations
        high_priority = [
            r for r in recommendations
            if r.get("priority") in ["high", "critical"]
        ]
        if high_priority:
            summary_parts.append("")
            summary_parts.append(f"⚠️ {len(high_priority)} high-priority recommendations require attention")

        summary_message = "\n".join(summary_parts)

        # Update state with results
        updated_state = {
            **state,
            "recommendations": recommendations,
            "confidence_scores": confidence_scores,
            "workflow_status": "recommendations_generated",
            "event_stream": event_stream,
            "messages": state["messages"] + [
                AIMessage(content=summary_message)
            ]
        }

        logger.info(
            "recommendation_author_node_completed",
            account_id=account_data.get("account_id"),
            recommendations_count=len(recommendations),
            high_priority_count=len(high_priority)
        )

        return updated_state

    except Exception as e:
        logger.error(
            "recommendation_author_node_failed",
            error=str(e),
            account_id=state.get("account_id")
        )

        # Update state with error
        return {
            **state,
            "workflow_status": "error",
            "error": str(e),
            "messages": state["messages"] + [
                AIMessage(
                    content=f"Error during recommendation generation: {str(e)}\n\n"
                            "Please verify:\n"
                            "- Account data is available\n"
                            "- Historical context has been retrieved"
                )
            ]
        }


async def format_recommendations_node(state: RecommendationAuthorState) -> RecommendationAuthorState:
    """
    Format recommendations for final delivery.

    This node enhances recommendations with:
    - User-friendly formatting
    - Actionable next steps
    - Priority indicators
    - Confidence score visualization

    Args:
        state: Current state with raw recommendations

    Returns:
        Updated state with formatted recommendations
    """

    logger.info(
        "format_recommendations_node_executing",
        recommendations_count=len(state.get("recommendations", []))
    )

    try:
        recommendations = state.get("recommendations", [])

        if not recommendations:
            return {
                **state,
                "messages": state["messages"] + [
                    AIMessage(content="No recommendations to format.")
                ]
            }

        # Format each recommendation
        formatted_recommendations = []
        for rec in recommendations:
            formatted = _format_single_recommendation(rec)
            formatted_recommendations.append(formatted)

        # Create formatted summary
        summary = _create_formatted_summary(formatted_recommendations)

        # Update state
        updated_state = {
            **state,
            "recommendations": formatted_recommendations,
            "workflow_status": "recommendations_formatted",
            "messages": state["messages"] + [
                AIMessage(content=summary)
            ]
        }

        logger.info("format_recommendations_node_completed")

        return updated_state

    except Exception as e:
        logger.error(
            "format_recommendations_node_failed",
            error=str(e)
        )

        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content=f"Error formatting recommendations: {str(e)}")
            ]
        }


async def approval_node(state: RecommendationAuthorState) -> RecommendationAuthorState:
    """
    Handle approval workflow for high-priority recommendations.

    This node manages the HITL approval process for recommendations that
    require user confirmation before execution.

    Args:
        state: Current state with recommendations

    Returns:
        Updated state with approval status

    HITL Integration:
        - Interrupts workflow at approval point
        - Waits for user input via CopilotKit UI
        - Resumes workflow after approval/rejection
        - Tracks approved vs rejected recommendations

    Non-invasive Approach:
        - Uses LangGraph interruption mechanism
        - No modifications to RecommendationAuthor
        - Simply adds approval checkpoint
    """

    logger.info(
        "approval_node_executing",
        recommendations_count=len(state.get("recommendations", []))
    )

    recommendations = state.get("recommendations", [])

    if not recommendations:
        return {
            **state,
            "approval_status": "no_recommendations",
            "messages": state["messages"] + [
                AIMessage(content="No recommendations require approval.")
            ]
        }

    # Filter high-priority recommendations
    high_priority_recs = [
        rec for rec in recommendations
        if rec.get("priority") in ["high", "critical"]
    ]

    # Format recommendations for user review
    approval_message = _format_approval_request(high_priority_recs)

    # In CopilotKit, approval is handled via:
    # 1. useCopilotAction hook in frontend
    # 2. Manual user input
    # 3. Graph interruption and resume

    # For now, mark as pending - frontend will handle approval UI
    return {
        **state,
        "approval_status": "pending_approval",
        "workflow_status": "awaiting_approval",
        "messages": state["messages"] + [
            AIMessage(content=approval_message)
        ]
    }


def should_request_approval(state: RecommendationAuthorState) -> str:
    """
    Conditional edge function to determine if approval is needed.

    Args:
        state: Current state

    Returns:
        Next node name: "approval" or "end"

    Logic:
        - If high-priority or critical recommendations exist -> "approval"
        - If high-confidence recommendations (>= 0.8) exist -> "approval"
        - Otherwise -> "end"

    High Priority Criteria:
        - Priority is "high" or "critical"
        - Confidence score >= 0.8
        - Category is risk_mitigation or retention
    """

    recommendations = state.get("recommendations", [])
    confidence_scores = state.get("confidence_scores", {})

    if not recommendations:
        return "end"

    # Check for high-priority recommendations
    high_priority = any(
        rec.get("priority") in ["high", "critical"]
        for rec in recommendations
    )

    # Check for high-confidence recommendations
    high_confidence = any(
        confidence_scores.get(rec.get("recommendation_id", ""), 0) >= 0.8
        for rec in recommendations
    )

    # Check for critical categories
    critical_categories = any(
        rec.get("category") in ["risk_mitigation", "retention"]
        for rec in recommendations
    )

    if high_priority or high_confidence or critical_categories:
        logger.info(
            "approval_required",
            recommendations_count=len(recommendations),
            high_priority=high_priority,
            high_confidence=high_confidence,
            critical_categories=critical_categories
        )
        return "approval"
    else:
        logger.info(
            "approval_skipped",
            recommendations_count=len(recommendations),
            reason="no_high_priority_recommendations"
        )
        return "end"


# ============================================================================
# LangGraph Graph Construction
# ============================================================================

def create_recommendation_author_graph() -> StateGraph:
    """
    Create the LangGraph graph for the recommendation author workflow.

    This builds the complete workflow graph that CopilotKit will execute:

    Flow:
        START -> recommendation_author_node -> format_recommendations_node
                                            -> conditional_edge
                                            -> approval_node -> END
                                            -> END

    Returns:
        Compiled LangGraph StateGraph ready for CopilotKit

    Example:
        >>> graph = create_recommendation_author_graph()
        >>> # Register with CopilotKit
        >>> copilot_kit.add_agent("recommendation_author", graph)

    Graph Structure:
        1. Entry Point: recommendation_author_node (generate recommendations)
        2. Processing: format_recommendations_node (format for delivery)
        3. Conditional Branch: should_request_approval
           - If approval needed -> approval_node -> END
           - Otherwise -> END
        4. Exit Point: END

    HITL Integration:
        - Recommendation node: Generate recommendations
        - Format node: Prepare for delivery
        - Conditional edge: Approval decision point
        - Approval node: HITL interruption point (waits for user input)
    """

    logger.info("creating_recommendation_author_graph")

    # Initialize graph with state schema
    workflow = StateGraph(RecommendationAuthorState)

    # Add nodes
    workflow.add_node("recommendation_author", recommendation_author_node)
    workflow.add_node("format_recommendations", format_recommendations_node)
    workflow.add_node("approval", approval_node)

    # Set entry point
    workflow.set_entry_point("recommendation_author")

    # Add edge from recommendation_author to format_recommendations
    workflow.add_edge("recommendation_author", "format_recommendations")

    # Add conditional edge after format_recommendations
    workflow.add_conditional_edges(
        "format_recommendations",
        should_request_approval,
        {
            "approval": "approval",
            "end": END
        }
    )

    # Add edge from approval to end
    workflow.add_edge("approval", END)

    # Compile graph with interruption at approval node for HITL
    compiled_graph = workflow.compile(
        interrupt_before=["approval"]
    )

    logger.info("recommendation_author_graph_created")

    return compiled_graph


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_historical_insights(historical_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract historical insights from MemoryAnalyst context.

    Args:
        historical_context: Historical context from MemoryAnalyst

    Returns:
        List of insight dictionaries
    """
    if not historical_context:
        return []

    # Extract patterns as insights
    patterns = historical_context.get("patterns", [])

    insights = []
    for pattern in patterns:
        insights.append({
            "pattern_type": pattern.get("pattern_type"),
            "insight": pattern.get("description"),
            "confidence_score": int(pattern.get("confidence", 0) * 100),
            "occurrence_count": 1,  # Placeholder - would come from Cognee
            "risk_score": pattern.get("risk_score", 0)
        })

    return insights


def _calculate_confidence_scores(recommendations: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate confidence scores for recommendations.

    Args:
        recommendations: List of recommendations

    Returns:
        Dictionary mapping recommendation_id to confidence score
    """
    scores = {}

    for rec in recommendations:
        rec_id = rec.get("recommendation_id")
        if not rec_id:
            continue

        # Use existing confidence_score from RecommendationAuthor
        confidence = rec.get("confidence_score", 50)

        # Convert to 0-1 scale
        normalized_score = confidence / 100.0

        scores[rec_id] = normalized_score

    return scores


def _format_single_recommendation(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a single recommendation for delivery.

    Args:
        rec: Raw recommendation dictionary

    Returns:
        Formatted recommendation
    """
    # Keep all original fields
    formatted = rec.copy()

    # Add priority indicator
    priority = rec.get("priority", "medium")
    priority_indicators = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }
    formatted["priority_indicator"] = priority_indicators.get(priority, "⚪")

    # Add confidence visualization
    confidence = rec.get("confidence_score", 50)
    confidence_bars = "█" * (confidence // 20)
    formatted["confidence_visual"] = f"{confidence_bars} ({confidence}%)"

    # Ensure next_steps is present
    if "next_steps" not in formatted:
        formatted["next_steps"] = ["Review recommendation details"]

    return formatted


def _create_formatted_summary(recommendations: List[Dict[str, Any]]) -> str:
    """
    Create formatted summary of all recommendations.

    Args:
        recommendations: List of formatted recommendations

    Returns:
        Formatted summary string
    """
    summary_parts = [
        "📋 Formatted Recommendations",
        "=" * 60,
        ""
    ]

    # Group by priority
    by_priority = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    for rec in recommendations:
        priority = rec.get("priority", "medium")
        by_priority[priority].append(rec)

    # Add recommendations by priority
    for priority in ["critical", "high", "medium", "low"]:
        recs = by_priority[priority]
        if not recs:
            continue

        summary_parts.append(f"\n{priority.upper()} Priority ({len(recs)}):")
        for rec in recs:
            summary_parts.append(
                f"{rec['priority_indicator']} {rec.get('title', 'Untitled')} "
                f"[{rec.get('confidence_visual', 'N/A')}]"
            )

    return "\n".join(summary_parts)


def _format_approval_request(recommendations: List[Dict[str, Any]]) -> str:
    """
    Format approval request for high-priority recommendations.

    Args:
        recommendations: List of high-priority recommendations

    Returns:
        Formatted approval request message
    """
    if not recommendations:
        return "No high-priority recommendations require approval."

    message_parts = [
        "🔔 Approval Required",
        "=" * 60,
        "",
        f"The following {len(recommendations)} recommendation(s) require your approval:",
        ""
    ]

    for i, rec in enumerate(recommendations, 1):
        message_parts.append(f"{i}. {rec.get('title', 'Untitled')}")
        message_parts.append(f"   Priority: {rec.get('priority_indicator', '')} {rec.get('priority', 'unknown')}")
        message_parts.append(f"   Confidence: {rec.get('confidence_visual', 'N/A')}")
        message_parts.append(f"   Category: {rec.get('category', 'unknown')}")
        message_parts.append(f"   Rationale: {rec.get('rationale', 'N/A')[:100]}...")
        message_parts.append("")

    message_parts.append("Please review and approve or reject each recommendation.")

    return "\n".join(message_parts)


# ============================================================================
# Testing and Validation
# ============================================================================

# Example: Testing the graph locally
if __name__ == "__main__":
    import asyncio

    async def test_recommendation_author_graph():
        """Test the recommendation author graph locally."""

        print("Creating recommendation author graph...")
        graph = create_recommendation_author_graph()

        # Mock account data
        account_data = {
            "account_id": "ACC-001",
            "health_score": 45,
            "annual_revenue": 75000,
            "last_activity_date": "2024-09-01T00:00:00Z",
            "contract_end_date": "2025-12-31T00:00:00Z"
        }

        # Mock historical context
        historical_context = {
            "patterns": [
                {
                    "pattern_type": "churn_risk",
                    "description": "Declining engagement over last 3 months",
                    "confidence": 0.85,
                    "risk_score": 75
                }
            ]
        }

        # Initial state
        initial_state = RecommendationAuthorState(
            messages=[
                HumanMessage(content="Generate recommendations for ACC-001")
            ],
            account_id="ACC-001",
            session_id="test_session",
            account_data=account_data,
            historical_context=historical_context
        )

        print("\nExecuting graph...")
        result = await graph.ainvoke(initial_state)

        print("\n" + "="*60)
        print("Graph execution completed:")
        print("="*60)
        print(f"Account ID: {result.get('account_id')}")
        print(f"Status: {result.get('workflow_status')}")
        print(f"Recommendations: {len(result.get('recommendations', []))}")
        print(f"Approval Status: {result.get('approval_status')}")

        # Print recommendations
        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\nGenerated Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec.get('title')} (priority: {rec.get('priority')})")

        # Print last message
        if result.get('messages'):
            print("\nLast message:")
            print(result['messages'][-1].content)

    # Run test
    print("Testing RecommendationAuthor LangGraph Wrapper")
    print("="*60)
    asyncio.run(test_recommendation_author_graph())
