"""End-to-end integration tests for webhook system.

Tests complete webhook flow from receiving to processing.
Target: 25+ integration tests.
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.asyncio import Redis
import redis.asyncio as aioredis

from src.sync.webhook_handler import WebhookHandler
from src.sync.webhook_processor import WebhookProcessor
from src.sync.webhook_config import WebhookConfig, ZohoModule, WebhookEventType
from src.services.memory_service import MemoryService


@pytest.fixture
async def redis_client():
    """Real Redis client for integration tests."""
    client = await aioredis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=False
    )

    # Clear test data
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "integration_test_secret_key"


@pytest.fixture
async def memory_service_mock():
    """Mock memory service."""
    mock = AsyncMock(spec=MemoryService)
    mock.sync_account_to_memory = AsyncMock(return_value=True)
    return mock


@pytest.fixture
async def webhook_handler(redis_client, webhook_secret):
    """WebhookHandler with real Redis."""
    return WebhookHandler(
        redis_client=redis_client,
        webhook_secret=webhook_secret,
        event_ttl=60,
        max_queue_size=100
    )


@pytest.fixture
async def webhook_processor(redis_client, memory_service_mock):
    """WebhookProcessor with real Redis."""
    return WebhookProcessor(
        redis_client=redis_client,
        memory_service=memory_service_mock,
        batch_size=5,
        batch_timeout=2,
        max_retries=3
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
    """Generate webhook signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


# End-to-End Flow Tests (8 tests)

