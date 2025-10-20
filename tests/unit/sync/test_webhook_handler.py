"""Comprehensive unit tests for WebhookHandler.

Tests webhook receiving, verification, parsing, deduplication, and queueing.
Target: 45+ tests with 90%+ coverage.
"""

import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.asyncio import Redis

from src.sync.webhook_handler import (
    WebhookHandler,
    WebhookEvent,
    WebhookResponse
)


@pytest.fixture
def redis_mock():
    """Mock Redis client."""
    mock = AsyncMock(spec=Redis)
    mock.ping = AsyncMock(return_value=True)
    mock.set = AsyncMock(return_value=True)
    mock.llen = AsyncMock(return_value=5)
    mock.lpush = AsyncMock(return_value=1)
    mock.publish = AsyncMock(return_value=1)
    return mock


@pytest.fixture
def webhook_secret():
    """Webhook secret key."""
    return "test_secret_key_12345"


@pytest.fixture
def webhook_handler(redis_mock, webhook_secret):
    """WebhookHandler instance."""
    return WebhookHandler(
        redis_client=redis_mock,
        webhook_secret=webhook_secret,
        event_ttl=3600,
        max_queue_size=1000
    )


@pytest.fixture
def app(webhook_handler):
    """FastAPI app with webhook routes."""
    app = FastAPI()
    webhook_handler.register_routes(app)
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return TestClient(app)


def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for payload."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


# WebhookEvent Model Tests (10 tests)

class TestWebhookEventModel:
    """Tests for WebhookEvent Pydantic model."""

    def test_valid_event_creation(self):
        """Test creating valid webhook event."""
        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456",
            record_data={"name": "Test Account"}
        )

        assert event.event_id == "evt_123"
        assert event.event_type == "create"
        assert event.module == "Accounts"
        assert event.record_id == "acc_456"

    def test_event_type_validation(self):
        """Test event type validation."""
        with pytest.raises(ValueError, match="Event type must be one of"):
            WebhookEvent(
                event_id="evt_123",
                event_type="invalid",
                module="Accounts",
                record_id="acc_456"
            )

    def test_module_validation(self):
        """Test module validation."""
        with pytest.raises(ValueError, match="Module must be one of"):
            WebhookEvent(
                event_id="evt_123",
                event_type="create",
                module="InvalidModule",
                record_id="acc_456"
            )

    def test_default_values(self):
        """Test default field values."""
        event = WebhookEvent(
            event_id="evt_123",
            event_type="update",
            module="Contacts",
            record_id="con_789"
        )

        assert event.record_data == {}
        assert event.modified_fields == []
        assert event.user_id is None
        assert isinstance(event.timestamp, datetime)

    def test_all_event_types(self):
        """Test all valid event types."""
        event_types = ['create', 'update', 'delete', 'restore']

        for event_type in event_types:
            event = WebhookEvent(
                event_id=f"evt_{event_type}",
                event_type=event_type,
                module="Accounts",
                record_id="acc_123"
            )
            assert event.event_type == event_type

    def test_all_modules(self):
        """Test all valid modules."""
        modules = ['Accounts', 'Contacts', 'Deals', 'Tasks', 'Notes', 'Activities']

        for module in modules:
            event = WebhookEvent(
                event_id=f"evt_{module}",
                event_type="create",
                module=module,
                record_id=f"rec_{module}"
            )
            assert event.module == module

    def test_modified_fields_list(self):
        """Test modified fields list."""
        event = WebhookEvent(
            event_id="evt_123",
            event_type="update",
            module="Accounts",
            record_id="acc_456",
            modified_fields=["Account_Name", "Health_Score"]
        )

        assert len(event.modified_fields) == 2
        assert "Account_Name" in event.modified_fields

    def test_record_data_dict(self):
        """Test record data dictionary."""
        data = {
            "id": "acc_123",
            "Account_Name": "Test Corp",
            "Health_Score": 85
        }

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_123",
            record_data=data
        )

        assert event.record_data["Account_Name"] == "Test Corp"
        assert event.record_data["Health_Score"] == 85

    def test_user_id_optional(self):
        """Test optional user_id field."""
        event = WebhookEvent(
            event_id="evt_123",
            event_type="update",
            module="Accounts",
            record_id="acc_456",
            user_id="user_789"
        )

        assert event.user_id == "user_789"

    def test_timestamp_auto_generation(self):
        """Test automatic timestamp generation."""
        event1 = WebhookEvent(
            event_id="evt_1",
            event_type="create",
            module="Accounts",
            record_id="acc_1"
        )

        event2 = WebhookEvent(
            event_id="evt_2",
            event_type="create",
            module="Accounts",
            record_id="acc_2"
        )

        assert event1.timestamp != event2.timestamp


