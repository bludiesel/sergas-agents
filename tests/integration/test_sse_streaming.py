"""Integration Tests for SSE Event Streaming.

Tests Server-Sent Events (SSE) streaming infrastructure for AG UI Protocol.

Week 6-9 Critical Implementation - SPARC V3 Compliance

Test Coverage:
- SSE connection lifecycle (open/stream/close)
- Event parsing and validation
- Reconnection on failure
- Multiple concurrent streams
- Event filtering and buffering
- Client disconnect detection
- SSE format compliance (data: prefix, double newline)
- Performance (latency, throughput)

Test Strategy:
- Use httpx AsyncClient for HTTP streaming
- Mock FastAPI application with test client
- Real SSE event formatting
- Realistic event sequences
"""

import asyncio
import json
import uuid
from typing import List, Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx

from src.events.ag_ui_emitter import AGUIEventEmitter


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_events():
    """Generate sample AG UI Protocol events for testing."""
    emitter = AGUIEventEmitter(session_id="test_session")

    return [
        emitter.emit_workflow_started("account_analysis", "acc_123"),
        emitter.emit_agent_started("zoho_scout", 1, "Fetching account data"),
        emitter.emit_agent_stream("zoho_scout", "Retrieved account snapshot", "text"),
        emitter.emit_agent_completed("zoho_scout", 1, {"status": "success"}),
        emitter.emit_agent_started("memory_analyst", 2, "Analyzing historical context"),
        emitter.emit_agent_stream("memory_analyst", "Found 5 patterns", "text"),
        emitter.emit_agent_completed("memory_analyst", 2, {"status": "success"}),
        emitter.emit_approval_required(
            {
                "recommendation_id": "rec_123",
                "account_id": "acc_123",
                "action_type": "review",
                "priority": "high",
                "reasoning": "Risk detected",
                "expected_impact": "Mitigate risk"
            },
            timeout_hours=72
        ),
        emitter.emit_workflow_completed(
            "account_analysis",
            "acc_123",
            {"status": "completed", "recommendations_generated": 1}
        )
    ]


@pytest.fixture
def test_app(sample_events):
    """Create minimal FastAPI app for SSE testing."""
    app = FastAPI()

    async def event_generator():
        """Generate SSE events."""
        for event in sample_events:
            # Format as SSE
            event_json = json.dumps(event)
            sse_line = f"data: {event_json}\n\n"
            yield sse_line
            await asyncio.sleep(0.01)  # Small delay between events

    @app.get("/stream")
    async def stream_events():
        """SSE streaming endpoint."""
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    @app.get("/stream-error")
    async def stream_with_error():
        """SSE stream that fails mid-stream."""
        async def error_generator():
            yield f"data: {json.dumps({'event': 'started'})}\n\n"
            await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'event': 'progress'})}\n\n"
            raise Exception("Stream error")

        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream"
        )

    @app.get("/stream-slow")
    async def stream_slow():
        """SSE stream with slow events."""
        async def slow_generator():
            for i in range(5):
                yield f"data: {json.dumps({'event': f'event_{i}'})}\n\n"
                await asyncio.sleep(0.5)  # 500ms delay

        return StreamingResponse(
            slow_generator(),
            media_type="text/event-stream"
        )

    return app


