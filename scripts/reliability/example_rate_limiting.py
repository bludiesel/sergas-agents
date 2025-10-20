#!/usr/bin/env python3
"""
Example rate limiting and queue management script.

Demonstrates rate limiting strategies, queue management, and backpressure handling.

Usage:
    python scripts/reliability/example_rate_limiting.py demo-token-bucket
    python scripts/reliability/example_rate_limiting.py demo-sliding-window
    python scripts/reliability/example_rate_limiting.py demo-queue
    python scripts/reliability/example_rate_limiting.py load-test
"""

import asyncio
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.reliability.rate_limiting import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    QueueManager,
    ThrottlingStrategy,
    BackpressureHandler,
)


async def demo_token_bucket():
    """Demonstrate token bucket rate limiting."""
    print("=" * 60)
    print("Token Bucket Rate Limiting Demo")
    print("=" * 60)

    # Create rate limiter: 10 requests per 5 seconds
    config = RateLimitConfig(
        name="api_rate_limiter",
        max_requests=10,
        window_seconds=5,
        strategy=RateLimitStrategy.TOKEN_BUCKET
    )

    limiter = RateLimiter(config)

    print(f"\nConfiguration:")
    print(f"  Max Requests: {config.max_requests}")
    print(f"  Window: {config.window_seconds}s")
    print(f"  Rate: {config.requests_per_second():.2f} req/s")
    print(f"  Strategy: {config.strategy.value}")

    print(f"\nSending 15 requests rapidly...")

    allowed = 0
    rejected = 0

    for i in range(15):
        is_allowed, retry_after = await limiter.allow_request()

        if is_allowed:
            allowed += 1
            print(f"  Request {i+1}: ✓ ALLOWED")
        else:
            rejected += 1
            print(f"  Request {i+1}: ✗ REJECTED (retry after {retry_after:.2f}s)")

    print(f"\nResults:")
    print(f"  Allowed: {allowed}")
    print(f"  Rejected: {rejected}")

    # Show metrics
    metrics = limiter.get_metrics()
    print(f"\nMetrics:")
    print(f"  Tokens Available: {metrics.get('tokens_available', 'N/A')}")
    print(f"  Utilization: {metrics['utilization_percent']:.2f}%")


async def demo_sliding_window():
    """Demonstrate sliding window rate limiting."""
    print("\n" + "=" * 60)
    print("Sliding Window Rate Limiting Demo")
    print("=" * 60)

    # Create rate limiter: 5 requests per 10 seconds
    config = RateLimitConfig(
        name="api_rate_limiter",
        max_requests=5,
        window_seconds=10,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )

    limiter = RateLimiter(config)

    print(f"\nConfiguration:")
    print(f"  Max Requests: {config.max_requests}")
    print(f"  Window: {config.window_seconds}s")

    print(f"\nSending 3 requests...")
    for i in range(3):
        is_allowed, _ = await limiter.allow_request()
        print(f"  Request {i+1}: {'✓ ALLOWED' if is_allowed else '✗ REJECTED'}")
        await asyncio.sleep(1)

    print(f"\nWaiting 5 seconds for window to slide...")
    await asyncio.sleep(5)

    print(f"\nSending 5 more requests...")
    for i in range(5):
        is_allowed, retry_after = await limiter.allow_request()
        if is_allowed:
            print(f"  Request {i+1}: ✓ ALLOWED")
        else:
            print(f"  Request {i+1}: ✗ REJECTED (retry after {retry_after:.2f}s)")

    # Show metrics
    metrics = limiter.get_metrics()
    print(f"\nMetrics:")
    print(f"  Current Requests: {metrics.get('current_requests', 'N/A')}")
    print(f"  Utilization: {metrics['utilization_percent']:.2f}%")


async def demo_queue_manager():
    """Demonstrate queue management."""
    print("\n" + "=" * 60)
    print("Queue Manager Demo")
    print("=" * 60)

    # Create queue manager
    queue = QueueManager(
        name="request_queue",
        max_size=100,
        max_workers=5,
        timeout=5.0
    )

    print(f"\nConfiguration:")
    print(f"  Max Queue Size: {queue.max_size}")
    print(f"  Max Workers: {queue.max_workers}")
    print(f"  Timeout: {queue.timeout}s")

    # Start queue processing
    await queue.start()
    print(f"\n✓ Queue started with {queue.max_workers} workers")

    # Define work function
    async def process_request(request_id: int):
        """Simulate processing a request."""
        print(f"  Processing request {request_id}...")
        await asyncio.sleep(0.5)  # Simulate work
        print(f"  ✓ Request {request_id} completed")

    # Enqueue requests
    print(f"\nEnqueuing 10 requests...")
    for i in range(10):
        success = await queue.enqueue(process_request, i+1)
        if success:
            print(f"  Request {i+1} enqueued")

    # Monitor queue
    print(f"\nMonitoring queue (5 seconds)...")
    for _ in range(5):
        await asyncio.sleep(1)
        metrics = queue.get_metrics()
        print(
            f"  Queue: {metrics['queue_size']}/{metrics['max_size']} | "
            f"Processed: {metrics['processed_count']} | "
            f"Failed: {metrics['failed_count']}"
        )

    # Stop queue
    await queue.stop()
    print(f"\n✓ Queue stopped")

    # Final metrics
    metrics = queue.get_metrics()
    print(f"\nFinal Metrics:")
    print(f"  Total Processed: {metrics['processed_count']}")
    print(f"  Total Failed: {metrics['failed_count']}")
    print(f"  Timeouts: {metrics['timeout_count']}")


