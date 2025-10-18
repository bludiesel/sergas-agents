"""Create zoho_tokens and token_refresh_audit tables.

Revision ID: 001_create_zoho_tokens
Revises:
Create Date: 2024-10-18 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_create_zoho_tokens'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - create token tables."""
    # Create zoho_tokens table
    op.create_table(
        'zoho_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('token_type', sa.String(length=50), nullable=False,
                  comment='Token type (oauth, grant, etc.)'),
        sa.Column('access_token', sa.Text(), nullable=False,
                  comment='OAuth access token'),
        sa.Column('refresh_token', sa.Text(), nullable=False,
                  comment='OAuth refresh token'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False,
                  comment='Access token expiration timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_type', name='uq_zoho_tokens_token_type'),
        comment='Stores Zoho OAuth tokens with expiration tracking'
    )

    # Create indexes for zoho_tokens
    op.create_index(
        'idx_zoho_tokens_expires_at',
        'zoho_tokens',
        ['expires_at']
    )
    op.create_index(
        'idx_zoho_tokens_updated_at',
        'zoho_tokens',
        ['updated_at']
    )

    # Create token_refresh_audit table
    op.create_table(
        'token_refresh_audit',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('token_id', sa.Integer(), nullable=True,
                  comment='Related token ID if exists'),
        sa.Column('token_type', sa.String(length=50), nullable=False),
        sa.Column('refreshed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('previous_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('new_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit log for token refresh operations'
    )

    # Create indexes for token_refresh_audit
    op.create_index(
        'idx_token_refresh_audit_refreshed_at',
        'token_refresh_audit',
        ['refreshed_at']
    )
    op.create_index(
        'idx_token_refresh_audit_success',
        'token_refresh_audit',
        ['success']
    )


def downgrade() -> None:
    """Downgrade database schema - drop token tables."""
    # Drop indexes first
    op.drop_index('idx_token_refresh_audit_success', table_name='token_refresh_audit')
    op.drop_index('idx_token_refresh_audit_refreshed_at', table_name='token_refresh_audit')
    op.drop_index('idx_zoho_tokens_updated_at', table_name='zoho_tokens')
    op.drop_index('idx_zoho_tokens_expires_at', table_name='zoho_tokens')

    # Drop tables
    op.drop_table('token_refresh_audit')
    op.drop_table('zoho_tokens')
