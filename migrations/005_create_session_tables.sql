-- Migration 005: Create session management tables
-- Created: 2025-10-19
-- Purpose: Add agent session tracking, scheduled reviews, and audit events

-- ========================================
-- 1. Agent Sessions Table
-- ========================================

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    orchestrator_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    session_type VARCHAR(50) NOT NULL,
    context_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    account_ids TEXT[],
    owner_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE agent_sessions IS 'Stores agent session state for recovery and tracking';
COMMENT ON COLUMN agent_sessions.session_id IS 'Unique session identifier';
COMMENT ON COLUMN agent_sessions.orchestrator_id IS 'Orchestrator agent ID';
COMMENT ON COLUMN agent_sessions.status IS 'Session status (pending, running, paused, completed, failed, interrupted)';
COMMENT ON COLUMN agent_sessions.session_type IS 'Session type (scheduled, on_demand, manual, recovery)';
COMMENT ON COLUMN agent_sessions.context_snapshot IS 'JSONB snapshot of session context';
COMMENT ON COLUMN agent_sessions.account_ids IS 'Array of account IDs in session';
COMMENT ON COLUMN agent_sessions.owner_id IS 'Account owner ID filter';

-- Indexes for agent_sessions
CREATE INDEX idx_agent_sessions_orchestrator ON agent_sessions(orchestrator_id);
CREATE INDEX idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX idx_agent_sessions_owner ON agent_sessions(owner_id);
CREATE INDEX idx_agent_sessions_created ON agent_sessions(created_at);
CREATE INDEX idx_agent_sessions_updated ON agent_sessions(updated_at);

-- GIN index for JSONB context searches
CREATE INDEX idx_agent_sessions_context_gin ON agent_sessions USING GIN (context_snapshot);

-- ========================================
-- 2. Scheduled Reviews Table
-- ========================================

CREATE TABLE IF NOT EXISTS scheduled_reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    schedule_type VARCHAR(50) NOT NULL,
    cron_expression VARCHAR(255),
    owner_id VARCHAR(255),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE scheduled_reviews IS 'Stores scheduled review configurations';
COMMENT ON COLUMN scheduled_reviews.review_id IS 'Unique review schedule identifier';
COMMENT ON COLUMN scheduled_reviews.schedule_type IS 'Schedule type (daily, weekly, biweekly, monthly, cron, interval, one_time)';
COMMENT ON COLUMN scheduled_reviews.cron_expression IS 'Cron expression for custom schedules';
COMMENT ON COLUMN scheduled_reviews.owner_id IS 'Account owner filter';
COMMENT ON COLUMN scheduled_reviews.enabled IS 'Schedule enabled flag';
COMMENT ON COLUMN scheduled_reviews.last_run IS 'Last execution timestamp';
COMMENT ON COLUMN scheduled_reviews.next_run IS 'Next scheduled execution';

-- Indexes for scheduled_reviews
CREATE INDEX idx_scheduled_reviews_owner ON scheduled_reviews(owner_id);
CREATE INDEX idx_scheduled_reviews_enabled ON scheduled_reviews(enabled);
CREATE INDEX idx_scheduled_reviews_next_run ON scheduled_reviews(next_run);
CREATE INDEX idx_scheduled_reviews_last_run ON scheduled_reviews(last_run);

-- ========================================
-- 3. Audit Events Table (Partitioned)
-- ========================================

-- Create parent table for partitioning
CREATE TABLE IF NOT EXISTS audit_events (
    event_id BIGSERIAL,
    session_id VARCHAR(255),
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (event_id, timestamp)
) PARTITION BY RANGE (timestamp);

COMMENT ON TABLE audit_events IS 'Stores audit events for complete activity tracking';
COMMENT ON COLUMN audit_events.event_id IS 'Unique event identifier';
COMMENT ON COLUMN audit_events.session_id IS 'Associated session ID';
COMMENT ON COLUMN audit_events.event_type IS 'Event type (tool_invocation, tool_success, tool_error, task_started, task_completed, etc.)';
COMMENT ON COLUMN audit_events.timestamp IS 'Event timestamp';
COMMENT ON COLUMN audit_events.actor IS 'Actor (agent or user)';
COMMENT ON COLUMN audit_events.action IS 'Action performed';
COMMENT ON COLUMN audit_events.resource IS 'Resource affected';
COMMENT ON COLUMN audit_events.metadata IS 'Additional event metadata';

