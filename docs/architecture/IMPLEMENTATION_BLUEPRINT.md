# CopilotKit Enhancement Implementation Blueprint

**Author**: Architecture Coordinator
**Date**: 2025-10-20
**Status**: Ready for Implementation
**Version**: 1.0

---

## Quick Start Implementation Guide

This blueprint provides concrete, copy-paste ready implementations for the enhanced CopilotKit-GLM integration architecture.

---

## Phase 1: Enhanced Backend Implementation

### 1.1 AG-UI Protocol Integration

**Install Required Packages**:
```bash
pip install ag-ui-protocol fastapi uvicorn pydantic structlog
```

**Create AG-UI Event Emitter**:

File: `/src/adapters/ag_ui_emitter.py`
```python
"""
AG-UI Protocol Event Emitter for Claude Agent SDK Integration

Bridges Claude Agent SDK agents to CopilotKit frontend via AG-UI protocol.
Emits structured events for real-time streaming and agent coordination.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional

from ag_ui.core import (
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallResultEvent,
    StateSnapshotEvent,
    StateDeltaEvent,
    AgentStatusEvent,
)
from ag_ui.encoder import EventEncoder

class AGUIEventEmitter:
    """
    Emits AG-UI protocol events from Claude Agent SDK execution.

    Handles:
    - Agent lifecycle events
    - Message streaming
    - Tool call visualization
    - State synchronization
    - Error handling and recovery
    """

    def __init__(self):
        self.encoder = EventEncoder()

    async def emit_agent_workflow(
        self,
        orchestrator,
        workflow_id: str,
        agents: List[str],
        messages: List[Dict[str, Any]],
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute multi-agent workflow and emit AG-UI events.

        Args:
            orchestrator: Agent orchestrator instance
            workflow_id: Unique workflow identifier
            agents: List of agent names to execute
            messages: Conversation history
            initial_state: Initial application state

        Yields:
            SSE-formatted AG-UI event strings
        """
        try:
            # Workflow initialization
            run_id = f"run_{uuid.uuid4().hex[:8]}"
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"

            # Start workflow
            yield self._encode_event(RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=thread_id,
                run_id=run_id,
                workflow_id=workflow_id,
                agents=agents,
                timestamp=datetime.utcnow().isoformat()
            ))

            # Initial state snapshot
            if initial_state:
                yield self._encode_event(StateSnapshotEvent(
                    type=EventType.STATE_SNAPSHOT,
                    state=initial_state,
                    thread_id=thread_id,
                    run_id=run_id
                ))

            # Start agent status tracking
            for agent_name in agents:
                yield self._encode_event(AgentStatusEvent(
                    type=EventType.AGENT_STATUS,
                    agent_id=agent_name,
                    status="initializing",
                    thread_id=thread_id,
                    run_id=run_id
                ))

            # Execute workflow with real-time events
            async for event in self._execute_workflow_streaming(
                orchestrator, workflow_id, agents, messages,
                thread_id, run_id
            ):
                yield self._encode_event(event)

            # Final state snapshot
            final_state = await orchestrator.get_final_state(workflow_id)
            yield self._encode_event(StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                state=final_state,
                thread_id=thread_id,
                run_id=run_id
            ))

            # Workflow completion
            yield self._encode_event(RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=thread_id,
                run_id=run_id,
                workflow_id=workflow_id,
                completed_at=datetime.utcnow().isoformat()
            ))

        except Exception as e:
            # Comprehensive error handling
            yield self._encode_event(RunErrorEvent(
                type=EventType.RUN_ERROR,
                thread_id=thread_id if 'thread_id' in locals() else "unknown",
                run_id=run_id if 'run_id' in locals() else "unknown",
                workflow_id=workflow_id,
                error={
                    "code": "WORKFLOW_ERROR",
                    "message": str(e),
                    "type": type(e).__name__,
                    "recoverable": self._is_recoverable_error(e),
                    "retry_after": self._calculate_retry_delay(e)
                }
            ))

    async def _execute_workflow_streaming(
        self,
        orchestrator,
        workflow_id: str,
        agents: List[str],
        messages: List[Dict[str, Any]],
        thread_id: str,
        run_id: str
    ) -> AsyncGenerator:
        """
        Execute workflow with streaming AG-UI events.
        """
        # Start message
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            thread_id=thread_id,
            run_id=run_id
        )

        # Execute each agent with status updates
        for i, agent_name in enumerate(agents):
            # Agent starting
            yield AgentStatusEvent(
                type=EventType.AGENT_STATUS,
                agent_id=agent_name,
                status="running",
                thread_id=thread_id,
                run_id=run_id
            )

            # Stream agent response
            async for chunk in orchestrator.execute_agent_streaming(
                agent_name, messages, thread_id, run_id
            ):
                if chunk["type"] == "text":
                    # Stream text content
                    yield TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        delta=chunk["content"],
                        thread_id=thread_id,
                        run_id=run_id
                    )

                elif chunk["type"] == "tool_call":
                    # Tool invocation with visualization
                    await self._emit_tool_call_events(
                        chunk, message_id, thread_id, run_id
                    )
                    for event in self._emit_tool_call_events(chunk, message_id, thread_id, run_id):
                        yield event

                elif chunk["type"] == "state_update":
                    # State change for UI updates
                    yield StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=chunk["delta"],
                        thread_id=thread_id,
                        run_id=run_id
                    )

                elif chunk["type"] == "agent_status":
                    # Agent status update
                    yield AgentStatusEvent(
                        type=EventType.AGENT_STATUS,
                        agent_id=chunk["agent_id"],
                        status=chunk["status"],
                        progress=chunk.get("progress"),
                        thread_id=thread_id,
                        run_id=run_id
                    )

            # Agent completed
            yield AgentStatusEvent(
                type=EventType.AGENT_STATUS,
                agent_id=agent_name,
                status="completed",
                thread_id=thread_id,
                run_id=run_id
            )

            # Progress update
            progress = int((i + 1) / len(agents) * 100)
            yield StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta={
                    "workflow_progress": progress,
                    "completed_agents": i + 1,
                    "current_agent": agent_name if i < len(agents) - 1 else None
                },
                thread_id=thread_id,
                run_id=run_id
            )

        # End message
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id,
            thread_id=thread_id,
            run_id=run_id
        )

    async def _emit_tool_call_events(
        self,
        chunk: Dict[str, Any],
        message_id: str,
        thread_id: str,
        run_id: str
    ) -> List:
        """
        Emit tool call start and result events.
        """
        tool_call_id = chunk["tool_call_id"]
        tool_name = chunk["tool_name"]

        events = [
            ToolCallStartEvent(
                type=EventType.TOOL_CALL_START,
                tool_call_id=tool_call_id,
                tool_call_name=tool_name,
                tool_call_args=chunk.get("arguments", {}),
                parent_message_id=message_id,
                thread_id=thread_id,
                run_id=run_id
            ),
            ToolCallResultEvent(
                type=EventType.TOOL_CALL_RESULT,
                tool_call_id=tool_call_id,
                result=chunk["result"],
                execution_time=chunk.get("execution_time"),
                thread_id=thread_id,
                run_id=run_id
            )
        ]

        return events

    def _encode_event(self, event) -> str:
        """Encode event as SSE format."""
        return f"data: {self.encoder.encode(event)}\n\n"

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Determine if error is recoverable."""
        recoverable_errors = (
            "TimeoutError",
            "ConnectionError",
            "NetworkError"
        )
        return type(error).__name__ in recoverable_errors

    def _calculate_retry_delay(self, error: Exception) -> int:
        """Calculate exponential backoff delay."""
        base_delay = 1  # seconds
        max_delay = 30  # seconds

        # Simple exponential backoff
        delay = min(base_delay * 2, max_delay)
        return delay
```

