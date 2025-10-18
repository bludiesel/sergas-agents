"""PostgreSQL-based token storage for Zoho OAuth tokens."""

import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import structlog

from src.integrations.zoho.exceptions import ZohoDatabaseError, ZohoTokenError

logger = structlog.get_logger(__name__)
Base = declarative_base()


class ZohoTokenModel(Base):
    """SQLAlchemy model for Zoho OAuth tokens."""

    __tablename__ = "zoho_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_type = Column(String(50), nullable=False, default="oauth", unique=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_zoho_tokens_expires_at", "expires_at"),
        Index("idx_zoho_tokens_token_type", "token_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of token
        """
        return {
            "id": self.id,
            "token_type": self.token_type,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_expired(self) -> bool:
        """Check if access token is expired.

        Returns:
            True if token is expired or expires within 5 minutes
        """
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (self.expires_at - buffer)


class TokenStore:
    """Thread-safe PostgreSQL token store for Zoho OAuth tokens."""

    def __init__(self, database_url: str) -> None:
        """Initialize token store.

        Args:
            database_url: PostgreSQL connection URL

        Raises:
            ZohoDatabaseError: If database connection fails
        """
        self._lock = threading.Lock()
        self.logger = logger.bind(component="TokenStore")

        try:
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("token_store_initialized", database_url=database_url)
        except Exception as e:
            self.logger.error("token_store_init_failed", error=str(e))
            raise ZohoDatabaseError(
                f"Failed to initialize token store: {str(e)}",
                details={"database_url": database_url}
            )

    def _get_session(self) -> Session:
        """Get database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    def save_token(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        token_type: str = "oauth",
    ) -> Dict[str, Any]:
        """Save or update OAuth token in database.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiration time in seconds
            token_type: Type of token (default: oauth)

        Returns:
            Dictionary representation of saved token

        Raises:
            ZohoDatabaseError: If database operation fails
        """
        with self._lock:
            session = self._get_session()
            try:
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                # Check if token exists
                token = session.query(ZohoTokenModel).filter_by(
                    token_type=token_type
                ).first()

                if token:
                    # Update existing token
                    token.access_token = access_token
                    token.refresh_token = refresh_token
                    token.expires_at = expires_at
                    token.updated_at = datetime.utcnow()
                    self.logger.info(
                        "token_updated",
                        token_type=token_type,
                        expires_at=expires_at.isoformat(),
                    )
                else:
                    # Create new token
                    token = ZohoTokenModel(
                        token_type=token_type,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_at=expires_at,
                    )
                    session.add(token)
                    self.logger.info(
                        "token_created",
                        token_type=token_type,
                        expires_at=expires_at.isoformat(),
                    )

                session.commit()
                result = token.to_dict()
                return result

            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error("save_token_failed", error=str(e), token_type=token_type)
                raise ZohoDatabaseError(
                    f"Failed to save token: {str(e)}",
                    details={"token_type": token_type}
                )
            finally:
                session.close()

    def get_token(self, token_type: str = "oauth") -> Optional[Dict[str, Any]]:
        """Retrieve OAuth token from database.

        Args:
            token_type: Type of token to retrieve

        Returns:
            Dictionary representation of token or None if not found

        Raises:
            ZohoDatabaseError: If database operation fails
        """
        with self._lock:
            session = self._get_session()
            try:
                token = session.query(ZohoTokenModel).filter_by(
                    token_type=token_type
                ).first()

                if not token:
                    self.logger.warning("token_not_found", token_type=token_type)
                    return None

                result = token.to_dict()
                self.logger.debug(
                    "token_retrieved",
                    token_type=token_type,
                    expired=token.is_expired(),
                )
                return result

            except SQLAlchemyError as e:
                self.logger.error("get_token_failed", error=str(e), token_type=token_type)
                raise ZohoDatabaseError(
                    f"Failed to retrieve token: {str(e)}",
                    details={"token_type": token_type}
                )
            finally:
                session.close()

    def is_token_expired(self, token_type: str = "oauth") -> bool:
        """Check if token is expired.

        Args:
            token_type: Type of token to check

        Returns:
            True if token is expired or not found

        Raises:
            ZohoDatabaseError: If database operation fails
        """
        session = self._get_session()
        try:
            token = session.query(ZohoTokenModel).filter_by(
                token_type=token_type
            ).first()

            if not token:
                return True

            return token.is_expired()

        except SQLAlchemyError as e:
            self.logger.error("check_expiry_failed", error=str(e), token_type=token_type)
            raise ZohoDatabaseError(
                f"Failed to check token expiration: {str(e)}",
                details={"token_type": token_type}
            )
        finally:
            session.close()

    def delete_token(self, token_type: str = "oauth") -> bool:
        """Delete token from database.

        Args:
            token_type: Type of token to delete

        Returns:
            True if token was deleted, False if not found

        Raises:
            ZohoDatabaseError: If database operation fails
        """
        with self._lock:
            session = self._get_session()
            try:
                token = session.query(ZohoTokenModel).filter_by(
                    token_type=token_type
                ).first()

                if not token:
                    self.logger.warning("delete_token_not_found", token_type=token_type)
                    return False

                session.delete(token)
                session.commit()
                self.logger.info("token_deleted", token_type=token_type)
                return True

            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error("delete_token_failed", error=str(e), token_type=token_type)
                raise ZohoDatabaseError(
                    f"Failed to delete token: {str(e)}",
                    details={"token_type": token_type}
                )
            finally:
                session.close()

    def cleanup_expired_tokens(self) -> int:
        """Remove all expired tokens from database.

        Returns:
            Number of tokens deleted

        Raises:
            ZohoDatabaseError: If database operation fails
        """
        with self._lock:
            session = self._get_session()
            try:
                count = session.query(ZohoTokenModel).filter(
                    ZohoTokenModel.expires_at <= datetime.utcnow()
                ).delete()
                session.commit()
                self.logger.info("expired_tokens_cleaned", count=count)
                return count

            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error("cleanup_failed", error=str(e))
                raise ZohoDatabaseError(f"Failed to cleanup expired tokens: {str(e)}")
            finally:
                session.close()
