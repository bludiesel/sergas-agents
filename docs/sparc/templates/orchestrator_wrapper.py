"""
LangGraph Wrapper for OrchestratorAgent

This module wraps the existing OrchestratorAgent (Claude Agent SDK) with
LangGraph to make it compatible with CopilotKit's agent interface.

Integration Pattern:
1. Existing Agent (Claude SDK) -> LangGraph Node -> CopilotKit
2. Maintains all existing functionality
3. Adds CopilotKit streaming and state management

Key Concepts:
- LangGraph State: Manages conversation and agent state
- Nodes: Individual processing steps (agents)
- Edges: Control flow between agents
- Streaming: Real-time updates to frontend
"""

from typing import TypedDict, Annotated, Dict, Any, List
from typing_extensions import NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import structlog

# Import existing Sergas agents
from src.agents.orchestrator import OrchestratorAgent
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.integrations.zoho.integration_manager import ZohoIntegrationManager
from src.services.memory_service import MemoryService
from src.integrations.cognee.cognee_client import CogneeClient
from src.events.approval_manager import ApprovalManager

logger = structlog.get_logger(__name__)


# ============================================================================
# LangGraph State Definition
# ============================================================================

class OrchestratorState(TypedDict):
    """
    State managed by LangGraph for orchestrator workflow.

    This state is shared across all nodes in the graph and persists
    throughout the conversation.

    Attributes:
        messages: Conversation history (managed by LangGraph)
        account_id: Current account being analyzed
        session_id: Unique session identifier
        account_data: Data from ZohoDataScout
        historical_context: Data from MemoryAnalyst
        recommendations: Generated recommendations
        approval_status: Approval workflow status
        workflow_status: Overall workflow status
        error: Error information if workflow fails
    """

    # Conversation history - automatically managed by LangGraph
    messages: Annotated[List[BaseMessage], add_messages]

    # Workflow context
    account_id: NotRequired[str]
    session_id: NotRequired[str]
    workflow: NotRequired[str]

    # Agent outputs
    account_data: NotRequired[Dict[str, Any]]
    historical_context: NotRequired[Dict[str, Any]]
    recommendations: NotRequired[List[Dict[str, Any]]]

    # Workflow tracking
    approval_status: NotRequired[str]
    workflow_status: NotRequired[str]
    error: NotRequired[str]


# ============================================================================
# LangGraph Nodes (Agent Wrappers)
# ============================================================================