### 1.2 Enhanced FastAPI Endpoint

File: `/src/api/copilotkit_enhanced.py`
```python
"""
Enhanced CopilotKit-compatible endpoint using AG-UI protocol.

Provides real-time streaming, multi-agent coordination, and enhanced error handling.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ag_ui.core import RunAgentInput, WorkflowInput
from src.adapters.ag_ui_emitter import AGUIEventEmitter
from src.agents.orchestrator import AgentOrchestrator
from src.monitoring.metrics import MetricsCollector
from src.monitoring.logger import setup_logging
import structlog

logger = structlog.get_logger(__name__)

# Initialize FastAPI with enhanced configuration
app = FastAPI(
    title="Sergas Agents - Enhanced CopilotKit Bridge",
    description="Real-time multi-agent coordination with AG-UI protocol",
    version="2.0.0"
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:7007",  # Next.js dev port
        "https://your-production-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Global components
ag_ui_emitter = AGUIEventEmitter()
orchestrator = AgentOrchestrator()
metrics = MetricsCollector()

# Request state management
active_workflows: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting enhanced CopilotKit bridge")

    # Initialize components
    await orchestrator.initialize()
    await metrics.initialize()

    yield

    # Cleanup
    logger.info("Shutting down enhanced CopilotKit bridge")
    await orchestrator.cleanup()
    await metrics.cleanup()

@app.post("/api/copilotkit")
async def copilotkit_enhanced_endpoint(
    input_data: RunAgentInput,
    authorization: str = Header(None),
    x_request_id: str = Header(None)
) -> StreamingResponse:
    """
    Enhanced AG-UI protocol endpoint for CopilotKit frontend.

    Features:
    - Real-time streaming with AG-UI events
    - Multi-agent workflow coordination
    - Enhanced error handling and recovery
    - Performance metrics and monitoring
    - Request deduplication
    """

    # Authentication and validation
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )

    request_id = x_request_id or f"req_{uuid.uuid4().hex[:8]}"

    # Request validation and deduplication
    if await _is_duplicate_request(request_id, input_data):
        logger.warning("duplicate_request", request_id=request_id)
        raise HTTPException(
            status_code=409,
            detail="Duplicate request detected"
        )

    # Register workflow
    workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
    active_workflows[workflow_id] = {
        "request_id": request_id,
        "status": "initializing",
        "started_at": datetime.utcnow().isoformat(),
        "input_data": input_data.dict()
    }

    logger.info(
        "workflow_started",
        request_id=request_id,
        workflow_id=workflow_id,
        message_count=len(input_data.messages),
        has_state=input_data.state is not None
    )

    # Record metrics
    await metrics.record_request_start(request_id, input_data)

    async def enhanced_event_generator():
        """Enhanced event generator with comprehensive error handling."""
        try:
            # Update workflow status
            active_workflows[workflow_id]["status"] = "running"

            # Stream AG-UI events
            async for event_string in ag_ui_emitter.emit_agent_workflow(
                orchestrator=orchestrator,
                workflow_id=workflow_id,
                agents=input_data.agents or ["memory_analyst", "zoho_data_scout"],
                messages=input_data.messages,
                initial_state=input_data.state
            ):
                yield event_string

        except Exception as e:
            logger.error(
                "workflow_error",
                workflow_id=workflow_id,
                error=str(e),
                error_type=type(e).__name__
            )

            # Emit structured error event
            from ag_ui.core import RunErrorEvent, EventType
            error_event = RunErrorEvent(
                type=EventType.RUN_ERROR,
                thread_id=input_data.thread_id or "default",
                run_id=request_id,
                workflow_id=workflow_id,
                error={
                    "code": "WORKFLOW_EXECUTION_ERROR",
                    "message": str(e),
                    "type": type(e).__name__,
                    "recoverable": _is_recoverable_error(e)
                }
            )

            yield f"data: {ag_ui_emitter.encoder.encode(error_event)}\n\n"

        finally:
            # Cleanup and metrics
            await metrics.record_request_end(request_id, workflow_id)
            if workflow_id in active_workflows:
                del active_workflows[workflow_id]

    return StreamingResponse(
        enhanced_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
            "X-Request-ID": request_id
        }
    )

@app.get("/api/copilotkit/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get real-time status of active workflow."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = active_workflows[workflow_id]

    # Get current agent states from orchestrator
    agent_states = await orchestrator.get_agent_states(workflow_id)

    return {
        "workflow_id": workflow_id,
        "status": workflow["status"],
        "started_at": workflow["started_at"],
        "agent_states": agent_states,
        "progress": await orchestrator.get_workflow_progress(workflow_id)
    }

@app.post("/api/copilotkit/interrupt/{workflow_id}")
async def interrupt_workflow(
    workflow_id: str,
    reason: Dict[str, Any]
):
    """Gracefully interrupt a running workflow."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    logger.info(
        "workflow_interrupt",
        workflow_id=workflow_id,
        reason=reason.get("message", "No reason provided")
    )

    # Interrupt orchestrator
    await orchestrator.interrupt_workflow(workflow_id, reason)

    # Update workflow status
    active_workflows[workflow_id]["status"] = "interrupted"
    active_workflows[workflow_id]["interrupted_at"] = datetime.utcnow().isoformat()
    active_workflows[workflow_id]["interrupt_reason"] = reason

    return {"status": "interrupted", "workflow_id": workflow_id}

@app.get("/health/enhanced")
async def enhanced_health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check all components
        orchestrator_status = await orchestrator.health_check()
        active_workflow_count = len(active_workflows)
        memory_usage = await metrics.get_memory_usage()
        cpu_usage = await metrics.get_cpu_usage()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "components": {
                "orchestrator": orchestrator_status,
                "metrics": await metrics.health_check(),
                "active_workflows": active_workflow_count
            },
            "system": {
                "memory_usage_mb": memory_usage,
                "cpu_usage_percent": cpu_usage
            },
            "capabilities": [
                "streaming_responses",
                "multi_agent_coordination",
                "real_time_status",
                "error_recovery",
                "performance_monitoring"
            ]
        }
    except Exception as e:
        logger.error("health_check_error", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

async def _is_duplicate_request(request_id: str, input_data: RunAgentInput) -> bool:
    """Check for duplicate requests using request ID."""
    # Simple in-memory check - in production, use Redis or similar
    recent_requests = getattr(app.state, "recent_requests", set())

    request_signature = f"{request_id}:{hash(str(input_data.dict()))}"

    if request_signature in recent_requests:
        return True

    recent_requests.add(request_signature)

    # Clean old requests (keep last 5 minutes worth)
    if len(recent_requests) > 1000:  # Safety limit
        recent_requests.clear()

    return False

def _is_recoverable_error(error: Exception) -> bool:
    """Determine if error is recoverable."""
    recoverable_types = (
        "TimeoutError",
        "ConnectionError",
        "NetworkError",
        "TemporaryFailure"
    )
    return type(error).__name__ in recoverable_types

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.copilotkit_enhanced:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )
```

