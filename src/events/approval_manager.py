"""Approval workflow manager for recommendation approvals.

Handles approval request/response flow with timeout and state management.
"""

import asyncio
import uuid
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Literal
from enum import Enum

logger = structlog.get_logger(__name__)


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"


class ApprovalRequest:
    """Represents an approval request."""

    def __init__(
        self,
        recommendation_id: str,
        recommendation: Dict[str, Any],
        run_id: str,
        timeout_seconds: int = 300
    ):
        """Initialize approval request.

        Args:
            recommendation_id: Recommendation being approved
            recommendation: Full recommendation data
            run_id: Workflow run identifier
            timeout_seconds: Timeout for response (default 5 minutes)
        """
        self.approval_id = f"approval_{uuid.uuid4().hex[:8]}"
        self.recommendation_id = recommendation_id
        self.recommendation = recommendation
        self.run_id = run_id
        self.timeout_seconds = timeout_seconds

        self.status = ApprovalStatus.PENDING
        self.action: Optional[Literal["approve", "reject", "modify"]] = None
        self.modified_data: Optional[Dict[str, Any]] = None
        self.reason: Optional[str] = None
        self.approved_by: Optional[str] = None

        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=timeout_seconds)
        self.responded_at: Optional[datetime] = None

        # Asyncio event for response notification
        self._response_event = asyncio.Event()

    def is_expired(self) -> bool:
        """Check if approval request has expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def set_response(
        self,
        action: Literal["approve", "reject", "modify"],
        modified_data: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        approved_by: Optional[str] = None
    ):
        """Set approval response.

        Args:
            action: User action (approve, reject, modify)
            modified_data: Modified recommendation data (for modify action)
            reason: User's reason for decision
            approved_by: User who responded
        """
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval already {self.status}")

        if self.is_expired():
            raise ValueError("Approval request expired")

        self.action = action
        self.modified_data = modified_data
        self.reason = reason
        self.approved_by = approved_by
        self.responded_at = datetime.utcnow()

        # Update status based on action
        if action == "approve":
            self.status = ApprovalStatus.APPROVED
        elif action == "reject":
            self.status = ApprovalStatus.REJECTED
        elif action == "modify":
            self.status = ApprovalStatus.MODIFIED

        # Notify waiters
        self._response_event.set()

        logger.info(
            "approval_response_received",
            approval_id=self.approval_id,
            action=action,
            status=self.status.value
        )

    async def wait_for_response(self, timeout: Optional[float] = None) -> bool:
        """Wait for approval response.

        Args:
            timeout: Optional timeout in seconds (defaults to request timeout)

        Returns:
            True if response received, False if timeout
        """
        timeout = timeout or self.timeout_seconds

        try:
            await asyncio.wait_for(self._response_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            self.status = ApprovalStatus.TIMEOUT
            logger.warning(
                "approval_timeout",
                approval_id=self.approval_id,
                recommendation_id=self.recommendation_id
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert approval request to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "approval_id": self.approval_id,
            "recommendation_id": self.recommendation_id,
            "recommendation": self.recommendation,
            "run_id": self.run_id,
            "status": self.status.value,
            "action": self.action,
            "modified_data": self.modified_data,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "timeout_seconds": self.timeout_seconds
        }


class ApprovalManager:
    """Manages approval requests and responses.

    Thread-safe approval workflow coordinator.
    """

    def __init__(self):
        """Initialize approval manager."""
        self.logger = logger.bind(component="approval_manager")
        self._active_approvals: Dict[str, ApprovalRequest] = {}
        self._lock = asyncio.Lock()

    async def create_approval_request(
        self,
        recommendation_id: str,
        recommendation: Dict[str, Any],
        run_id: str,
        timeout_seconds: int = 300
    ) -> ApprovalRequest:
        """Create new approval request.

        Args:
            recommendation_id: Recommendation being approved
            recommendation: Full recommendation data
            run_id: Workflow run identifier
            timeout_seconds: Timeout for response

        Returns:
            ApprovalRequest object
        """
        approval = ApprovalRequest(
            recommendation_id=recommendation_id,
            recommendation=recommendation,
            run_id=run_id,
            timeout_seconds=timeout_seconds
        )

        async with self._lock:
            self._active_approvals[approval.approval_id] = approval

        self.logger.info(
            "approval_request_created",
            approval_id=approval.approval_id,
            recommendation_id=recommendation_id,
            timeout_seconds=timeout_seconds
        )

        return approval

    async def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID.

        Args:
            approval_id: Approval request ID

        Returns:
            ApprovalRequest or None if not found
        """
        async with self._lock:
            return self._active_approvals.get(approval_id)

    async def respond_to_approval(
        self,
        approval_id: str,
        action: Literal["approve", "reject", "modify"],
        modified_data: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> ApprovalRequest:
        """Respond to approval request.

        Args:
            approval_id: Approval request ID
            action: User action (approve, reject, modify)
            modified_data: Modified recommendation data (for modify action)
            reason: User's reason for decision
            approved_by: User who responded

        Returns:
            Updated ApprovalRequest

        Raises:
            ValueError: If approval not found or already responded
        """
        approval = await self.get_approval_request(approval_id)

        if not approval:
            raise ValueError(f"Approval request {approval_id} not found")

        approval.set_response(
            action=action,
            modified_data=modified_data,
            reason=reason,
            approved_by=approved_by
        )

        return approval

    async def cleanup_expired(self):
        """Remove expired approval requests from memory."""
        async with self._lock:
            expired_ids = [
                approval_id
                for approval_id, approval in self._active_approvals.items()
                if approval.is_expired() and approval.status == ApprovalStatus.PENDING
            ]

            for approval_id in expired_ids:
                approval = self._active_approvals[approval_id]
                approval.status = ApprovalStatus.TIMEOUT
                del self._active_approvals[approval_id]

            if expired_ids:
                self.logger.info(
                    "expired_approvals_cleaned",
                    count=len(expired_ids)
                )

    async def get_active_count(self) -> int:
        """Get count of active approval requests.

        Returns:
            Number of pending approvals
        """
        async with self._lock:
            return len([
                a for a in self._active_approvals.values()
                if a.status == ApprovalStatus.PENDING
            ])


# Singleton instance
approval_manager = ApprovalManager()