async def orchestrator_node(state: OrchestratorState) -> OrchestratorState:
    """
    Main orchestrator node that coordinates all specialist agents.

    This wraps the existing OrchestratorAgent and makes it compatible with
    LangGraph's state management.

    Args:
        state: Current LangGraph state

    Returns:
        Updated state with orchestration results

    Flow:
        1. Extract account_id from user message
        2. Initialize orchestrator with all specialist agents
        3. Execute orchestration workflow
        4. Stream results back to frontend via CopilotKit
        5. Update state with final results
    """

    logger.info(
        "orchestrator_node_executing",
        session_id=state.get("session_id"),
        account_id=state.get("account_id")
    )

    try:
        # Extract user request from messages
        last_message = state["messages"][-1]
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # Parse account_id from user input if not in state
        account_id = state.get("account_id")
        if not account_id:
            # Simple extraction - in production, use better parsing
            if "ACC-" in user_input:
                account_id = user_input.split("ACC-")[1].split()[0]
                account_id = f"ACC-{account_id}"

        if not account_id:
            raise ValueError(
                "Could not extract account_id. Please provide account ID in format ACC-XXX"
            )

        # Initialize dependencies
        # Note: In production, these should be injected via dependency injection
        session_id = state.get("session_id", "default_session")

        # Initialize Zoho integration
        zoho_manager = ZohoIntegrationManager.from_env()

        # Initialize ZohoDataScout
        zoho_scout = ZohoDataScout(zoho_manager=zoho_manager)

        # Initialize MemoryAnalyst
        memory_service = MemoryService()
        cognee_client = CogneeClient()
        memory_analyst = MemoryAnalyst(
            memory_service=memory_service,
            cognee_client=cognee_client,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # Initialize ApprovalManager
        approval_manager = ApprovalManager()

        # Create OrchestratorAgent
        orchestrator = OrchestratorAgent(
            session_id=session_id,
            zoho_scout=zoho_scout,
            memory_analyst=memory_analyst,
            approval_manager=approval_manager
        )

        # Execute orchestration
        execution_context = {
            "account_id": account_id,
            "workflow": state.get("workflow", "account_analysis"),
            "timeout_seconds": 300
        }

        # Collect results from streaming execution
        final_output = None
        agent_messages = []

        async for event in orchestrator.execute_with_events(execution_context):
            event_type = event.get("event")

            # Collect agent progress messages
            if event_type == "agent_stream":
                content = event.get("data", {}).get("content", "")
                agent_messages.append(content)

            # Capture final output
            elif event_type == "workflow_completed":
                final_output = event.get("data", {}).get("final_output")

            # Note: CopilotKit will automatically handle streaming these events
            # to the frontend via Server-Sent Events

        if not final_output:
            raise RuntimeError("Orchestration did not complete successfully")

        # Update state with results
        updated_state = {
            **state,
            "account_id": account_id,
            "account_data": final_output.get("execution_summary", {}).get("account_data"),
            "historical_context": final_output.get("execution_summary", {}).get("historical_context"),
            "recommendations": final_output.get("recommendations", []),
            "approval_status": final_output.get("approval", {}).get("status"),
            "workflow_status": final_output.get("status"),
            "messages": state["messages"] + [
                AIMessage(content="\n".join(agent_messages))
            ]
        }

        logger.info(
            "orchestrator_node_completed",
            account_id=account_id,
            status=final_output.get("status")
        )

        return updated_state

    except Exception as e:
        logger.error(
            "orchestrator_node_failed",
            error=str(e),
            account_id=state.get("account_id")
        )

        # Update state with error
        return {
            **state,
            "workflow_status": "error",
            "error": str(e),
            "messages": state["messages"] + [
                AIMessage(content=f"Error during orchestration: {str(e)}")
            ]
        }


async def approval_node(state: OrchestratorState) -> OrchestratorState:
    """
    Handle approval workflow for recommendations.

    This node manages the user approval process for generated recommendations.
    It integrates with CopilotKit's UI components for interactive approval.

    Args:
        state: Current state with recommendations

    Returns:
        Updated state with approval status
    """

    logger.info(
        "approval_node_executing",
        recommendations_count=len(state.get("recommendations", []))
    )

    recommendations = state.get("recommendations", [])

    if not recommendations:
        # No recommendations to approve
        return {
            **state,
            "approval_status": "no_recommendations",
            "messages": state["messages"] + [
                AIMessage(content="No recommendations require approval.")
            ]
        }

    # In CopilotKit, approval can be handled via:
    # 1. useCopilotAction hook in frontend
    # 2. Manual user input
    # 3. Automatic approval for low-risk actions

    # For now, mark as pending - frontend will handle approval UI
    return {
        **state,
        "approval_status": "pending_approval",
        "messages": state["messages"] + [
            AIMessage(
                content=f"Generated {len(recommendations)} recommendations. "
                        "Please review and approve."
            )
        ]
    }


def should_request_approval(state: OrchestratorState) -> str:
    """
    Conditional edge function to determine if approval is needed.

    Args:
        state: Current state

    Returns:
        Next node name: "approval" or "end"
    """

    recommendations = state.get("recommendations", [])
    high_priority = any(
        rec.get("priority") in ["high", "critical"]
        for rec in recommendations
    )

    if recommendations and high_priority:
        return "approval"
    else:
        return "end"


# ============================================================================
# LangGraph Graph Construction
# ============================================================================

def create_orchestrator_graph() -> StateGraph:
    """
    Create the LangGraph graph for the orchestrator workflow.

    This builds the complete workflow graph that CopilotKit will execute:

    Flow:
        START -> orchestrator_node -> conditional_edge
                                    -> approval_node -> END
                                    -> END

    Returns:
        Compiled LangGraph StateGraph ready for CopilotKit

    Example:
        >>> graph = create_orchestrator_graph()
        >>> # Register with CopilotKit
        >>> copilot_kit.add_agent("orchestrator", graph)
    """

    logger.info("creating_orchestrator_graph")

    # Initialize graph with state schema
    workflow = StateGraph(OrchestratorState)

    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("approval", approval_node)

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Add conditional edge after orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        should_request_approval,
        {
            "approval": "approval",
            "end": END
        }
    )

    # Add edge from approval to end
    workflow.add_edge("approval", END)

    # Compile graph
    compiled_graph = workflow.compile()

    logger.info("orchestrator_graph_created")

    return compiled_graph


# ============================================================================
# Helper Functions
# ============================================================================

import os


def initialize_orchestrator_dependencies() -> Dict[str, Any]:
    """
    Initialize all dependencies required by the orchestrator.

    This function sets up all the components needed by the OrchestratorAgent:
    - Zoho integration
    - Memory services
    - Agent instances

    Returns:
        Dictionary of initialized components

    Example:
        >>> deps = initialize_orchestrator_dependencies()
        >>> orchestrator = OrchestratorAgent(**deps)
    """

    logger.info("initializing_orchestrator_dependencies")

    try:
        # Zoho integration
        zoho_manager = ZohoIntegrationManager.from_env()

        # ZohoDataScout
        zoho_scout = ZohoDataScout(zoho_manager=zoho_manager)

        # Memory services
        memory_service = MemoryService()
        cognee_client = CogneeClient()

        # MemoryAnalyst
        memory_analyst = MemoryAnalyst(
            memory_service=memory_service,
            cognee_client=cognee_client,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # ApprovalManager
        approval_manager = ApprovalManager()

        dependencies = {
            "zoho_manager": zoho_manager,
            "zoho_scout": zoho_scout,
            "memory_service": memory_service,
            "cognee_client": cognee_client,
            "memory_analyst": memory_analyst,
            "approval_manager": approval_manager
        }

        logger.info("orchestrator_dependencies_initialized")

        return dependencies

    except Exception as e:
        logger.error(
            "orchestrator_dependencies_initialization_failed",
            error=str(e)
        )
        raise


# Example: Testing the graph locally
if __name__ == "__main__":
    import asyncio

    async def test_orchestrator_graph():
        """Test the orchestrator graph locally."""

        # Create graph
        graph = create_orchestrator_graph()

        # Initial state
        initial_state = OrchestratorState(
            messages=[
                HumanMessage(content="Analyze account ACC-001")
            ],
            session_id="test_session",
            workflow="account_analysis"
        )

        # Execute graph
        result = await graph.ainvoke(initial_state)

        print("Graph execution completed:")
        print(f"Account ID: {result.get('account_id')}")
        print(f"Status: {result.get('workflow_status')}")
        print(f"Recommendations: {len(result.get('recommendations', []))}")

    # Run test
    asyncio.run(test_orchestrator_graph())
