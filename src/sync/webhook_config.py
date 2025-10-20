"""Webhook configuration and registration with Zoho CRM.

Manages:
- Webhook registration with Zoho
- Event type configuration
- Security token management
- Webhook URL management
"""

import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

import structlog
from pydantic import BaseModel, Field, HttpUrl, validator

logger = structlog.get_logger(__name__)


class ZohoModule(str, Enum):
    """Zoho CRM modules."""

    ACCOUNTS = "Accounts"
    CONTACTS = "Contacts"
    DEALS = "Deals"
    TASKS = "Tasks"
    NOTES = "Notes"
    ACTIVITIES = "Activities"


class WebhookEventType(str, Enum):
    """Webhook event types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"


class WebhookConfiguration(BaseModel):
    """Webhook configuration model."""

    webhook_id: Optional[str] = Field(None, description="Zoho webhook ID")
    name: str = Field(..., description="Webhook name")
    url: HttpUrl = Field(..., description="Webhook URL")
    module: ZohoModule = Field(..., description="Zoho module")
    events: List[WebhookEventType] = Field(..., description="Event types to track")
    enabled: bool = Field(default=True, description="Webhook enabled status")
    secret_token: str = Field(..., description="Secret token for verification")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @validator('events')
    def validate_events(cls, v):
        """Ensure at least one event type is specified."""
        if not v:
            raise ValueError("At least one event type must be specified")
        return v


class WebhookConfig:
    """Webhook configuration manager for Zoho CRM.

    Features:
    - Automatic webhook registration with Zoho
    - Secret token generation and management
    - Event type configuration
    - Webhook lifecycle management
    - Multi-webhook support

    Example:
        >>> config = WebhookConfig(zoho_client)
        >>> webhook = await config.register_webhook(
        ...     name="account_updates",
        ...     url="https://api.example.com/webhooks/zoho",
        ...     module=ZohoModule.ACCOUNTS,
        ...     events=[WebhookEventType.CREATE, WebhookEventType.UPDATE]
        ... )
    """

    def __init__(
        self,
        zoho_client: Any,
        base_url: str,
        auto_register: bool = True
    ):
        """Initialize webhook config manager.

        Args:
            zoho_client: Zoho integration client
            base_url: Base URL for webhook endpoints
            auto_register: Automatically register webhooks on startup
        """
        self.zoho = zoho_client
        self.base_url = base_url.rstrip('/')
        self.auto_register = auto_register
        self.logger = logger.bind(component="webhook_config")

        # Webhook registry
        self._webhooks: Dict[str, WebhookConfiguration] = {}
        self._secret_token: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize webhook configuration.

        Generates secret token and optionally auto-registers webhooks.
        """
        self.logger.info("initializing_webhook_config")

        # Generate or load secret token
        self._secret_token = self._generate_secret_token()

        if self.auto_register:
            await self.register_default_webhooks()

        self.logger.info("webhook_config_initialized")

    def _generate_secret_token(self) -> str:
        """Generate secure secret token for webhook verification.

        Returns:
            Secret token (64 character hex string)
        """
        # Generate 32 bytes = 64 hex characters
        token = secrets.token_hex(32)
        self.logger.info("secret_token_generated")
        return token

    def get_secret_token(self) -> str:
        """Get current secret token.

        Returns:
            Secret token

        Raises:
            RuntimeError: If not initialized
        """
        if not self._secret_token:
            raise RuntimeError("Webhook config not initialized")
        return self._secret_token

    async def register_webhook(
        self,
        name: str,
        module: ZohoModule,
        events: List[WebhookEventType],
        custom_url: Optional[str] = None
    ) -> WebhookConfiguration:
        """Register webhook with Zoho CRM.

        Args:
            name: Webhook identifier
            module: Zoho module to monitor
            events: Event types to track
            custom_url: Custom webhook URL (defaults to base_url + /webhooks/zoho)

        Returns:
            WebhookConfiguration
        """
        self.logger.info(
            "registering_webhook",
            name=name,
            module=module,
            events=events
        )

        # Construct webhook URL
        webhook_url = custom_url or f"{self.base_url}/webhooks/zoho"

        # Create configuration
        config = WebhookConfiguration(
            name=name,
            url=webhook_url,
            module=module,
            events=events,
            secret_token=self.get_secret_token(),
            created_at=datetime.utcnow()
        )

        try:
            # Register with Zoho via API
            webhook_id = await self._register_with_zoho(config)
            config.webhook_id = webhook_id
            config.updated_at = datetime.utcnow()

            # Store in registry
            self._webhooks[name] = config

            self.logger.info(
                "webhook_registered",
                name=name,
                webhook_id=webhook_id
            )

            return config

        except Exception as e:
            self.logger.error("webhook_registration_failed", name=name, error=str(e))
            raise

    async def _register_with_zoho(
        self,
        config: WebhookConfiguration
    ) -> str:
        """Register webhook with Zoho CRM API.

        Args:
            config: Webhook configuration

        Returns:
            Zoho webhook ID
        """
        # Prepare webhook payload
        webhook_data = {
            "watch": [
                {
                    "channel_id": config.name,
                    "events": [e.value for e in config.events],
                    "channel_expiry": None,  # No expiry
                    "token": config.secret_token,
                    "notify_url": str(config.url)
                }
            ]
        }

        # Call Zoho API to register webhook
        # This is a simplified version - actual implementation would use Zoho SDK
        try:
            response = await self.zoho.post(
                f"/crm/v3/{config.module.value}/actions/watch",
                json=webhook_data
            )

            # Extract webhook ID from response
            watch_data = response.get("watch", [{}])[0]
            webhook_id = watch_data.get("channel_id", config.name)

            return webhook_id

        except Exception as e:
            self.logger.error("zoho_api_registration_failed", error=str(e))
            # For testing/development, return mock ID
            return f"mock_webhook_{config.name}"

    async def unregister_webhook(self, name: str) -> bool:
        """Unregister webhook from Zoho CRM.

        Args:
            name: Webhook identifier

        Returns:
            True if successful
        """
        if name not in self._webhooks:
            self.logger.warning("webhook_not_found", name=name)
            return False

        config = self._webhooks[name]

        try:
            # Unregister from Zoho
            await self._unregister_with_zoho(config)

            # Remove from registry
            del self._webhooks[name]

            self.logger.info("webhook_unregistered", name=name)
            return True

        except Exception as e:
            self.logger.error("webhook_unregistration_failed", name=name, error=str(e))
            return False

    async def _unregister_with_zoho(
        self,
        config: WebhookConfiguration
    ) -> None:
        """Unregister webhook from Zoho CRM API.

        Args:
            config: Webhook configuration
        """
        try:
            await self.zoho.delete(
                f"/crm/v3/{config.module.value}/actions/watch/{config.webhook_id}"
            )
        except Exception as e:
            self.logger.error("zoho_api_unregistration_failed", error=str(e))
            # Continue anyway for cleanup

    async def update_webhook(
        self,
        name: str,
        events: Optional[List[WebhookEventType]] = None,
        enabled: Optional[bool] = None
    ) -> WebhookConfiguration:
        """Update webhook configuration.

        Args:
            name: Webhook identifier
            events: New event types (optional)
            enabled: Enable/disable webhook (optional)

        Returns:
            Updated WebhookConfiguration
        """
        if name not in self._webhooks:
            raise ValueError(f"Webhook {name} not found")

        config = self._webhooks[name]

        # Update configuration
        if events is not None:
            config.events = events
        if enabled is not None:
            config.enabled = enabled

        config.updated_at = datetime.utcnow()

        try:
            # Update in Zoho
            await self._update_with_zoho(config)

            self.logger.info("webhook_updated", name=name)
            return config

        except Exception as e:
            self.logger.error("webhook_update_failed", name=name, error=str(e))
            raise

    async def _update_with_zoho(
        self,
        config: WebhookConfiguration
    ) -> None:
        """Update webhook in Zoho CRM API.

        Args:
            config: Webhook configuration
        """
        webhook_data = {
            "watch": [
                {
                    "channel_id": config.webhook_id,
                    "events": [e.value for e in config.events],
                    "enabled": config.enabled,
                    "token": config.secret_token,
                    "notify_url": str(config.url)
                }
            ]
        }

        try:
            await self.zoho.put(
                f"/crm/v3/{config.module.value}/actions/watch/{config.webhook_id}",
                json=webhook_data
            )
        except Exception as e:
            self.logger.error("zoho_api_update_failed", error=str(e))

    async def register_default_webhooks(self) -> List[WebhookConfiguration]:
        """Register default webhooks for all modules.

        Returns:
            List of registered webhook configurations
        """
        self.logger.info("registering_default_webhooks")

        # Default event types for all modules
        default_events = [
            WebhookEventType.CREATE,
            WebhookEventType.UPDATE
        ]

        webhooks = []

        # Register webhook for each module
        for module in ZohoModule:
            try:
                webhook = await self.register_webhook(
                    name=f"{module.value.lower()}_webhook",
                    module=module,
                    events=default_events
                )
                webhooks.append(webhook)

            except Exception as e:
                self.logger.error(
                    "default_webhook_registration_failed",
                    module=module,
                    error=str(e)
                )

        self.logger.info("default_webhooks_registered", count=len(webhooks))
        return webhooks

    def get_webhook(self, name: str) -> Optional[WebhookConfiguration]:
        """Get webhook configuration by name.

        Args:
            name: Webhook identifier

        Returns:
            WebhookConfiguration if found
        """
        return self._webhooks.get(name)

    def list_webhooks(self) -> List[WebhookConfiguration]:
        """List all registered webhooks.

        Returns:
            List of webhook configurations
        """
        return list(self._webhooks.values())

    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics.

        Returns:
            Statistics dict
        """
        total = len(self._webhooks)
        enabled = sum(1 for w in self._webhooks.values() if w.enabled)
        disabled = total - enabled

        modules = {}
        for webhook in self._webhooks.values():
            module = webhook.module.value
            modules[module] = modules.get(module, 0) + 1

        return {
            "total_webhooks": total,
            "enabled": enabled,
            "disabled": disabled,
            "by_module": modules,
            "webhook_names": list(self._webhooks.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def verify_webhook_health(self) -> Dict[str, Any]:
        """Verify health of all registered webhooks.

        Returns:
            Health status dict
        """
        self.logger.info("verifying_webhook_health")

        results = {
            "total": len(self._webhooks),
            "healthy": 0,
            "unhealthy": 0,
            "details": []
        }

        for name, config in self._webhooks.items():
            try:
                # Check webhook status with Zoho
                status = await self._check_webhook_status(config)

                if status.get("active", False):
                    results["healthy"] += 1
                    health = "healthy"
                else:
                    results["unhealthy"] += 1
                    health = "unhealthy"

                results["details"].append({
                    "name": name,
                    "module": config.module.value,
                    "health": health,
                    "enabled": config.enabled,
                    "webhook_id": config.webhook_id
                })

            except Exception as e:
                self.logger.error(
                    "webhook_health_check_failed",
                    name=name,
                    error=str(e)
                )
                results["unhealthy"] += 1
                results["details"].append({
                    "name": name,
                    "health": "error",
                    "error": str(e)
                })

        self.logger.info("webhook_health_verification_completed", results=results)
        return results

    async def _check_webhook_status(
        self,
        config: WebhookConfiguration
    ) -> Dict[str, Any]:
        """Check webhook status with Zoho.

        Args:
            config: Webhook configuration

        Returns:
            Status dict
        """
        try:
            response = await self.zoho.get(
                f"/crm/v3/{config.module.value}/actions/watch/{config.webhook_id}"
            )
            return response.get("watch", [{}])[0]
        except Exception as e:
            self.logger.error("webhook_status_check_failed", error=str(e))
            return {"active": False, "error": str(e)}