# Signature Verification Tests (8 tests)

class TestSignatureVerification:
    """Tests for webhook signature verification."""

    @pytest.mark.asyncio
    async def test_valid_signature(self, webhook_handler, webhook_secret):
        """Test valid signature verification."""
        payload = b'{"test": "data"}'
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = await webhook_handler._verify_signature(payload, signature)
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_signature(self, webhook_handler):
        """Test invalid signature rejection."""
        payload = b'{"test": "data"}'
        invalid_signature = "invalid_signature_12345"

        result = await webhook_handler._verify_signature(payload, invalid_signature)
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_signature(self, webhook_handler):
        """Test missing signature rejection."""
        payload = b'{"test": "data"}'

        result = await webhook_handler._verify_signature(payload, None)
        assert result is False

    @pytest.mark.asyncio
    async def test_signature_with_different_payload(self, webhook_handler, webhook_secret):
        """Test signature mismatch with different payload."""
        original_payload = b'{"test": "original"}'
        modified_payload = b'{"test": "modified"}'

        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            original_payload,
            hashlib.sha256
        ).hexdigest()

        result = await webhook_handler._verify_signature(modified_payload, signature)
        assert result is False

    @pytest.mark.asyncio
    async def test_signature_timing_attack_resistance(self, webhook_handler, webhook_secret):
        """Test constant-time comparison (timing attack resistance)."""
        payload = b'{"test": "data"}'
        correct_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Create similar but wrong signature
        wrong_signature = correct_signature[:-1] + "0"

        result = await webhook_handler._verify_signature(payload, wrong_signature)
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_payload_signature(self, webhook_handler, webhook_secret):
        """Test signature verification with empty payload."""
        payload = b''
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = await webhook_handler._verify_signature(payload, signature)
        assert result is True

    @pytest.mark.asyncio
    async def test_large_payload_signature(self, webhook_handler, webhook_secret):
        """Test signature verification with large payload."""
        payload = b'{"data": "' + b'x' * 10000 + b'"}'
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = await webhook_handler._verify_signature(payload, signature)
        assert result is True

    @pytest.mark.asyncio
    async def test_case_sensitive_signature(self, webhook_handler, webhook_secret):
        """Test case sensitivity of signature."""
        payload = b'{"test": "data"}'
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Change case
        wrong_case_signature = signature.upper()

        result = await webhook_handler._verify_signature(payload, wrong_case_signature)
        assert result is False


# Event Parsing Tests (7 tests)

