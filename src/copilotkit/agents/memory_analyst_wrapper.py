"""
LangGraph Wrapper for MemoryAnalyst Agent

This module wraps the existing MemoryAnalyst (Claude Agent SDK) with
LangGraph to make it compatible with CopilotKit's agent interface.

Integration Pattern:
1. Existing MemoryAnalyst -> LangGraph Node -> CopilotKit
2. Maintains all existing functionality (Cognee integration, pattern recognition)
3. Adds CopilotKit streaming and state management
4. Outputs formatted for next agent (RecommendationAuthor)

Key Capabilities:
- Historical pattern analysis via Cognee knowledge graph
- Sentiment trend detection
- Relationship strength assessment
- Commitment tracking
- Prior recommendation retrieval
- Risk level calculation
"""

from typing import TypedDict, Annotated, Dict, Any, List, Optional
from typing_extensions import NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import structlog
import os
from datetime import datetime

# Import existing Sergas agents and services
from src.agents.memory_analyst import MemoryAnalyst
from src.services.memory_service import MemoryService
from src.integrations.cognee.cognee_client import CogneeClient
from src.agents.memory_models import (
    HistoricalContext,
    SentimentTrend,
    RelationshipStrength,
    RiskLevel,
    Pattern,
    PatternType
)

logger = structlog.get_logger(__name__)


# ============================================================================
# LangGraph State Definition
# ============================================================================

class MemoryAnalystState(TypedDict):
    """
    State managed by LangGraph for memory analysis workflow.

    This state is shared across all nodes in the graph and persists
    throughout the analysis process.

    Attributes:
        messages: Conversation history (managed by LangGraph)
        account_id: Account being analyzed
        session_id: Unique session identifier
        lookback_days: How far back to analyze (default: 365)
        include_patterns: Whether to include pattern detection
        historical_context: Complete historical analysis from MemoryAnalyst
        key_events: Significant events identified
        patterns: Detected patterns (churn risk, upsell, etc.)
        sentiment_analysis: Sentiment trend analysis
        relationship_assessment: Relationship strength assessment
        commitments: Tracked commitments and promises
        risk_level: Calculated risk level
        analysis_metadata: Performance and diagnostic metadata
        workflow_status: Current workflow status
        error: Error information if analysis fails
    """

    # Conversation history - automatically managed by LangGraph
    messages: Annotated[List[BaseMessage], add_messages]

    # Input parameters
    account_id: NotRequired[str]
    session_id: NotRequired[str]
    lookback_days: NotRequired[int]
    include_patterns: NotRequired[bool]

    # Analysis outputs
    historical_context: NotRequired[Dict[str, Any]]
    key_events: NotRequired[List[Dict[str, Any]]]
    patterns: NotRequired[List[Dict[str, Any]]]
    sentiment_analysis: NotRequired[Dict[str, Any]]
    relationship_assessment: NotRequired[Dict[str, Any]]
    commitments: NotRequired[List[Dict[str, Any]]]
    risk_level: NotRequired[str]

    # Metadata
    analysis_metadata: NotRequired[Dict[str, Any]]
    workflow_status: NotRequired[str]
    error: NotRequired[str]


# ============================================================================
# LangGraph Nodes (Agent Wrappers)
# ============================================================================

