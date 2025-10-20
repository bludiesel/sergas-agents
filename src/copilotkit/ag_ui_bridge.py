"""
AG UI Protocol Bridge for CopilotKit.

This module provides a communication bridge between CopilotKit's SDK
and the AG UI protocol for standardized agent communication.

The AG UI protocol provides:
- Standardized message format
- Type-safe agent responses
- UI component hints
- Action buttons and suggestions
- Rich media support

Reference:
    - /docs/research/AG_UI_PROTOCOL_Complete_Research.md
    - /docs/integrations/CLAUDE_SDK_AG_UI_Integration_Guide.md

Architecture:
    CopilotKit Frontend <-> AG UI Protocol <-> Python Agents

    Message Flow:
    1. Frontend sends user message via CopilotKit
    2. AG UI Bridge transforms to agent-compatible format
    3. Agent processes and returns structured response
    4. AG UI Bridge formats response with UI hints
    5. CopilotKit renders structured response in UI

Message Format:
    {
        "type": "agent_message",
        "agent_id": "zoho_scout",
        "content": "Found 3 high-priority accounts",
        "metadata": {
            "ui_hints": {
                "type": "table",
                "columns": ["Account", "Status", "Risk"],
                "actions": ["view_details", "add_note"]
            }
        },
        "timestamp": "2025-10-19T12:00:00Z"
    }
"""

import json
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    """AG UI Protocol message types."""
    AGENT_MESSAGE = "agent_message"
    USER_MESSAGE = "user_message"
    SYSTEM_MESSAGE = "system_message"
    ACTION_REQUEST = "action_request"
    ACTION_RESPONSE = "action_response"
    ERROR = "error"


class UIHintType(str, Enum):
    """UI component types for rendering hints."""
    TEXT = "text"
    TABLE = "table"
    CARD = "card"
    LIST = "list"
    CHART = "chart"
    TIMELINE = "timeline"
    FORM = "form"
    ALERT = "alert"


@dataclass
class UIHint:
    """
    UI rendering hints for agent responses.

    Tells the frontend how to best display the agent's response.
    """
    type: UIHintType
    title: Optional[str] = None
    description: Optional[str] = None
    columns: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AGUIMessage:
    """
    AG UI Protocol message structure.

    Standardized message format for agent communication.
    """
    type: MessageType
    agent_id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    message_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AGUIBridge:
    """
    Bridge between CopilotKit and AG UI Protocol.

    This class handles:
    1. Message transformation (CopilotKit <-> AG UI)
    2. UI hint generation for agent responses
    3. Action mapping for interactive elements
    4. Error handling and validation

    Example:
        >>> bridge = AGUIBridge()
        >>> agent_response = {"content": "Found 3 accounts", "data": [...]}
        >>> ag_ui_message = bridge.create_agent_message(
        ...     agent_id="zoho_scout",
        ...     content=agent_response["content"],
        ...     ui_hint=UIHint(type=UIHintType.TABLE, columns=["Name", "Status"])
        ... )
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AG UI Bridge.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.message_history: List[AGUIMessage] = []
        logger.info("ag_ui_bridge_initialized", config=self.config)

    def create_agent_message(
        self,
        agent_id: str,
        content: str,
        ui_hint: Optional[UIHint] = None,
        actions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AGUIMessage:
        """
        Create an AG UI formatted agent message.

        Args:
            agent_id: Identifier of the agent sending the message
            content: Text content of the message
            ui_hint: Optional UI rendering hints
            actions: Optional list of available actions
            metadata: Optional additional metadata

        Returns:
            AGUIMessage instance

        Example:
            >>> message = bridge.create_agent_message(
            ...     agent_id="zoho_scout",
            ...     content="Found 3 high-priority accounts",
            ...     ui_hint=UIHint(
            ...         type=UIHintType.TABLE,
            ...         columns=["Account", "Status", "Risk"]
            ...     ),
            ...     actions=["view_details", "add_note"]
            ... )
        """

        # Build metadata
        msg_metadata = metadata or {}

        # Add UI hints if provided
        if ui_hint:
            msg_metadata["ui_hints"] = ui_hint.to_dict()

        # Add actions if provided
        if actions:
            msg_metadata["actions"] = actions

        # Create message
        message = AGUIMessage(
            type=MessageType.AGENT_MESSAGE,
            agent_id=agent_id,
            content=content,
            metadata=msg_metadata,
            timestamp=datetime.utcnow().isoformat() + "Z",
            message_id=self._generate_message_id()
        )

        # Store in history
        self.message_history.append(message)

        logger.debug(
            "agent_message_created",
            agent_id=agent_id,
            has_ui_hint=ui_hint is not None,
            has_actions=actions is not None
        )

        return message

    def create_error_message(
        self,
        agent_id: str,
        error: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AGUIMessage:
        """
        Create an AG UI formatted error message.

        Args:
            agent_id: Identifier of the agent that encountered the error
            error: Error message
            error_code: Optional error code
            details: Optional error details

        Returns:
            AGUIMessage instance with error type
        """

        metadata = {
            "error_code": error_code,
            "details": details or {},
            "ui_hints": UIHint(
                type=UIHintType.ALERT,
                title="Error",
                description=error
            ).to_dict()
        }

        message = AGUIMessage(
            type=MessageType.ERROR,
            agent_id=agent_id,
            content=f"Error: {error}",
            metadata=metadata,
            timestamp=datetime.utcnow().isoformat() + "Z",
            message_id=self._generate_message_id()
        )

        logger.error(
            "error_message_created",
            agent_id=agent_id,
            error_code=error_code,
            error=error
        )

        return message

    def transform_copilotkit_message(
        self,
        copilotkit_message: Dict[str, Any]
    ) -> AGUIMessage:
        """
        Transform CopilotKit message to AG UI format.

        Args:
            copilotkit_message: Message from CopilotKit frontend

        Returns:
            AGUIMessage instance
        """

        # Extract message components
        message_type = copilotkit_message.get("type", "user_message")
        content = copilotkit_message.get("content", "")
        metadata = copilotkit_message.get("metadata", {})

        # Create AG UI message
        message = AGUIMessage(
            type=MessageType(message_type),
            agent_id=copilotkit_message.get("agent_id", "user"),
            content=content,
            metadata=metadata,
            timestamp=copilotkit_message.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            message_id=copilotkit_message.get("message_id", self._generate_message_id())
        )

        return message

    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        import uuid
        return f"msg_{uuid.uuid4().hex[:12]}"

    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AGUIMessage]:
        """
        Retrieve message history.

        Args:
            agent_id: Optional filter by agent ID
            limit: Optional limit number of messages

        Returns:
            List of AGUIMessage instances
        """

        messages = self.message_history

        # Filter by agent_id if provided
        if agent_id:
            messages = [m for m in messages if m.agent_id == agent_id]

        # Apply limit if provided
        if limit:
            messages = messages[-limit:]

        return messages

    def clear_history(self):
        """Clear message history."""
        self.message_history.clear()
        logger.info("message_history_cleared")


def create_ag_ui_bridge(config: Optional[Dict[str, Any]] = None) -> AGUIBridge:
    """
    Factory function to create AG UI Bridge instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured AGUIBridge instance

    Example:
        >>> bridge = create_ag_ui_bridge()
        >>> message = bridge.create_agent_message(
        ...     agent_id="zoho_scout",
        ...     content="Analysis complete"
        ... )
    """
    return AGUIBridge(config=config)