async def demo_backpressure():
    """Demonstrate backpressure handling."""
    print("\n" + "=" * 60)
    print("Backpressure Handling Demo")
    print("=" * 60)

    # Create components
    config = RateLimitConfig(
        name="api_rate_limiter",
        max_requests=100,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )

    limiter = RateLimiter(config)

    queue = QueueManager(
        name="request_queue",
        max_size=50,
        max_workers=5,
        timeout=5.0
    )

    handler = BackpressureHandler(
        name="api_backpressure",
        queue_manager=queue,
        rate_limiter=limiter,
        alert_threshold=0.8
    )

    await queue.start()

    # Define work function
    async def slow_request(request_id: int):
        await asyncio.sleep(2)  # Slow processing

    print(f"\nEnqueuing 45 requests (90% of queue capacity)...")

    for i in range(45):
        await queue.enqueue(slow_request, i+1)

    # Check backpressure
    print(f"\nChecking backpressure...")
    is_active = await handler.check_and_apply_backpressure()

    status = handler.get_status()
    print(f"\nBackpressure Status:")
    print(f"  Active: {status['backpressure_active']}")
    print(f"  Queue Utilization: {status['queue_utilization']:.2%}")
    print(f"  Alert Threshold: {status['alert_threshold']:.2%}")
    print(f"  Queue Size: {status['queue_size']}")

    await queue.stop()


async def load_test():
    """Run a simple load test."""
    print("\n" + "=" * 60)
    print("Load Test")
    print("=" * 60)

    # Create rate limiter
    config = RateLimitConfig(
        name="load_test",
        max_requests=100,
        window_seconds=10,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )

    limiter = RateLimiter(config)

    # Test parameters
    num_requests = 200
    concurrency = 20

    print(f"\nTest Configuration:")
    print(f"  Total Requests: {num_requests}")
    print(f"  Concurrency: {concurrency}")
    print(f"  Rate Limit: {config.max_requests} req/{config.window_seconds}s")

    # Run load test
    print(f"\nRunning load test...")
    start_time = time.time()

    allowed_count = 0
    rejected_count = 0

    async def send_request(request_id: int):
        nonlocal allowed_count, rejected_count

        is_allowed, retry_after = await limiter.allow_request()

        if is_allowed:
            allowed_count += 1
        else:
            rejected_count += 1

            # Retry after specified time
            if retry_after:
                await asyncio.sleep(retry_after)
                is_allowed, _ = await limiter.allow_request()
                if is_allowed:
                    allowed_count += 1
                    rejected_count -= 1

    # Send requests in batches
    for batch_start in range(0, num_requests, concurrency):
        batch_end = min(batch_start + concurrency, num_requests)
        batch = [
            send_request(i)
            for i in range(batch_start, batch_end)
        ]
        await asyncio.gather(*batch)

        # Show progress
        progress = (batch_end / num_requests) * 100
        print(f"  Progress: {progress:.1f}% ({batch_end}/{num_requests})")

    elapsed = time.time() - start_time

    # Results
    print(f"\nLoad Test Results:")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  Requests Sent: {num_requests}")
    print(f"  Allowed: {allowed_count}")
    print(f"  Rejected: {rejected_count}")
    print(f"  Throughput: {allowed_count / elapsed:.2f} req/s")

    # Metrics
    metrics = limiter.get_metrics()
    print(f"\nRate Limiter Metrics:")
    print(f"  Strategy: {metrics['strategy']}")
    print(f"  Utilization: {metrics['utilization_percent']:.2f}%")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Rate limiting and queue management examples"
    )

    parser.add_argument(
        "demo",
        choices=[
            "demo-token-bucket",
            "demo-sliding-window",
            "demo-queue",
            "demo-backpressure",
            "load-test",
            "all"
        ],
        help="Demo to run"
    )

    args = parser.parse_args()

    if args.demo == "demo-token-bucket":
        await demo_token_bucket()
    elif args.demo == "demo-sliding-window":
        await demo_sliding_window()
    elif args.demo == "demo-queue":
        await demo_queue_manager()
    elif args.demo == "demo-backpressure":
        await demo_backpressure()
    elif args.demo == "load-test":
        await load_test()
    elif args.demo == "all":
        await demo_token_bucket()
        await demo_sliding_window()
        await demo_queue_manager()
        await demo_backpressure()
        await load_test()


if __name__ == "__main__":
    asyncio.run(main())
