"""Custom exceptions for Zoho SDK operations."""

from typing import Optional, Dict, Any


class ZohoBaseError(Exception):
    """Base exception for all Zoho-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize base error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """String representation of error."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class ZohoAuthError(ZohoBaseError):
    """Raised when OAuth authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: Optional[int] = 401,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize authentication error."""
        super().__init__(message, status_code, details)


class ZohoTokenError(ZohoBaseError):
    """Raised when token operations fail."""

    def __init__(
        self,
        message: str = "Token operation failed",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize token error."""
        super().__init__(message, status_code, details)


class ZohoAPIError(ZohoBaseError):
    """Raised when API calls fail."""

    def __init__(
        self,
        message: str = "API request failed",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize API error."""
        super().__init__(message, status_code, details)


class ZohoRateLimitError(ZohoAPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        self.retry_after = retry_after
        super().__init__(message, 429, details)

    def __str__(self) -> str:
        """String representation with retry info."""
        base = super().__str__()
        if self.retry_after:
            return f"{base} | Retry after: {self.retry_after}s"
        return base


class ZohoDatabaseError(ZohoBaseError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize database error."""
        super().__init__(message, None, details)


class ZohoConfigError(ZohoBaseError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str = "Invalid configuration",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize configuration error."""
        super().__init__(message, None, details)