class TestEventParsing:
    """Tests for webhook event parsing."""

    @pytest.mark.asyncio
    async def test_parse_zoho_v2_format(self, webhook_handler):
        """Test parsing Zoho CRM v2 webhook format."""
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [{
                "id": "acc_123",
                "Account_Name": "Test Corp"
            }]
        }

        event = await webhook_handler._parse_event(payload, "evt_123")

        assert event.event_id == "evt_123"
        assert event.event_type == "create"
        assert event.module == "Accounts"
        assert event.record_id == "acc_123"

    @pytest.mark.asyncio
    async def test_parse_generic_format(self, webhook_handler):
        """Test parsing generic webhook format."""
        payload = {
            "event_type": "update",
            "module": "Contacts",
            "record_id": "con_456",
            "record_data": {"name": "John Doe"}
        }

        event = await webhook_handler._parse_event(payload, "evt_456")

        assert event.event_type == "update"
        assert event.module == "Contacts"
        assert event.record_id == "con_456"

    @pytest.mark.asyncio
    async def test_parse_with_modified_fields(self, webhook_handler):
        """Test parsing with modified fields."""
        payload = {
            "operation": "update",
            "module": "Accounts",
            "data": [{"id": "acc_123"}],
            "modified_fields": ["Account_Name", "Health_Score"]
        }

        event = await webhook_handler._parse_event(payload, "evt_123")

        assert len(event.modified_fields) == 2
        assert "Account_Name" in event.modified_fields

    @pytest.mark.asyncio
    async def test_parse_with_user_info(self, webhook_handler):
        """Test parsing with user information."""
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [{"id": "acc_123"}],
            "user": {"id": "user_789"}
        }

        event = await webhook_handler._parse_event(payload, "evt_123")

        assert event.user_id == "user_789"

    @pytest.mark.asyncio
    async def test_parse_without_event_id(self, webhook_handler):
        """Test parsing generates event ID if not provided."""
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [{"id": "acc_123"}]
        }

        event = await webhook_handler._parse_event(payload, None)

        assert event.event_id is not None
        assert len(event.event_id) > 0

    @pytest.mark.asyncio
    async def test_parse_multiple_data_records(self, webhook_handler):
        """Test parsing takes first record from data array."""
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [
                {"id": "acc_1", "name": "First"},
                {"id": "acc_2", "name": "Second"}
            ]
        }

        event = await webhook_handler._parse_event(payload, "evt_123")

        assert event.record_id == "acc_1"

    @pytest.mark.asyncio
    async def test_parse_empty_data(self, webhook_handler):
        """Test parsing with empty data."""
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [{}]
        }

        event = await webhook_handler._parse_event(payload, "evt_123")

        assert event.record_id == ""


# Deduplication Tests (5 tests)

class TestDeduplication:
    """Tests for webhook event deduplication."""

    @pytest.mark.asyncio
    async def test_first_event_not_duplicate(self, webhook_handler, redis_mock):
        """Test first event is not marked as duplicate."""
        redis_mock.set = AsyncMock(return_value=True)

        is_duplicate = await webhook_handler._is_duplicate("evt_123")

        assert is_duplicate is False
        redis_mock.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_event_detected(self, webhook_handler, redis_mock):
        """Test duplicate event detection."""
        redis_mock.set = AsyncMock(return_value=None)  # None means key existed

        is_duplicate = await webhook_handler._is_duplicate("evt_123")

        assert is_duplicate is True

    @pytest.mark.asyncio
    async def test_deduplication_key_format(self, webhook_handler, redis_mock):
        """Test deduplication key format."""
        redis_mock.set = AsyncMock(return_value=True)

        await webhook_handler._is_duplicate("evt_123")

        call_args = redis_mock.set.call_args
        assert call_args[0][0] == "webhook:processed:evt_123"

    @pytest.mark.asyncio
    async def test_deduplication_ttl(self, webhook_handler, redis_mock):
        """Test deduplication TTL is set."""
        redis_mock.set = AsyncMock(return_value=True)

        await webhook_handler._is_duplicate("evt_123")

        call_args = redis_mock.set.call_args
        assert call_args[1]['ex'] == webhook_handler.event_ttl

    @pytest.mark.asyncio
    async def test_deduplication_nx_flag(self, webhook_handler, redis_mock):
        """Test NX flag is used (only set if not exists)."""
        redis_mock.set = AsyncMock(return_value=True)

        await webhook_handler._is_duplicate("evt_123")

        call_args = redis_mock.set.call_args
        assert call_args[1]['nx'] is True


# Event Queueing Tests (6 tests)

