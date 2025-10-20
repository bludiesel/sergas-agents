"""
LangGraph Wrapper for ZohoDataScout Agent

This module wraps the ZohoDataScout agent with LangGraph for CopilotKit integration.
Provides focused account data retrieval from Zoho CRM with state management.

Key Features:
- Single-agent focused on Zoho data
- Streaming account snapshots via LangGraph
- Real-time risk signal detection
- Non-invasive wrapper (preserves original agent logic)
- Compatible with CopilotKit's agent interface
- Seamless handoff to MemoryAnalyst

Architecture:
    START -> validate_input -> fetch_account_data -> analyze_risks
          -> format_for_memory_analyst -> END

Integration Points:
    - Input: account_id from user/orchestrator
    - Output: account_snapshot formatted for MemoryAnalyst
    - Events: AG UI Protocol events for real-time streaming
"""

from typing import TypedDict, Annotated, List, Dict, Any, Literal
from typing_extensions import NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import structlog
from datetime import datetime

from src.agents.zoho_data_scout import ZohoDataScout
from src.integrations.zoho.integration_manager import ZohoIntegrationManager
from src.agents.config import DataScoutConfig

logger = structlog.get_logger(__name__)


# ============================================================================
# LangGraph State Definition
# ============================================================================

class ZohoScoutState(TypedDict):
    """
    State for ZohoDataScout LangGraph workflow.

    This state tracks the complete lifecycle of account data retrieval
    from Zoho CRM, including validation, fetching, risk analysis, and
    formatting for the next agent in the pipeline.

    Attributes:
        messages: Conversation history for CopilotKit
        account_id: Target account identifier (format: ACC-XXX or Zoho ID)
        session_id: Session identifier for tracking
        account_snapshot: Complete account snapshot with all data
        risk_signals: Identified risk signals with severity
        change_summary: Summary of detected changes since last sync
        aggregated_data: Related records (deals, activities, notes)
        workflow_status: Current workflow status
        error: Error message if any occurred
        next_agent_input: Formatted input for MemoryAnalyst
    """

    messages: Annotated[List[BaseMessage], add_messages]
    account_id: NotRequired[str]
    session_id: NotRequired[str]
    account_snapshot: NotRequired[Dict[str, Any]]
    risk_signals: NotRequired[List[Dict[str, Any]]]
    change_summary: NotRequired[Dict[str, Any]]
    aggregated_data: NotRequired[Dict[str, Any]]
    workflow_status: NotRequired[Literal["validating", "fetching", "analyzing", "completed", "error"]]
    error: NotRequired[str]
    next_agent_input: NotRequired[Dict[str, Any]]


# ============================================================================
# LangGraph Nodes
# ============================================================================

async def validate_input_node(state: ZohoScoutState) -> ZohoScoutState:
    """
    Validate input and extract account_id.

    This node ensures that:
    1. Account ID is provided in some form
    2. Account ID is in correct format (ACC-XXX or Zoho format)
    3. Session ID is available

    Args:
        state: Current state with messages

    Returns:
        Updated state with validated account_id

    Raises:
        ValueError: If account_id cannot be extracted or is invalid
    """

    logger.info("validate_input_node_executing")

    try:
        # Try to get account_id from state
        account_id = state.get("account_id")

        # If not in state, try to extract from last message
        if not account_id:
            last_message = state["messages"][-1]
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

            # Try multiple extraction patterns
            if "ACC-" in user_input:
                # Format: ACC-XXX
                account_id = user_input.split("ACC-")[1].split()[0]
                account_id = f"ACC-{account_id}"
            elif "account_id" in user_input.lower():
                # Format: account_id: XXX
                parts = user_input.lower().split("account_id")
                if len(parts) > 1:
                    account_id = parts[1].strip().split()[0].strip(":").strip()
            elif len(user_input.split()) == 1 and user_input.strip():
                # Assume single word is account_id
                account_id = user_input.strip()

        if not account_id:
            raise ValueError(
                "Could not extract account_id. Please provide account ID in format ACC-XXX or specify account_id explicitly."
            )

        # Ensure session_id
        session_id = state.get("session_id", f"session_{datetime.utcnow().isoformat()}")

        logger.info(
            "validate_input_completed",
            account_id=account_id,
            session_id=session_id
        )

        return {
            **state,
            "account_id": account_id,
            "session_id": session_id,
            "workflow_status": "fetching",
            "messages": state["messages"] + [
                AIMessage(content=f"Validated account ID: {account_id}. Fetching account data from Zoho CRM...")
            ]
        }

    except Exception as e:
        logger.error(
            "validate_input_failed",
            error=str(e)
        )

        return {
            **state,
            "workflow_status": "error",
            "error": str(e),
            "messages": state["messages"] + [
                AIMessage(content=f"Validation error: {str(e)}")
            ]
        }


