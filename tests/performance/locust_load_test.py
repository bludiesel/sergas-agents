"""
Locust Load Testing for AG UI Protocol Streaming Endpoint.

Week 8 Performance Validation - Load Testing Suite

Simulates realistic user load patterns for:
- Account analysis workflows
- Concurrent SSE connections
- Sustained load over time
- Spike traffic patterns

Usage:
    # Run headless (CI/CD)
    locust -f locust_load_test.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000

    # Run with web UI
    locust -f locust_load_test.py --host http://localhost:8000

Author: Performance Benchmarker Agent
Date: 2025-10-19
"""

from locust import HttpUser, task, between, events, constant_pacing
import json
import random
import time
from datetime import datetime


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_account_id() -> str:
    """Generate realistic account ID."""
    return f"ACC-LOAD-{random.randint(1000, 9999)}"


def generate_workflow_type() -> str:
    """Generate random workflow type (weighted)."""
    workflows = [
        ("account_analysis", 0.7),     # 70% account analysis
        ("daily_review", 0.2),         # 20% daily review
        ("risk_assessment", 0.1)       # 10% risk assessment
    ]

    rand = random.random()
    cumulative = 0
    for workflow, weight in workflows:
        cumulative += weight
        if rand <= cumulative:
            return workflow

    return "account_analysis"


# ============================================================================
# User Behavior Patterns
# ============================================================================

