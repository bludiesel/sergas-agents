"""
Sergas Super Account Manager - Monitoring Integration Example
Demonstrates how to integrate Prometheus metrics into application code
Generated: 2025-10-19
"""

import time
import random
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
import asyncio

# Import metrics collector
from src.monitoring import (
    metrics_collector,
    setup_metrics,
    track_time,
    track_inprogress,
    count_errors,
)
from src.monitoring.metrics import (
    http_requests_in_progress,
    agent_queue_size,
    agent_concurrent_tasks,
    accounts_active_total,
    memory_graph_nodes_total,
    zoho_rate_limit_remaining,
)

# ============================================
# FastAPI Application Setup
# ============================================

app = FastAPI(
    title="Sergas Super Account Manager",
    version="1.0.0",
    description="Production monitoring example"
)

# Setup metrics endpoint
setup_metrics(app)


# ============================================
# Middleware for Automatic HTTP Metrics
# ============================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Automatically track HTTP request metrics"""
    method = request.method
    endpoint = request.url.path

    # Track in-progress requests
    with track_inprogress(
        http_requests_in_progress,
        labels={"method": method, "endpoint": endpoint}
    ):
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            metrics_collector.record_http_request(
                method=method,
                endpoint=endpoint,
                status=status,
                duration=duration
            )

    return response


# ============================================
# Example: Zoho Integration with Metrics
# ============================================

class ZohoClient:
    """Example Zoho client with metrics integration"""

    def __init__(self):
        self.rate_limit = 10000
        self.rate_limit_remaining = 10000

    async def get_accounts(self, limit: int = 100) -> dict:
        """Fetch accounts from Zoho with metrics tracking"""
        operation = "get_accounts"
        start_time = time.time()

        try:
            # Simulate API call
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # Simulate rate limit tracking
            self.rate_limit_remaining -= 1
            zoho_rate_limit_remaining.labels(api_type='crm').set(
                self.rate_limit_remaining
            )

            # Simulate success/failure
            if random.random() < 0.95:  # 95% success rate
                status = "success"
                result = {"accounts": [{"id": i} for i in range(limit)]}
            else:
                status = "error"
                raise Exception("Zoho API error")

            return result

        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_zoho_api_call(
                operation=operation,
                status=status,
                duration=duration,
                rate_limit_remaining=self.rate_limit_remaining
            )


# ============================================
# Example: Agent Task with Metrics
# ============================================