async def fetch_account_data_node(state: ZohoScoutState) -> ZohoScoutState:
    """
    Fetch complete account data from Zoho CRM.

    This node wraps ZohoDataScout.get_account_snapshot() to:
    1. Initialize ZohoDataScout with proper configuration
    2. Fetch complete account snapshot
    3. Detect changes since last sync
    4. Aggregate related records (deals, activities, notes)
    5. Update state with all retrieved data

    Args:
        state: Current state with validated account_id

    Returns:
        Updated state with account snapshot and aggregated data
    """

    account_id = state.get("account_id")

    logger.info(
        "fetch_account_data_node_executing",
        account_id=account_id
    )

    try:
        # Initialize Zoho integration
        zoho_manager = ZohoIntegrationManager.from_env()

        # Initialize ZohoDataScout with configuration
        config = DataScoutConfig.from_env()
        scout = ZohoDataScout(
            zoho_manager=zoho_manager,
            config=config
        )

        # Fetch complete account snapshot (wraps existing logic)
        snapshot = await scout.get_account_snapshot(account_id)

        # Extract key information for state
        account_info = {
            "snapshot_id": snapshot.snapshot_id,
            "account_id": snapshot.account.account_id,
            "account_name": snapshot.account.account_name,
            "owner_id": snapshot.account.owner_id,
            "owner_name": snapshot.account.owner_name,
            "status": snapshot.account.status.value,
            "risk_level": snapshot.risk_level.value,
            "priority_score": snapshot.priority_score,
            "needs_review": snapshot.needs_review,
            "deal_count": snapshot.account.deal_count,
            "total_value": float(snapshot.account.total_value),
            "annual_revenue": float(snapshot.account.annual_revenue),
            "industry": snapshot.account.industry,
            "last_activity": snapshot.account.last_activity_date.isoformat() if snapshot.account.last_activity_date else None,
            "last_modified": snapshot.account.last_modified.isoformat() if snapshot.account.last_modified else None,
            "created_time": snapshot.account.created_time.isoformat() if snapshot.account.created_time else None,
        }

        # Extract risk signals
        risk_signals_list = [
            {
                "signal_type": signal.signal_type.value,
                "severity": signal.severity.value,
                "description": signal.description,
                "detected_at": signal.detected_at.isoformat(),
                "confidence_score": signal.confidence_score,
                "metadata": signal.metadata
            }
            for signal in snapshot.risk_signals
        ]

        # Extract change summary
        change_summary = {
            "changes_detected": snapshot.changes.changes_detected,
            "field_changes_count": len(snapshot.changes.field_changes),
            "change_types": [ct.value for ct in snapshot.changes.change_types],
            "requires_attention": snapshot.changes.requires_attention,
            "comparison_baseline": snapshot.changes.comparison_baseline.isoformat() if snapshot.changes.comparison_baseline else None,
            "field_changes": [
                {
                    "field_name": fc.field_name,
                    "old_value": fc.old_value,
                    "new_value": fc.new_value,
                    "change_type": fc.change_type.value
                }
                for fc in snapshot.changes.field_changes[:10]  # Limit to first 10
            ]
        }

        # Extract aggregated data summary
        aggregated_data_summary = {
            "deal_count": len(snapshot.aggregated_data.deals),
            "activity_count": len(snapshot.aggregated_data.activities),
            "note_count": len(snapshot.aggregated_data.notes),
            "total_deal_value": float(snapshot.aggregated_data.total_deal_value) if snapshot.aggregated_data.total_deal_value else 0,
            "active_deals": snapshot.aggregated_data.active_deals,
            "stalled_deals": snapshot.aggregated_data.stalled_deals,
            "recent_activity_count": snapshot.aggregated_data.recent_activity_count,
            "engagement_score": snapshot.aggregated_data.engagement_score,
            "data_freshness": snapshot.aggregated_data.data_freshness
        }

        # Format response message
        response_parts = [
            f"✓ Retrieved account: {snapshot.account.account_name}",
            f"✓ Owner: {snapshot.account.owner_name}",
            f"✓ Risk level: {snapshot.risk_level.value}",
            f"✓ Priority score: {snapshot.priority_score}/100",
            f"✓ Detected {len(risk_signals_list)} risk signals",
        ]

        if snapshot.changes.changes_detected:
            response_parts.append(
                f"✓ Found {len(snapshot.changes.field_changes)} field changes since last sync"
            )

        response_parts.append(f"✓ Aggregated {len(snapshot.aggregated_data.deals)} deals, {len(snapshot.aggregated_data.activities)} activities, {len(snapshot.aggregated_data.notes)} notes")

        response_message = "\n".join(response_parts)

        logger.info(
            "fetch_account_data_completed",
            account_id=account_id,
            risk_level=snapshot.risk_level.value,
            priority_score=snapshot.priority_score,
            risk_signals_count=len(risk_signals_list)
        )

        return {
            **state,
            "account_snapshot": account_info,
            "risk_signals": risk_signals_list,
            "change_summary": change_summary,
            "aggregated_data": aggregated_data_summary,
            "workflow_status": "analyzing",
            "messages": state["messages"] + [
                AIMessage(content=response_message)
            ]
        }

    except Exception as e:
        logger.error(
            "fetch_account_data_failed",
            account_id=account_id,
            error=str(e)
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
    Analyze and categorize risk signals.

    This node provides detailed risk analysis:
    1. Categorizes signals by severity (critical, high, medium, low)
    2. Groups signals by type
    3. Identifies patterns and trends
    4. Suggests immediate actions for critical risks

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
        logger.info("no_risk_signals_detected")

        return {
            **state,
            "workflow_status": "completed",
            "messages": state["messages"] + [
                AIMessage(content="✓ No risk signals detected. Account appears healthy.")
            ]
        }

    # Categorize by severity
    critical_signals = [s for s in risk_signals if s["severity"] == "critical"]
    high_signals = [s for s in risk_signals if s["severity"] == "high"]
    medium_signals = [s for s in risk_signals if s["severity"] == "medium"]
    low_signals = [s for s in risk_signals if s["severity"] == "low"]

    # Group by type
    signal_types = {}
    for signal in risk_signals:
        signal_type = signal["signal_type"]
        if signal_type not in signal_types:
            signal_types[signal_type] = []
        signal_types[signal_type].append(signal)

    # Build detailed analysis message
    analysis_parts = ["", "=== Risk Signal Analysis ===", ""]

    if critical_signals:
        analysis_parts.append(f"🔴 CRITICAL ({len(critical_signals)} signals):")
        for signal in critical_signals:
            analysis_parts.append(f"   - [{signal['signal_type']}] {signal['description']}")
        analysis_parts.append("")

    if high_signals:
        analysis_parts.append(f"🟠 HIGH ({len(high_signals)} signals):")
        for signal in high_signals:
            analysis_parts.append(f"   - [{signal['signal_type']}] {signal['description']}")
        analysis_parts.append("")

    if medium_signals:
        analysis_parts.append(f"🟡 MEDIUM ({len(medium_signals)} signals):")
        for signal in medium_signals:
            analysis_parts.append(f"   - [{signal['signal_type']}] {signal['description']}")
        analysis_parts.append("")

    if low_signals:
        analysis_parts.append(f"🟢 LOW ({len(low_signals)} signals):")
        for signal in low_signals[:3]:  # Show first 3
            analysis_parts.append(f"   - [{signal['signal_type']}] {signal['description']}")
        if len(low_signals) > 3:
            analysis_parts.append(f"   ... and {len(low_signals) - 3} more")
        analysis_parts.append("")

    # Add signal type summary
    analysis_parts.append("Signal Types:")
    for signal_type, signals in signal_types.items():
        analysis_parts.append(f"  • {signal_type}: {len(signals)}")

    analysis_message = "\n".join(analysis_parts)

    logger.info(
        "analyze_risk_signals_completed",
        critical=len(critical_signals),
        high=len(high_signals),
        medium=len(medium_signals),
        low=len(low_signals)
    )

    return {
        **state,
        "workflow_status": "completed",
        "messages": state["messages"] + [
            AIMessage(content=analysis_message)
        ]
    }


async def format_for_memory_analyst_node(state: ZohoScoutState) -> ZohoScoutState:
    """
    Format data for MemoryAnalyst agent.

    This node prepares the account snapshot data in the exact format
    expected by MemoryAnalyst for memory search and pattern analysis.

    Args:
        state: State with complete account data

    Returns:
        Updated state with formatted next_agent_input
    """

    logger.info("format_for_memory_analyst_node_executing")

    try:
        # Extract data from state
        account_snapshot = state.get("account_snapshot", {})
        risk_signals = state.get("risk_signals", [])
        change_summary = state.get("change_summary", {})
        aggregated_data = state.get("aggregated_data", {})

        # Format for MemoryAnalyst
        next_agent_input = {
            "agent": "memory_analyst",
            "context": {
                "account_id": account_snapshot.get("account_id"),
                "account_name": account_snapshot.get("account_name"),
                "snapshot_id": account_snapshot.get("snapshot_id"),
                "session_id": state.get("session_id")
            },
            "input_data": {
                "account_snapshot": account_snapshot,
                "risk_signals": risk_signals,
                "change_summary": change_summary,
                "aggregated_data": aggregated_data
            },
            "task": "Search memory for historical patterns and previous interactions related to this account"
        }

        logger.info(
            "format_for_memory_analyst_completed",
            account_id=account_snapshot.get("account_id")
        )

        return {
            **state,
            "next_agent_input": next_agent_input,
            "messages": state["messages"] + [
                AIMessage(content=f"✓ Data formatted for MemoryAnalyst. Ready for memory search.")
            ]
        }

    except Exception as e:
        logger.error(
            "format_for_memory_analyst_failed",
            error=str(e)
        )

        return {
            **state,
            "error": str(e),
            "messages": state["messages"] + [
                AIMessage(content=f"Error formatting data for MemoryAnalyst: {str(e)}")
            ]
        }


# ============================================================================
# Conditional Edges
# ============================================================================

def should_analyze_risks(state: ZohoScoutState) -> str:
    """
    Determine if risk analysis is needed.

    Args:
        state: Current state

    Returns:
        Next node: "analyze_risks" or "format_output"
    """

    risk_signals = state.get("risk_signals", [])
    has_risks = len(risk_signals) > 0

    logger.debug(
        "should_analyze_risks_decision",
        has_risks=has_risks,
        risk_count=len(risk_signals)
    )

    return "analyze_risks" if has_risks else "format_output"


def check_workflow_status(state: ZohoScoutState) -> str:
    """
    Check if workflow completed successfully or has error.

    Args:
        state: Current state

    Returns:
        Next node: "format_output" or "end"
    """

    status = state.get("workflow_status", "")
    has_error = bool(state.get("error"))

    if has_error or status == "error":
        logger.warning("workflow_has_error", status=status)
        return "end"

    if status == "completed":
        return "format_output"

    return "end"


# ============================================================================
# LangGraph Graph Construction
# ============================================================================

def create_zoho_scout_graph() -> StateGraph:
    """
    Create LangGraph graph for ZohoDataScout workflow.

    Workflow:
        START
          -> validate_input
          -> fetch_account_data
          -> conditional_edge (has risks?)
               -> analyze_risks -> check_status
               -> check_status
          -> format_output (if completed)
          -> END

    Returns:
        Compiled LangGraph StateGraph

    Example:
        >>> graph = create_zoho_scout_graph()
        >>> result = await graph.ainvoke({
        ...     "messages": [HumanMessage(content="Fetch account ACC-001")],
        ...     "session_id": "session_123"
        ... })
        >>> print(result["account_snapshot"]["account_name"])
    """

    logger.info("creating_zoho_scout_graph")

    # Initialize graph
    workflow = StateGraph(ZohoScoutState)

    # Add nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("fetch_account_data", fetch_account_data_node)
    workflow.add_node("analyze_risks", analyze_risk_signals_node)
    workflow.add_node("format_output", format_for_memory_analyst_node)

    # Set entry point
    workflow.set_entry_point("validate_input")

    # Add edges
    workflow.add_edge("validate_input", "fetch_account_data")

    # Conditional edge after fetch
    workflow.add_conditional_edges(
        "fetch_account_data",
        should_analyze_risks,
        {
            "analyze_risks": "analyze_risks",
            "format_output": "format_output"
        }
    )

    # After analysis, check status
    workflow.add_conditional_edges(
        "analyze_risks",
        check_workflow_status,
        {
            "format_output": "format_output",
            "end": END
        }
    )

    # Format output to END
    workflow.add_edge("format_output", END)

    # Compile
    compiled_graph = workflow.compile()

    logger.info("zoho_scout_graph_created")

    return compiled_graph


# ============================================================================
# Standalone Functions (for direct use without LangGraph)
# ============================================================================

async def fetch_account_data_direct(account_id: str) -> Dict[str, Any]:
    """
    Fetch account data directly without LangGraph overhead.

    This is a utility function for quick account lookups when you don't need
    the full LangGraph workflow and state management.

    Args:
        account_id: Account to fetch

    Returns:
        Account data dictionary with snapshot, risks, and changes

    Example:
        >>> data = await fetch_account_data_direct("ACC-001")
        >>> print(data["account_name"])
        >>> print(f"Risk level: {data['risk_level']}")
    """

    logger.info("fetching_account_data_direct", account_id=account_id)

    try:
        # Initialize Zoho integration
        zoho_manager = ZohoIntegrationManager.from_env()
        config = DataScoutConfig.from_env()
        scout = ZohoDataScout(zoho_manager=zoho_manager, config=config)

        # Fetch snapshot (wraps existing ZohoDataScout logic)
        snapshot = await scout.get_account_snapshot(account_id)

        return {
            "account_id": account_id,
            "snapshot_id": snapshot.snapshot_id,
            "account_name": snapshot.account.account_name,
            "owner": snapshot.account.owner_name,
            "status": snapshot.account.status.value,
            "risk_level": snapshot.risk_level.value,
            "priority_score": snapshot.priority_score,
            "needs_review": snapshot.needs_review,
            "risk_signals": [
                {
                    "type": s.signal_type.value,
                    "severity": s.severity.value,
                    "description": s.description,
                    "confidence": s.confidence_score
                }
                for s in snapshot.risk_signals
            ],
            "changes_detected": snapshot.changes.changes_detected,
            "change_count": len(snapshot.changes.field_changes),
            "deal_count": len(snapshot.aggregated_data.deals),
            "activity_count": len(snapshot.aggregated_data.activities)
        }

    except Exception as e:
        logger.error(
            "fetch_account_data_direct_failed",
            account_id=account_id,
            error=str(e)
        )
        raise


# ============================================================================
# Testing and Examples
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_zoho_scout_graph():
        """Test the ZohoDataScout LangGraph wrapper locally."""

        print("Testing ZohoDataScout LangGraph Wrapper")
        print("=" * 60)

        # Create graph
        graph = create_zoho_scout_graph()

        # Initial state
        initial_state = ZohoScoutState(
            messages=[
                HumanMessage(content="Fetch account ACC-001")
            ],
            session_id="test_session_123"
        )

        print("\nExecuting workflow...")

        # Execute graph
        result = await graph.ainvoke(initial_state)

        # Display results
        print("\n✓ Workflow completed successfully!")
        print(f"\nAccount ID: {result.get('account_id')}")
        print(f"Status: {result.get('workflow_status')}")
        print(f"Risk Signals: {len(result.get('risk_signals', []))}")

        if result.get('account_snapshot'):
            snapshot = result['account_snapshot']
            print(f"\nAccount Details:")
            print(f"  Name: {snapshot.get('account_name')}")
            print(f"  Owner: {snapshot.get('owner_name')}")
            print(f"  Risk Level: {snapshot.get('risk_level')}")
            print(f"  Priority Score: {snapshot.get('priority_score')}")

        if result.get('next_agent_input'):
            print(f"\n✓ Data formatted for MemoryAnalyst")
            print(f"  Ready for: {result['next_agent_input']['agent']}")

        print("\n" + "=" * 60)

    async def test_direct_fetch():
        """Test direct fetch without LangGraph."""

        print("\nTesting direct fetch (no LangGraph)...")

        data = await fetch_account_data_direct("ACC-001")

        print(f"\n✓ Direct fetch completed!")
        print(f"  Account: {data['account_name']}")
        print(f"  Risk Level: {data['risk_level']}")
        print(f"  Risk Signals: {len(data['risk_signals'])}")

    # Run tests
    # asyncio.run(test_zoho_scout_graph())
    # asyncio.run(test_direct_fetch())