---

## Phase 2: Enhanced Frontend Implementation

### 2.1 AG-UI Client Integration

**Install Frontend Packages**:
```bash
npm install @ag-ui/client @copilotkit/react-core@latest
```

**Enhanced CopilotProvider**:

File: `/frontend/components/copilot/EnhancedCopilotProvider.tsx`
```typescript
/**
 * Enhanced Copilot Provider with AG-UI integration.
 *
 * Features:
 * - Real-time agent coordination
 * - Centralized state management
 * - WebSocket fallback for bidirectional communication
 * - Enhanced error handling and recovery
 * - Performance monitoring
 */

'use client';

import React, { createContext, useContext, useReducer, useEffect, useCallback, useMemo } from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { HttpAgent } from '@ag-ui/client';

// Enhanced state management
interface EnhancedAgentState {
  activeWorkflows: Record<string, WorkflowState>;
  agentStatuses: Record<string, AgentStatus>;
  connectionStatus: ConnectionStatus;
  lastError: Error | null;
  metrics: PerformanceMetrics;
}

interface WorkflowState {
  id: string;
  status: 'initializing' | 'running' | 'completed' | 'error' | 'interrupted';
  startedAt: Date;
  agents: string[];
  progress: number;
  currentAgent?: string;
}

interface AgentStatus {
  id: string;
  status: 'idle' | 'initializing' | 'running' | 'completed' | 'error';
  lastUpdate: Date;
  progress?: number;
  currentTask?: string;
}

interface PerformanceMetrics {
  responseTime: number;
  throughput: number;
  errorRate: number;
  activeConnections: number;
}

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'reconnecting';

type EnhancedAgentAction =
  | { type: 'WORKFLOW_STARTED'; payload: WorkflowState }
  | { type: 'WORKFLOW_UPDATED'; payload: { id: string; updates: Partial<WorkflowState> } }
  | { type: 'WORKFLOW_COMPLETED'; payload: { id: string } }
  | { type: 'AGENT_STATUS_CHANGED'; payload: AgentStatus }
  | { type: 'CONNECTION_CHANGED'; payload: ConnectionStatus }
  | { type: 'ERROR_OCCURRED'; payload: Error }
  | { type: 'METRICS_UPDATED'; payload: Partial<PerformanceMetrics> }
  | { type: 'STATE_RESET' };

const initialState: EnhancedAgentState = {
  activeWorkflows: {},
  agentStatuses: {},
  connectionStatus: 'disconnected',
  lastError: null,
  metrics: {
    responseTime: 0,
    throughput: 0,
    errorRate: 0,
    activeConnections: 0
  }
};

function agentReducer(state: EnhancedAgentState, action: EnhancedAgentAction): EnhancedAgentState {
  switch (action.type) {
    case 'WORKFLOW_STARTED':
      return {
        ...state,
        activeWorkflows: {
          ...state.activeWorkflows,
          [action.payload.id]: action.payload
        }
      };

    case 'WORKFLOW_UPDATED':
      return {
        ...state,
        activeWorkflows: {
          ...state.activeWorkflows,
          [action.payload.id]: {
            ...state.activeWorkflows[action.payload.id],
            ...action.payload.updates
          }
        }
      };

    case 'WORKFLOW_COMPLETED':
      const { [id, ...remainingWorkflows] } = state.activeWorkflows;
      return {
        ...state,
        activeWorkflows: remainingWorkflows
      };

    case 'AGENT_STATUS_CHANGED':
      return {
        ...state,
        agentStatuses: {
          ...state.agentStatuses,
          [action.payload.id]: action.payload
        }
      };

    case 'CONNECTION_CHANGED':
      return {
        ...state,
        connectionStatus: action.payload,
        lastError: action.payload === 'disconnected' ? state.lastError : null
      };

    case 'ERROR_OCCURRED':
      return {
        ...state,
        lastError: action.payload
      };

    case 'METRICS_UPDATED':
      return {
        ...state,
        metrics: {
          ...state.metrics,
          ...action.payload
        }
      };

    case 'STATE_RESET':
      return initialState;

    default:
      return state;
  }
}

const EnhancedAgentContext = createContext<{
  state: EnhancedAgentState;
  dispatch: React.Dispatch<EnhancedAgentAction>;
  agent: HttpAgent;
  actions: {
    startWorkflow: (config: WorkflowConfig) => Promise<string>;
    interruptWorkflow: (workflowId: string) => Promise<void>;
    getWorkflowStatus: (workflowId: string) => Promise<WorkflowState>;
    retryWorkflow: (workflowId: string) => Promise<void>;
  };
} | null>(null);

interface WorkflowConfig {
  agents: string[];
  messages: Array<{ role: string; content: string }>;
  state?: Record<string, any>;
  metadata?: Record<string, any>;
}

interface EnhancedCopilotProviderProps {
  children: React.ReactNode;
  runtimeUrl?: string;
  authToken?: string;
  enableWebSocket?: boolean;
  reconnectAttempts?: number;
}

export function EnhancedCopilotProvider({
  children,
  runtimeUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8008',
  authToken = process.env.NEXT_PUBLIC_API_TOKEN,
  enableWebSocket = true,
  reconnectAttempts = 5
}: EnhancedCopilotProviderProps) {
  const [state, dispatch] = useReducer(agentReducer, initialState);

  // Initialize AG-UI client with enhanced configuration
  const agent = useMemo(() => new HttpAgent({
    url: `${runtimeUrl}/api/copilotkit`,
    headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    options: {
      enableStreaming: true,
      enableRetries: true,
      maxRetries: 3,
      retryDelay: 1000,
      timeout: 30000,
      // WebSocket fallback configuration
      enableWebSocket,
      wsUrl: runtimeUrl?.replace('http', 'ws') + '/ws/copilotkit'
    }
  }), [runtimeUrl, authToken, enableWebSocket]);

  // Enhanced action implementations
  const actions = useMemo(() => ({
    startWorkflow: async (config: WorkflowConfig): Promise<string> => {
      const workflowId = `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      dispatch({
        type: 'WORKFLOW_STARTED',
        payload: {
          id: workflowId,
          status: 'initializing',
          startedAt: new Date(),
          agents: config.agents,
          progress: 0
        }
      });

      try {
        await agent.run({
          messages: config.messages,
          state: config.state,
          agents: config.agents,
          metadata: {
            ...config.metadata,
            workflowId,
            clientTimestamp: new Date().toISOString()
          }
        });

        return workflowId;
      } catch (error) {
        dispatch({
          type: 'ERROR_OCCURRED',
          payload: error instanceof Error ? error : new Error(String(error))
        });
        throw error;
      }
    },

    interruptWorkflow: async (workflowId: string): Promise<void> => {
      try {
        await fetch(`${runtimeUrl}/api/copilotkit/interrupt/${workflowId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken && { Authorization: `Bearer ${authToken}` })
          },
          body: JSON.stringify({
            reason: { message: 'User initiated interruption' }
          })
        });

        dispatch({
          type: 'WORKFLOW_UPDATED',
          payload: {
            id: workflowId,
            updates: { status: 'interrupted' }
          }
        });
      } catch (error) {
        dispatch({
          type: 'ERROR_OCCURRED',
          payload: error instanceof Error ? error : new Error(String(error))
        });
      }
    },

    getWorkflowStatus: async (workflowId: string): Promise<WorkflowState> => {
      try {
        const response = await fetch(`${runtimeUrl}/api/copilotkit/status/${workflowId}`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {}
        });

        if (!response.ok) {
          throw new Error(`Status check failed: ${response.statusText}`);
        }

        const status = await response.json();

        dispatch({
          type: 'WORKFLOW_UPDATED',
          payload: {
            id: workflowId,
            updates: status
          }
        });

        return status;
      } catch (error) {
        dispatch({
          type: 'ERROR_OCCURRED',
          payload: error instanceof Error ? error : new Error(String(error))
        });
        throw error;
      }
    },

    retryWorkflow: async (workflowId: string): Promise<void> => {
      try {
        await fetch(`${runtimeUrl}/api/copilotkit/retry/${workflowId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken && { Authorization: `Bearer ${authToken}` })
          }
        });

        dispatch({
          type: 'WORKFLOW_UPDATED',
          payload: {
            id: workflowId,
            updates: { status: 'initializing' }
          }
        });
      } catch (error) {
        dispatch({
          type: 'ERROR_OCCURRED',
          payload: error instanceof Error ? error : new Error(String(error))
        });
      }
    }
  }), [runtimeUrl, authToken, agent]);

  // Connection status monitoring
  useEffect(() => {
    const handleConnectionChange = (status: ConnectionStatus) => {
      dispatch({ type: 'CONNECTION_CHANGED', payload: status });
    };

    const handleMetricsUpdate = (metrics: Partial<PerformanceMetrics>) => {
      dispatch({ type: 'METRICS_UPDATED', payload: metrics });
    };

    const handleError = (error: Error) => {
      dispatch({ type: 'ERROR_OCCURRED', payload: error });
    };

    // Register event listeners
    agent.on('connectionChanged', handleConnectionChange);
    agent.on('metricsUpdated', handleMetricsUpdate);
    agent.on('error', handleError);

    return () => {
      agent.off('connectionChanged', handleConnectionChange);
      agent.off('metricsUpdated', handleMetricsUpdate);
      agent.off('error', handleError);
    };
  }, [agent]);

  // Auto-reconnect logic
  useEffect(() => {
    if (state.connectionStatus === 'disconnected' && reconnectAttempts > 0) {
      const reconnectTimer = setTimeout(() => {
        console.log('Attempting to reconnect...');
        agent.reconnect();
      }, 2000); // Wait 2 seconds before reconnecting

      return () => clearTimeout(reconnectTimer);
    }
  }, [state.connectionStatus, reconnectAttempts, agent]);

  const contextValue = useMemo(() => ({
    state,
    dispatch,
    agent,
    actions
  }), [state, dispatch, agent, actions]);

  return (
    <EnhancedAgentContext.Provider value={contextValue}>
      <CopilotKit
        runtimeUrl="/api/copilotkit"
        agent={agent}
        headers={authToken ? { Authorization: `Bearer ${authToken}` } : undefined}
        properties={{
          origin: 'sergas-enhanced-frontend',
          version: '2.0.0',
          features: [
            'real-time-streaming',
            'multi-agent-coordination',
            'error-recovery',
            'performance-monitoring'
          ]
        }}
      >
        {children}
      </CopilotKit>
    </EnhancedAgentContext.Provider>
  );
}