async def memory_analyst_node(state: MemoryAnalystState) -> MemoryAnalystState:
    """
    Main memory analyst node that performs historical context analysis.

    This wraps the existing MemoryAnalyst and makes it compatible with
    LangGraph's state management.

    Args:
        state: Current LangGraph state

    Returns:
        Updated state with historical analysis results

    Flow:
        1. Extract account_id and parameters from state
        2. Initialize MemoryAnalyst with Cognee integration
        3. Execute comprehensive historical context retrieval
        4. Parse and structure results for downstream agents
        5. Calculate risk level and identify patterns
        6. Update state with all analysis outputs
    """

    logger.info(
        "memory_analyst_node_executing",
        session_id=state.get("session_id"),
        account_id=state.get("account_id")
    )

    try:
        # Extract parameters
        account_id = state.get("account_id")
        if not account_id:
            # Try to extract from messages
            last_message = state["messages"][-1]
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

            # Simple extraction - in production, use better parsing
            if "account" in user_input.lower():
                # Extract account ID (various formats: ACC-001, account 123, etc.)
                import re
                match = re.search(r'ACC-\d+|\baccount[:\s]+(\w+)', user_input, re.IGNORECASE)
                if match:
                    account_id = match.group(0) if match.group(0).startswith('ACC-') else match.group(1)

        if not account_id:
            raise ValueError(
                "Could not extract account_id. Please provide account ID."
            )

        lookback_days = state.get("lookback_days", 365)
        include_patterns = state.get("include_patterns", True)
        session_id = state.get("session_id", "default_session")

        # Initialize dependencies
        memory_service = MemoryService()
        cognee_client = CogneeClient()

        # Create MemoryAnalyst instance
        memory_analyst = MemoryAnalyst(
            memory_service=memory_service,
            cognee_client=cognee_client,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-5-sonnet-20241022"
        )

        # Execute historical context retrieval
        logger.info(
            "retrieving_historical_context",
            account_id=account_id,
            lookback_days=lookback_days
        )

        historical_context: HistoricalContext = await memory_analyst.get_historical_context(
            account_id=account_id,
            lookback_days=lookback_days,
            include_patterns=include_patterns
        )

        # Parse historical context into state-friendly format
        key_events = [
            {
                "event_id": event.event_id,
                "event_date": event.event_date.isoformat(),
                "event_type": event.event_type,
                "title": event.title,
                "description": event.description,
                "impact_level": event.impact_level,
                "stakeholders": event.stakeholders,
                "outcome": event.outcome
            }
            for event in historical_context.key_events
        ]

        patterns = [
            {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type.value,
                "confidence": pattern.confidence,
                "description": pattern.description,
                "evidence": pattern.evidence,
                "risk_score": pattern.risk_score,
                "recommendations": pattern.recommendations
            }
            for pattern in historical_context.patterns
        ]

        commitments = [
            {
                "commitment_id": commitment.commitment_id,
                "commitment_text": commitment.commitment_text,
                "committed_by": commitment.committed_by,
                "committed_to": commitment.committed_to,
                "commitment_date": commitment.commitment_date.isoformat(),
                "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
                "status": commitment.status.value,
                "priority": commitment.priority
            }
            for commitment in historical_context.commitment_tracking
        ]

        # Build sentiment analysis summary
        sentiment_analysis = {
            "trend": historical_context.sentiment_trend.value,
            "risk_indicators": [
                p.description for p in historical_context.patterns
                if p.pattern_type == PatternType.CHURN_RISK
            ]
        }

        # Build relationship assessment summary
        relationship_assessment = {
            "strength": historical_context.relationship_strength.value,
            "engagement_quality": (
                "high" if historical_context.engagement_metrics and
                historical_context.engagement_metrics.quality_score > 0.7
                else "moderate"
            ) if historical_context.engagement_metrics else "unknown"
        }

        # Get performance metrics
        metrics = memory_analyst.get_metrics()

        # Build comprehensive historical context for downstream agents
        context_output = {
            "account_id": account_id,
            "key_events": key_events,
            "sentiment_trend": historical_context.sentiment_trend.value,
            "relationship_strength": historical_context.relationship_strength.value,
            "commitment_tracking": commitments,
            "patterns": patterns,
            "risk_level": historical_context.risk_level.value,
            "analysis_timestamp": historical_context.last_updated.isoformat()
        }

        # Create summary message
        summary_parts = [
            f"Historical Analysis Complete for {account_id}:",
            f"- {len(key_events)} key events identified",
            f"- Sentiment trend: {historical_context.sentiment_trend.value}",
            f"- Relationship strength: {historical_context.relationship_strength.value}",
            f"- Risk level: {historical_context.risk_level.value}",
            f"- {len(patterns)} patterns detected",
            f"- {len(commitments)} commitments tracked"
        ]

        if patterns:
            high_risk_patterns = [p for p in patterns if p["risk_score"] > 50]
            if high_risk_patterns:
                summary_parts.append(
                    f"- ⚠️ {len(high_risk_patterns)} high-risk patterns require attention"
                )

        summary_message = "\n".join(summary_parts)

        # Update state with all results
        updated_state = {
            **state,
            "account_id": account_id,
            "historical_context": context_output,
            "key_events": key_events,
            "patterns": patterns,
            "sentiment_analysis": sentiment_analysis,
            "relationship_assessment": relationship_assessment,
            "commitments": commitments,
            "risk_level": historical_context.risk_level.value,
            "analysis_metadata": {
                "lookback_days": lookback_days,
                "include_patterns": include_patterns,
                "total_analyses": metrics.get("total_analyses", 0),
                "avg_duration_seconds": metrics.get("avg_duration_seconds", 0.0),
                "pattern_detections": metrics.get("pattern_detections", 0)
            },
            "workflow_status": "completed",
            "messages": state["messages"] + [
                AIMessage(content=summary_message)
            ]
        }

        logger.info(
            "memory_analyst_node_completed",
            account_id=account_id,
            risk_level=historical_context.risk_level.value,
            patterns_count=len(patterns)
        )

        return updated_state

    except Exception as e:
        logger.error(
            "memory_analyst_node_failed",
            error=str(e),
            account_id=state.get("account_id")
        )

        # Update state with error
        return {
            **state,
            "workflow_status": "error",
            "error": str(e),
            "messages": state["messages"] + [
                AIMessage(content=f"Error during memory analysis: {str(e)}")
            ]
        }


