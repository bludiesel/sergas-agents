"""SQLAlchemy ORM models for token persistence and session management."""

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Text, DateTime, Integer, Index, UniqueConstraint, Boolean, JSON, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class ZohoToken(Base):
    """Zoho OAuth token storage with expiration tracking.

    Attributes:
        id: Primary key auto-increment
        token_type: Type of token (e.g., 'oauth', 'grant')
        access_token: Current OAuth access token
        refresh_token: OAuth refresh token for renewals
        expires_at: Timestamp when access token expires
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "zoho_tokens"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Token data
    token_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Token type (oauth, grant, etc.)"
    )
    access_token: Mapped[str] = mapped_column(
        Text, nullable=False, comment="OAuth access token"
    )
    refresh_token: Mapped[str] = mapped_column(
        Text, nullable=False, comment="OAuth refresh token"
    )

    # Expiration tracking
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Access token expiration timestamp",
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("token_type", name="uq_zoho_tokens_token_type"),
        Index("idx_zoho_tokens_expires_at", "expires_at"),
        Index("idx_zoho_tokens_updated_at", "updated_at"),
        {"comment": "Stores Zoho OAuth tokens with expiration tracking"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ZohoToken(id={self.id}, type={self.token_type}, "
            f"expires_at={self.expires_at})>"
        )

    def is_expired(self) -> bool:
        """Check if access token is expired.

        Returns:
            bool: True if token is expired or expiring within 5 minutes
        """
        from datetime import timedelta

        # Add 5 minute buffer for token refresh
        buffer_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        return self.expires_at <= buffer_time


class TokenRefreshAudit(Base):
    """Audit log for token refresh operations.

    Tracks all token refresh attempts for security and debugging.
    """

    __tablename__ = "token_refresh_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Related token ID if exists"
    )
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)

    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    previous_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    new_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_token_refresh_audit_refreshed_at", "refreshed_at"),
        Index("idx_token_refresh_audit_success", "success"),
        {"comment": "Audit log for token refresh operations"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TokenRefreshAudit(id={self.id}, token_type={self.token_type}, "
            f"success={self.success})>"
        )


class AgentSession(Base):
    """Agent orchestrator session storage.

    Tracks session lifecycle, context, and state for recovery.

    Attributes:
        session_id: Unique session identifier
        orchestrator_id: ID of orchestrator agent
        status: Current session status
        session_type: Type of session (scheduled, on_demand, etc.)
        context_snapshot: JSONB snapshot of session context
        account_ids: Array of account IDs being processed
        owner_id: Optional account owner ID
        created_at: Session creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "agent_sessions"

    # Primary key
    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Session metadata
    orchestrator_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Orchestrator agent ID"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Session status"
    )
    session_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Session type"
    )

    # Context and state
    context_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, comment="Session context snapshot"
    )
    account_ids: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Account IDs in session"
    )
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Account owner ID"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Session creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Constraints
    __table_args__ = (
        Index("idx_agent_sessions_orchestrator", "orchestrator_id"),
        Index("idx_agent_sessions_status", "status"),
        Index("idx_agent_sessions_owner", "owner_id"),
        Index("idx_agent_sessions_created", "created_at"),
        Index("idx_agent_sessions_updated", "updated_at"),
        {"comment": "Stores agent session state for recovery and tracking"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AgentSession(session_id={self.session_id}, "
            f"orchestrator={self.orchestrator_id}, status={self.status})>"
        )


class ScheduledReview(Base):
    """Scheduled account review configuration.

    Attributes:
        review_id: Unique review schedule identifier
        schedule_type: Type of schedule (daily, weekly, cron, etc.)
        cron_expression: Optional cron expression for custom schedules
        owner_id: Optional owner ID filter
        enabled: Whether schedule is active
        last_run: Timestamp of last execution
        next_run: Timestamp of next scheduled execution
        created_at: Schedule creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "scheduled_reviews"

    # Primary key
    review_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Schedule configuration
    schedule_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Schedule type"
    )
    cron_expression: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Cron expression for custom schedules"
    )
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Account owner filter"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Schedule enabled flag"
    )

    # Execution tracking
    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last execution timestamp"
    )
    next_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Next scheduled execution"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Schedule creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Constraints
    __table_args__ = (
        Index("idx_scheduled_reviews_owner", "owner_id"),
        Index("idx_scheduled_reviews_enabled", "enabled"),
        Index("idx_scheduled_reviews_next_run", "next_run"),
        Index("idx_scheduled_reviews_last_run", "last_run"),
        {"comment": "Stores scheduled review configurations"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ScheduledReview(review_id={self.review_id}, "
            f"type={self.schedule_type}, enabled={self.enabled})>"
        )


class AuditEvent(Base):
    """Audit event log for complete activity tracking.

    Tracks all agent actions, tool invocations, and decisions.

    Attributes:
        event_id: Unique event identifier
        session_id: Associated session ID
        event_type: Type of event
        timestamp: Event occurrence timestamp
        actor: Agent or user performing action
        action: Action performed
        resource: Resource affected
        metadata: Additional event metadata (JSONB)
    """

    __tablename__ = "audit_events"

    # Primary key
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Event identification
    session_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Associated session ID"
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Event type"
    )

    # Event details
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Event timestamp",
    )
    actor: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Actor (agent or user)"
    )
    action: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Action performed"
    )
    resource: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Resource affected"
    )

    # Flexible metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict, comment="Additional event metadata"
    )

    # Constraints
    __table_args__ = (
        Index("idx_audit_events_session", "session_id"),
        Index("idx_audit_events_type", "event_type"),
        Index("idx_audit_events_timestamp", "timestamp"),
        Index("idx_audit_events_actor", "actor"),
        Index("idx_audit_events_resource", "resource"),
        {
            "comment": "Stores audit events for complete activity tracking",
            "postgresql_partition_by": "RANGE (timestamp)",  # Enable partitioning
        },
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditEvent(event_id={self.event_id}, "
            f"type={self.event_type}, action={self.action})>"
        )
