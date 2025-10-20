"""
LangGraph Wrapper for ZohoDataScout Agent

This module wraps the ZohoDataScout agent with LangGraph for CopilotKit integration.
Provides focused account data retrieval from Zoho CRM.

Key Features:
- Single-agent focused on Zoho data
- Streaming account snapshots
- Real-time risk signal detection
- Compatible with CopilotKit's agent interface
"""

from typing import TypedDict, Annotated, List, Dict, Any
from typing_extensions import NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import structlog
import os

from src.agents.zoho_data_scout import ZohoDataScout
from src.integrations.zoho.integration_manager import ZohoIntegrationManager

logger = structlog.get_logger(__name__)


# ============================================================================
# LangGraph State Definition
# ============================================================================

class ZohoScoutState(TypedDict):
    """
    State for ZohoDataScout workflow.

    Attributes:
        messages: Conversation history
        account_id: Account to analyze
        session_id: Session identifier
        account_snapshot: Complete account snapshot from Zoho
        risk_signals: Identified risk signals
        change_summary: Detected changes since last sync
        workflow_status: Current status
        error: Error message if any
    """

    messages: Annotated[List[BaseMessage], add_messages]
    account_id: NotRequired[str]
    session_id: NotRequired[str]
    account_snapshot: NotRequired[Dict[str, Any]]
    risk_signals: NotRequired[List[Dict[str, Any]]]
    change_summary: NotRequired[Dict[str, Any]]
    workflow_status: NotRequired[str]
    error: NotRequired[str]


# ============================================================================
# LangGraph Nodes
# ============================================================================

async def fetch_account_node(state: ZohoScoutState) -> ZohoScoutState:
    """
    Fetch account data from Zoho CRM.

    This node:
    1. Initializes ZohoDataScout
    2. Fetches complete account snapshot
    3. Detects changes since last sync
    4. Identifies risk signals
    5. Updates state with results

    Args:
        state: Current state with account_id

    Returns:
        Updated state with account data
    """

    logger.info(
        "fetch_account_node_executing",
        account_id=state.get("account_id")
    )

    try:
        # Extract account_id
        account_id = state.get("account_id")

        if not account_id:
            # Try to extract from last message
            last_message = state["messages"][-1]
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

            # Simple extraction
            if "ACC-" in user_input:
                account_id = user_input.split("ACC-")[1].split()[0]
                account_id = f"ACC-{account_id}"

        if not account_id:
            raise ValueError(
                "Could not extract account_id. Please provide account ID in format ACC-XXX"
            )

        # Initialize ZohoDataScout
        zoho_manager = ZohoIntegrationManager.from_env()
        scout = ZohoDataScout(zoho_manager=zoho_manager)

        # Fetch account snapshot
        snapshot = await scout.get_account_snapshot(account_id)

        # Format response message
        response_parts = [
            f"Retrieved account: {snapshot.account.account_name}",
            f"Risk level: {snapshot.risk_level.value}",
            f"Priority score: {snapshot.priority_score}",
            f"Detected {len(snapshot.risk_signals)} risk signals",
        ]

        if snapshot.changes.changes_detected:
            response_parts.append(
                f"Found {len(snapshot.changes.field_changes)} field changes since last sync"
            )

        response_message = "\n".join(response_parts)

        # Update state
        updated_state = {
            **state,
            "account_id": account_id,
            "account_snapshot": {
                "snapshot_id": snapshot.snapshot_id,
                "account_name": snapshot.account.account_name,
                "owner_name": snapshot.account.owner_name,
                "status": snapshot.account.status.value,
                "risk_level": snapshot.risk_level.value,
                "priority_score": snapshot.priority_score,
                "needs_review": snapshot.needs_review,
                "deal_count": snapshot.account.deal_count,
                "total_value": float(snapshot.account.total_value),
                "last_activity": snapshot.account.last_activity_date.isoformat() if snapshot.account.last_activity_date else None,
            },
            "risk_signals": [
                {
                    "signal_type": signal.signal_type.value,
                    "severity": signal.severity.value,
                    "description": signal.description,
                    "detected_at": signal.detected_at.isoformat()
                }
                for signal in snapshot.risk_signals
            ],
            "change_summary": {
                "changes_detected": snapshot.changes.changes_detected,
                "field_changes_count": len(snapshot.changes.field_changes),
                "change_types": [ct.value for ct in snapshot.changes.change_types],
                "requires_attention": snapshot.changes.requires_attention
            },
            "workflow_status": "completed",
            "messages": state["messages"] + [
                AIMessage(content=response_message)
            ]
        }

        logger.info(
            "fetch_account_node_completed",
            account_id=account_id,
            risk_level=snapshot.risk_level.value
        )

        return updated_state

    except Exception as e:
        logger.error(
            "fetch_account_node_failed",
            error=str(e),
            account_id=state.get("account_id")
        )

        return {
            **state,
            "workflow_status": "error",
            "error": str(e),
            "messages": state["messages"] + [
                AIMessage(content=f"Error fetching account data: {str(e)}")
            ]
        }