class ExampleAgent:
    """Example agent with comprehensive metrics tracking"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.queue = []
        self.concurrent_tasks = 0

    async def process_task(self, task_type: str, task_data: dict) -> dict:
        """Process a task with full metrics tracking"""
        start_time = time.time()

        # Update queue size
        agent_queue_size.labels(agent_type=self.agent_type).set(
            len(self.queue)
        )

        # Track concurrent tasks
        self.concurrent_tasks += 1
        agent_concurrent_tasks.labels(agent_type=self.agent_type).set(
            self.concurrent_tasks
        )

        try:
            # Simulate task processing
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Simulate success/failure
            if random.random() < 0.97:  # 97% success rate
                status = "success"
                error_type = None
                result = {"status": "completed"}
            else:
                status = "failure"
                error_type = "ProcessingError"
                raise Exception("Task processing failed")

            return result

        except Exception as e:
            status = "failure"
            error_type = type(e).__name__
            raise
        finally:
            duration = time.time() - start_time
            self.concurrent_tasks -= 1

            # Record all metrics
            metrics_collector.record_agent_task(
                agent_type=self.agent_type,
                task_type=task_type,
                duration=duration,
                status=status,
                error_type=error_type
            )

            agent_concurrent_tasks.labels(agent_type=self.agent_type).set(
                self.concurrent_tasks
            )


# ============================================
# Example: Memory Processing with Metrics
# ============================================

async def process_account_to_memory(account_data: dict) -> dict:
    """Process account into knowledge graph with metrics"""
    operation = "account_ingestion"
    start_time = time.time()

    try:
        # Simulate memory processing
        await asyncio.sleep(random.uniform(0.5, 2.0))

        # Update graph metrics
        memory_graph_nodes_total.labels(node_type='account').inc()
        memory_graph_nodes_total.labels(node_type='interaction').inc(3)

        status = "success"
        return {"nodes_created": 4, "relationships": 5}

    except Exception as e:
        status = "failure"
        raise
    finally:
        duration = time.time() - start_time
        metrics_collector.record_memory_operation(
            operation=operation,
            duration=duration,
            document_type='account',
            status=status
        )


# ============================================
# Example: Recommendation Generation
# ============================================

async def generate_recommendation(
    account_id: str,
    recommendation_type: str
) -> dict:
    """Generate recommendation with metrics tracking"""
    start_time = time.time()

    try:
        # Simulate recommendation generation
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Generate confidence score
        confidence = random.uniform(0.6, 0.95)
        priority = "high" if confidence > 0.8 else "medium"

        # Record metrics
        generation_time = time.time() - start_time
        metrics_collector.record_recommendation(
            recommendation_type=recommendation_type,
            priority=priority,
            confidence=confidence,
            generation_time=generation_time
        )

        return {
            "recommendation_id": f"rec_{account_id}",
            "type": recommendation_type,
            "confidence": confidence,
            "priority": priority
        }

    except Exception as e:
        raise


# ============================================
# Example API Endpoints
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/v1/accounts/{account_id}")
async def get_account(account_id: str):
    """Example endpoint with automatic metrics"""
    # Metrics tracked automatically by middleware

    # Simulate processing
    await asyncio.sleep(random.uniform(0.1, 0.3))

    if random.random() < 0.95:
        return {
            "account_id": account_id,
            "name": f"Account {account_id}",
            "status": "active"
        }
    else:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/sync/zoho")
async def sync_zoho_accounts():
    """Sync accounts from Zoho with metrics tracking"""
    zoho_client = ZohoClient()

    try:
        # Fetch accounts
        accounts = await zoho_client.get_accounts(limit=50)

        # Process each account
        for account in accounts.get("accounts", []):
            await process_account_to_memory(account)

        # Update active accounts metric
        accounts_active_total.labels(account_type='zoho').inc(
            len(accounts.get("accounts", []))
        )

        return {
            "status": "success",
            "accounts_synced": len(accounts.get("accounts", []))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/recommendations/generate")
async def generate_recommendations(account_id: str):
    """Generate recommendations with metrics"""

    try:
        # Generate different types of recommendations
        cross_sell = await generate_recommendation(
            account_id,
            "cross_sell"
        )

        upsell = await generate_recommendation(
            account_id,
            "upsell"
        )

        return {
            "account_id": account_id,
            "recommendations": [cross_sell, upsell]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agents/process")
async def process_agent_task(
    agent_type: str,
    task_type: str,
    task_data: dict
):
    """Process agent task with metrics"""
    agent = ExampleAgent(agent_type=agent_type)

    try:
        result = await agent.process_task(task_type, task_data)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Example: Cache Operations with Metrics
# ============================================

class MetricsAwareCache:
    """Example cache with metrics integration"""

    def __init__(self, cache_type: str = "redis"):
        self.cache_type = cache_type
        self.cache = {}

    async def get(self, key: str) -> Optional[str]:
        """Get from cache with metrics"""
        start_time = time.time()

        value = self.cache.get(key)
        hit = value is not None

        duration = time.time() - start_time
        metrics_collector.record_cache_operation(
            operation="get",
            cache_type=self.cache_type,
            hit=hit,
            duration=duration
        )

        return value

    async def set(self, key: str, value: str) -> None:
        """Set cache value with metrics"""
        start_time = time.time()

        self.cache[key] = value

        duration = time.time() - start_time
        metrics_collector.record_cache_operation(
            operation="set",
            cache_type=self.cache_type,
            hit=True,
            duration=duration
        )


# ============================================
# Usage Example
# ============================================

if __name__ == "__main__":
    import uvicorn

    # Run application with metrics enabled
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

    # Access metrics at: http://localhost:8000/metrics
    # View in Prometheus: http://localhost:9090
    # View dashboards: http://localhost:3000
