"""Repository pattern for Zoho token persistence."""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.models import ZohoToken, TokenRefreshAudit
from src.db.config import get_db_session

logger = structlog.get_logger(__name__)


class TokenRepository:
    """Repository for managing Zoho OAuth tokens in the database.

    Implements the repository pattern for clean separation of data access logic.
    All methods are async and handle database transactions properly.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        """Initialize repository.

        Args:
            session: Optional database session. If not provided, uses context manager.
        """
        self._session = session
        self._owns_session = session is None

    async def save_token(
        self,
        token_type: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> ZohoToken:
        """Save or update a Zoho OAuth token.

        Args:
            token_type: Type of token (e.g., 'oauth')
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token lifetime in seconds

        Returns:
            ZohoToken: Saved token record

        Raises:
            Exception: If database operation fails
        """
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        if self._owns_session:
            async with get_db_session() as session:
                return await self._save_token_impl(
                    session, token_type, access_token, refresh_token, expires_at
                )
        else:
            return await self._save_token_impl(
                self._session, token_type, access_token, refresh_token, expires_at
            )

    async def _save_token_impl(
        self,
        session: AsyncSession,
        token_type: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
    ) -> ZohoToken:
        """Internal implementation of save_token."""
        try:
            # Check if token already exists
            stmt = select(ZohoToken).where(ZohoToken.token_type == token_type)
            result = await session.execute(stmt)
            existing_token = result.scalar_one_or_none()

            if existing_token:
                # Update existing token
                existing_token.access_token = access_token
                existing_token.refresh_token = refresh_token
                existing_token.expires_at = expires_at
                existing_token.updated_at = datetime.now(timezone.utc)
                token = existing_token
                logger.info(
                    "Updated existing token",
                    token_id=token.id,
                    token_type=token_type,
                    expires_at=expires_at,
                )
            else:
                # Create new token
                token = ZohoToken(
                    token_type=token_type,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                )
                session.add(token)
                logger.info(
                    "Created new token",
                    token_type=token_type,
                    expires_at=expires_at,
                )

            await session.flush()
            return token

        except Exception as e:
            logger.error("Failed to save token", error=str(e), token_type=token_type)
            raise

    async def get_latest_token(
        self, token_type: str = "oauth"
    ) -> Optional[ZohoToken]:
        """Retrieve the latest token of specified type.

        Args:
            token_type: Type of token to retrieve

        Returns:
            ZohoToken or None: Latest token record if exists
        """
        if self._owns_session:
            async with get_db_session() as session:
                return await self._get_latest_token_impl(session, token_type)
        else:
            return await self._get_latest_token_impl(self._session, token_type)

    async def _get_latest_token_impl(
        self, session: AsyncSession, token_type: str
    ) -> Optional[ZohoToken]:
        """Internal implementation of get_latest_token."""
        try:
            stmt = (
                select(ZohoToken)
                .where(ZohoToken.token_type == token_type)
                .order_by(ZohoToken.updated_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            token = result.scalar_one_or_none()

            if token:
                logger.debug(
                    "Retrieved token",
                    token_id=token.id,
                    token_type=token_type,
                    expires_at=token.expires_at,
                    is_expired=token.is_expired(),
                )
            else:
                logger.debug("No token found", token_type=token_type)

            return token

        except Exception as e:
            logger.error(
                "Failed to retrieve token", error=str(e), token_type=token_type
            )
            raise

    def is_token_expired(self, token: ZohoToken) -> bool:
        """Check if a token is expired.

        Args:
            token: Token to check

        Returns:
            bool: True if token is expired or expiring soon
        """
        return token.is_expired()

    async def refresh_token_record(
        self,
        token_id: int,
        new_access_token: str,
        new_expires_in: int,
        new_refresh_token: Optional[str] = None,
    ) -> ZohoToken:
        """Update token record after refresh operation.

        Args:
            token_id: ID of token to update
            new_access_token: New access token
            new_expires_in: New token lifetime in seconds
            new_refresh_token: New refresh token (if provided by API)

        Returns:
            ZohoToken: Updated token record

        Raises:
            ValueError: If token not found
        """
        if self._owns_session:
            async with get_db_session() as session:
                return await self._refresh_token_impl(
                    session, token_id, new_access_token, new_expires_in, new_refresh_token
                )
        else:
            return await self._refresh_token_impl(
                self._session, token_id, new_access_token, new_expires_in, new_refresh_token
            )

    async def _refresh_token_impl(
        self,
        session: AsyncSession,
        token_id: int,
        new_access_token: str,
        new_expires_in: int,
        new_refresh_token: Optional[str],
    ) -> ZohoToken:
        """Internal implementation of refresh_token_record."""
        try:
            # Get existing token
            stmt = select(ZohoToken).where(ZohoToken.id == token_id)
            result = await session.execute(stmt)
            token = result.scalar_one_or_none()

            if not token:
                raise ValueError(f"Token with ID {token_id} not found")

            # Store old expiration for audit
            old_expires_at = token.expires_at
            new_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=new_expires_in
            )

            # Update token
            token.access_token = new_access_token
            token.expires_at = new_expires_at
            token.updated_at = datetime.now(timezone.utc)

            if new_refresh_token:
                token.refresh_token = new_refresh_token

            # Create audit record
            audit = TokenRefreshAudit(
                token_id=token_id,
                token_type=token.token_type,
                previous_expires_at=old_expires_at,
                new_expires_at=new_expires_at,
                success=True,
            )
            session.add(audit)

            await session.flush()

            logger.info(
                "Token refreshed successfully",
                token_id=token_id,
                old_expires_at=old_expires_at,
                new_expires_at=new_expires_at,
            )

            return token

        except Exception as e:
            # Log failed refresh attempt
            audit = TokenRefreshAudit(
                token_id=token_id,
                token_type="unknown",
                success=False,
                error_message=str(e),
            )
            session.add(audit)
            await session.flush()

            logger.error("Failed to refresh token", error=str(e), token_id=token_id)
            raise

    async def delete_token(self, token_type: str) -> bool:
        """Delete a token by type.

        Args:
            token_type: Type of token to delete

        Returns:
            bool: True if token was deleted, False if not found
        """
        if self._owns_session:
            async with get_db_session() as session:
                return await self._delete_token_impl(session, token_type)
        else:
            return await self._delete_token_impl(self._session, token_type)

    async def _delete_token_impl(
        self, session: AsyncSession, token_type: str
    ) -> bool:
        """Internal implementation of delete_token."""
        try:
            stmt = delete(ZohoToken).where(ZohoToken.token_type == token_type)
            result = await session.execute(stmt)
            deleted = result.rowcount > 0

            if deleted:
                logger.info("Token deleted", token_type=token_type)
            else:
                logger.debug("No token to delete", token_type=token_type)

            return deleted

        except Exception as e:
            logger.error("Failed to delete token", error=str(e), token_type=token_type)
            raise

    async def get_token_as_dict(self, token_type: str = "oauth") -> Optional[Dict[str, Any]]:
        """Get token as dictionary for SDK compatibility.

        Args:
            token_type: Type of token to retrieve

        Returns:
            Dict or None: Token data as dictionary
        """
        token = await self.get_latest_token(token_type)
        if not token:
            return None

        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at.isoformat(),
            "expires_in": int((token.expires_at - datetime.now(timezone.utc)).total_seconds()),
            "token_type": token.token_type,
        }
