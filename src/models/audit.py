"""Audit data models - Pydantic models for business logic."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Pydantic model for audit events - business logic layer.

    This represents the audit event as used in the application logic,
    separate from the database persistence layer.
    """

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    event_type: str = Field(description="Type of event")
    agent_id: Optional[str] = Field(default=None, description="Agent ID performing the action")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    tool_name: Optional[str] = Field(default=None, description="Name of the tool being executed")
    tool_input: Optional[Dict[str, Any]] = Field(default=None, description="Input parameters for the tool")
    tool_output: Optional[Any] = Field(default=None, description="Output/result from the tool")
    status: str = Field(default="pending", description="Status of the operation")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


__all__ = ["AuditEvent"]