class TestWebhookE2EFlow:
    """End-to-end webhook processing tests."""

    @pytest.mark.asyncio
    async def test_complete_webhook_flow(
        self,
        client,
        webhook_handler,
        webhook_processor,
        redis_client,
        webhook_secret,
        memory_service_mock
    ):
        """Test complete flow from webhook to memory update."""
        # Start processor
        await webhook_processor.start(num_workers=1)

        # Prepare webhook payload
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [{
                "id": "acc_123",
                "Account_Name": "Integration Test Corp"
            }]
        }

        payload_str = json.dumps(payload)
        signature = generate_signature(payload_str, webhook_secret)

        # Send webhook
        response = client.post(
            "/webhooks/zoho",
            data=payload_str,
            headers={
                "X-Zoho-Signature": signature,
                "X-Zoho-Event-Id": "evt_integration_1",
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

        # Wait for processing
        await asyncio.sleep(3)

        # Verify memory service was called
        memory_service_mock.sync_account_to_memory.assert_called()

        # Stop processor
        await webhook_processor.stop()

    @pytest.mark.asyncio
    async def test_webhook_to_queue_latency(
        self,
        client,
        redis_client,
        webhook_secret
    ):
        """Test webhook to queue latency is < 100ms."""
        payload = {
            "operation": "update",
            "module": "Accounts",
            "data": [{"id": "acc_456"}]
        }

        payload_str = json.dumps(payload)
        signature = generate_signature(payload_str, webhook_secret)

        start = datetime.utcnow()

        response = client.post(
            "/webhooks/zoho",
            data=payload_str,
            headers={
                "X-Zoho-Signature": signature,
                "X-Zoho-Event-Id": "evt_latency_test"
            }
        )

        latency = (datetime.utcnow() - start).total_seconds() * 1000

        assert response.status_code == 200
        assert latency < 100  # Less than 100ms

    @pytest.mark.asyncio
    async def test_multiple_webhooks_sequential(
        self,
        client,
        redis_client,
        webhook_secret
    ):
        """Test multiple webhooks processed sequentially."""
        for i in range(5):
            payload = {
                "operation": "create",
                "module": "Accounts",
                "data": [{"id": f"acc_{i}"}]
            }

            payload_str = json.dumps(payload)
            signature = generate_signature(payload_str, webhook_secret)

            response = client.post(
                "/webhooks/zoho",
                data=payload_str,
                headers={
                    "X-Zoho-Signature": signature,
                    "X-Zoho-Event-Id": f"evt_seq_{i}"
                }
            )

            assert response.status_code == 200

        # Check queue size
        queue_size = await redis_client.llen("webhook:queue")
        assert queue_size == 5

    @pytest.mark.asyncio
    async def test_concurrent_webhooks(
        self,
        client,
        redis_client,
        webhook_secret
    ):
        """Test concurrent webhook processing."""
        async def send_webhook(index: int):
            payload = {
                "operation": "create",
                "module": "Accounts",
                "data": [{"id": f"acc_concurrent_{index}"}]
            }

            payload_str = json.dumps(payload)
            signature = generate_signature(payload_str, webhook_secret)

            return client.post(
                "/webhooks/zoho",
                data=payload_str,
                headers={
                    "X-Zoho-Signature": signature,
                    "X-Zoho-Event-Id": f"evt_concurrent_{index}"
                }
            )

        # Send 10 webhooks concurrently
        tasks = [send_webhook(i) for i in range(10)]
        responses = await asyncio.gather(*[asyncio.to_thread(t) for t in tasks])

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_deduplication_across_requests(
        self,
        client,
        webhook_secret
    ):
        """Test deduplication works across multiple requests."""
        payload = {
            "operation": "create",
            "module": "Accounts",
            "data": [{"id": "acc_duplicate"}]
        }

        payload_str = json.dumps(payload)
        signature = generate_signature(payload_str, webhook_secret)
        event_id = "evt_dedup_test"

        # First request
        response1 = client.post(
            "/webhooks/zoho",
            data=payload_str,
            headers={
                "X-Zoho-Signature": signature,
                "X-Zoho-Event-Id": event_id
            }
        )

        assert response1.json()["status"] == "accepted"

        # Second request (duplicate)
        response2 = client.post(
            "/webhooks/zoho",
            data=payload_str,
            headers={
                "X-Zoho-Signature": signature,
                "X-Zoho-Event-Id": event_id
            }
        )

        assert response2.json()["status"] == "duplicate"

    @pytest.mark.asyncio
    async def test_batch_processing(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test batch processing of events."""
        # Queue multiple events
        for i in range(10):
            event_data = {
                "event_id": f"evt_batch_{i}",
                "event_type": "create",
                "module": "Accounts",
                "record_id": f"acc_batch_{i}",
                "record_data": {},
                "modified_fields": [],
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": None
            }

            await redis_client.lpush(
                "webhook:queue",
                json.dumps(event_data)
            )

        # Start processor
        await webhook_processor.start(num_workers=2)

        # Wait for processing
        await asyncio.sleep(5)

        # Stop processor
        await webhook_processor.stop()

        # Check all events processed
        assert memory_service_mock.sync_account_to_memory.call_count == 10

    @pytest.mark.asyncio
    async def test_error_recovery(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test error recovery and retry logic."""
        # Make first call fail, then succeed
        memory_service_mock.sync_account_to_memory = AsyncMock(
            side_effect=[Exception("Temporary error"), True, True]
        )

        # Queue event
        event_data = {
            "event_id": "evt_error_recovery",
            "event_type": "create",
            "module": "Accounts",
            "record_id": "acc_error",
            "record_data": {},
            "modified_fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        # Start processor
        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(5)
        await webhook_processor.stop()

        # Should have retried
        assert memory_service_mock.sync_account_to_memory.call_count >= 2

    @pytest.mark.asyncio
    async def test_dead_letter_queue(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test dead letter queue for failed events."""
        # Make all calls fail
        memory_service_mock.sync_account_to_memory = AsyncMock(
            side_effect=Exception("Permanent error")
        )

        # Queue event
        event_data = {
            "event_id": "evt_dead_letter",
            "event_type": "create",
            "module": "Accounts",
            "record_id": "acc_failed",
            "record_data": {},
            "modified_fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        # Start processor
        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(10)
        await webhook_processor.stop()

        # Check dead letter queue
        dlq_size = await redis_client.llen("webhook:dead_letter")
        assert dlq_size > 0


# Module-Specific Processing Tests (6 tests)

class TestModuleSpecificProcessing:
    """Tests for module-specific event processing."""

    @pytest.mark.asyncio
    async def test_account_create_processing(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test Account create event processing."""
        event_data = {
            "event_id": "evt_acc_create",
            "event_type": "create",
            "module": "Accounts",
            "record_id": "acc_new_123",
            "record_data": {"Account_Name": "New Corp"},
            "modified_fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": "user_1"
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(3)
        await webhook_processor.stop()

        memory_service_mock.sync_account_to_memory.assert_called_with(
            "acc_new_123",
            force=True
        )

    @pytest.mark.asyncio
    async def test_contact_update_processing(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test Contact update triggers account sync."""
        event_data = {
            "event_id": "evt_con_update",
            "event_type": "update",
            "module": "Contacts",
            "record_id": "con_456",
            "record_data": {
                "Account_Name": {"id": "acc_parent_123"}
            },
            "modified_fields": ["Email"],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(3)
        await webhook_processor.stop()

        # Should sync parent account
        memory_service_mock.sync_account_to_memory.assert_called()

    @pytest.mark.asyncio
    async def test_deal_create_processing(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test Deal create triggers account sync."""
        event_data = {
            "event_id": "evt_deal_create",
            "event_type": "create",
            "module": "Deals",
            "record_id": "deal_789",
            "record_data": {
                "Account_Name": {"id": "acc_related_456"},
                "Deal_Name": "Big Deal"
            },
            "modified_fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(3)
        await webhook_processor.stop()

        memory_service_mock.sync_account_to_memory.assert_called()

    @pytest.mark.asyncio
    async def test_critical_field_update(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test critical field update forces sync."""
        event_data = {
            "event_id": "evt_critical_update",
            "event_type": "update",
            "module": "Accounts",
            "record_id": "acc_critical_123",
            "record_data": {"Health_Score": 25},
            "modified_fields": ["Health_Score"],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(3)
        await webhook_processor.stop()

        # Force should be True for critical fields
        call_args = memory_service_mock.sync_account_to_memory.call_args
        assert call_args[1]['force'] is True

    @pytest.mark.asyncio
    async def test_note_create_processing(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test Note create triggers account sync."""
        event_data = {
            "event_id": "evt_note_create",
            "event_type": "create",
            "module": "Notes",
            "record_id": "note_123",
            "record_data": {
                "Parent_Id": {
                    "id": "acc_note_parent",
                    "module": "Accounts"
                }
            },
            "modified_fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(3)
        await webhook_processor.stop()

        memory_service_mock.sync_account_to_memory.assert_called()

    @pytest.mark.asyncio
    async def test_activity_create_processing(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test Activity create triggers account sync."""
        event_data = {
            "event_id": "evt_activity_create",
            "event_type": "create",
            "module": "Activities",
            "record_id": "activity_456",
            "record_data": {
                "What_Id": {
                    "id": "acc_activity_parent",
                    "module": "Accounts"
                }
            },
            "modified_fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": None
        }

        await redis_client.lpush("webhook:queue", json.dumps(event_data))

        await webhook_processor.start(num_workers=1)
        await asyncio.sleep(3)
        await webhook_processor.stop()

        memory_service_mock.sync_account_to_memory.assert_called()


# Performance Tests (5 tests)

class TestWebhookPerformance:
    """Performance and scalability tests."""

    @pytest.mark.asyncio
    async def test_high_throughput(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test processing 100 events in < 30 seconds."""
        # Queue 100 events
        for i in range(100):
            event_data = {
                "event_id": f"evt_throughput_{i}",
                "event_type": "create",
                "module": "Accounts",
                "record_id": f"acc_throughput_{i}",
                "record_data": {},
                "modified_fields": [],
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": None
            }

            await redis_client.lpush("webhook:queue", json.dumps(event_data))

        start = datetime.utcnow()

        # Process with multiple workers
        await webhook_processor.start(num_workers=5)

        # Wait for completion
        while await redis_client.llen("webhook:queue") > 0:
            await asyncio.sleep(1)
            if (datetime.utcnow() - start).total_seconds() > 30:
                break

        await webhook_processor.stop()

        duration = (datetime.utcnow() - start).total_seconds()

        assert duration < 30
        assert memory_service_mock.sync_account_to_memory.call_count == 100

    @pytest.mark.asyncio
    async def test_memory_efficiency(
        self,
        webhook_handler,
        redis_client
    ):
        """Test memory usage stays reasonable with many events."""
        # Process 1000 events
        initial_memory = await redis_client.memory_usage("webhook:queue") or 0

        for i in range(1000):
            event = {
                "event_id": f"evt_mem_{i}",
                "event_type": "create",
                "module": "Accounts",
                "record_id": f"acc_mem_{i}",
                "record_data": {},
                "modified_fields": [],
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": None
            }

            await redis_client.lpush("webhook:queue", json.dumps(event))

        final_memory = await redis_client.memory_usage("webhook:queue") or 0

        # Memory should be reasonable (< 10MB for 1000 events)
        memory_used = final_memory - initial_memory
        assert memory_used < 10_000_000

    @pytest.mark.asyncio
    async def test_queue_overflow_handling(
        self,
        webhook_handler,
        redis_client
    ):
        """Test graceful handling of queue overflow."""
        # Fill queue to capacity
        for i in range(100):
            await redis_client.lpush("webhook:queue", f"event_{i}")

        # Try to add more
        from src.sync.webhook_handler import WebhookEvent

        event = WebhookEvent(
            event_id="evt_overflow",
            event_type="create",
            module="Accounts",
            record_id="acc_overflow"
        )

        result = await webhook_handler._queue_event(event)

        assert result is False

    @pytest.mark.asyncio
    async def test_processor_scalability(
        self,
        webhook_processor,
        redis_client,
        memory_service_mock
    ):
        """Test processor scales with more workers."""
        # Queue 50 events
        for i in range(50):
            event_data = {
                "event_id": f"evt_scale_{i}",
                "event_type": "create",
                "module": "Accounts",
                "record_id": f"acc_scale_{i}",
                "record_data": {},
                "modified_fields": [],
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": None
            }

            await redis_client.lpush("webhook:queue", json.dumps(event_data))

        # Process with multiple workers
        await webhook_processor.start(num_workers=10)
        await asyncio.sleep(5)
        await webhook_processor.stop()

        # Should process faster with more workers
        queue_size = await redis_client.llen("webhook:queue")
        assert queue_size < 10  # Most should be processed

    @pytest.mark.asyncio
    async def test_dead_letter_reprocessing(
        self,
        webhook_processor,
        redis_client
    ):
        """Test reprocessing from dead letter queue."""
        # Add events to dead letter queue
        for i in range(5):
            dlq_entry = {
                "event": {
                    "event_id": f"evt_dlq_{i}",
                    "event_type": "create",
                    "module": "Accounts",
                    "record_id": f"acc_dlq_{i}",
                    "record_data": {},
                    "modified_fields": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": None
                },
                "error": "Test error",
                "failed_at": datetime.utcnow().isoformat(),
                "retry_count": 3
            }

            await redis_client.lpush(
                "webhook:dead_letter",
                json.dumps(dlq_entry)
            )

        # Reprocess
        results = await webhook_processor.reprocess_dead_letter(limit=5)

        assert results["attempted"] == 5


# Health Check Tests (6 tests)

class TestHealthChecks:
    """Health check and monitoring tests."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/webhooks/health")

        assert response.status_code == 200
        assert "status" in response.json()

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns data."""
        response = client.get("/webhooks/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "acceptance_rate" in data

    @pytest.mark.asyncio
    async def test_redis_health_check(
        self,
        webhook_handler,
        redis_client
    ):
        """Test Redis health check."""
        health = await webhook_handler.get_health_status()

        assert health["redis_connected"] is True
        assert health["queue_size"] >= 0

    @pytest.mark.asyncio
    async def test_processor_metrics(
        self,
        webhook_processor
    ):
        """Test processor metrics."""
        metrics = await webhook_processor.get_metrics()

        assert "events_processed" in metrics
        assert "success_rate" in metrics
        assert "workers_running" in metrics

    @pytest.mark.asyncio
    async def test_queue_utilization(
        self,
        webhook_handler,
        redis_client
    ):
        """Test queue utilization reporting."""
        # Add some events
        for i in range(25):
            await redis_client.lpush("webhook:queue", f"event_{i}")

        health = await webhook_handler.get_health_status()

        assert "queue_utilization" in health
        # Should be ~25%
        assert "25" in health["queue_utilization"]

    @pytest.mark.asyncio
    async def test_health_timestamp(
        self,
        webhook_handler
    ):
        """Test health check includes timestamp."""
        health = await webhook_handler.get_health_status()

        assert "timestamp" in health
        # Should be recent ISO format
        timestamp = datetime.fromisoformat(health["timestamp"])
        assert (datetime.utcnow() - timestamp).total_seconds() < 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
