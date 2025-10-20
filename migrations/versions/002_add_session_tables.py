"""Add session and audit tables with cross-database types

Revision ID: 002_add_session_tables
Revises: 001_create_zoho_tokens
Create Date: 2025-10-19 20:56:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_session_tables'
down_revision: Union[str, None] = '001_create_zoho_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # AgentSession table with JSON and Array support
    op.create_table('agent_sessions',
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('orchestrator_id', sa.String(length=255), nullable=False, comment='Orchestrator agent ID'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='Session status'),
        sa.Column('session_type', sa.String(length=50), nullable=False, comment='Session type'),
        # Use TEXT for cross-database JSON storage (will be JSON string in SQLite, JSONB in PostgreSQL)
        sa.Column('context_snapshot', sa.Text(), nullable=False, comment='Session context snapshot'),
        sa.Column('account_ids', sa.Text(), nullable=True, comment='Account IDs in session'),
        sa.Column('owner_id', sa.String(length=255), nullable=True, comment='Account owner ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Session creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('session_id'),
        comment='Stores agent session state for recovery and tracking'
    )
    op.create_index('idx_agent_sessions_created', 'agent_sessions', ['created_at'], unique=False)
    op.create_index('idx_agent_sessions_orchestrator', 'agent_sessions', ['orchestrator_id'], unique=False)
    op.create_index('idx_agent_sessions_owner', 'agent_sessions', ['owner_id'], unique=False)
    op.create_index('idx_agent_sessions_status', 'agent_sessions', ['status'], unique=False)
    op.create_index('idx_agent_sessions_updated', 'agent_sessions', ['updated_at'], unique=False)

    # AuditEvent table with JSON metadata
    op.create_table('audit_events',
        sa.Column('event_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=True, comment='Associated session ID'),
        sa.Column('event_type', sa.String(length=100), nullable=False, comment='Event type'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, comment='Event timestamp'),
        sa.Column('actor', sa.String(length=255), nullable=True, comment='Actor (agent or user)'),
        sa.Column('action', sa.String(length=255), nullable=False, comment='Action performed'),
        sa.Column('resource', sa.String(length=255), nullable=True, comment='Resource affected'),
        sa.Column('event_metadata', sa.Text(), nullable=True, comment='Additional event metadata'),
        sa.PrimaryKeyConstraint('event_id'),
        comment='Stores audit events for complete activity tracking'
    )
    op.create_index('idx_audit_events_actor', 'audit_events', ['actor'], unique=False)
    op.create_index('idx_audit_events_resource', 'audit_events', ['resource'], unique=False)
    op.create_index('idx_audit_events_session', 'audit_events', ['session_id'], unique=False)
    op.create_index('idx_audit_events_timestamp', 'audit_events', ['timestamp'], unique=False)
    op.create_index('idx_audit_events_type', 'audit_events', ['event_type'], unique=False)

    # ScheduledReview table
    op.create_table('scheduled_reviews',
        sa.Column('review_id', sa.String(length=255), nullable=False),
        sa.Column('schedule_type', sa.String(length=50), nullable=False, comment='Schedule type'),
        sa.Column('cron_expression', sa.String(length=255), nullable=True, comment='Cron expression for custom schedules'),
        sa.Column('owner_id', sa.String(length=255), nullable=True, comment='Account owner filter'),
        sa.Column('enabled', sa.Boolean(), nullable=False, comment='Schedule enabled flag'),
        sa.Column('last_run', sa.DateTime(timezone=True), nullable=True, comment='Last execution timestamp'),
        sa.Column('next_run', sa.DateTime(timezone=True), nullable=True, comment='Next scheduled execution'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Schedule creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('review_id'),
        comment='Stores scheduled review configurations'
    )
    op.create_index('idx_scheduled_reviews_enabled', 'scheduled_reviews', ['enabled'], unique=False)
    op.create_index('idx_scheduled_reviews_last_run', 'scheduled_reviews', ['last_run'], unique=False)
    op.create_index('idx_scheduled_reviews_next_run', 'scheduled_reviews', ['next_run'], unique=False)
    op.create_index('idx_scheduled_reviews_owner', 'scheduled_reviews', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index('idx_scheduled_reviews_owner', table_name='scheduled_reviews')
    op.drop_index('idx_scheduled_reviews_next_run', table_name='scheduled_reviews')
    op.drop_index('idx_scheduled_reviews_last_run', table_name='scheduled_reviews')
    op.drop_index('idx_scheduled_reviews_enabled', table_name='scheduled_reviews')
    op.drop_table('scheduled_reviews')

    op.drop_index('idx_audit_events_type', table_name='audit_events')
    op.drop_index('idx_audit_events_timestamp', table_name='audit_events')
    op.drop_index('idx_audit_events_session', table_name='audit_events')
    op.drop_index('idx_audit_events_resource', table_name='audit_events')
    op.drop_index('idx_audit_events_actor', table_name='audit_events')
    op.drop_table('audit_events')

    op.drop_index('idx_agent_sessions_updated', table_name='agent_sessions')
    op.drop_index('idx_agent_sessions_status', table_name='agent_sessions')
    op.drop_index('idx_agent_sessions_owner', table_name='agent_sessions')
    op.drop_index('idx_agent_sessions_orchestrator', table_name='agent_sessions')
    op.drop_index('idx_agent_sessions_created', table_name='agent_sessions')
    op.drop_table('agent_sessions')