async def pattern_analysis_node(state: MemoryAnalystState) -> MemoryAnalystState:
    """
    Deep pattern analysis node for complex pattern recognition.

    This node performs advanced pattern analysis when high-risk patterns
    are detected or when detailed pattern investigation is needed.

    Args:
        state: Current state with initial patterns

    Returns:
        Updated state with enhanced pattern insights
    """

    logger.info(
        "pattern_analysis_node_executing",
        patterns_count=len(state.get("patterns", []))
    )

    try:
        patterns = state.get("patterns", [])

        if not patterns:
            return {
                **state,
                "messages": state["messages"] + [
                    AIMessage(content="No patterns detected for deep analysis.")
                ]
            }

        # Categorize patterns
        churn_patterns = [p for p in patterns if p["pattern_type"] == "churn_risk"]
        upsell_patterns = [p for p in patterns if p["pattern_type"] == "upsell_opportunity"]
        renewal_patterns = [p for p in patterns if p["pattern_type"] == "renewal_risk"]

        # Build detailed analysis
        analysis_parts = ["Deep Pattern Analysis:"]

        if churn_patterns:
            analysis_parts.append(
                f"\n🚨 Churn Risk Patterns ({len(churn_patterns)}):"
            )
            for pattern in churn_patterns[:3]:  # Top 3
                analysis_parts.append(
                    f"  - {pattern['description']} "
                    f"(confidence: {pattern['confidence']:.1%}, "
                    f"risk: {pattern['risk_score']}/100)"
                )

        if upsell_patterns:
            analysis_parts.append(
                f"\n💰 Upsell Opportunities ({len(upsell_patterns)}):"
            )
            for pattern in upsell_patterns[:3]:  # Top 3
                analysis_parts.append(
                    f"  - {pattern['description']} "
                    f"(confidence: {pattern['confidence']:.1%})"
                )

        if renewal_patterns:
            analysis_parts.append(
                f"\n📅 Renewal Risk Patterns ({len(renewal_patterns)}):"
            )
            for pattern in renewal_patterns[:3]:  # Top 3
                analysis_parts.append(
                    f"  - {pattern['description']} "
                    f"(confidence: {pattern['confidence']:.1%})"
                )

        pattern_analysis_message = "\n".join(analysis_parts)

        # Enhance state with pattern insights
        updated_state = {
            **state,
            "analysis_metadata": {
                **state.get("analysis_metadata", {}),
                "churn_patterns_count": len(churn_patterns),
                "upsell_patterns_count": len(upsell_patterns),
                "renewal_patterns_count": len(renewal_patterns),
                "deep_analysis_completed": True
            },
            "messages": state["messages"] + [
                AIMessage(content=pattern_analysis_message)
            ]
        }

        logger.info(
            "pattern_analysis_node_completed",
            churn_patterns=len(churn_patterns),
            upsell_patterns=len(upsell_patterns)
        )

        return updated_state

    except Exception as e:
        logger.error(
            "pattern_analysis_node_failed",
            error=str(e)
        )

        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content=f"Error during pattern analysis: {str(e)}")
            ]
        }


def should_analyze_patterns(state: MemoryAnalystState) -> str:
    """
    Conditional edge function to determine if deep pattern analysis is needed.

    Args:
        state: Current state

    Returns:
        Next node name: "pattern_analysis" or "end"
    """

    patterns = state.get("patterns", [])
    risk_level = state.get("risk_level", "low")

    # Perform deep analysis if:
    # 1. High or critical risk level
    # 2. 3+ patterns detected
    # 3. Any high-risk patterns (risk_score > 50)

    high_risk = risk_level in ["high", "critical"]
    many_patterns = len(patterns) >= 3
    high_risk_patterns = any(
        p.get("risk_score", 0) > 50 for p in patterns
    )

    if high_risk or many_patterns or high_risk_patterns:
        return "pattern_analysis"
    else:
        return "end"