// Hook for using enhanced context
export function useEnhancedAgent() {
  const context = useContext(EnhancedAgentContext);
  if (!context) {
    throw new Error('useEnhancedAgent must be used within EnhancedCopilotProvider');
  }
  return context;
}

export { EnhancedAgentContext };
export type { EnhancedAgentState, WorkflowState, AgentStatus, PerformanceMetrics };
```

### 2.2 Real-time Agent Dashboard

File: `/frontend/components/copilot/RealTimeAgentDashboard.tsx`
```typescript
/**
 * Real-time Agent Dashboard with multi-agent coordination.
 *
 * Features:
 * - Live agent status monitoring
 * - Workflow progress tracking
 * - Performance metrics
 * - Interactive controls (interrupt, retry)
 * - Error visualization and recovery
 */

'use client';

import React, { useEffect, useMemo } from 'react';
import { useEnhancedAgent } from './EnhancedCopilotProvider';
import { Activity, CheckCircle, AlertTriangle, XCircle, RefreshCw, Square } from 'lucide-react';

interface AgentDashboardProps {
  className?: string;
}

export function RealTimeAgentDashboard({ className = '' }: AgentDashboardProps) {
  const { state } = useEnhancedAgent();

  // Compute derived metrics
  const metrics = useMemo(() => {
    const workflows = Object.values(state.activeWorkflows);
    const totalAgents = workflows.reduce((sum, wf) => sum + wf.agents.length, 0);
    const runningAgents = workflows.filter(wf => wf.status === 'running').length;
    const averageProgress = workflows.length > 0
      ? workflows.reduce((sum, wf) => sum + wf.progress, 0) / workflows.length
      : 0;

    return {
      totalWorkflows: workflows.length,
      totalAgents,
      runningAgents,
      averageProgress: Math.round(averageProgress),
      errorRate: state.lastError ? 1 : 0
    };
  }, [state.activeWorkflows, state.lastError]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'interrupted': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Activity className="h-4 w-4 animate-pulse" />;
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'error': return <XCircle className="h-4 w-4" />;
      case 'interrupted': return <AlertTriangle className="h-4 w-4" />;
      default: return <div className="h-4 w-4 bg-gray-300 rounded" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Connection Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          System Status
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            state.connectionStatus === 'connected'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}>
            {state.connectionStatus}
          </span>
        </h2>

        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Active Workflows"
            value={metrics.totalWorkflows.toString()}
            icon={<Activity className="h-5 w-5 text-blue-600" />}
          />
          <MetricCard
            label="Running Agents"
            value={metrics.runningAgents.toString()}
            icon={<RefreshCw className="h-5 w-5 text-green-600" />}
          />
          <MetricCard
            label="Avg Progress"
            value={`${metrics.averageProgress}%`}
            icon={<CheckCircle className="h-5 w-5 text-purple-600" />}
          />
          <MetricCard
            label="Error Rate"
            value={`${(metrics.errorRate * 100).toFixed(1)}%`}
            icon={<AlertTriangle className="h-5 w-5 text-red-600" />}
          />
        </div>
      </div>

      {/* Active Workflows */}
      {Object.values(state.activeWorkflows).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Active Workflows ({Object.values(state.activeWorkflows).length})
          </h3>

          <div className="space-y-4">
            {Object.values(state.activeWorkflows).map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {state.lastError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <h4 className="font-semibold text-red-900">Last Error</h4>
              <p className="text-red-700 text-sm mt-1">
                {state.lastError.message}
              </p>
              <p className="text-red-600 text-xs mt-2">
                {state.lastError.stack}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Sub-components
interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
}

function MetricCard({ label, value, icon }: MetricCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">{icon}</div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

interface WorkflowCardProps {
  workflow: WorkflowState;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ReactNode;
}

function WorkflowCard({ workflow, getStatusColor, getStatusIcon }: WorkflowCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {getStatusIcon(workflow.status)}
          <div>
            <h4 className="font-medium text-gray-900">{workflow.id}</h4>
            <p className="text-sm text-gray-600">
              Started: {workflow.startedAt.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(workflow.status)}`}>
            {workflow.status}
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-gray-600">Progress</span>
          <span className="text-sm font-medium">{workflow.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${workflow.progress}%` }}
          />
        </div>
      </div>

      {/* Expandable Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 pt-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Agents</p>
              <p className="font-medium">{workflow.agents.join(', ')}</p>
            </div>
            {workflow.currentAgent && (
              <div>
                <p className="text-sm text-gray-600">Current Agent</p>
                <p className="font-medium">{workflow.currentAgent}</p>
              </div>
            )}
          </div>

          {/* Agent Statuses */}
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-700 mb-2">Agent Statuses</p>
            <div className="space-y-1">
              {workflow.agents.map((agentId) => (
                <div key={agentId} className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span>{agentId}: Running</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Phase 3: Testing and Validation

### 3.1 Integration Tests

**Backend Tests**: `/tests/integration/test_enhanced_copilotkit.py`
```python
"""Integration tests for enhanced CopilotKit implementation."""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from ag_ui.core import RunAgentInput

from src.api.copilotkit_enhanced import app

client = TestClient(app)

class TestEnhancedCopilotKit:
    """Test suite for enhanced CopilotKit AG-UI integration."""

    def test_health_check(self):
        """Test comprehensive health check endpoint."""
        response = client.get("/health/enhanced")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "capabilities" in data
        assert "streaming_responses" in data["capabilities"]
        assert "multi_agent_coordination" in data["capabilities"]

    def test_workflow_start_and_streaming(self):
        """Test complete workflow with AG-UI streaming."""
        response = client.post(
            "/api/copilotkit",
            json={
                "threadId": "test_thread",
                "runId": "test_run",
                "agents": ["memory_analyst", "zoho_data_scout"],
                "messages": [
                    {"role": "user", "content": "Analyze account ACC-001"}
                ],
                "state": {"account_id": "ACC-001"}
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Parse SSE events
        events = self._parse_sse_events(response)

        # Verify event sequence
        event_types = [event["type"] for event in events]
        assert "RUN_STARTED" in event_types
        assert "AGENT_STATUS" in event_types
        assert "TEXT_MESSAGE_START" in event_types
        assert "TEXT_MESSAGE_CONTENT" in event_types
        assert "RUN_FINISHED" in event_types

    def test_workflow_status_endpoint(self):
        """Test workflow status tracking endpoint."""
        # Start a workflow first
        start_response = client.post(
            "/api/copilotkit",
            json={
                "threadId": "status_test",
                "runId": "status_run",
                "agents": ["memory_analyst"],
                "messages": [{"role": "user", "content": "test"}]
            },
            headers={"Authorization": "Bearer test_token"}
        )

        # Extract workflow ID from events (simplified for test)
        workflow_id = "test_workflow_id"

        # Check status
        status_response = client.get(f"/api/copilotkit/status/{workflow_id}")

        assert status_response.status_code == 200

        status_data = status_response.json()
        assert "workflow_id" in status_data
        assert "status" in status_data
        assert "progress" in status_data

    def test_workflow_interruption(self):
        """Test graceful workflow interruption."""
        workflow_id = "interrupt_test_workflow"

        # Start workflow
        client.post(
            "/api/copilotkit",
            json={
                "threadId": "interrupt_test",
                "runId": "interrupt_run",
                "agents": ["memory_analyst"],
                "messages": [{"role": "user", "content": "long running task"}]
            },
            headers={"Authorization": "Bearer test_token"}
        )

        # Interrupt workflow
        interrupt_response = client.post(
            f"/api/copilotkit/interrupt/{workflow_id}",
            json={"reason": {"message": "Test interruption"}},
            headers={"Authorization": "Bearer test_token"}
        )

        assert interrupt_response.status_code == 200

        interrupt_data = interrupt_response.json()
        assert interrupt_data["status"] == "interrupted"

    def _parse_sse_events(self, response):
        """Parse Server-Sent Events from response."""
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:].decode('utf-8').strip()
                if event_data:
                    events.append(json.loads(event_data))
        return events

    def test_error_handling_and_recovery(self):
        """Test error handling and automatic recovery."""
        # Test with invalid agent configuration
        response = client.post(
            "/api/copilotkit",
            json={
                "threadId": "error_test",
                "runId": "error_run",
                "agents": ["invalid_agent"],  # This should cause an error
                "messages": [{"role": "user", "content": "test error"}]
            },
            headers={"Authorization": "Bearer test_token"}
        )

        # Should still return 200 with error events in stream
        assert response.status_code == 200

        events = self._parse_sse_events(response)
        error_events = [e for e in events if e["type"] == "RUN_ERROR"]

        assert len(error_events) > 0
        assert "recoverable" in error_events[0]["error"]
        assert "retry_after" in error_events[0]["error"]

if __name__ == "__main__":
    pytest.main([__file__])
```

### 3.2 Frontend Tests

**Frontend Tests**: `/frontend/tests/enhanced-copilot.test.tsx`
```typescript
/**
 * React testing for enhanced CopilotKit integration.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EnhancedCopilotProvider, useEnhancedAgent } from '../components/copilot/EnhancedCopilotProvider';
import { RealTimeAgentDashboard } from '../components/copilot/RealTimeAgentDashboard';

// Mock AG-UI client
jest.mock('@ag-ui/client', () => ({
  HttpAgent: jest.fn().mockImplementation(() => ({
    run: jest.fn().mockResolvedValue(undefined),
    on: jest.fn(),
    off: jest.fn(),
    reconnect: jest.fn()
  }))
}));

describe('Enhanced CopilotKit Integration', () => {
  it('renders agent dashboard with initial state', () => {
    render(
      <EnhancedCopilotProvider>
        <RealTimeAgentDashboard />
      </EnhancedCopilotProvider>
    );

    expect(screen.getByText('System Status')).toBeInTheDocument();
    expect(screen.getByText('Active Workflows')).toBeInTheDocument();
    expect(screen.getByText('Running Agents')).toBeInTheDocument();
  });

  it('handles workflow initiation', async () => {
    function TestComponent() {
      const { actions } = useEnhancedAgent();

      const handleStartWorkflow = async () => {
        try {
          const workflowId = await actions.startWorkflow({
            agents: ['memory_analyst'],
            messages: [{ role: 'user', content: 'Test message' }]
          });

          console.log('Workflow started:', workflowId);
        } catch (error) {
          console.error('Workflow failed:', error);
        }
      }

      return (
        <button onClick={handleStartWorkflow}>
          Start Test Workflow
        </button>
      );
    }

    render(
      <EnhancedCopilotProvider>
        <TestComponent />
      </EnhancedCopilotProvider>
    );

    const startButton = screen.getByText('Start Test Workflow');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/workflow_[0-9]/)).toBeInTheDocument();
    });
  });

  it('displays workflow progress updates', async () => {
    const mockAgent = {
      run: jest.fn().mockImplementation(async function* () {
        yield { type: 'RUN_STARTED' };
        yield { type: 'AGENT_STATUS', status: 'running', progress: 25 };
        yield { type: 'AGENT_STATUS', status: 'running', progress: 50 };
        yield { type: 'AGENT_STATUS', status: 'running', progress: 75 };
        yield { type: 'AGENT_STATUS', status: 'completed', progress: 100 };
        yield { type: 'RUN_FINISHED' };
      })
    };

    jest.mocked(require('@ag-ui/client').HttpAgent).mockImplementation(() => mockAgent);

    render(
      <EnhancedCopilotProvider>
        <RealTimeAgentDashboard />
      </EnhancedCopilotProvider>
    );

    // Start a workflow to trigger progress updates
    const startButton = screen.getByText('Start Test Workflow');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('50%')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  it('handles connection errors gracefully', async () => {
    const mockAgent = {
      run: jest.fn().mockRejectedValue(new Error('Connection failed')),
      on: jest.fn()
    };

    jest.mocked(require('@ag-ui/client').HttpAgent).mockImplementation(() => mockAgent);

    function ErrorTestComponent() {
      const { state } = useEnhancedAgent();

      return (
        <div>
          <div data-testid="connection-status">
            {state.connectionStatus}
          </div>
          <div data-testid="error-message">
            {state.lastError?.message || 'No error'}
          </div>
        </div>
      );
    }

    render(
      <EnhancedCopilotProvider>
        <ErrorTestComponent />
      </EnhancedCopilotProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('disconnected');
      expect(screen.getByTestId('error-message')).toHaveTextContent('Connection failed');
    });
  });
});
```

---

## Deployment Checklist

### Production Deployment

#### Backend (FastAPI + AG-UI)
- [ ] Configure production environment variables
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting middleware
- [ ] Set up monitoring and alerting
- [ ] Configure database connections (PostgreSQL)
- [ ] Set up Redis for session management
- [ ] Configure logging (structured JSON)
- [ ] Performance testing with load simulation
- [ ] Security audit and penetration testing

#### Frontend (Next.js + CopilotKit)
- [ ] Configure production build settings
- [ ] Set up environment variables
- [ ] Configure CORS and security headers
- [ ] Implement error boundaries and monitoring
- [ ] Set up performance monitoring
- [ ] Configure CDN for static assets
- [ ] Mobile responsiveness testing
- [ ] Accessibility compliance testing

#### Infrastructure
- [ ] Docker containerization
- [ ] Kubernetes deployment configuration
- [ ] Auto-scaling policies
- [ ] Load balancer configuration
- [ ] Database clustering and backups
- [ ] Monitoring dashboards (Grafana/Prometheus)
- [ ] Log aggregation (ELK stack)
- [ ] Alert configuration (PagerDuty)

---

## Performance Monitoring

### Key Metrics to Track

#### Backend Metrics
- **Response Time**: p50, p95, p99 percentiles
- **Throughput**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Agent Execution Time**: Time per agent type
- **Memory Usage**: Per workflow and system-wide
- **CPU Usage**: During peak loads
- **Database Performance**: Query times and connection pools

#### Frontend Metrics
- **Time to First Byte**: Initial response time
- **Streaming Performance**: Chunk delivery intervals
- **UI Responsiveness**: Frame rate and interaction latency
- **Error Boundary Triggers**: JavaScript errors and failures
- **User Engagement**: Session duration and interactions
- **Bundle Performance**: Load times and sizes

#### Integration Metrics
- **End-to-End Latency**: From user action to result
- **Workflow Success Rate**: Percentage of completed workflows
- **Agent Coordination Efficiency**: Time between agent handoffs
- **Recovery Success Rate**: Automatic error recovery performance

### Monitoring Setup

#### Prometheus Metrics Export
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics definitions
REQUEST_COUNT = Counter('copilotkit_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('copilotkit_request_duration_seconds', 'Request duration')
ACTIVE_WORKFLOWS = Gauge('copilotkit_active_workflows', 'Active workflows')
AGENT_EXECUTION_TIME = Histogram('agent_execution_duration_seconds', 'Agent execution time', ['agent_type'])

# Usage in endpoints
REQUEST_COUNT.labels(method='POST', endpoint='/api/copilotkit').inc()
REQUEST_DURATION.observe(response_time)
ACTIVE_WORKFLOWS.set(len(active_workflows))
```

#### Grafana Dashboards
- System Overview Dashboard
- Workflow Performance Dashboard
- Agent Health Dashboard
- Error Analysis Dashboard
- User Experience Dashboard

This implementation blueprint provides everything needed to transform the current simple proxy into a robust, real-time, multi-agent coordination system with CopilotKit's excellent UI components.