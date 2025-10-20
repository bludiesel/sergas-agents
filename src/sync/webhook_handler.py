"""Zoho webhook receiver with FastAPI endpoints and security verification.

Handles incoming webhook events from Zoho CRM with:
- Webhook signature verification
- Event parsing and routing
- Deduplication logic
- Async processing with Redis queue
"""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


class WebhookEvent(BaseModel):
    """Zoho webhook event model."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (create, update, delete)")
    module: str = Field(..., description="Zoho module (Accounts, Contacts, etc)")
    record_id: str = Field(..., description="Record identifier")
    record_data: Dict[str, Any] = Field(default_factory=dict, description="Record data")
    modified_fields: List[str] = Field(default_factory=list, description="Modified fields")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User who triggered event")

    @validator('event_type')
    def validate_event_type(cls, v):
        """Validate event type."""
        allowed = {'create', 'update', 'delete', 'restore'}
        if v not in allowed:
            raise ValueError(f"Event type must be one of {allowed}")
        return v

    @validator('module')
    def validate_module(cls, v):
        """Validate module name."""
        allowed = {'Accounts', 'Contacts', 'Deals', 'Tasks', 'Notes', 'Activities'}
        if v not in allowed:
            raise ValueError(f"Module must be one of {allowed}")
        return v


class WebhookResponse(BaseModel):
    """Standard webhook response."""

    status: str = Field(..., description="Response status")
    event_id: str = Field(..., description="Event identifier")
    message: str = Field(..., description="Response message")
    queued: bool = Field(..., description="Whether event was queued for processing")


class WebhookHandler:
    """FastAPI webhook handler for Zoho CRM events.

    Features:
    - Webhook signature verification using HMAC-SHA256
    - Event deduplication using Redis
    - Async event queueing
    - Comprehensive error handling
    - Request validation and sanitization

    Example:
        >>> app = FastAPI()
        >>> handler = WebhookHandler(redis_client, secret_key)
        >>> handler.register_routes(app)
        >>> # Webhooks available at /webhooks/zoho
    """

    def __init__(
        self,
        redis_client: Redis,
        webhook_secret: str,
        event_ttl: int = 3600,
        max_queue_size: int = 10000
    ):
        """Initialize webhook handler.

        Args:
            redis_client: Redis client for queue and deduplication
            webhook_secret: Secret key for webhook verification
            event_ttl: Event deduplication TTL in seconds (default: 1 hour)
            max_queue_size: Maximum events in queue
        """
        self.redis = redis_client
        self.webhook_secret = webhook_secret.encode('utf-8')
        self.event_ttl = event_ttl
        self.max_queue_size = max_queue_size
        self.logger = logger.bind(component="webhook_handler")

        # Metrics
        self._metrics = {
            "total_events": 0,
            "verified_events": 0,
            "rejected_events": 0,
            "duplicated_events": 0,
            "queued_events": 0,
            "failed_events": 0
        }

    def register_routes(self, app: FastAPI) -> None:
        """Register webhook routes with FastAPI app.

        Args:
            app: FastAPI application instance
        """

        @app.post("/webhooks/zoho", response_model=WebhookResponse)
        async def receive_webhook(
            request: Request,
            x_zoho_signature: Optional[str] = Header(None),
            x_zoho_event_id: Optional[str] = Header(None)
        ):
            """Receive and process Zoho webhook event.

            Headers:
                X-Zoho-Signature: HMAC-SHA256 signature of request body
                X-Zoho-Event-Id: Unique event identifier

            Returns:
                WebhookResponse with processing status
            """
            return await self.handle_webhook(request, x_zoho_signature, x_zoho_event_id)

        @app.get("/webhooks/health")
        async def webhook_health():
            """Webhook system health check.

            Returns:
                Health status and metrics
            """
            return await self.get_health_status()

        @app.get("/webhooks/metrics")
        async def webhook_metrics():
            """Get webhook processing metrics.

            Returns:
                Processing metrics and statistics
            """
            return await self.get_metrics()

    async def handle_webhook(
        self,
        request: Request,
        signature: Optional[str],
        event_id: Optional[str]
    ) -> WebhookResponse:
        """Handle incoming webhook request.

        Args:
            request: FastAPI request object
            signature: Webhook signature from header
            event_id: Event ID from header

        Returns:
            WebhookResponse with processing status

        Raises:
            HTTPException: If verification fails or processing error occurs
        """
        self._metrics["total_events"] += 1

        try:
            # Read request body
            body = await request.body()
            body_str = body.decode('utf-8')

            self.logger.info(
                "webhook_received",
                event_id=event_id,
                content_length=len(body)
            )

            # Verify webhook signature
            if not await self._verify_signature(body, signature):
                self._metrics["rejected_events"] += 1
                self.logger.warning(
                    "webhook_signature_verification_failed",
                    event_id=event_id
                )
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )

            self._metrics["verified_events"] += 1

            # Parse webhook payload
            try:
                payload = json.loads(body_str)
            except json.JSONDecodeError as e:
                self.logger.error("webhook_json_parse_failed", error=str(e))
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON payload"
                )

            # Extract event data
            event = await self._parse_event(payload, event_id)

            # Check for duplicate
            if await self._is_duplicate(event.event_id):
                self._metrics["duplicated_events"] += 1
                self.logger.info("webhook_duplicate_detected", event_id=event.event_id)
                return WebhookResponse(
                    status="duplicate",
                    event_id=event.event_id,
                    message="Event already processed",
                    queued=False
                )

            # Queue event for processing
            queued = await self._queue_event(event)

            if queued:
                self._metrics["queued_events"] += 1
                self.logger.info("webhook_event_queued", event_id=event.event_id)
                return WebhookResponse(
                    status="accepted",
                    event_id=event.event_id,
                    message="Event queued for processing",
                    queued=True
                )
            else:
                self._metrics["failed_events"] += 1
                raise HTTPException(
                    status_code=503,
                    detail="Queue full or unavailable"
                )

        except HTTPException:
            raise
        except Exception as e:
            self._metrics["failed_events"] += 1
            self.logger.error("webhook_processing_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Internal processing error: {str(e)}"
            )

    async def _verify_signature(
        self,
        body: bytes,
        signature: Optional[str]
    ) -> bool:
        """Verify webhook signature using HMAC-SHA256.

        Args:
            body: Request body bytes
            signature: Signature from X-Zoho-Signature header

        Returns:
            True if signature is valid
        """
        if not signature:
            self.logger.warning("webhook_missing_signature")
            return False

        # Compute expected signature
        expected = hmac.new(
            self.webhook_secret,
            body,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected)

    async def _parse_event(
        self,
        payload: Dict[str, Any],
        event_id: Optional[str]
    ) -> WebhookEvent:
        """Parse webhook payload into WebhookEvent.

        Args:
            payload: Webhook JSON payload
            event_id: Event ID from header (fallback to generated)

        Returns:
            Parsed WebhookEvent
        """
        # Handle different Zoho webhook formats
        if 'data' in payload:
            # Zoho CRM v2/v3 format
            data = payload['data']
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            return WebhookEvent(
                event_id=event_id or str(uuid4()),
                event_type=payload.get('operation', 'update').lower(),
                module=payload.get('module', 'Accounts'),
                record_id=data.get('id', ''),
                record_data=data,
                modified_fields=payload.get('modified_fields', []),
                timestamp=datetime.utcnow(),
                user_id=payload.get('user', {}).get('id')
            )
        else:
            # Generic format
            return WebhookEvent(
                event_id=event_id or str(uuid4()),
                event_type=payload.get('event_type', 'update'),
                module=payload.get('module', 'Accounts'),
                record_id=payload.get('record_id', ''),
                record_data=payload.get('record_data', {}),
                modified_fields=payload.get('modified_fields', []),
                timestamp=datetime.utcnow(),
                user_id=payload.get('user_id')
            )

    async def _is_duplicate(self, event_id: str) -> bool:
        """Check if event has already been processed.

        Uses Redis SET with TTL for deduplication.

        Args:
            event_id: Event identifier

        Returns:
            True if duplicate
        """
        key = f"webhook:processed:{event_id}"

        # Try to set key with NX (only if not exists)
        result = await self.redis.set(
            key,
            "1",
            nx=True,
            ex=self.event_ttl
        )

        # If set() returns None, key already existed (duplicate)
        return result is None

    async def _queue_event(self, event: WebhookEvent) -> bool:
        """Queue event for async processing.

        Args:
            event: WebhookEvent to queue

        Returns:
            True if queued successfully
        """
        try:
            # Check queue size
            queue_size = await self.redis.llen("webhook:queue")
            if queue_size >= self.max_queue_size:
                self.logger.warning(
                    "webhook_queue_full",
                    queue_size=queue_size,
                    max_size=self.max_queue_size
                )
                return False

            # Serialize event
            event_json = json.dumps({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "module": event.module,
                "record_id": event.record_id,
                "record_data": event.record_data,
                "modified_fields": event.modified_fields,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id
            })

            # Push to queue (LPUSH for FIFO with BRPOP)
            await self.redis.lpush("webhook:queue", event_json)

            # Publish notification for processors
            await self.redis.publish("webhook:events", event_json)

            return True

        except Exception as e:
            self.logger.error("event_queue_failed", error=str(e))
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """Get webhook system health status.

        Returns:
            Health status dict
        """
        try:
            # Check Redis connectivity
            await self.redis.ping()
            redis_healthy = True
        except Exception as e:
            self.logger.error("redis_health_check_failed", error=str(e))
            redis_healthy = False

        # Get queue size
        try:
            queue_size = await self.redis.llen("webhook:queue")
        except Exception:
            queue_size = -1

        return {
            "status": "healthy" if redis_healthy else "unhealthy",
            "redis_connected": redis_healthy,
            "queue_size": queue_size,
            "queue_capacity": self.max_queue_size,
            "queue_utilization": (
                f"{(queue_size / self.max_queue_size * 100):.1f}%"
                if queue_size >= 0 else "unknown"
            ),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get webhook processing metrics.

        Returns:
            Metrics dict
        """
        try:
            queue_size = await self.redis.llen("webhook:queue")
        except Exception:
            queue_size = -1

        return {
            **self._metrics,
            "current_queue_size": queue_size,
            "acceptance_rate": (
                f"{(self._metrics['verified_events'] / self._metrics['total_events'] * 100):.1f}%"
                if self._metrics['total_events'] > 0 else "0.0%"
            ),
            "deduplication_rate": (
                f"{(self._metrics['duplicated_events'] / self._metrics['total_events'] * 100):.1f}%"
                if self._metrics['total_events'] > 0 else "0.0%"
            ),
            "timestamp": datetime.utcnow().isoformat()
        }