class TestEventQueueing:
    """Tests for webhook event queueing."""

    @pytest.mark.asyncio
    async def test_successful_queue(self, webhook_handler, redis_mock):
        """Test successful event queueing."""
        redis_mock.llen = AsyncMock(return_value=5)

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456"
        )

        result = await webhook_handler._queue_event(event)

        assert result is True
        redis_mock.lpush.assert_called_once()
        redis_mock.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_queue_full_rejection(self, webhook_handler, redis_mock):
        """Test queue rejection when full."""
        redis_mock.llen = AsyncMock(return_value=1000)  # At max capacity

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456"
        )

        result = await webhook_handler._queue_event(event)

        assert result is False
        redis_mock.lpush.assert_not_called()

    @pytest.mark.asyncio
    async def test_queue_serialization(self, webhook_handler, redis_mock):
        """Test event serialization for queue."""
        redis_mock.llen = AsyncMock(return_value=5)

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456",
            record_data={"name": "Test"}
        )

        await webhook_handler._queue_event(event)

        call_args = redis_mock.lpush.call_args
        queued_data = json.loads(call_args[0][1])

        assert queued_data["event_id"] == "evt_123"
        assert queued_data["record_data"]["name"] == "Test"

    @pytest.mark.asyncio
    async def test_queue_publish_notification(self, webhook_handler, redis_mock):
        """Test publish notification after queueing."""
        redis_mock.llen = AsyncMock(return_value=5)

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456"
        )

        await webhook_handler._queue_event(event)

        redis_mock.publish.assert_called_once_with(
            "webhook:events",
            unittest.mock.ANY
        )

    @pytest.mark.asyncio
    async def test_queue_error_handling(self, webhook_handler, redis_mock):
        """Test queue error handling."""
        redis_mock.llen = AsyncMock(side_effect=Exception("Redis error"))

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456"
        )

        result = await webhook_handler._queue_event(event)

        assert result is False

    @pytest.mark.asyncio
    async def test_queue_key_name(self, webhook_handler, redis_mock):
        """Test queue uses correct Redis key."""
        redis_mock.llen = AsyncMock(return_value=5)

        event = WebhookEvent(
            event_id="evt_123",
            event_type="create",
            module="Accounts",
            record_id="acc_456"
        )

        await webhook_handler._queue_event(event)

        call_args = redis_mock.lpush.call_args
        assert call_args[0][0] == "webhook:queue"


# Health and Metrics Tests (6 tests)

class TestHealthAndMetrics:
    """Tests for health checks and metrics."""

    @pytest.mark.asyncio
    async def test_health_status_healthy(self, webhook_handler, redis_mock):
        """Test healthy status when Redis is available."""
        redis_mock.ping = AsyncMock(return_value=True)
        redis_mock.llen = AsyncMock(return_value=50)

        health = await webhook_handler.get_health_status()

        assert health["status"] == "healthy"
        assert health["redis_connected"] is True

    @pytest.mark.asyncio
    async def test_health_status_unhealthy(self, webhook_handler, redis_mock):
        """Test unhealthy status when Redis fails."""
        redis_mock.ping = AsyncMock(side_effect=Exception("Redis down"))

        health = await webhook_handler.get_health_status()

        assert health["status"] == "unhealthy"
        assert health["redis_connected"] is False

    @pytest.mark.asyncio
    async def test_health_queue_size(self, webhook_handler, redis_mock):
        """Test health includes queue size."""
        redis_mock.ping = AsyncMock(return_value=True)
        redis_mock.llen = AsyncMock(return_value=75)

        health = await webhook_handler.get_health_status()

        assert health["queue_size"] == 75

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, webhook_handler):
        """Test metrics are tracked."""
        webhook_handler._metrics["total_events"] = 100
        webhook_handler._metrics["verified_events"] = 95

        metrics = await webhook_handler.get_metrics()

        assert metrics["total_events"] == 100
        assert metrics["verified_events"] == 95

    @pytest.mark.asyncio
    async def test_metrics_acceptance_rate(self, webhook_handler):
        """Test acceptance rate calculation."""
        webhook_handler._metrics["total_events"] = 100
        webhook_handler._metrics["verified_events"] = 95

        metrics = await webhook_handler.get_metrics()

        assert metrics["acceptance_rate"] == "95.0%"

    @pytest.mark.asyncio
    async def test_metrics_deduplication_rate(self, webhook_handler):
        """Test deduplication rate calculation."""
        webhook_handler._metrics["total_events"] = 100
        webhook_handler._metrics["duplicated_events"] = 10

        metrics = await webhook_handler.get_metrics()

        assert metrics["deduplication_rate"] == "10.0%"


# Additional helper for import
import unittest.mock

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
