"""Audit repository for storing and querying audit events.

Part of Week 6: Base Agent Infrastructure - Database Support.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditEvent
from src.db.models import AuditEventModel


class AuditRepository:
    """Repository for audit event storage and retrieval."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def save(self, event: AuditEvent) -> AuditEventModel:
        """Save audit event to database.

        Args:
            event: Audit event to save

        Returns:
            Saved database model
        """
        # Convert Pydantic model to SQLAlchemy model
        db_event = AuditEventModel(
            timestamp=event.timestamp,
            event_type=event.event_type,
            agent_id=event.agent_id,
            session_id=event.session_id,
            tool_name=event.tool_name,
            tool_input=event.tool_input,
            tool_output=event.tool_output,
            status=event.status,
            error_message=event.error_message,
            execution_time_ms=event.execution_time_ms,
        )

        self.session.add(db_event)
        await self.session.commit()
        await self.session.refresh(db_event)

        return db_event

    async def query_events(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events with filters.

        Args:
            session_id: Filter by session
            agent_id: Filter by agent
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events to return

        Returns:
            List of audit events
        """
        # Build query with filters
        conditions = []
        if session_id:
            conditions.append(AuditEventModel.session_id == session_id)
        if agent_id:
            conditions.append(AuditEventModel.agent_id == agent_id)
        if start_time:
            conditions.append(AuditEventModel.timestamp >= start_time)
        if end_time:
            conditions.append(AuditEventModel.timestamp <= end_time)

        query = (
            select(AuditEventModel)
            .where(and_(*conditions) if conditions else True)
            .order_by(AuditEventModel.timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        db_events = result.scalars().all()

        # Convert to Pydantic models
        return [
            AuditEvent(
                timestamp=db_event.timestamp,
                event_type=db_event.event_type,
                agent_id=db_event.agent_id,
                session_id=db_event.session_id,
                tool_name=db_event.tool_name,
                tool_input=db_event.tool_input,
                tool_output=db_event.tool_output,
                status=db_event.status,
                error_message=db_event.error_message,
                execution_time_ms=db_event.execution_time_ms,
            )
            for db_event in db_events
        ]

    async def get_session_events(self, session_id: str) -> List[AuditEvent]:
        """Get all events for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            List of audit events for the session
        """
        return await self.query_events(session_id=session_id)

    async def get_agent_events(
        self, agent_id: str, limit: int = 100
    ) -> List[AuditEvent]:
        """Get recent events for a specific agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of events

        Returns:
            List of audit events for the agent
        """
        return await self.query_events(agent_id=agent_id, limit=limit)
