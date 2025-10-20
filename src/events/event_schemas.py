"""AG UI Protocol event schemas using Pydantic models.

Reference: AG_UI_PROTOCOL_Implementation_Requirements.md
"""

from datetime import datetime
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# AG UI Event Base Models
# ============================================================================

class BaseAGUIEvent(BaseModel):
    """Base model for all AG UI Protocol events."""
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Workflow Events
# ============================================================================

class WorkflowStartedEventData(BaseModel):
    """Data for workflow_started event."""
    workflow: str = Field(..., description="Workflow type (e.g., 'account_analysis')")
    account_id: str = Field(..., description="Account identifier")
    session_id: str = Field(..., description="Unique session identifier")


class WorkflowStartedEvent(BaseAGUIEvent):
    """Event emitted when a workflow starts."""
    type: Literal["workflow_started"] = "workflow_started"
    data: WorkflowStartedEventData


class WorkflowCompletedEventData(BaseModel):
    """Data for workflow_completed event."""
    workflow: str
    account_id: str
    session_id: str
    total_duration_ms: int = Field(..., description="Total execution time in milliseconds")
    final_output: Optional[Dict[str, Any]] = Field(None, description="Final workflow output")


class WorkflowCompletedEvent(BaseAGUIEvent):
    """Event emitted when a workflow completes."""
    type: Literal["workflow_completed"] = "workflow_completed"
    data: WorkflowCompletedEventData


# ============================================================================
# Agent Events
# ============================================================================

class AgentStartedEventData(BaseModel):
    """Data for agent_started event."""
    agent: str = Field(..., description="Agent identifier (e.g., 'zoho_scout')")
    step: int = Field(..., description="Step number in workflow")
    task: Optional[str] = Field(None, description="Task description for the agent")


class AgentStartedEvent(BaseAGUIEvent):
    """Event emitted when an agent starts execution."""
    type: Literal["agent_started"] = "agent_started"
    data: AgentStartedEventData


class AgentStreamEventData(BaseModel):
    """Data for agent_stream event."""
    agent: str
    content: str = Field(..., description="Streamed content from agent")
    content_type: Literal["text", "tool_call", "tool_result"] = Field(
        default="text",
        description="Type of streamed content"
    )


class AgentStreamEvent(BaseAGUIEvent):
    """Event emitted when an agent streams content."""
    type: Literal["agent_stream"] = "agent_stream"
    data: AgentStreamEventData


class AgentCompletedEventData(BaseModel):
    """Data for agent_completed event."""
    agent: str
    step: int
    duration_ms: int = Field(..., description="Agent execution time in milliseconds")
    output: Optional[Dict[str, Any]] = Field(None, description="Agent output data")


class AgentCompletedEvent(BaseAGUIEvent):
    """Event emitted when an agent completes execution."""
    type: Literal["agent_completed"] = "agent_completed"
    data: AgentCompletedEventData


class AgentErrorEventData(BaseModel):
    """Data for agent_error event."""
    agent: str
    step: int
    error_type: str = Field(..., description="Error classification")
    error_message: str = Field(..., description="Human-readable error message")
    stack_trace: Optional[str] = Field(None, description="Error stack trace for debugging")


class AgentErrorEvent(BaseAGUIEvent):
    """Event emitted when an agent encounters an error."""
    type: Literal["agent_error"] = "agent_error"
    data: AgentErrorEventData


# ============================================================================
# Approval Events
# ============================================================================

class RecommendationData(BaseModel):
    """Recommendation data structure."""
    recommendation_id: str
    account_id: str
    recommendation_type: str = Field(..., description="Type of recommendation")
    action: str = Field(..., description="Recommended action")
    rationale: str = Field(..., description="Why this recommendation was made")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    estimated_impact: Optional[str] = Field(None, description="Expected impact if approved")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional recommendation data")


class ApprovalRequiredEventData(BaseModel):
    """Data for approval_required event."""
    recommendation: RecommendationData
    timeout_hours: int = Field(default=72, description="Hours until auto-rejection")


class ApprovalRequiredEvent(BaseAGUIEvent):
    """Event emitted when human approval is required."""
    type: Literal["approval_required"] = "approval_required"
    data: ApprovalRequiredEventData


class ApprovalResponseData(BaseModel):
    """Data for approval responses."""
    recommendation_id: str
    action: Literal["approve", "reject", "modify"] = Field(..., description="Approval action taken")
    modified_data: Optional[Dict[str, Any]] = Field(None, description="Modified recommendation data")
    reason: Optional[str] = Field(None, description="Reason for decision")
    approved_by: str = Field(..., description="User who made the approval decision")


# ============================================================================
# Tool Call Events
# ============================================================================

class ToolCallEventData(BaseModel):
    """Data for tool_call events."""
    tool_name: str = Field(..., description="Name of the tool being called")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    tool_call_id: str = Field(..., description="Unique identifier for this tool call")


class ToolCallEvent(BaseAGUIEvent):
    """Event emitted when a tool is called."""
    type: Literal["tool_call"] = "tool_call"
    data: ToolCallEventData


class ToolResultEventData(BaseModel):
    """Data for tool_result events."""
    tool_call_id: str
    tool_name: str
    result: Any = Field(..., description="Tool execution result")
    success: bool = Field(default=True, description="Whether tool call succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class ToolResultEvent(BaseAGUIEvent):
    """Event emitted when a tool call completes."""
    type: Literal["tool_result"] = "tool_result"
    data: ToolResultEventData


# ============================================================================
# State Snapshot Events
# ============================================================================

class StateSnapshotEventData(BaseModel):
    """Data for state_snapshot events."""
    session_id: str
    workflow: str
    current_step: int
    total_steps: int
    agent_states: Dict[str, Any] = Field(default_factory=dict, description="Current state of each agent")
    context: Dict[str, Any] = Field(default_factory=dict, description="Workflow context")


class StateSnapshotEvent(BaseAGUIEvent):
    """Event emitted to provide workflow state snapshot."""
    type: Literal["state_snapshot"] = "state_snapshot"
    data: StateSnapshotEventData


# ============================================================================
# Event Type Union
# ============================================================================

AGUIEvent = (
    WorkflowStartedEvent |
    WorkflowCompletedEvent |
    AgentStartedEvent |
    AgentStreamEvent |
    AgentCompletedEvent |
    AgentErrorEvent |
    ApprovalRequiredEvent |
    ToolCallEvent |
    ToolResultEvent |
    StateSnapshotEvent
)