class AccountAnalysisUser(HttpUser):
    """
    Simulates user requesting account analysis via AG UI Protocol.

    User Behavior:
    - Requests account analysis
    - Waits for SSE stream to complete
    - Waits 1-3 seconds between requests (think time)
    """

    wait_time = between(1, 3)  # Think time between requests

    def on_start(self):
        """Called when user starts."""
        self.user_id = f"user-{self.environment.runner.user_count}"
        print(f"[{datetime.now().isoformat()}] User {self.user_id} started")

    @task(10)  # Weight: 10 (most common)
    def analyze_account(self):
        """Request account analysis with SSE streaming."""

        account_id = generate_account_id()
        workflow = generate_workflow_type()

        request_body = {
            "account_id": account_id,
            "workflow": workflow,
            "thread_id": f"load-test-{account_id}",
            "run_id": f"run-{int(time.time() * 1000)}",
            "options": {}
        }

        # Track streaming performance
        event_count = 0
        first_event_time = None
        last_event_time = None

        with self.client.post(
            "/api/copilotkit",
            json=request_body,
            headers={"Accept": "text/event-stream"},
            stream=True,
            catch_response=True,
            name="/api/copilotkit [account_analysis]"
        ) as response:

            try:
                for line in response.iter_lines():
                    if line and line.startswith(b"data:"):
                        event_count += 1

                        if first_event_time is None:
                            first_event_time = time.time()

                        last_event_time = time.time()

                        # Check for workflow completion
                        if b"workflow_completed" in line or b"RUN_FINISHED" in line:
                            response.success()

                            # Calculate streaming duration
                            if first_event_time and last_event_time:
                                duration = last_event_time - first_event_time
                                print(f"  Stream completed: {event_count} events in {duration:.2f}s")
                            break

                        # Safety: timeout after 100 events
                        if event_count >= 100:
                            response.failure("Stream exceeded 100 events without completion")
                            break

                if event_count == 0:
                    response.failure("No events received from stream")

            except Exception as e:
                response.failure(f"Stream error: {str(e)}")

    @task(3)  # Weight: 3 (less common)
    def daily_review(self):
        """Request daily review workflow."""

        account_id = generate_account_id()

        request_body = {
            "account_id": account_id,
            "workflow": "daily_review",
            "thread_id": f"daily-{account_id}",
            "run_id": f"run-{int(time.time() * 1000)}"
        }

        with self.client.post(
            "/api/copilotkit",
            json=request_body,
            headers={"Accept": "text/event-stream"},
            stream=True,
            catch_response=True,
            name="/api/copilotkit [daily_review]"
        ) as response:

            event_count = 0

            for line in response.iter_lines():
                if line and line.startswith(b"data:"):
                    event_count += 1

                    if b"workflow_completed" in line or event_count >= 50:
                        response.success()
                        break

            if event_count == 0:
                response.failure("No events received")

    @task(1)  # Weight: 1 (rare)
    def health_check(self):
        """Check service health."""

        with self.client.get(
            "/api/copilotkit/health",
            catch_response=True,
            name="/api/copilotkit/health"
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class BurstTrafficUser(HttpUser):
    """
    Simulates burst traffic patterns (spike tests).

    User Behavior:
    - Sends requests in rapid bursts
    - Minimal wait time between requests
    """

    wait_time = constant_pacing(0.5)  # Constant 0.5s between requests

    @task
    def burst_request(self):
        """Send burst request."""

        account_id = generate_account_id()

        request_body = {
            "account_id": account_id,
            "workflow": "account_analysis",
            "thread_id": f"burst-{account_id}",
            "run_id": f"run-{int(time.time() * 1000)}"
        }

        with self.client.post(
            "/api/copilotkit",
            json=request_body,
            headers={"Accept": "text/event-stream"},
            stream=True,
            catch_response=True,
            name="/api/copilotkit [burst]"
        ) as response:

            # Just verify stream starts
            event_count = 0

            for line in response.iter_lines():
                if line and line.startswith(b"data:"):
                    event_count += 1

                    if event_count >= 5:  # Only read first 5 events
                        response.success()
                        break

            if event_count == 0:
                response.failure("No events received")


# ============================================================================
# Event Listeners (Metrics & Reporting)
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*80)
    print("LOAD TEST STARTED")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Host: {environment.host}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n" + "="*80)
    print("LOAD TEST COMPLETED")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")

    stats = environment.runner.stats.total

    print(f"\nAggregate Results:")
    print(f"  Total Requests:        {stats.num_requests}")
    print(f"  Total Failures:        {stats.num_failures}")
    print(f"  Failure Rate:          {(stats.num_failures / stats.num_requests * 100) if stats.num_requests > 0 else 0:.2f}%")
    print(f"  Average Response Time: {stats.avg_response_time:.2f}ms")
    print(f"  Min Response Time:     {stats.min_response_time:.2f}ms")
    print(f"  Max Response Time:     {stats.max_response_time:.2f}ms")
    print(f"  Median Response Time:  {stats.median_response_time:.2f}ms")
    print(f"  P95 Response Time:     {stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"  P99 Response Time:     {stats.get_response_time_percentile(0.99):.2f}ms")
    print(f"  Requests/Second:       {stats.total_rps:.2f}")

    # Performance validation
    print(f"\nPerformance Validation:")

    failure_rate = (stats.num_failures / stats.num_requests * 100) if stats.num_requests > 0 else 0
    avg_response_time = stats.avg_response_time
    p95_response_time = stats.get_response_time_percentile(0.95)

    print(f"  Target Failure Rate:   <5%")
    print(f"  Actual Failure Rate:   {failure_rate:.2f}% {'✅ PASS' if failure_rate < 5 else '❌ FAIL'}")

    print(f"  Target Avg Response:   <2000ms")
    print(f"  Actual Avg Response:   {avg_response_time:.2f}ms {'✅ PASS' if avg_response_time < 2000 else '❌ FAIL'}")

    print(f"  Target P95 Response:   <5000ms")
    print(f"  Actual P95 Response:   {p95_response_time:.2f}ms {'✅ PASS' if p95_response_time < 5000 else '❌ FAIL'}")

    print("="*80 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called for each request (for detailed logging if needed)."""
    # Can add custom metrics here
    pass


# ============================================================================
# Load Test Scenarios
# ============================================================================

# Example usage:
#
# Scenario 1: Steady Load (50 users, 10/s spawn rate, 60s duration)
# locust -f locust_load_test.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000
#
# Scenario 2: Spike Test (100 users, 50/s spawn rate, 30s duration)
# locust -f locust_load_test.py --headless -u 100 -r 50 -t 30s --host http://localhost:8000 --user-classes BurstTrafficUser
#
# Scenario 3: Sustained Load (200 users, 20/s spawn rate, 300s duration)
# locust -f locust_load_test.py --headless -u 200 -r 20 -t 300s --host http://localhost:8000