-- Create initial partitions (current month and next 3 months)
-- This function creates monthly partitions
CREATE OR REPLACE FUNCTION create_audit_partition(start_date DATE, end_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
BEGIN
    partition_name := 'audit_events_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_events
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        start_date,
        end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Create partitions for current and next 3 months
DO $$
DECLARE
    i INTEGER;
    start_date DATE;
    end_date DATE;
BEGIN
    FOR i IN 0..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        end_date := start_date + INTERVAL '1 month';
        PERFORM create_audit_partition(start_date, end_date);
    END LOOP;
END $$;

-- Indexes for audit_events (will be created on partitions)
CREATE INDEX idx_audit_events_session ON audit_events(session_id, timestamp);
CREATE INDEX idx_audit_events_type ON audit_events(event_type, timestamp);
CREATE INDEX idx_audit_events_actor ON audit_events(actor, timestamp);
CREATE INDEX idx_audit_events_resource ON audit_events(resource, timestamp);

-- GIN index for JSONB metadata searches
CREATE INDEX idx_audit_events_metadata_gin ON audit_events USING GIN (metadata);

-- ========================================
-- 4. Triggers for Updated At
-- ========================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to agent_sessions
DROP TRIGGER IF EXISTS update_agent_sessions_updated_at ON agent_sessions;
CREATE TRIGGER update_agent_sessions_updated_at
    BEFORE UPDATE ON agent_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to scheduled_reviews
DROP TRIGGER IF EXISTS update_scheduled_reviews_updated_at ON scheduled_reviews;
CREATE TRIGGER update_scheduled_reviews_updated_at
    BEFORE UPDATE ON scheduled_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 5. Cleanup Function for Old Audit Events
-- ========================================

-- Function to drop old audit partitions
CREATE OR REPLACE FUNCTION cleanup_old_audit_partitions(retention_months INTEGER DEFAULT 6)
RETURNS VOID AS $$
DECLARE
    partition_record RECORD;
    cutoff_date DATE;
BEGIN
    cutoff_date := date_trunc('month', CURRENT_DATE - (retention_months || ' months')::INTERVAL);

    FOR partition_record IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'audit_events_%'
        AND tablename < 'audit_events_' || to_char(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', partition_record.tablename);
        RAISE NOTICE 'Dropped old partition: %', partition_record.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 6. Scheduled Partition Maintenance
-- ========================================

-- Function to create future partitions (run monthly via cron)
CREATE OR REPLACE FUNCTION maintain_audit_partitions()
RETURNS VOID AS $$
DECLARE
    i INTEGER;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Create partitions for next 3 months if they don't exist
    FOR i IN 1..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        end_date := start_date + INTERVAL '1 month';
        PERFORM create_audit_partition(start_date, end_date);
    END LOOP;

    -- Cleanup old partitions (older than 6 months)
    PERFORM cleanup_old_audit_partitions(6);
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 7. Data Constraints and Validation
-- ========================================

-- Add check constraints for status values
ALTER TABLE agent_sessions
    ADD CONSTRAINT chk_agent_sessions_status
    CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'interrupted'));

ALTER TABLE agent_sessions
    ADD CONSTRAINT chk_agent_sessions_type
    CHECK (session_type IN ('scheduled', 'on_demand', 'manual', 'recovery'));

-- Add check constraints for schedule types
ALTER TABLE scheduled_reviews
    ADD CONSTRAINT chk_scheduled_reviews_type
    CHECK (schedule_type IN ('daily', 'weekly', 'biweekly', 'monthly', 'cron', 'interval', 'one_time'));

-- ========================================
-- 8. Foreign Key Relationships
-- ========================================

-- Add foreign key from audit_events to agent_sessions (optional reference)
ALTER TABLE audit_events
    ADD CONSTRAINT fk_audit_events_session
    FOREIGN KEY (session_id)
    REFERENCES agent_sessions(session_id)
    ON DELETE SET NULL;

-- ========================================
-- 9. Grant Permissions
-- ========================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON agent_sessions TO sergas_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON scheduled_reviews TO sergas_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON audit_events TO sergas_app;
-- GRANT USAGE, SELECT ON SEQUENCE audit_events_event_id_seq TO sergas_app;

-- ========================================
-- 10. Migration Metadata
-- ========================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_migrations (version, description)
VALUES (5, 'Create session management tables')
ON CONFLICT (version) DO NOTHING;

-- ========================================
-- Success Message
-- ========================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 005 completed successfully!';
    RAISE NOTICE 'Created tables: agent_sessions, scheduled_reviews, audit_events (partitioned)';
    RAISE NOTICE 'Created partition maintenance functions';
    RAISE NOTICE 'Created indexes and constraints';
END $$;
