-- Migration: Create zoho_tokens table for OAuth token persistence
-- Version: 001
-- Created: 2025-10-18
-- Description: Stores Zoho OAuth tokens with automatic expiration tracking

CREATE TABLE IF NOT EXISTS zoho_tokens (
    id SERIAL PRIMARY KEY,
    token_type VARCHAR(50) NOT NULL DEFAULT 'oauth',
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_token_type UNIQUE (token_type)
);

-- Index for efficient token lookup
CREATE INDEX IF NOT EXISTS idx_zoho_tokens_expires_at ON zoho_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_zoho_tokens_token_type ON zoho_tokens(token_type);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_zoho_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zoho_tokens_updated_at
    BEFORE UPDATE ON zoho_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_zoho_tokens_updated_at();

-- Comments for documentation
COMMENT ON TABLE zoho_tokens IS 'Stores Zoho CRM OAuth tokens with automatic refresh tracking';
COMMENT ON COLUMN zoho_tokens.token_type IS 'Type of token (default: oauth)';
COMMENT ON COLUMN zoho_tokens.access_token IS 'Current access token for API calls';
COMMENT ON COLUMN zoho_tokens.refresh_token IS 'Refresh token for obtaining new access tokens';
COMMENT ON COLUMN zoho_tokens.expires_at IS 'Timestamp when access token expires';
