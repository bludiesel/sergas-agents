# CopilotKit Integration Refinement Plan
# SPARC Phase 4: Refinement & Testing Strategy

**Document Version:** 1.0
**Date:** 2025-10-19
**Status:** Ready for Implementation
**Owner:** Refinement Team

---

## Executive Summary

This document defines the migration path, testing strategy, and refinement approach for transitioning from custom AG UI Protocol SSE implementation to the official CopilotKit SDK. The migration ensures zero downtime, maintains backward compatibility, and validates all 8 integration requirements.

**Migration Duration:** 4 weeks
**Risk Level:** Medium (mitigated by phased rollout)
**Backward Compatibility:** Full (dual-system coexistence)
**Rollback Time:** < 5 minutes

---

## Table of Contents

1. [Migration Overview](#1-migration-overview)
2. [Current State Analysis](#2-current-state-analysis)
3. [Migration Phases](#3-migration-phases)
4. [Backward Compatibility Strategy](#4-backward-compatibility-strategy)
5. [Testing Strategy](#5-testing-strategy)
6. [Validation Checkpoints](#6-validation-checkpoints)
7. [Rollback Procedures](#7-rollback-procedures)
8. [Monitoring Strategy](#8-monitoring-strategy)
9. [Risk Assessment](#9-risk-assessment)
10. [Success Criteria](#10-success-criteria)

---

## 1. Migration Overview

### 1.1 Migration Goals

**Primary Objectives:**
1. Replace custom SSE implementation with official CopilotKit SDK
2. Maintain 100% backward compatibility during transition
3. Achieve zero-downtime migration
4. Validate all 8 integration requirements
5. Establish comprehensive monitoring

**Non-Goals:**
- Rewrite existing agent logic (OrchestratorAgent, ZohoDataScout, MemoryAnalyst)
- Change API contracts with frontend
- Modify database schemas
- Alter approval workflow semantics

### 1.2 Migration Approach

**Strategy:** Blue-Green Deployment with Feature Flags

```
┌─────────────────────────────────────────────────────────┐
│           Load Balancer (Nginx/ALB)                      │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │   Feature Flag    │
        │   (copilotkit_v2) │
        └─────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│  Blue System  │   │ Green System  │
│  (Current)    │   │ (CopilotKit)  │
├───────────────┤   ├───────────────┤
│ • Custom SSE  │   │ • CopilotKit  │
│ • AG UI       │   │   SDK         │
│   Events      │   │ • LangGraph   │
│ • Works       │   │   Wrappers    │
└───────────────┘   └───────────────┘
```

**Key Principle:** Both systems run in parallel with traffic routing via feature flag.

---

## 2. Current State Analysis

### 2.1 Existing Implementation Inventory

**Backend Components:**
```
src/
├── api/routers/
│   └── copilotkit_router.py          # Custom SSE endpoint
├── agents/
│   ├── orchestrator.py                # OrchestratorAgent
│   ├── zoho_data_scout.py             # ZohoDataScout
│   └── memory_analyst.py              # MemoryAnalyst
├── events/
│   ├── ag_ui_emitter.py               # Event emitter
│   └── approval_manager.py            # Approval workflow
└── orchestrator/
    └── main_orchestrator.py           # MainOrchestrator
```

**Current Dependencies:**
```txt
# requirements.txt
ag-ui-protocol>=0.1.0
sse-starlette>=1.6.5
claude-agent-sdk>=0.1.4
```

**Current Endpoints:**
- `POST /api/copilotkit` - SSE stream endpoint
- `GET /api/copilotkit/health` - Health check

### 2.2 Agent Architecture

**Agent Hierarchy:**
```
OrchestratorAgent (FastAPI SSE)
  ├── ZohoDataScout (Claude SDK)
  │   └── Fetches account data from Zoho CRM
  ├── MemoryAnalyst (Claude SDK)
  │   └── Retrieves historical context from Cognee
  └── RecommendationAuthor (Claude SDK) [Week 7]
      └── Generates actionable recommendations
```

**Event Flow:**
```
1. Client connects → SSE /api/copilotkit
2. OrchestratorAgent.execute_with_events()
3. Yields AG UI events → SSE stream
4. Frontend receives events → Updates UI
5. Approval required → Waits for response
6. Workflow completed → Close stream
```

### 2.3 Gaps Identified

| Gap | Current State | Target State | Migration Action |
|-----|---------------|--------------|------------------|
| **1. SDK Integration** | Custom SSE server | CopilotKit SDK | Wrap agents with `CoAgent` |
| **2. LangGraph Wrapper** | Direct Claude SDK | LangGraph integration | Create graph wrappers |
| **3. Streaming Protocol** | Manual SSE formatting | CopilotKit streaming | Use SDK streaming |
| **4. State Management** | In-memory dict | CopilotKit state | Migrate to SDK state |
| **5. Approval Pattern** | Custom ApprovalManager | `renderAndWaitForResponse` | Implement SDK pattern |

---

## 3. Migration Phases

### Phase 1: Parallel Implementation (Week 1)

**Goal:** Install CopilotKit SDK and create parallel implementation without affecting production

#### Day 1-2: Dependency Installation

**Tasks:**
```bash
# Install CopilotKit SDK
pip install copilotkit>=1.0.0

# Install LangGraph for agent wrappers
pip install langgraph>=0.2.0

# Update requirements.txt
cat >> requirements.txt <<EOF
# CopilotKit Integration
copilotkit>=1.0.0
langgraph>=0.2.0
EOF

# Verify installation
python -c "import copilotkit; print(copilotkit.__version__)"
python -c "import langgraph; print(langgraph.__version__)"
```

**Deliverable:** ✅ CopilotKit SDK installed and verified

#### Day 3-5: LangGraph Agent Wrappers

**File:** `src/copilotkit/agent_wrappers.py`

```python
"""LangGraph wrappers for existing Claude SDK agents.

Wraps OrchestratorAgent, ZohoDataScout, MemoryAnalyst with LangGraph
for CopilotKit compatibility while preserving existing logic.
"""

from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from src.agents.orchestrator import OrchestratorAgent
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst


class AgentState(BaseModel):
    """Shared state for LangGraph agents."""

    account_id: str
    workflow: str
    session_id: str

    # Data accumulated across agents
    account_data: Dict[str, Any] = Field(default_factory=dict)
    historical_context: Dict[str, Any] = Field(default_factory=dict)
    recommendations: list = Field(default_factory=list)

    # Approval state
    approval_required: bool = False
    approval_result: Dict[str, Any] = Field(default_factory=dict)

    # Execution metadata
    current_step: str = "init"
    errors: list = Field(default_factory=list)


class ZohoDataScoutWrapper:
    """LangGraph wrapper for ZohoDataScout."""

    def __init__(self, scout: ZohoDataScout):
        self.scout = scout

    async def __call__(self, state: AgentState) -> AgentState:
        """Execute ZohoDataScout and update state."""

        try:
            # Fetch account snapshot
            snapshot = await self.scout.get_account_snapshot(state.account_id)

            # Update state
            state.account_data = {
                "snapshot_id": snapshot.snapshot_id,
                "account": snapshot.account.model_dump(),
                "risk_level": snapshot.risk_level.value,
                "priority_score": snapshot.priority_score,
                "risk_signals": [s.model_dump() for s in snapshot.risk_signals]
            }
            state.current_step = "zoho_scout_completed"

        except Exception as e:
            state.errors.append({
                "agent": "zoho_scout",
                "error": str(e),
                "step": "data_fetch"
            })
            state.current_step = "error"

        return state


class MemoryAnalystWrapper:
    """LangGraph wrapper for MemoryAnalyst."""

    def __init__(self, analyst: MemoryAnalyst):
        self.analyst = analyst

    async def __call__(self, state: AgentState) -> AgentState:
        """Execute MemoryAnalyst and update state."""

        try:
            # Get historical context
            context = await self.analyst.get_historical_context(
                account_id=state.account_id,
                lookback_days=365,
                include_patterns=True
            )

            # Update state
            state.historical_context = context.model_dump()
            state.current_step = "memory_analyst_completed"

        except Exception as e:
            state.errors.append({
                "agent": "memory_analyst",
                "error": str(e),
                "step": "memory_retrieval"
            })
            state.current_step = "error"

        return state


class OrchestratorGraph:
    """LangGraph orchestrator for multi-agent workflow."""

    def __init__(
        self,
        zoho_scout: ZohoDataScout,
        memory_analyst: MemoryAnalyst
    ):
        # Create wrappers
        self.zoho_wrapper = ZohoDataScoutWrapper(zoho_scout)
        self.memory_wrapper = MemoryAnalystWrapper(memory_analyst)

        # Build graph
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("zoho_scout", self.zoho_wrapper)
        workflow.add_node("memory_analyst", self.memory_wrapper)
        workflow.add_node("approval_gate", self._approval_gate)

        # Define edges
        workflow.set_entry_point("zoho_scout")
        workflow.add_edge("zoho_scout", "memory_analyst")
        workflow.add_edge("memory_analyst", "approval_gate")
        workflow.add_edge("approval_gate", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def _approval_gate(self, state: AgentState) -> AgentState:
        """Handle approval workflow."""

        # Check if recommendations exist
        if state.get("recommendations"):
            state.approval_required = True
            state.current_step = "awaiting_approval"
        else:
            state.current_step = "completed"

        return state

    async def stream_events(
        self,
        initial_state: AgentState,
        config: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream graph execution events for CopilotKit."""

        async for event in self.graph.astream(
            initial_state,
            config=config
        ):
            # Convert LangGraph events to CopilotKit format
            yield self._convert_to_copilotkit_event(event)

    def _convert_to_copilotkit_event(
        self,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert LangGraph event to CopilotKit format."""

        # Map LangGraph events to CopilotKit structure
        # This ensures compatibility with existing frontend

        return {
            "type": "agent_update",
            "data": event,
            "timestamp": datetime.utcnow().isoformat()
        }
```

**Deliverable:** ✅ LangGraph wrappers preserve existing agent logic

#### Testing Checklist (Phase 1)

- [ ] ZohoDataScoutWrapper fetches data correctly
- [ ] MemoryAnalystWrapper retrieves context correctly
- [ ] OrchestratorGraph executes workflow end-to-end
- [ ] State propagates between agents
- [ ] Errors are captured and handled
- [ ] Events stream in correct order

---

### Phase 2: CopilotKit Integration (Week 2)

**Goal:** Integrate CopilotKit SDK with FastAPI and test new implementation

#### Day 1-3: CopilotKit FastAPI Endpoint

**File:** `src/copilotkit/copilotkit_server.py`

```python
"""CopilotKit FastAPI integration.

Official CopilotKit SDK endpoint replacing custom SSE implementation.
"""

from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CoAgent, AgentStateMessage
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, AsyncGenerator
import structlog

from src.copilotkit.agent_wrappers import (
    OrchestratorGraph,
    AgentState
)
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst
from src.services.memory_service import MemoryService
from src.integrations.zoho.integration_manager import ZohoIntegrationManager

logger = structlog.get_logger(__name__)


def create_copilotkit_agents(
    memory_service: MemoryService,
    zoho_manager: ZohoIntegrationManager
) -> list:
    """Create CopilotKit CoAgents from existing agents."""

    # Initialize existing agents
    zoho_scout = ZohoDataScout(
        zoho_manager=zoho_manager,
        memory_service=memory_service
    )

    memory_analyst = MemoryAnalyst(
        memory_service=memory_service
    )

    # Create LangGraph orchestrator
    orchestrator_graph = OrchestratorGraph(
        zoho_scout=zoho_scout,
        memory_analyst=memory_analyst
    )

    # Wrap as CoAgent
    orchestrator_coagent = CoAgent(
        name="orchestrator",
        description="Coordinates multi-agent account analysis workflow",

        # Define agent state schema
        state_render=lambda state: AgentStateMessage(
            agent_name="orchestrator",
            state={
                "current_step": state.get("current_step", "init"),
                "account_id": state.get("account_id", ""),
                "workflow": state.get("workflow", "")
            },
            done=state.get("current_step") in ["completed", "error"]
        ),

        # Execution function
        run=lambda state, config: orchestrator_graph.stream_events(
            initial_state=AgentState(**state),
            config=config
        )
    )

    return [orchestrator_coagent]


def setup_copilotkit_endpoint(
    app: FastAPI,
    memory_service: MemoryService,
    zoho_manager: ZohoIntegrationManager,
    endpoint_path: str = "/api/copilotkit/v2"
) -> None:
    """Add CopilotKit endpoint to FastAPI app.

    Args:
        app: FastAPI application instance
        memory_service: Memory service for agent context
        zoho_manager: Zoho integration manager
        endpoint_path: Path for CopilotKit endpoint (default: /api/copilotkit/v2)
    """

    logger.info(
        "setting_up_copilotkit_endpoint",
        endpoint=endpoint_path
    )

    try:
        # Create CoAgents
        agents = create_copilotkit_agents(
            memory_service=memory_service,
            zoho_manager=zoho_manager
        )

        # Add CopilotKit endpoint (uses official SDK)
        add_fastapi_endpoint(
            app,
            agents=agents,
            endpoint=endpoint_path
        )

        logger.info(
            "copilotkit_endpoint_configured",
            endpoint=endpoint_path,
            agent_count=len(agents)
        )

    except Exception as e:
        logger.error(
            "copilotkit_setup_failed",
            error=str(e),
            endpoint=endpoint_path
        )
        raise


# Health check for new endpoint
async def copilotkit_v2_health_check() -> Dict[str, str]:
    """Health check for CopilotKit v2 endpoint."""

    return {
        "status": "healthy",
        "service": "copilotkit-v2",
        "protocol": "official-sdk",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Deliverable:** ✅ CopilotKit endpoint functional alongside existing endpoint

#### Day 4-5: Feature Flag Implementation

**File:** `src/config/feature_flags.py`

```python
"""Feature flag system for gradual rollout.

Allows traffic splitting between old and new CopilotKit implementations.
"""

from enum import Enum
from typing import Optional
import redis
import structlog

logger = structlog.get_logger(__name__)


class CopilotKitVersion(str, Enum):
    """CopilotKit implementation versions."""
    V1_CUSTOM_SSE = "v1"          # Current custom SSE
    V2_OFFICIAL_SDK = "v2"        # New official SDK


class FeatureFlagManager:
    """Manage feature flags for CopilotKit migration."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_version = CopilotKitVersion.V1_CUSTOM_SSE

    def get_copilotkit_version(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> CopilotKitVersion:
        """Determine which CopilotKit version to use.

        Decision flow:
        1. Check user-specific override
        2. Check session-specific override
        3. Check global rollout percentage
        4. Default to V1

        Args:
            user_id: User identifier for per-user rollout
            session_id: Session identifier for per-session testing

        Returns:
            CopilotKit version to use
        """

        # Check user override
        if user_id:
            override = self.redis.get(f"feature:copilotkit:user:{user_id}")
            if override:
                return CopilotKitVersion(override.decode())

        # Check session override
        if session_id:
            override = self.redis.get(f"feature:copilotkit:session:{session_id}")
            if override:
                return CopilotKitVersion(override.decode())

        # Check global rollout percentage
        rollout_pct = int(self.redis.get("feature:copilotkit:rollout_pct") or 0)

        if rollout_pct > 0:
            # Use hash of user_id or session_id to deterministically assign
            key = user_id or session_id or "anonymous"
            hash_value = hash(key) % 100

            if hash_value < rollout_pct:
                logger.info(
                    "copilotkit_version_selected",
                    version="v2",
                    reason="rollout_percentage",
                    key=key
                )
                return CopilotKitVersion.V2_OFFICIAL_SDK

        # Default to V1
        return self.default_version

    def set_rollout_percentage(self, percentage: int) -> None:
        """Set global rollout percentage for V2.

        Args:
            percentage: 0-100, percentage of traffic to route to V2
        """

        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        self.redis.set("feature:copilotkit:rollout_pct", percentage)

        logger.info(
            "copilotkit_rollout_updated",
            percentage=percentage
        )

    def enable_for_user(self, user_id: str, version: CopilotKitVersion) -> None:
        """Enable specific version for user (testing/debugging)."""

        self.redis.set(
            f"feature:copilotkit:user:{user_id}",
            version.value
        )

        logger.info(
            "copilotkit_user_override",
            user_id=user_id,
            version=version.value
        )


# Router modification to use feature flags
# File: src/api/routers/copilotkit_router.py (UPDATE)

from src.config.feature_flags import FeatureFlagManager, CopilotKitVersion

@router.post("/copilotkit")
async def stream_agent_execution(
    request: Request,
    body: AgentExecutionRequest,
    feature_flags: FeatureFlagManager = Depends(get_feature_flags)
) -> StreamingResponse:
    """Route to appropriate CopilotKit implementation based on feature flag."""

    # Determine which version to use
    version = feature_flags.get_copilotkit_version(
        user_id=request.state.user_id if hasattr(request.state, 'user_id') else None,
        session_id=body.thread_id
    )

    if version == CopilotKitVersion.V2_OFFICIAL_SDK:
        # Route to new CopilotKit SDK endpoint
        logger.info("routing_to_copilotkit_v2", thread_id=body.thread_id)
        return await _route_to_v2(request, body)
    else:
        # Route to existing custom SSE implementation
        logger.info("routing_to_copilotkit_v1", thread_id=body.thread_id)
        return await _route_to_v1(request, body)
```

**Deliverable:** ✅ Feature flag system enables traffic splitting

#### Testing Checklist (Phase 2)

- [ ] CopilotKit SDK endpoint responds to requests
- [ ] CoAgent wrapping preserves agent behavior
- [ ] Feature flag routes traffic correctly
- [ ] V1 and V2 can run simultaneously
- [ ] Redis feature flags update in real-time
- [ ] Health checks pass for both versions

---

### Phase 3: Traffic Switch & Validation (Week 3)

**Goal:** Gradually shift traffic to CopilotKit SDK and validate requirements

#### Day 1: Canary Deployment (1% traffic)

**Tasks:**
```bash
# Set rollout to 1%
redis-cli SET feature:copilotkit:rollout_pct 1

# Monitor metrics
watch -n 5 'curl -s http://localhost:8000/metrics | grep copilotkit'
```

**Validation:**
- [ ] No increase in error rate
- [ ] Latency within acceptable range (< 500ms)
- [ ] Events streaming correctly
- [ ] Approval workflow functional

#### Day 2-3: Expand to 10% traffic

**Tasks:**
```bash
# Increase rollout
redis-cli SET feature:copilotkit:rollout_pct 10

# A/B test comparison
python scripts/ab_test_copilotkit.py --duration 2h
```

**Validation:**
- [ ] Compare metrics: V1 vs V2
  - Latency (p50, p95, p99)
  - Error rate
  - Approval success rate
  - User satisfaction
- [ ] No regressions detected

#### Day 4: Expand to 50% traffic

**Tasks:**
```bash
# Increase rollout
redis-cli SET feature:copilotkit:rollout_pct 50

# Load test
locust -f tests/load/copilotkit_load.py --users 100 --spawn-rate 10
```

**Validation:**
- [ ] System handles 50% load on V2
- [ ] No performance degradation
- [ ] Approval workflow scales correctly

#### Day 5: Full rollout (100% traffic)

**Tasks:**
```bash
# Full rollout
redis-cli SET feature:copilotkit:rollout_pct 100

# Monitor for 24 hours
python scripts/monitor_copilotkit.py --duration 24h --alert-on-error
```

**Validation:**
- [ ] All traffic on V2
- [ ] No critical errors
- [ ] User feedback positive
- [ ] Performance metrics stable

---

### Phase 4: Deprecation & Cleanup (Week 4)

**Goal:** Remove old implementation and finalize migration

#### Day 1-2: Code Deprecation

**Tasks:**
1. Mark old code as deprecated:

```python
# src/api/routers/copilotkit_router.py

@deprecated(
    version="2.0.0",
    reason="Replaced by official CopilotKit SDK at /api/copilotkit/v2"
)
async def stream_agent_execution_v1(...):
    """DEPRECATED: Use /api/copilotkit/v2 instead."""
    ...
```

2. Update documentation
3. Notify users of deprecation

#### Day 3-4: Remove Old Code

**Files to Remove:**
```
src/
├── api/routers/
│   └── copilotkit_router.py       # DELETE (replaced by copilotkit_server.py)
├── events/
│   └── ag_ui_emitter.py           # DELETE (replaced by CopilotKit SDK)
└── [other deprecated files]
```

**Commit Message:**
```
feat: Complete migration to CopilotKit SDK

BREAKING CHANGE: Remove custom SSE implementation in favor of
official CopilotKit SDK. All traffic now uses /api/copilotkit/v2.

- Remove src/api/routers/copilotkit_router.py
- Remove src/events/ag_ui_emitter.py
- Update all references to use CopilotKit SDK
- Update documentation

Ref: docs/sparc/04_COPILOTKIT_REFINEMENT.md
```

#### Day 5: Final Validation

**Tasks:**
- [ ] Run full test suite
- [ ] Verify all 8 requirements
- [ ] Update deployment documentation
- [ ] Archive old code in git history

---

## 4. Backward Compatibility Strategy

### 4.1 Coexistence Approach

**Can both systems coexist?** YES ✅

**Architecture:**
```
┌────────────────────────────────────────┐
│      Load Balancer / Nginx             │
└──────────────┬─────────────────────────┘
               │
    ┌──────────┴──────────┐
    │  Feature Flag Check │
    │  (Redis)            │
    └──────────┬──────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ V1: Custom  │   │ V2: CopilotKit│
│ SSE         │   │ SDK         │
├─────────────┤   ├─────────────┤
│ /api/       │   │ /api/       │
│ copilotkit  │   │ copilotkit  │
│             │   │ /v2         │
└─────────────┘   └─────────────┘
      │                 │
      └────────┬────────┘
               │
               ▼
    ┌──────────────────┐
    │  Shared Services │
    │  • ZohoManager   │
    │  • MemoryService │
    │  • PostgreSQL    │
    └──────────────────┘
```

### 4.2 Compatibility Matrix

| Component | V1 Support | V2 Support | Shared |
|-----------|-----------|-----------|--------|
| **Agents** | ✅ Direct | ✅ LangGraph wrapped | Same logic |
| **Zoho API** | ✅ | ✅ | ✅ Shared client |
| **Memory (Cognee)** | ✅ | ✅ | ✅ Shared service |
| **Database** | ✅ | ✅ | ✅ Same schema |
| **Approval Workflow** | ✅ Custom | ✅ SDK pattern | Different API |
| **Event Format** | ✅ AG UI | ✅ CopilotKit | Compatible |

### 4.3 API Compatibility

**Endpoint Mapping:**
| V1 Endpoint | V2 Endpoint | Compatibility |
|-------------|-------------|---------------|
| `POST /api/copilotkit` | `POST /api/copilotkit` (feature flag) | 100% compatible |
| `GET /api/copilotkit/health` | `GET /api/copilotkit/v2/health` | New endpoint |

**Event Format Compatibility:**

Both V1 and V2 emit compatible events for frontend:

```json
// V1 (Custom SSE)
{
  "event": "agent_started",
  "data": {
    "agent": "zoho_scout",
    "step": 1,
    "task": "Fetching account data"
  }
}

// V2 (CopilotKit SDK) - COMPATIBLE
{
  "event": "agent_started",
  "data": {
    "agent": "zoho_scout",
    "step": 1,
    "task": "Fetching account data"
  }
}
```

**Backward Compatibility Guarantee:** Frontend code requires ZERO changes.

---

## 5. Testing Strategy

### 5.1 Testing Pyramid

```
        /\
       /  \      E2E Tests (5%)
      /────\     - Complete workflow tests
     /  /\  \    - Multi-agent orchestration
    /  /  \  \   - Approval workflow end-to-end
   /──/────\──\
  /  /  /\  \  \ Integration Tests (20%)
 /  /  /  \  \  \ - Agent wrappers
/──/──/────\──\──\ - CopilotKit SDK integration
\  \  \    /  /  / - SSE streaming
 \  \  \  /  /  /
  \  \  \/  /  /  Unit Tests (75%)
   \  \    /  /   - Individual agents
    \  \  /  /    - State management
     \  \/  /     - Error handling
      \    /
       \  /
        \/
```

### 5.2 Unit Tests (75% of test suite)

#### 5.2.1 LangGraph Wrapper Tests

**File:** `tests/unit/copilotkit/test_agent_wrappers.py`

```python
"""Unit tests for LangGraph agent wrappers."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.copilotkit.agent_wrappers import (
    ZohoDataScoutWrapper,
    MemoryAnalystWrapper,
    OrchestratorGraph,
    AgentState
)


@pytest.mark.asyncio
async def test_zoho_scout_wrapper_success():
    """Test ZohoDataScoutWrapper with successful data fetch."""

    # Mock ZohoDataScout
    mock_scout = MagicMock()
    mock_snapshot = MagicMock()
    mock_snapshot.snapshot_id = "snapshot_123"
    mock_snapshot.risk_level.value = "high"
    mock_snapshot.priority_score = 85
    mock_scout.get_account_snapshot = AsyncMock(return_value=mock_snapshot)

    # Create wrapper
    wrapper = ZohoDataScoutWrapper(mock_scout)

    # Initial state
    state = AgentState(
        account_id="ACC-001",
        workflow="account_analysis",
        session_id="session_123"
    )

    # Execute
    result = await wrapper(state)

    # Assertions
    assert result.account_data["snapshot_id"] == "snapshot_123"
    assert result.account_data["risk_level"] == "high"
    assert result.current_step == "zoho_scout_completed"
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_zoho_scout_wrapper_error():
    """Test ZohoDataScoutWrapper with error handling."""

    # Mock ZohoDataScout with error
    mock_scout = MagicMock()
    mock_scout.get_account_snapshot = AsyncMock(
        side_effect=Exception("Zoho API timeout")
    )

    wrapper = ZohoDataScoutWrapper(mock_scout)

    state = AgentState(
        account_id="ACC-001",
        workflow="account_analysis",
        session_id="session_123"
    )

    # Execute
    result = await wrapper(state)

    # Assertions
    assert result.current_step == "error"
    assert len(result.errors) == 1
    assert result.errors[0]["agent"] == "zoho_scout"
    assert "Zoho API timeout" in result.errors[0]["error"]


@pytest.mark.asyncio
async def test_orchestrator_graph_full_workflow():
    """Test OrchestratorGraph executes full workflow."""

    # Mock agents
    mock_scout = MagicMock()
    mock_analyst = MagicMock()

    # ... setup mocks ...

    graph = OrchestratorGraph(
        zoho_scout=mock_scout,
        memory_analyst=mock_analyst
    )

    initial_state = AgentState(
        account_id="ACC-001",
        workflow="account_analysis",
        session_id="session_123"
    )

    # Execute
    events = []
    async for event in graph.stream_events(
        initial_state,
        config={"thread_id": "thread_123"}
    ):
        events.append(event)

    # Assertions
    assert len(events) > 0
    assert any(e.get("type") == "agent_update" for e in events)
```

**Test Coverage Targets:**
- Line coverage: > 90%
- Branch coverage: > 85%
- All error paths tested

#### 5.2.2 CopilotKit Integration Tests

**File:** `tests/unit/copilotkit/test_copilotkit_server.py`

```python
"""Unit tests for CopilotKit FastAPI integration."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.copilotkit.copilotkit_server import (
    create_copilotkit_agents,
    setup_copilotkit_endpoint
)


def test_create_copilotkit_agents():
    """Test CoAgent creation from existing agents."""

    mock_memory = MagicMock()
    mock_zoho = MagicMock()

    agents = create_copilotkit_agents(
        memory_service=mock_memory,
        zoho_manager=mock_zoho
    )

    assert len(agents) == 1
    assert agents[0].name == "orchestrator"
    assert callable(agents[0].run)


@pytest.mark.asyncio
async def test_copilotkit_endpoint_setup():
    """Test CopilotKit endpoint setup on FastAPI."""

    from fastapi import FastAPI

    app = FastAPI()
    mock_memory = MagicMock()
    mock_zoho = MagicMock()

    # Setup endpoint
    setup_copilotkit_endpoint(
        app=app,
        memory_service=mock_memory,
        zoho_manager=mock_zoho,
        endpoint_path="/api/copilotkit/v2"
    )

    # Verify routes added
    routes = [route.path for route in app.routes]
    assert "/api/copilotkit/v2" in routes
```

### 5.3 Integration Tests (20% of test suite)

#### 5.3.1 Agent Wrapper Integration

**File:** `tests/integration/copilotkit/test_agent_integration.py`

```python
"""Integration tests for CopilotKit agent wrappers."""

import pytest
from datetime import datetime

from src.copilotkit.agent_wrappers import OrchestratorGraph, AgentState
from src.agents.zoho_data_scout import ZohoDataScout
from src.agents.memory_analyst import MemoryAnalyst


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_graph_with_real_agents(
    memory_service,
    zoho_manager,
    test_account_id
):
    """Test OrchestratorGraph with real agent instances."""

    # Create real agents
    zoho_scout = ZohoDataScout(
        zoho_manager=zoho_manager,
        memory_service=memory_service
    )

    memory_analyst = MemoryAnalyst(
        memory_service=memory_service
    )

    # Create graph
    graph = OrchestratorGraph(
        zoho_scout=zoho_scout,
        memory_analyst=memory_analyst
    )

    # Initial state
    state = AgentState(
        account_id=test_account_id,
        workflow="account_analysis",
        session_id=f"test_session_{datetime.utcnow().timestamp()}"
    )

    # Execute workflow
    events = []
    async for event in graph.stream_events(
        initial_state=state,
        config={"thread_id": state.session_id}
    ):
        events.append(event)

    # Assertions
    assert len(events) > 0

    # Verify workflow progression
    event_types = [e.get("type") for e in events]
    assert "agent_update" in event_types

    # Verify data was fetched
    final_state = events[-1].get("data", {})
    assert "account_data" in final_state
    assert "historical_context" in final_state


@pytest.mark.integration
@pytest.mark.asyncio
async def test_copilotkit_endpoint_e2e(
    test_client,
    test_account_id
):
    """Test CopilotKit endpoint end-to-end."""

    # Request payload
    payload = {
        "account_id": test_account_id,
        "workflow": "account_analysis",
        "thread_id": "test_thread_123",
        "run_id": "test_run_456"
    }

    # Make request to CopilotKit v2 endpoint
    response = test_client.post(
        "/api/copilotkit",
        json=payload,
        headers={"X-Feature-Flag-CopilotKit": "v2"}
    )

    # Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    # Parse SSE events
    events = []
    for line in response.iter_lines():
        if line.startswith(b"data:"):
            events.append(json.loads(line[5:]))

    assert len(events) > 0
```

#### 5.3.2 SSE Streaming Tests

**File:** `tests/integration/copilotkit/test_sse_streaming.py`

```python
"""Integration tests for SSE streaming with CopilotKit."""

import pytest
import asyncio
from httpx import AsyncClient
import json


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sse_stream_connection():
    """Test SSE connection and event streaming."""

    async with AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/copilotkit",
            json={
                "account_id": "ACC-TEST-001",
                "workflow": "account_analysis"
            },
            headers={"X-Feature-Flag-CopilotKit": "v2"}
        ) as response:
            assert response.status_code == 200

            events_received = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    event = json.loads(line[5:])
                    events_received.append(event)

                    # Stop after first event for test
                    if len(events_received) >= 1:
                        break

            assert len(events_received) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sse_stream_disconnect_handling():
    """Test SSE stream handles client disconnect gracefully."""

    async with AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/copilotkit",
            json={"account_id": "ACC-TEST-002", "workflow": "account_analysis"},
            headers={"X-Feature-Flag-CopilotKit": "v2"}
        ) as response:
            # Read one event then disconnect
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    break  # Disconnect after first event

    # Verify no resource leaks (check logs, metrics)
    # Server should cleanup connection gracefully
```

### 5.4 End-to-End Tests (5% of test suite)

#### 5.4.1 Complete Workflow Test

**File:** `tests/e2e/copilotkit/test_complete_workflow.py`

```python
"""End-to-end tests for complete CopilotKit workflow."""

import pytest
from playwright.async_api import async_playwright
import asyncio


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_account_analysis_workflow():
    """Test complete workflow: Request → Agent execution → Approval → Completion."""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to dashboard
        await page.goto("http://localhost:3000")

        # Trigger account analysis
        await page.click("button[data-testid='analyze-account']")
        await page.fill("input[name='account_id']", "ACC-E2E-001")
        await page.click("button[type='submit']")

        # Wait for agent activity to appear
        await page.wait_for_selector(".agent-activity", timeout=10000)

        # Verify agent events streaming
        zoho_scout_started = await page.wait_for_selector(
            "text=Zoho Data Scout started",
            timeout=15000
        )
        assert zoho_scout_started is not None

        memory_analyst_started = await page.wait_for_selector(
            "text=Memory Analyst started",
            timeout=15000
        )
        assert memory_analyst_started is not None

        # Wait for approval request
        approval_card = await page.wait_for_selector(
            ".approval-card",
            timeout=20000
        )
        assert approval_card is not None

        # Approve recommendation
        await page.click("button[data-action='approve']")

        # Wait for workflow completion
        completion_message = await page.wait_for_selector(
            "text=Workflow completed",
            timeout=10000
        )
        assert completion_message is not None

        # Close browser
        await browser.close()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_agent_orchestration():
    """Test multi-agent orchestration with CopilotKit."""

    # Similar structure testing:
    # - Multiple agents running in parallel
    # - Agent handoffs
    # - State synchronization
    # - Error recovery
    ...
```

#### 5.4.2 HITL Approval Tests

**File:** `tests/e2e/copilotkit/test_hitl_workflow.py`

```python
"""End-to-end tests for human-in-the-loop approval workflow."""

import pytest
from playwright.async_api import async_playwright


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_approval_with_inline_editing():
    """Test approval workflow with inline editing."""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await (await browser.new_context()).new_page()

        # ... trigger workflow ...

        # Wait for approval card
        await page.wait_for_selector(".approval-card")

        # Click edit button
        await page.click("button[data-action='edit']")

        # Modify recommendation
        await page.fill("textarea[name='recommendation']", "Updated recommendation text")

        # Approve with modifications
        await page.click("button[data-action='approve-modified']")

        # Verify modified data was sent
        # Check backend received modified recommendation
        ...


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_approval_timeout():
    """Test approval workflow timeout handling."""

    # Set short timeout
    timeout_seconds = 5

    # Trigger workflow
    # ... send request with timeout=5 ...

    # Wait for timeout
    await asyncio.sleep(timeout_seconds + 1)

    # Verify auto-rejection
    # Check workflow marked as timed out
    ...


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_approval_rejection():
    """Test approval rejection with reason."""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await (await browser.new_context()).new_page()

        # ... trigger workflow, wait for approval ...

        # Click reject
        await page.click("button[data-action='reject']")

        # Enter rejection reason
        await page.fill("textarea[name='reason']", "Data quality concerns")
        await page.click("button[data-action='confirm-reject']")

        # Verify rejection recorded
        # Check audit log
        ...
```

### 5.5 Load Testing

#### 5.5.1 Multi-Agent Load Test

**File:** `tests/performance/copilotkit_load.py`

```python
"""Load testing for CopilotKit endpoint."""

from locust import HttpUser, task, between
import random


class CopilotKitUser(HttpUser):
    """Simulate user interacting with CopilotKit endpoint."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    @task
    def analyze_account(self):
        """Trigger account analysis workflow."""

        account_id = f"ACC-LOAD-{random.randint(1, 1000)}"

        with self.client.post(
            "/api/copilotkit",
            json={
                "account_id": account_id,
                "workflow": "account_analysis",
                "thread_id": f"thread_{random.randint(1, 10000)}",
                "run_id": f"run_{random.randint(1, 100000)}"
            },
            headers={"X-Feature-Flag-CopilotKit": "v2"},
            catch_response=True,
            stream=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
            else:
                # Read SSE stream
                for line in response.iter_lines():
                    if line.startswith(b"data:"):
                        # Process event
                        pass


# Run load test:
# locust -f tests/performance/copilotkit_load.py --users 100 --spawn-rate 10
```

**Load Test Targets:**
- 100 concurrent users
- 1000 requests per minute
- < 2% error rate
- p95 latency < 2 seconds
- p99 latency < 5 seconds

---

## 6. Validation Checkpoints

### 6.1 Requirement Validation Matrix

| Requirement | Validation Test | Success Criteria | Status |
|-------------|----------------|------------------|--------|
| **REQ-1: Multi-Agent Orchestration** | `test_orchestrator_graph_full_workflow()` | All agents execute in sequence | ⏳ |
| **REQ-2: Real-Time Streaming** | `test_sse_stream_connection()` | Events stream < 500ms latency | ⏳ |
| **REQ-3: HITL Approval** | `test_approval_with_inline_editing()` | Approval workflow functional | ⏳ |
| **REQ-4: State Persistence** | `test_state_propagates_between_agents()` | State shared across agents | ⏳ |
| **REQ-5: Error Recovery** | `test_zoho_scout_wrapper_error()` | Errors captured, workflow continues | ⏳ |
| **REQ-6: Audit Trail** | `test_approval_events_logged()` | All decisions audited | ⏳ |
| **REQ-7: Scalability** | `copilotkit_load.py` | Handles 100 concurrent users | ⏳ |
| **REQ-8: Backward Compatibility** | `test_v1_v2_parity()` | V1 and V2 produce same results | ⏳ |

### 6.2 Checkpoint Schedule

**Week 1 Checkpoint (End of Phase 1):**
- [ ] REQ-1: Multi-Agent Orchestration validated
- [ ] REQ-4: State Persistence validated
- [ ] REQ-5: Error Recovery validated

**Week 2 Checkpoint (End of Phase 2):**
- [ ] REQ-2: Real-Time Streaming validated
- [ ] REQ-3: HITL Approval validated
- [ ] REQ-6: Audit Trail validated

**Week 3 Checkpoint (End of Phase 3):**
- [ ] REQ-7: Scalability validated (load testing)
- [ ] REQ-8: Backward Compatibility validated (A/B testing)

**Week 4 Checkpoint (Final):**
- [ ] ALL requirements validated
- [ ] Production metrics confirm success
- [ ] User acceptance complete

---

## 7. Rollback Procedures

### 7.1 Rollback Decision Criteria

**Trigger rollback if ANY of these occur:**

| Severity | Condition | Threshold | Action |
|----------|-----------|-----------|--------|
| **P0 - Critical** | System downtime | > 1 minute | Immediate rollback |
| **P0 - Critical** | Data loss | ANY occurrence | Immediate rollback |
| **P1 - High** | Error rate spike | > 5% | Rollback within 5 minutes |
| **P1 - High** | Approval workflow failure | > 10% | Rollback within 10 minutes |
| **P2 - Medium** | Latency degradation | p95 > 3 seconds | Rollback within 30 minutes |
| **P2 - Medium** | User complaints | > 20% of users | Rollback within 1 hour |

### 7.2 Rollback Procedures

#### 7.2.1 Immediate Rollback (< 5 minutes)

**Procedure:**

```bash
# Step 1: Set feature flag to 0% (route all traffic to V1)
redis-cli SET feature:copilotkit:rollout_pct 0

# Step 2: Verify traffic routing
curl -s http://localhost:8000/metrics | grep "copilotkit_version=\"v1\""
# Should show 100% traffic on v1

# Step 3: Monitor for 5 minutes
watch -n 10 'curl -s http://localhost:8000/metrics | grep copilotkit'

# Step 4: Alert team
python scripts/alert_team.py --message "CopilotKit rolled back to V1" --severity high
```

**Expected Time:** < 5 minutes
**Downtime:** 0 seconds (traffic switches instantly)

#### 7.2.2 Code Rollback (< 30 minutes)

**If feature flag rollback insufficient:**

```bash
# Step 1: Revert to previous commit
git revert HEAD --no-edit

# Step 2: Rebuild Docker image
docker build -t sergas-agents:rollback .

# Step 3: Deploy to production
kubectl rollout undo deployment/sergas-agents

# Step 4: Wait for rollout
kubectl rollout status deployment/sergas-agents

# Step 5: Verify
curl -s http://localhost:8000/api/copilotkit/health
```

**Expected Time:** < 30 minutes
**Downtime:** < 2 minutes (during pod restart)

### 7.3 Rollback Validation

**After rollback, verify:**
- [ ] Error rate returns to baseline (< 1%)
- [ ] Latency returns to baseline (p95 < 1s)
- [ ] No user complaints
- [ ] Approval workflow functional
- [ ] All agents operational

### 7.4 Post-Rollback Actions

**Root Cause Analysis:**
1. Collect logs from failed deployment
2. Analyze metrics during incident
3. Identify root cause
4. Document in incident report
5. Create fix and test in staging
6. Schedule re-deployment

---

## 8. Monitoring Strategy

### 8.1 Metrics to Track

#### 8.1.1 System Metrics

**Availability:**
- Uptime (target: > 99.9%)
- Request success rate (target: > 99%)
- SSE connection stability (target: > 99%)

**Performance:**
- Latency: p50, p95, p99 (target: p95 < 1s)
- Throughput: requests/minute
- Event emission rate: events/second

**Resource Usage:**
- CPU utilization (target: < 70%)
- Memory utilization (target: < 80%)
- Database connections (monitor for leaks)

#### 8.1.2 Application Metrics

**CopilotKit-Specific:**
```python
# Prometheus metrics

# Request count by version
copilotkit_requests_total{version="v1"} 1243
copilotkit_requests_total{version="v2"} 857

# Latency by version
copilotkit_request_duration_seconds{version="v1", quantile="0.95"} 0.8
copilotkit_request_duration_seconds{version="v2", quantile="0.95"} 0.9

# Error rate by version
copilotkit_errors_total{version="v1", error_type="timeout"} 5
copilotkit_errors_total{version="v2", error_type="timeout"} 2

# Active SSE connections
copilotkit_active_connections{version="v1"} 23
copilotkit_active_connections{version="v2"} 17
```

**Agent Metrics:**
```python
# Agent execution duration
agent_execution_duration_seconds{agent="zoho_scout", quantile="0.95"} 1.2
agent_execution_duration_seconds{agent="memory_analyst", quantile="0.95"} 0.8

# Agent success rate
agent_success_rate{agent="zoho_scout"} 0.99
agent_success_rate{agent="memory_analyst"} 0.98

# Approval workflow metrics
approval_requests_total 145
approval_approved_total 87
approval_rejected_total 23
approval_timeout_total 35
```

#### 8.1.3 Business Metrics

**Workflow Success:**
- Workflows completed (target: > 95%)
- Average workflow duration (target: < 2 minutes)
- Approval rate (target: > 60%)

**User Engagement:**
- Daily active users
- Workflows per user per day
- User satisfaction score (from surveys)

### 8.2 Monitoring Tools

**Infrastructure Monitoring:**
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **AlertManager**: Alert routing

**Application Monitoring:**
- **Structlog**: Structured logging
- **Datadog**: APM and distributed tracing
- **Sentry**: Error tracking

**Log Aggregation:**
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **CloudWatch Logs**: AWS-native logging

### 8.3 Alert Configuration

**Critical Alerts (PagerDuty):**
```yaml
# alertmanager.yml

groups:
  - name: copilotkit_critical
    interval: 30s
    rules:
      - alert: CopilotKitHighErrorRate
        expr: rate(copilotkit_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "CopilotKit error rate above 5%"
          description: "Version {{ $labels.version }} has {{ $value }} error rate"

      - alert: CopilotKitHighLatency
        expr: histogram_quantile(0.95, copilotkit_request_duration_seconds) > 3
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "CopilotKit p95 latency above 3 seconds"

      - alert: CopilotKitConnectionDrops
        expr: rate(copilotkit_connection_drops_total[5m]) > 10
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "CopilotKit SSE connections dropping frequently"
```

**Warning Alerts (Slack):**
```yaml
  - name: copilotkit_warnings
    interval: 1m
    rules:
      - alert: CopilotKitSlowPerformance
        expr: histogram_quantile(0.95, copilotkit_request_duration_seconds) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CopilotKit performance degrading"

      - alert: AgentExecutionSlow
        expr: histogram_quantile(0.95, agent_execution_duration_seconds) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Agent {{ $labels.agent }} taking longer than expected"
```

### 8.4 Monitoring Dashboards

**Dashboard 1: CopilotKit Overview**
- Request rate (V1 vs V2)
- Error rate (V1 vs V2)
- Latency distribution (V1 vs V2)
- Active SSE connections
- Feature flag rollout percentage

**Dashboard 2: Agent Performance**
- Agent execution time by agent type
- Agent success rate by agent type
- Workflow completion rate
- Approval workflow funnel

**Dashboard 3: System Health**
- CPU/Memory utilization
- Database connections
- Redis operations
- External API latency (Zoho, Cognee)

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Severity | Probability | Impact | Mitigation | Contingency |
|------|----------|-------------|--------|------------|-------------|
| **R1: LangGraph wrapper breaks agent logic** | High | 30% | Incorrect recommendations | Comprehensive unit tests, pair programming | Rollback to V1 |
| **R2: CopilotKit SDK performance issues** | Medium | 20% | Slow response times | Load testing before rollout, gradual rollout | Performance tuning or rollback |
| **R3: SSE connection instability** | Medium | 25% | Disconnects during workflow | Connection pooling, retry logic, keepalive | WebSocket fallback |
| **R4: State loss between agents** | High | 15% | Incomplete workflows | State persistence tests, checkpointing | State recovery mechanism |
| **R5: Approval workflow regression** | High | 10% | Cannot approve recommendations | E2E tests, manual QA | Rollback immediately |
| **R6: Memory leaks in new implementation** | Medium | 20% | Server crashes | Memory profiling, load testing | Add memory limits, rollback |

**Total Risk Score:** Medium (6.2/10)

### 9.2 Operational Risks

| Risk | Severity | Probability | Impact | Mitigation | Contingency |
|------|----------|-------------|--------|------------|-------------|
| **R7: Migration takes longer than planned** | Low | 40% | Delayed launch | Buffer 1 week in timeline | Extend timeline, increase resources |
| **R8: Team unfamiliar with CopilotKit SDK** | Low | 30% | Slower development | Training sessions, pair programming | Hire contractor with expertise |
| **R9: Frontend requires changes** | Medium | 15% | Additional work | Maintain event format compatibility | Revert to V1 if too complex |
| **R10: Production incident during migration** | High | 10% | User impact | Gradual rollout, monitoring | Immediate rollback |

### 9.3 Risk Mitigation Summary

**Preventive Measures:**
1. ✅ Comprehensive test suite (75% unit, 20% integration, 5% E2E)
2. ✅ Gradual rollout (1% → 10% → 50% → 100%)
3. ✅ Feature flag system for instant rollback
4. ✅ Blue-green deployment for zero downtime
5. ✅ Monitoring and alerting on all key metrics

**Detective Measures:**
1. ✅ Real-time metrics dashboards
2. ✅ Automated alerts for anomalies
3. ✅ Log aggregation and analysis
4. ✅ A/B testing comparison between V1 and V2

**Corrective Measures:**
1. ✅ Rollback procedures (< 5 minutes)
2. ✅ On-call rotation for incident response
3. ✅ Runbooks for common issues
4. ✅ Post-incident reviews and improvements

---

## 10. Success Criteria

### 10.1 Technical Success Criteria

**Functionality:**
- [ ] All 8 requirements validated (100% pass rate)
- [ ] Zero data loss during migration
- [ ] Zero downtime during migration
- [ ] Backward compatibility maintained (V1 and V2 produce identical results)

**Performance:**
- [ ] p95 latency < 1 second (same as V1)
- [ ] p99 latency < 2 seconds
- [ ] Event emission latency < 500ms
- [ ] Handles 100 concurrent users (load test pass)

**Reliability:**
- [ ] Error rate < 1% (same as V1)
- [ ] Uptime > 99.9%
- [ ] SSE connection stability > 99%
- [ ] Zero critical bugs in production

### 10.2 Business Success Criteria

**User Adoption:**
- [ ] 90% of users successfully use V2 endpoint
- [ ] User satisfaction > 80% (survey)
- [ ] No increase in support tickets
- [ ] Average approval time < 2 minutes (vs 2.5 minutes in V1)

**Operational:**
- [ ] Migration completed within 4 weeks
- [ ] Code coverage > 85%
- [ ] Documentation complete and up-to-date
- [ ] Team trained on CopilotKit SDK

### 10.3 Acceptance Criteria

**Phase 1 (Week 1):**
- [ ] LangGraph wrappers implemented
- [ ] Unit tests pass (> 90% coverage)
- [ ] Agent logic preserved (parity tests pass)

**Phase 2 (Week 2):**
- [ ] CopilotKit SDK endpoint functional
- [ ] Feature flag system operational
- [ ] Integration tests pass

**Phase 3 (Week 3):**
- [ ] 100% traffic on V2
- [ ] Load tests pass
- [ ] User acceptance testing complete

**Phase 4 (Week 4):**
- [ ] Old code removed
- [ ] Documentation updated
- [ ] Post-migration review complete

---

## Appendices

### Appendix A: Testing Commands

**Run Unit Tests:**
```bash
pytest tests/unit/copilotkit/ -v --cov=src/copilotkit --cov-report=html
```

**Run Integration Tests:**
```bash
pytest tests/integration/copilotkit/ -v -m integration
```

**Run E2E Tests:**
```bash
pytest tests/e2e/copilotkit/ -v -m e2e --headless
```

**Run Load Tests:**
```bash
locust -f tests/performance/copilotkit_load.py --users 100 --spawn-rate 10 --run-time 10m
```

**Run All Tests:**
```bash
pytest tests/ -v --cov=src --cov-report=html --cov-report=term
```

### Appendix B: Monitoring Queries

**Prometheus Queries:**

```promql
# Request rate by version
sum(rate(copilotkit_requests_total[5m])) by (version)

# Error rate by version
sum(rate(copilotkit_errors_total[5m])) by (version) / sum(rate(copilotkit_requests_total[5m])) by (version)

# Latency p95 by version
histogram_quantile(0.95, sum(rate(copilotkit_request_duration_seconds_bucket[5m])) by (le, version))

# Active connections by version
copilotkit_active_connections

# Agent execution time p95
histogram_quantile(0.95, sum(rate(agent_execution_duration_seconds_bucket[5m])) by (le, agent))
```

**Grafana Dashboard JSON:** Available at `docs/monitoring/copilotkit_dashboard.json`

### Appendix C: Rollback Playbook

**Step-by-Step Rollback:**

1. **Detect Issue** (automated alerts or manual observation)
2. **Assess Severity** (use decision criteria from Section 7.1)
3. **Execute Rollback** (use procedures from Section 7.2)
4. **Verify Rollback** (use validation checklist from Section 7.3)
5. **Notify Stakeholders** (send incident report)
6. **Root Cause Analysis** (schedule post-incident review)
7. **Implement Fix** (in staging environment)
8. **Re-Deploy** (after thorough testing)

**Rollback Contacts:**
- On-Call Engineer: [PagerDuty rotation]
- Engineering Manager: [Name, Phone, Email]
- Product Manager: [Name, Phone, Email]

### Appendix D: Migration Checklist

**Pre-Migration:**
- [ ] All requirements documented
- [ ] Test suite complete (> 85% coverage)
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Rollback procedures documented
- [ ] Team trained on CopilotKit SDK
- [ ] Stakeholders notified of timeline

**During Migration:**
- [ ] Phase 1 complete (LangGraph wrappers)
- [ ] Phase 2 complete (CopilotKit integration)
- [ ] Phase 3 complete (Traffic switch)
- [ ] All validation checkpoints passed
- [ ] No critical incidents

**Post-Migration:**
- [ ] Old code removed
- [ ] Documentation updated
- [ ] Metrics stable for 7 days
- [ ] User feedback positive
- [ ] Post-migration review complete
- [ ] Lessons learned documented

---

## Document Control

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-19 | Refinement Team | Initial version |

**Review and Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | [Name] | _________ | _____ |
| Product Manager | [Name] | _________ | _____ |
| QA Lead | [Name] | _________ | _____ |
| DevOps Lead | [Name] | _________ | _____ |

**Next Review Date:** 2025-10-26 (after Week 1 checkpoint)

---

**END OF DOCUMENT**