# ============================================================================
# SSE CONNECTION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_connection_lifecycle(test_app):
    """Test SSE connection open → stream → close lifecycle."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        async with client.stream("GET", "/stream") as response:
            # Validate connection established
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"

            # Read events
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    event_count += 1

            # Should receive all events
            assert event_count == 9  # Based on sample_events fixture


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_event_parsing(test_app):
    """Test SSE event parsing and validation."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        async with client.stream("GET", "/stream") as response:
            events = []

            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    # Parse JSON from SSE line
                    json_str = line[5:].strip()  # Remove "data:" prefix
                    event = json.loads(json_str)
                    events.append(event)

            # Validate all events parsed successfully
            assert len(events) == 9

            # Validate event structure
            for event in events:
                assert "event" in event
                assert "data" in event
                assert "timestamp" in event

            # Validate event sequence
            event_types = [e["event"] for e in events]
            assert event_types[0] == "workflow_started"
            assert event_types[-1] == "workflow_completed"
            assert "agent_started" in event_types
            assert "agent_completed" in event_types
            assert "approval_required" in event_types


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_format_compliance(test_app):
    """Test SSE format compliance (RFC 8895).

    Validates:
    - Lines start with "data:"
    - Events end with double newline
    - JSON is valid
    """
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        async with client.stream("GET", "/stream") as response:
            raw_content = b""

            async for chunk in response.aiter_bytes():
                raw_content += chunk

            # Decode to string
            content = raw_content.decode("utf-8")

            # Split by double newline
            sse_events = content.split("\n\n")

            # Validate each event
            for sse_event in sse_events:
                if sse_event.strip():
                    # Should start with "data:"
                    assert sse_event.startswith("data:"), f"Invalid SSE format: {sse_event[:50]}"

                    # Extract JSON
                    json_str = sse_event[5:].strip()
                    if json_str:
                        # Should be valid JSON
                        event = json.loads(json_str)
                        assert isinstance(event, dict)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_stream_error_handling(test_app):
    """Test handling of stream errors mid-connection."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        events = []

        try:
            async with client.stream("GET", "/stream-error") as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        json_str = line[5:].strip()
                        event = json.loads(json_str)
                        events.append(event)
        except Exception:
            # Stream error expected
            pass

        # Should have received partial events before error
        assert len(events) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_reconnection(test_app):
    """Test SSE reconnection after disconnect."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        # First connection
        connection_1_events = []
        async with client.stream("GET", "/stream") as response:
            count = 0
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    event = json.loads(json_str)
                    connection_1_events.append(event)
                    count += 1
                    if count >= 3:
                        break  # Disconnect early

        # Reconnect
        connection_2_events = []
        async with client.stream("GET", "/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    event = json.loads(json_str)
                    connection_2_events.append(event)

        # Both connections should work
        assert len(connection_1_events) >= 3
        assert len(connection_2_events) == 9


# ============================================================================
# CONCURRENT STREAMING TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_multiple_concurrent_streams(test_app):
    """Test multiple concurrent SSE streams."""
    num_streams = 5

    async def consume_stream(stream_id: int) -> List[Dict[str, Any]]:
        """Consume single SSE stream."""
        async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
            events = []
            async with client.stream("GET", "/stream") as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        json_str = line[5:].strip()
                        event = json.loads(json_str)
                        events.append(event)
            return events

    # Run concurrent streams
    results = await asyncio.gather(
        *[consume_stream(i) for i in range(num_streams)],
        return_exceptions=True
    )

    # All streams should succeed
    assert len(results) == num_streams
    assert all(not isinstance(r, Exception) for r in results)

    # Each stream should receive all events
    for events in results:
        assert len(events) == 9
        assert events[0]["event"] == "workflow_started"
        assert events[-1]["event"] == "workflow_completed"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_event_latency(test_app):
    """Test SSE event streaming latency (<200ms target)."""
    import time

    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        async with client.stream("GET", "/stream") as response:
            event_timestamps = []

            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    event_timestamps.append(time.time())

            # Calculate gaps between events
            if len(event_timestamps) > 1:
                gaps = [
                    event_timestamps[i+1] - event_timestamps[i]
                    for i in range(len(event_timestamps) - 1)
                ]

                # Average latency should be very low (events streamed fast)
                avg_gap = sum(gaps) / len(gaps)
                assert avg_gap < 0.2, f"Average event gap {avg_gap:.3f}s exceeds 200ms"

                # Max gap should also be reasonable
                max_gap = max(gaps)
                assert max_gap < 0.5, f"Max event gap {max_gap:.3f}s too high"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_throughput(test_app):
    """Test SSE event throughput (events/second)."""
    import time

    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        start_time = time.time()

        event_count = 0
        async with client.stream("GET", "/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    event_count += 1

        elapsed = time.time() - start_time

        # Calculate throughput
        throughput = event_count / elapsed if elapsed > 0 else 0

        # Should stream events quickly (>10 events/sec with mocks)
        assert throughput > 10, f"Throughput {throughput:.1f} events/s too low"


# ============================================================================
# CLIENT DISCONNECT TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_client_early_disconnect(test_app):
    """Test handling of client disconnect mid-stream."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        events_received = 0

        async with client.stream("GET", "/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    events_received += 1
                    if events_received >= 3:
                        break  # Simulate client disconnect

        # Should have received partial stream
        assert events_received == 3


# ============================================================================
# EVENT FILTERING TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_event_filtering_by_type(test_app):
    """Test filtering SSE events by type."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        agent_events = []

        async with client.stream("GET", "/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    event = json.loads(json_str)

                    # Filter only agent_* events
                    if event["event"].startswith("agent_"):
                        agent_events.append(event)

        # Should have filtered agent events
        assert len(agent_events) > 0
        assert all(e["event"].startswith("agent_") for e in agent_events)


# ============================================================================
# SSE EMITTER TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_ag_ui_emitter_sse_formatting():
    """Test AGUIEventEmitter SSE formatting."""
    emitter = AGUIEventEmitter(session_id="test_session")

    # Create sample event
    event = emitter.emit_workflow_started("test_workflow", "acc_123")

    # Format as SSE
    sse_formatted = emitter.format_sse_event(event)

    # Validate SSE format
    assert sse_formatted.startswith("data: ")
    assert sse_formatted.endswith("\n\n")

    # Extract and validate JSON
    json_part = sse_formatted[6:-2]  # Remove "data: " and "\n\n"
    parsed_event = json.loads(json_part)

    assert parsed_event["event"] == "workflow_started"
    assert parsed_event["data"]["workflow"] == "test_workflow"
    assert parsed_event["data"]["account_id"] == "acc_123"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ag_ui_emitter_stream_events():
    """Test AGUIEventEmitter stream_events method."""
    emitter = AGUIEventEmitter(session_id="test_session")

    # Create event generator
    async def sample_event_generator():
        """Generate sample events."""
        yield emitter.emit_workflow_started("test", "acc_123")
        yield emitter.emit_agent_started("scout", 1, "Fetching")
        yield emitter.emit_agent_completed("scout", 1)
        yield emitter.emit_workflow_completed("test", "acc_123")

    # Stream events with SSE formatting
    sse_events = []
    async for sse_event in emitter.stream_events(sample_event_generator()):
        sse_events.append(sse_event)

    # Validate all events formatted
    assert len(sse_events) == 4

    # Validate SSE format
    for sse_event in sse_events:
        assert sse_event.startswith("data: ")
        assert sse_event.endswith("\n\n")

        # Validate parseable
        json_str = sse_event[6:-2]
        event = json.loads(json_str)
        assert "event" in event
        assert "data" in event


# ============================================================================
# SLOW STREAM TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_slow_event_stream(test_app):
    """Test handling of slow event streams."""
    import time

    async with httpx.AsyncClient(
        app=test_app,
        base_url="http://test",
        timeout=httpx.Timeout(10.0)  # 10s timeout
    ) as client:
        start_time = time.time()
        events = []

        async with client.stream("GET", "/stream-slow") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    event = json.loads(json_str)
                    events.append(event)

        elapsed = time.time() - start_time

        # Should receive all events despite slow stream
        assert len(events) == 5

        # Should take approximately 2.5s (5 events * 0.5s)
        assert 2.0 < elapsed < 3.5


# ============================================================================
# HEADERS VALIDATION
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sse_headers_validation(test_app):
    """Test that SSE response has correct headers."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        async with client.stream("GET", "/stream") as response:
            headers = response.headers

            # Required SSE headers
            assert headers.get("content-type") == "text/event-stream"
            assert headers.get("cache-control") == "no-cache"
            assert headers.get("connection") == "keep-alive"
            assert headers.get("x-accel-buffering") == "no"  # Disable nginx buffering

            # Should not have content-length (streaming)
            assert "content-length" not in headers


# ============================================================================
# MALFORMED EVENT HANDLING
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_malformed_sse_event_handling():
    """Test handling of malformed SSE events."""
    # Create app with malformed events
    app = FastAPI()

    async def malformed_generator():
        """Generate malformed SSE events."""
        yield "data: valid_json\n\n"  # Missing JSON structure
        yield "invalid line without data prefix\n\n"
        yield "data: {\"valid\": \"json\"}\n\n"

    @app.get("/malformed")
    async def malformed_stream():
        return StreamingResponse(
            malformed_generator(),
            media_type="text/event-stream"
        )

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        valid_events = []
        invalid_lines = []

        async with client.stream("GET", "/malformed") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    try:
                        event = json.loads(json_str)
                        valid_events.append(event)
                    except json.JSONDecodeError:
                        invalid_lines.append(line)
                elif line.strip():
                    invalid_lines.append(line)

        # Should handle mix of valid/invalid
        assert len(valid_events) >= 1
        assert len(invalid_lines) >= 1
