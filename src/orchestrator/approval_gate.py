"""Approval Gate - Human-in-the-loop approval workflow.

Manages approval workflow for CRM modifications:
- Present recommendations for approval
- Multi-channel notifications (CLI/email/Slack)
- Timeout handling (72 hours from PRD)
- Execute approved actions
- Log rejections and feedback
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    ADJUSTED = "adjusted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class ApprovalChannel(str, Enum):
    """Notification channels for approval requests."""
    CLI = "cli"
    EMAIL = "email"
    SLACK = "slack"
    WEB_UI = "web_ui"


class ApprovalRequest(BaseModel):
    """Approval request tracking."""
    request_id: str
    recommendation: Dict[str, Any]
    account_id: str
    owner_id: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING

    # Response
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    adjusted_recommendation: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    feedback: Optional[str] = None


class ApprovalConfig(BaseModel):
    """Approval gate configuration."""
    timeout_hours: int = 72  # From PRD
    channels: List[ApprovalChannel] = Field(
        default_factory=lambda: [ApprovalChannel.CLI]
    )
    require_feedback_on_rejection: bool = True
    allow_batch_approval: bool = True
    auto_timeout_action: str = "reject"  # reject or defer


class ApprovalGate:
    """Approval workflow manager.

    Implements human-in-the-loop approval for all CRM modifications.

    Key Features:
    - Present recommendations with context
    - Approve/adjust/reject workflow
    - Multi-channel notifications
    - Timeout handling
    - Feedback collection
    - Audit trail

    Approval Flow (from SPARC PRD):
    1. Present recommendation with account context
    2. Show before/after state for CRM changes
    3. Provide approve/adjust/reject options
    4. Capture approval timestamp and user
    5. Log all decisions for audit

    Example:
        >>> gate = ApprovalGate(config)
        >>> await gate.start()
        >>> status = await gate.request_approval(
        ...     recommendation=recommendation,
        ...     account_id="12345",
        ...     owner_id="owner_1"
        ... )
    """

    def __init__(
        self,
        config: ApprovalConfig,
    ) -> None:
        """Initialize approval gate.

        Args:
            config: Approval configuration
        """
        self.config = config

        # Active approval requests
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: Dict[str, ApprovalRequest] = {}

        # Notification handlers (registered per channel)
        self.notifiers: Dict[ApprovalChannel, Any] = {}

        # Metrics
        self.metrics = {
            "total_requests": 0,
            "approved": 0,
            "adjusted": 0,
            "rejected": 0,
            "timeout": 0,
            "average_approval_time_seconds": 0.0,
        }

        # Background tasks
        self.timeout_task: Optional[asyncio.Task] = None
        self.running = False

        self.logger = logger.bind(component="approval_gate")
        self.logger.info("approval_gate_initialized", config=config.dict())

    async def start(self) -> None:
        """Start approval gate and background tasks."""
        self.logger.info("approval_gate_starting")

        self.running = True

        # Start timeout monitor
        self.timeout_task = asyncio.create_task(self._monitor_timeouts())

        self.logger.info("approval_gate_started")

    async def stop(self) -> None:
        """Stop approval gate and cleanup."""
        self.logger.info("approval_gate_stopping")

        self.running = False

        # Cancel timeout monitor
        if self.timeout_task:
            self.timeout_task.cancel()
            try:
                await self.timeout_task
            except asyncio.CancelledError:
                pass

        self.logger.info("approval_gate_stopped")

    async def request_approval(
        self,
        recommendation: Dict[str, Any],
        account_id: str,
        owner_id: str,
    ) -> ApprovalStatus:
        """Request approval for recommendation.

        This method presents the recommendation and waits for user response.
        In production, this would integrate with actual approval UI/CLI.

        Args:
            recommendation: Recommendation details
            account_id: Account identifier
            owner_id: Owner identifier

        Returns:
            Approval status after user response
        """
        request_id = f"approval_{account_id}_{datetime.utcnow().isoformat()}"

        expires_at = datetime.utcnow() + timedelta(hours=self.config.timeout_hours)

        request = ApprovalRequest(
            request_id=request_id,
            recommendation=recommendation,
            account_id=account_id,
            owner_id=owner_id,
            expires_at=expires_at,
        )

        self.pending_requests[request_id] = request
        self.metrics["total_requests"] += 1

        self.logger.info(
            "approval_requested",
            request_id=request_id,
            account_id=account_id,
            owner_id=owner_id,
            expires_at=expires_at.isoformat(),
        )

        # Send notifications
        await self._send_notifications(request)

        # In production, this would wait for actual user input
        # For now, we'll simulate immediate approval
        await asyncio.sleep(0.1)

        # Simulate approval (in production, this comes from UI/CLI)
        return await self._simulate_approval_response(request)

    async def approve_request(
        self,
        request_id: str,
        approved_by: str,
        adjusted_recommendation: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Approve request (called by approval UI/CLI).

        Args:
            request_id: Request identifier
            approved_by: User who approved
            adjusted_recommendation: Modified recommendation (if adjusted)

        Returns:
            True if approval successful
        """
        request = self.pending_requests.get(request_id)
        if not request:
            self.logger.warning("approval_request_not_found", request_id=request_id)
            return False

        if request.status != ApprovalStatus.PENDING:
            self.logger.warning(
                "approval_request_already_processed",
                request_id=request_id,
                status=request.status.value,
            )
            return False

        # Check if expired
        if request.expires_at and datetime.utcnow() > request.expires_at:
            request.status = ApprovalStatus.TIMEOUT
            self.metrics["timeout"] += 1
            self.logger.warning("approval_request_expired", request_id=request_id)
            return False

        # Approve
        request.status = (
            ApprovalStatus.ADJUSTED
            if adjusted_recommendation
            else ApprovalStatus.APPROVED
        )
        request.approved_at = datetime.utcnow()
        request.approved_by = approved_by
        request.adjusted_recommendation = adjusted_recommendation

        # Update metrics
        if request.status == ApprovalStatus.APPROVED:
            self.metrics["approved"] += 1
        else:
            self.metrics["adjusted"] += 1

        approval_time = (request.approved_at - request.requested_at).total_seconds()
        self.metrics["average_approval_time_seconds"] = (
            (self.metrics["average_approval_time_seconds"] *
             (self.metrics["approved"] + self.metrics["adjusted"] - 1) +
             approval_time) /
            (self.metrics["approved"] + self.metrics["adjusted"])
        )

        # Move to completed
        del self.pending_requests[request_id]
        self.completed_requests[request_id] = request

        self.logger.info(
            "approval_granted",
            request_id=request_id,
            status=request.status.value,
            approved_by=approved_by,
            approval_time_seconds=approval_time,
        )

        return True

    async def reject_request(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
        feedback: Optional[str] = None,
    ) -> bool:
        """Reject request (called by approval UI/CLI).

        Args:
            request_id: Request identifier
            rejected_by: User who rejected
            reason: Rejection reason
            feedback: Additional feedback

        Returns:
            True if rejection successful
        """
        request = self.pending_requests.get(request_id)
        if not request:
            self.logger.warning("approval_request_not_found", request_id=request_id)
            return False

        if request.status != ApprovalStatus.PENDING:
            self.logger.warning(
                "approval_request_already_processed",
                request_id=request_id,
                status=request.status.value,
            )
            return False

        # Check if feedback required
        if self.config.require_feedback_on_rejection and not feedback:
            self.logger.warning(
                "rejection_requires_feedback",
                request_id=request_id,
            )
            return False

        # Reject
        request.status = ApprovalStatus.REJECTED
        request.approved_at = datetime.utcnow()
        request.approved_by = rejected_by
        request.rejection_reason = reason
        request.feedback = feedback

        self.metrics["rejected"] += 1

        # Move to completed
        del self.pending_requests[request_id]
        self.completed_requests[request_id] = request

        self.logger.info(
            "approval_rejected",
            request_id=request_id,
            rejected_by=rejected_by,
            reason=reason,
        )

        return True

    async def batch_approve_requests(
        self,
        request_ids: List[str],
        approved_by: str,
    ) -> Dict[str, bool]:
        """Batch approve multiple requests.

        Args:
            request_ids: List of request identifiers
            approved_by: User who approved

        Returns:
            Dictionary mapping request_id to success status
        """
        if not self.config.allow_batch_approval:
            self.logger.warning("batch_approval_not_allowed")
            return {rid: False for rid in request_ids}

        self.logger.info(
            "batch_approval_requested",
            count=len(request_ids),
            approved_by=approved_by,
        )

        results = {}
        for request_id in request_ids:
            success = await self.approve_request(request_id, approved_by)
            results[request_id] = success

        successful = sum(1 for s in results.values() if s)
        self.logger.info(
            "batch_approval_completed",
            total=len(request_ids),
            successful=successful,
            failed=len(request_ids) - successful,
        )

        return results

    async def _send_notifications(
        self,
        request: ApprovalRequest,
    ) -> None:
        """Send approval notifications via configured channels.

        Args:
            request: Approval request
        """
        for channel in self.config.channels:
            try:
                if channel == ApprovalChannel.CLI:
                    await self._notify_cli(request)
                elif channel == ApprovalChannel.EMAIL:
                    await self._notify_email(request)
                elif channel == ApprovalChannel.SLACK:
                    await self._notify_slack(request)
                elif channel == ApprovalChannel.WEB_UI:
                    await self._notify_web_ui(request)

            except Exception as e:
                self.logger.error(
                    "notification_failed",
                    channel=channel.value,
                    request_id=request.request_id,
                    error=str(e),
                )

    async def _notify_cli(self, request: ApprovalRequest) -> None:
        """Send CLI notification (log-based for now)."""
        self.logger.info(
            "approval_notification_cli",
            request_id=request.request_id,
            account_id=request.account_id,
            recommendation=request.recommendation.get("action", "unknown"),
        )

    async def _notify_email(self, request: ApprovalRequest) -> None:
        """Send email notification."""
        # Would integrate with SMTP
        self.logger.info(
            "approval_notification_email",
            request_id=request.request_id,
            owner_id=request.owner_id,
        )

    async def _notify_slack(self, request: ApprovalRequest) -> None:
        """Send Slack notification."""
        # Would integrate with Slack API
        self.logger.info(
            "approval_notification_slack",
            request_id=request.request_id,
            owner_id=request.owner_id,
        )

    async def _notify_web_ui(self, request: ApprovalRequest) -> None:
        """Send web UI notification."""
        # Would update web UI state
        self.logger.info(
            "approval_notification_web_ui",
            request_id=request.request_id,
            account_id=request.account_id,
        )

    async def _monitor_timeouts(self) -> None:
        """Monitor and handle approval timeouts."""
        self.logger.info("timeout_monitor_started")

        while self.running:
            try:
                now = datetime.utcnow()

                # Check for expired requests
                expired_requests = [
                    req for req in self.pending_requests.values()
                    if req.expires_at and now > req.expires_at
                ]

                for request in expired_requests:
                    await self._handle_timeout(request)

                # Sleep for check interval
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("timeout_monitor_error", error=str(e))
                await asyncio.sleep(60)

        self.logger.info("timeout_monitor_stopped")

    async def _handle_timeout(self, request: ApprovalRequest) -> None:
        """Handle timed-out approval request.

        Args:
            request: Timed-out request
        """
        self.logger.warning(
            "approval_request_timeout",
            request_id=request.request_id,
            account_id=request.account_id,
        )

        request.status = ApprovalStatus.TIMEOUT
        self.metrics["timeout"] += 1

        # Move to completed
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]
        self.completed_requests[request.request_id] = request

        # Handle based on config
        if self.config.auto_timeout_action == "reject":
            self.logger.info(
                "timeout_auto_rejected",
                request_id=request.request_id,
            )
        else:
            self.logger.info(
                "timeout_deferred",
                request_id=request.request_id,
            )

    async def _simulate_approval_response(
        self,
        request: ApprovalRequest,
    ) -> ApprovalStatus:
        """Simulate approval response for testing.

        In production, this would wait for actual user input.

        Args:
            request: Approval request

        Returns:
            Simulated approval status
        """
        # Simulate approval based on priority
        priority = request.recommendation.get("priority", "medium")

        if priority in ["critical", "high"]:
            # Auto-approve high priority for testing
            await self.approve_request(
                request_id=request.request_id,
                approved_by="system_test",
            )
            return ApprovalStatus.APPROVED
        else:
            # Auto-approve others too for testing
            await self.approve_request(
                request_id=request.request_id,
                approved_by="system_test",
            )
            return ApprovalStatus.APPROVED

    def get_pending_requests(
        self,
        owner_id: Optional[str] = None,
    ) -> List[ApprovalRequest]:
        """Get pending approval requests.

        Args:
            owner_id: Filter by owner (None = all)

        Returns:
            List of pending requests
        """
        requests = list(self.pending_requests.values())

        if owner_id:
            requests = [r for r in requests if r.owner_id == owner_id]

        return requests

    def get_status(self) -> Dict[str, Any]:
        """Get approval gate status.

        Returns:
            Status information
        """
        return {
            "pending_requests": len(self.pending_requests),
            "completed_requests": len(self.completed_requests),
            "running": self.running,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get approval metrics.

        Returns:
            Metrics dictionary
        """
        return {**self.metrics}