# ============================================================================
# LangGraph Graph Construction
# ============================================================================

def create_memory_analyst_graph() -> StateGraph:
    """
    Create the LangGraph graph for the memory analyst workflow.

    This builds the complete workflow graph that CopilotKit will execute:

    Flow:
        START -> memory_analyst_node -> conditional_edge
                                      -> pattern_analysis_node -> END
                                      -> END

    Returns:
        Compiled LangGraph StateGraph ready for CopilotKit

    Example:
        >>> graph = create_memory_analyst_graph()
        >>> # Register with CopilotKit
        >>> copilot_kit.add_agent("memory_analyst", graph)
    """

    logger.info("creating_memory_analyst_graph")

    # Initialize graph with state schema
    workflow = StateGraph(MemoryAnalystState)

    # Add nodes
    workflow.add_node("memory_analyst", memory_analyst_node)
    workflow.add_node("pattern_analysis", pattern_analysis_node)

    # Set entry point
    workflow.set_entry_point("memory_analyst")

    # Add conditional edge after memory_analyst
    workflow.add_conditional_edges(
        "memory_analyst",
        should_analyze_patterns,
        {
            "pattern_analysis": "pattern_analysis",
            "end": END
        }
    )

    # Add edge from pattern_analysis to end
    workflow.add_edge("pattern_analysis", END)

    # Compile graph
    compiled_graph = workflow.compile()

    logger.info("memory_analyst_graph_created")

    return compiled_graph


# ============================================================================
# Helper Functions
# ============================================================================

def initialize_memory_analyst_dependencies() -> Dict[str, Any]:
    """
    Initialize all dependencies required by MemoryAnalyst.

    This function sets up all the components needed:
    - Memory services
    - Cognee client
    - MemoryAnalyst instance

    Returns:
        Dictionary of initialized components

    Example:
        >>> deps = initialize_memory_analyst_dependencies()
        >>> memory_analyst = deps["memory_analyst"]
    """

    logger.info("initializing_memory_analyst_dependencies")

    try:
        # Memory services
        memory_service = MemoryService()
        cognee_client = CogneeClient()

        # MemoryAnalyst
        memory_analyst = MemoryAnalyst(
            memory_service=memory_service,
            cognee_client=cognee_client,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-5-sonnet-20241022"
        )

        dependencies = {
            "memory_service": memory_service,
            "cognee_client": cognee_client,
            "memory_analyst": memory_analyst
        }

        logger.info("memory_analyst_dependencies_initialized")

        return dependencies

    except Exception as e:
        logger.error(
            "memory_analyst_dependencies_initialization_failed",
            error=str(e)
        )
        raise


# ============================================================================
# State Conversion Utilities
# ============================================================================

def convert_historical_context_to_dict(context: HistoricalContext) -> Dict[str, Any]:
    """
    Convert HistoricalContext Pydantic model to dictionary for LangGraph state.

    Args:
        context: HistoricalContext from MemoryAnalyst

    Returns:
        Dictionary representation for state
    """
    return {
        "account_id": context.account_id,
        "key_events": [
            {
                "event_id": event.event_id,
                "event_date": event.event_date.isoformat(),
                "event_type": event.event_type,
                "title": event.title,
                "description": event.description,
                "impact_level": event.impact_level
            }
            for event in context.key_events
        ],
        "sentiment_trend": context.sentiment_trend.value,
        "relationship_strength": context.relationship_strength.value,
        "risk_level": context.risk_level.value,
        "patterns_count": len(context.patterns),
        "commitments_count": len(context.commitment_tracking),
        "last_updated": context.last_updated.isoformat()
    }


# Example: Testing the graph locally
if __name__ == "__main__":
    import asyncio

    async def test_memory_analyst_graph():
        """Test the memory analyst graph locally."""

        # Create graph
        graph = create_memory_analyst_graph()

        # Initial state
        initial_state = MemoryAnalystState(
            messages=[
                HumanMessage(content="Analyze historical patterns for account ACC-001")
            ],
            account_id="ACC-001",
            session_id="test_session",
            lookback_days=365,
            include_patterns=True
        )

        # Execute graph
        result = await graph.ainvoke(initial_state)

        print("Graph execution completed:")
        print(f"Account ID: {result.get('account_id')}")
        print(f"Status: {result.get('workflow_status')}")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"Patterns: {len(result.get('patterns', []))}")
        print(f"Key Events: {len(result.get('key_events', []))}")

    # Run test
    asyncio.run(test_memory_analyst_graph())