async def analyze_risk_signals_node(state: ZohoScoutState) -> ZohoScoutState:
    """
    Analyze and prioritize risk signals.

    This node provides detailed analysis of detected risk signals:
    - Categorizes by severity
    - Identifies trends
    - Suggests immediate actions

    Args:
        state: State with risk signals

    Returns:
        Updated state with risk analysis
    """

    logger.info(
        "analyze_risk_signals_node_executing",
        risk_signals_count=len(state.get("risk_signals", []))
    )

    risk_signals = state.get("risk_signals", [])

    if not risk_signals:
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="No risk signals detected. Account appears healthy.")
            ]
        }

    # Categorize by severity
    critical = [s for s in risk_signals if s["severity"] == "critical"]
    high = [s for s in risk_signals if s["severity"] == "high"]
    medium = [s for s in risk_signals if s["severity"] == "medium"]

    # Build analysis message
    analysis_parts = ["Risk Signal Analysis:", ""]

    if critical:
        analysis_parts.append(f"🔴 CRITICAL ({len(critical)} signals):")
        for signal in critical:
            analysis_parts.append(f"  - {signal['description']}")
        analysis_parts.append("")

    if high:
        analysis_parts.append(f"🟠 HIGH ({len(high)} signals):")
        for signal in high:
            analysis_parts.append(f"  - {signal['description']}")
        analysis_parts.append("")

    if medium:
        analysis_parts.append(f"🟡 MEDIUM ({len(medium)} signals):")
        for signal in medium:
            analysis_parts.append(f"  - {signal['description']}")

    analysis_message = "\n".join(analysis_parts)

    return {
        **state,
        "messages": state["messages"] + [
            AIMessage(content=analysis_message)
        ]
    }


def should_analyze_risks(state: ZohoScoutState) -> str:
    """
    Conditional edge: Determine if risk analysis is needed.

    Args:
        state: Current state

    Returns:
        Next node: "analyze_risks" or "end"
    """

    risk_signals = state.get("risk_signals", [])
    has_risks = len(risk_signals) > 0

    return "analyze_risks" if has_risks else "end"


# ============================================================================
# LangGraph Graph Construction
# ============================================================================

def create_zoho_scout_graph() -> StateGraph:
    """
    Create LangGraph graph for ZohoDataScout workflow.

    Flow:
        START -> fetch_account -> conditional_edge
                                -> analyze_risks -> END
                                -> END

    Returns:
        Compiled LangGraph StateGraph

    Example:
        >>> graph = create_zoho_scout_graph()
        >>> copilot_kit.add_agent("zoho_scout", graph)
    """

    logger.info("creating_zoho_scout_graph")

    # Initialize graph
    workflow = StateGraph(ZohoScoutState)

    # Add nodes
    workflow.add_node("fetch_account", fetch_account_node)
    workflow.add_node("analyze_risks", analyze_risk_signals_node)

    # Set entry point
    workflow.set_entry_point("fetch_account")

    # Add conditional edge
    workflow.add_conditional_edges(
        "fetch_account",
        should_analyze_risks,
        {
            "analyze_risks": "analyze_risks",
            "end": END
        }
    )

    # Add edge from analysis to end
    workflow.add_edge("analyze_risks", END)

    # Compile
    compiled_graph = workflow.compile()

    logger.info("zoho_scout_graph_created")

    return compiled_graph


# ============================================================================
# Standalone Functions (for direct use)
# ============================================================================

async def fetch_account_data(account_id: str) -> Dict[str, Any]:
    """
    Fetch account data directly without LangGraph.

    This is a utility function for quick account lookups without
    the full LangGraph workflow overhead.

    Args:
        account_id: Account to fetch

    Returns:
        Account data dictionary

    Example:
        >>> data = await fetch_account_data("ACC-001")
        >>> print(data["account_name"])
    """

    logger.info("fetching_account_data_direct", account_id=account_id)

    try:
        zoho_manager = ZohoIntegrationManager.from_env()
        scout = ZohoDataScout(zoho_manager=zoho_manager)

        snapshot = await scout.get_account_snapshot(account_id)

        return {
            "account_id": account_id,
            "account_name": snapshot.account.account_name,
            "owner": snapshot.account.owner_name,
            "risk_level": snapshot.risk_level.value,
            "priority_score": snapshot.priority_score,
            "risk_signals": [
                {
                    "type": s.signal_type.value,
                    "severity": s.severity.value,
                    "description": s.description
                }
                for s in snapshot.risk_signals
            ],
            "changes_detected": snapshot.changes.changes_detected,
            "needs_review": snapshot.needs_review
        }

    except Exception as e:
        logger.error(
            "fetch_account_data_failed",
            account_id=account_id,
            error=str(e)
        )
        raise


# Example: Testing locally
if __name__ == "__main__":
    import asyncio

    async def test_zoho_scout_graph():
        """Test the ZohoDataScout graph locally."""

        # Create graph
        graph = create_zoho_scout_graph()

        # Initial state
        initial_state = ZohoScoutState(
            messages=[
                HumanMessage(content="Fetch account ACC-001")
            ],
            session_id="test_session"
        )

        # Execute
        result = await graph.ainvoke(initial_state)

        print("Graph execution completed:")
        print(f"Account ID: {result.get('account_id')}")
        print(f"Status: {result.get('workflow_status')}")
        print(f"Risk Signals: {len(result.get('risk_signals', []))}")

    # Run test
    asyncio.run(test_zoho_scout_graph())
