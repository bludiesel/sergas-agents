# CopilotKit Integration Pseudocode

**SPARC Phase**: Pseudocode
**Version**: 1.0
**Date**: 2025-10-19
**Author**: Pseudocode Agent

---

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Algorithm Outlines](#algorithm-outlines)
4. [Data Structures](#data-structures)
5. [State Management](#state-management)
6. [Error Handling](#error-handling)
7. [HITL Workflow](#hitl-workflow)
8. [Function Signatures](#function-signatures)

---

## Overview

This document provides detailed pseudocode and algorithm outlines for integrating existing agents with CopilotKit using LangGraph wrappers. The integration enables browser-based UI interaction via AG UI Protocol.

**Key Components**:
- LangGraph agent wrappers for existing agents
- `/agent-orchestrator` endpoint as gateway
- Next.js API route proxy to FastAPI
- State management between agents
- Human-in-the-loop approval workflows

---

## Core Architecture

### System Flow Diagram (Pseudocode)

```
SYSTEM FLOW: CopilotKit UI → Next.js → FastAPI → Agents → Response

COMPONENTS:
├── CopilotKit Frontend (Browser)
│   └── Emits user messages
├── Next.js API Route (/api/copilotkit/[...action].ts)
│   └── Proxies requests to FastAPI
├── FastAPI Backend (Python)
│   ├── /copilotkit endpoint (CopilotKitSDK)
│   └── /agent-orchestrator endpoint (LangGraph gateway)
├── LangGraph Agents (Wrappers)
│   ├── OrchestratorAgent → LangGraphAgent
│   ├── ZohoDataScout → LangGraphAgent
│   ├── MemoryAnalyst → LangGraphAgent
│   └── RecommendationAuthor → LangGraphAgent
└── AG UI Protocol Events
    └── Streamed to frontend via SSE
```

---

## Algorithm Outlines

### 1. LangGraph Agent Wrapper Algorithm

**Purpose**: Wrap existing agents with LangGraph interface for CopilotKit compatibility.

```python
ALGORITHM: CreateLangGraphWrapper
INPUT:
    - agent_instance: BaseAgent (existing agent)
    - agent_name: string
    - agent_description: string
OUTPUT:
    - langgraph_agent: LangGraphAgent

BEGIN
    # Define agent state schema
    state_schema ← CREATE StateGraph({
        "messages": List[BaseMessage],
        "context": Dict[str, Any],
        "approval_required": bool,
        "approval_response": Optional[ApprovalResponse],
        "agent_outputs": Dict[str, Any],
        "error": Optional[str]
    })

    # Define agent node function
    FUNCTION agent_node(state: AgentState) → AgentState:
        BEGIN
            # Extract context from state
            context ← state["context"]

            # Initialize event accumulator
            events ← []

            # Execute agent with event streaming
            TRY:
                ASYNC FOR event IN agent_instance.execute_with_events(context):
                    events.append(event)

                    # Translate AG UI events to LangGraph state updates
                    IF event["event"] == "agent_completed":
                        state["agent_outputs"][agent_name] ← event["data"]["output"]
                        state["messages"].append(
                            AIMessage(content=event["data"]["output"])
                        )
                    END IF

                    IF event["event"] == "approval_required":
                        state["approval_required"] ← true
                        state["context"]["approval_data"] ← event["data"]
                    END IF

                    IF event["event"] == "agent_error":
                        state["error"] ← event["data"]["error_message"]
                        RAISE AgentExecutionError(event["data"])
                    END IF
                END FOR

            CATCH Exception as e:
                state["error"] ← str(e)
                LOG_ERROR("agent_execution_failed", agent=agent_name, error=e)
            END TRY

            RETURN state
        END FUNCTION

    # Build LangGraph workflow
    workflow ← StateGraph(state_schema)
    workflow.add_node(agent_name, agent_node)
    workflow.set_entry_point(agent_name)
    workflow.add_edge(agent_name, END)

    # Compile graph
    agent_graph ← workflow.compile()

    # Create LangGraphAgent wrapper
    langgraph_agent ← LangGraphAgent(
        name=agent_name,
        description=agent_description,
        agent=agent_graph
    )

    RETURN langgraph_agent
END
```

**Time Complexity**: O(1) for wrapper creation, O(n) for agent execution
**Space Complexity**: O(k) where k = state size

---

### 2. Orchestrator Workflow Algorithm

**Purpose**: Coordinate multiple agents in sequence with state passing.

```python
ALGORITHM: OrchestratAgents
INPUT:
    - account_id: string
    - session_id: string
    - user_message: string
OUTPUT:
    - final_output: Dict[str, Any]

BEGIN
    # Initialize shared state
    shared_state ← {
        "account_id": account_id,
        "session_id": session_id,
        "user_message": user_message,
        "workflow": "account_analysis",
        "step": 0,
        "agents_completed": [],
        "errors": []
    }

    # Define workflow steps
    workflow_steps ← [
        {
            "agent": "zoho_scout",
            "input_keys": ["account_id", "session_id"],
            "output_key": "account_snapshot",
            "required": true
        },
        {
            "agent": "memory_analyst",
            "input_keys": ["account_id", "account_snapshot"],
            "output_key": "historical_context",
            "required": true
        },
        {
            "agent": "recommendation_author",
            "input_keys": ["account_id", "account_snapshot", "historical_context"],
            "output_key": "recommendations",
            "required": true
        }
    ]

    # Execute workflow
    FOR EACH step IN workflow_steps:
        shared_state["step"] ← shared_state["step"] + 1

        # Build agent context from shared state
        agent_context ← {}
        FOR EACH key IN step["input_keys"]:
            agent_context[key] ← shared_state.get(key)
        END FOR

        agent_context["step"] ← shared_state["step"]
        agent_context["session_id"] ← session_id

        # Invoke agent
        TRY:
            agent_output ← AWAIT invoke_agent(
                agent_name=step["agent"],
                context=agent_context
            )

            # Store output in shared state
            shared_state[step["output_key"]] ← agent_output
            shared_state["agents_completed"].append(step["agent"])

        CATCH Exception as e:
            IF step["required"]:
                # Critical error - stop workflow
                shared_state["errors"].append({
                    "agent": step["agent"],
                    "error": str(e),
                    "critical": true
                })

                RETURN {
                    "status": "error",
                    "message": f"Critical agent {step['agent']} failed",
                    "error": str(e),
                    "partial_results": shared_state
                }
            ELSE:
                # Non-critical - log and continue
                shared_state["errors"].append({
                    "agent": step["agent"],
                    "error": str(e),
                    "critical": false
                })
                LOG_WARNING("agent_failed", agent=step["agent"], error=e)
            END IF
        END TRY
    END FOR

    # Check if approval required
    IF shared_state.get("recommendations"):
        approval_result ← AWAIT request_approval(
            recommendations=shared_state["recommendations"],
            session_id=session_id
        )

        shared_state["approval"] ← approval_result
    END IF

    # Build final output
    final_output ← {
        "status": "completed",
        "account_id": account_id,
        "workflow": shared_state["workflow"],
        "agents_completed": shared_state["agents_completed"],
        "results": {
            "account_snapshot": shared_state.get("account_snapshot"),
            "historical_context": shared_state.get("historical_context"),
            "recommendations": shared_state.get("recommendations")
        },
        "approval": shared_state.get("approval"),
        "errors": shared_state["errors"]
    }

    RETURN final_output
END
```

**Time Complexity**: O(n) where n = number of agents
**Space Complexity**: O(m) where m = accumulated state size

---

### 3. Next.js API Route Proxy Algorithm

**Purpose**: Proxy CopilotKit requests from Next.js to FastAPI backend.

```typescript
ALGORITHM: ProxyCopilotKitRequest
INPUT:
    - req: NextApiRequest
    - res: NextApiResponse
OUTPUT:
    - proxied_response: StreamedResponse

BEGIN
    # Extract request details
    action ← req.query.action as string[]
    method ← req.method
    body ← req.body
    headers ← req.headers

    # Build FastAPI URL
    fastapi_base_url ← process.env.FASTAPI_URL || "http://localhost:8000"
    target_url ← `${fastapi_base_url}/copilotkit/${action.join('/')}`

    # Log incoming request
    LOG_INFO("proxy_request", {
        method: method,
        url: target_url,
        action: action
    })

    TRY:
        # Forward request to FastAPI
        IF method == "POST":
            # Handle streaming response for agent execution
            response ← AWAIT fetch(target_url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "Authorization": headers.authorization || ""
                },
                body: JSON.stringify(body)
            })

            # Check response status
            IF NOT response.ok:
                error_body ← AWAIT response.text()
                LOG_ERROR("fastapi_error", {
                    status: response.status,
                    error: error_body
                })

                RETURN res.status(response.status).json({
                    error: "FastAPI request failed",
                    details: error_body
                })
            END IF

            # Setup SSE streaming
            res.setHeader("Content-Type", "text/event-stream")
            res.setHeader("Cache-Control", "no-cache")
            res.setHeader("Connection", "keep-alive")

            # Stream response chunks
            reader ← response.body.getReader()
            decoder ← new TextDecoder()

            WHILE true:
                chunk_result ← AWAIT reader.read()

                IF chunk_result.done:
                    BREAK
                END IF

                # Decode and forward chunk
                chunk_text ← decoder.decode(chunk_result.value, {stream: true})
                res.write(chunk_text)
            END WHILE

            # Complete response
            res.end()

        ELSE IF method == "GET":
            # Handle GET requests (status, metadata, etc.)
            response ← AWAIT fetch(target_url, {
                method: "GET",
                headers: {
                    "Accept": "application/json",
                    "Authorization": headers.authorization || ""
                }
            })

            data ← AWAIT response.json()
            RETURN res.status(response.status).json(data)

        ELSE:
            RETURN res.status(405).json({
                error: "Method not allowed",
                allowed: ["GET", "POST"]
            })
        END IF

    CATCH Exception as error:
        LOG_ERROR("proxy_error", {
            error: error.message,
            stack: error.stack
        })

        RETURN res.status(500).json({
            error: "Proxy request failed",
            message: error.message
        })
    END TRY
END
```

**Time Complexity**: O(n) where n = response size
**Space Complexity**: O(1) (streaming)

---

### 4. CopilotKitSDK Initialization Algorithm

**Purpose**: Initialize CopilotKit SDK with all agents registered.

```python
ALGORITHM: InitializeCopilotKitSDK
INPUT:
    - fastapi_app: FastAPI
    - agents: List[BaseAgent]
    - config: SDKConfig
OUTPUT:
    - sdk: CopilotKitSDK

BEGIN
    # Create LangGraph wrappers for all agents
    langgraph_agents ← []

    FOR EACH agent IN agents:
        # Determine agent metadata
        agent_metadata ← {
            "name": agent.agent_id,
            "description": agent.system_prompt[:200],
            "tools": agent.allowed_tools,
            "permission_mode": agent.permission_mode
        }

        # Create LangGraph wrapper
        langgraph_agent ← CreateLangGraphWrapper(
            agent_instance=agent,
            agent_name=agent_metadata["name"],
            agent_description=agent_metadata["description"]
        )

        langgraph_agents.append(langgraph_agent)

        LOG_INFO("agent_registered", agent=agent_metadata["name"])
    END FOR

    # Initialize CopilotKitSDK
    sdk ← CopilotKitSDK(
        agents=langgraph_agents,
        config={
            "model": config.model || "claude-3-5-sonnet-20241022",
            "api_key": config.api_key,
            "stream_mode": "events",
            "enable_approval_workflow": true,
            "session_ttl": config.session_ttl || 3600,
            "max_concurrent_agents": config.max_concurrent_agents || 3
        }
    )

    # Register FastAPI endpoint
    add_fastapi_endpoint(
        app=fastapi_app,
        sdk=sdk,
        path="/copilotkit"
    )

    LOG_INFO("copilotkit_sdk_initialized", {
        "agents_count": len(langgraph_agents),
        "endpoint": "/copilotkit"
    })

    RETURN sdk
END
```

**Time Complexity**: O(n) where n = number of agents
**Space Complexity**: O(n)

---

### 5. Agent State Management Algorithm

**Purpose**: Maintain state consistency across agents during orchestration.

```python
ALGORITHM: ManageAgentState
INPUT:
    - session_id: string
    - agent_name: string
    - state_update: Dict[str, Any]
OUTPUT:
    - updated_state: AgentState

BEGIN
    # Retrieve or initialize session state
    session_state ← state_store.get(session_id) OR {
        "session_id": session_id,
        "created_at": current_timestamp(),
        "agents": {},
        "shared_context": {},
        "workflow_status": "initialized",
        "approval_requests": []
    }

    # Update agent-specific state
    IF agent_name NOT IN session_state["agents"]:
        session_state["agents"][agent_name] ← {
            "status": "idle",
            "outputs": [],
            "errors": [],
            "start_time": null,
            "end_time": null
        }
    END IF

    agent_state ← session_state["agents"][agent_name]

    # Apply state update
    FOR EACH key, value IN state_update.items():
        IF key == "status":
            agent_state["status"] ← value

            IF value == "running":
                agent_state["start_time"] ← current_timestamp()
            ELSE IF value IN ["completed", "failed"]:
                agent_state["end_time"] ← current_timestamp()
            END IF

        ELSE IF key == "output":
            agent_state["outputs"].append(value)

            # Store in shared context for downstream agents
            session_state["shared_context"][f"{agent_name}_output"] ← value

        ELSE IF key == "error":
            agent_state["errors"].append(value)
            agent_state["status"] ← "failed"

        ELSE:
            agent_state[key] ← value
        END IF
    END FOR

    # Update workflow status
    all_agents ← session_state["agents"].values()

    IF ALL(a["status"] == "completed" FOR a IN all_agents):
        session_state["workflow_status"] ← "completed"
    ELSE IF ANY(a["status"] == "failed" FOR a IN all_agents):
        session_state["workflow_status"] ← "failed"
    ELSE IF ANY(a["status"] == "running" FOR a IN all_agents):
        session_state["workflow_status"] ← "running"
    END IF

    # Persist updated state
    state_store.set(session_id, session_state, ttl=3600)

    # Emit state change event
    emit_event("agent_state_changed", {
        "session_id": session_id,
        "agent_name": agent_name,
        "state_update": state_update,
        "workflow_status": session_state["workflow_status"]
    })

    RETURN session_state
END
```

**Time Complexity**: O(1) average (hash table operations)
**Space Complexity**: O(k) where k = state size per session

---

## Data Structures

### 1. AgentState Schema

```python
DATACLASS AgentState:
    # Session identification
    session_id: string
    run_id: string

    # Message history
    messages: List[BaseMessage]  # LangChain message format

    # Execution context
    context: Dict[string, Any] = {
        "account_id": Optional[string],
        "workflow": string,
        "step": integer,
        "timeout_seconds": integer = 300
    }

    # Agent outputs (keyed by agent name)
    agent_outputs: Dict[string, Any] = {}

    # Approval workflow state
    approval_required: boolean = false
    approval_data: Optional[Dict[string, Any]] = null
    approval_response: Optional[ApprovalResponse] = null
    approval_timeout: Optional[integer] = null

    # Error tracking
    error: Optional[string] = null
    error_stack: Optional[string] = null
    failed_agents: List[string] = []

    # Metadata
    created_at: datetime
    updated_at: datetime
    ttl: integer = 3600

    # Performance metrics
    metrics: Dict[string, Any] = {
        "total_duration_ms": 0,
        "agent_durations": {},
        "token_usage": {}
    }
END DATACLASS
```

### 2. LangGraphAgent Configuration

```python
DATACLASS LangGraphAgentConfig:
    # Agent identification
    name: string
    description: string
    version: string = "1.0"

    # LangGraph graph instance
    agent: CompiledGraph

    # State schema
    state_schema: Type[BaseModel]

    # Tool configuration
    tools: List[string] = []
    tool_permissions: Dict[string, List[string]] = {}

    # Execution settings
    max_iterations: integer = 10
    timeout_seconds: integer = 300
    enable_tracing: boolean = true

    # Streaming configuration
    stream_mode: string = "events"  # "events" | "updates" | "full"
    stream_chunk_size: integer = 1024

    # Error handling
    retry_config: RetryConfig = {
        "max_retries": 3,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60
    }
END DATACLASS
```

### 3. ApprovalRequest Schema

```python
DATACLASS ApprovalRequest:
    # Identification
    approval_id: string
    session_id: string
    recommendation_id: string

    # Approval data
    recommendation: Dict[string, Any] = {
        "account_id": string,
        "action_type": string,
        "priority": string,
        "reasoning": string,
        "expected_impact": string
    }

    # Status
    status: ApprovalStatus = "pending"  # pending | approved | rejected | timeout

    # Response data
    approved_by: Optional[string] = null
    rejected_by: Optional[string] = null
    reason: Optional[string] = null

    # Timing
    created_at: datetime
    timeout_at: datetime
    responded_at: Optional[datetime] = null

    # Callback mechanism
    response_event: asyncio.Event

    FUNCTION wait_for_response(timeout: integer) -> boolean:
        """Wait for approval response with timeout."""
        BEGIN
            TRY:
                AWAIT asyncio.wait_for(
                    self.response_event.wait(),
                    timeout=timeout
                )
                RETURN true
            CATCH asyncio.TimeoutError:
                self.status ← "timeout"
                RETURN false
            END TRY
        END

    FUNCTION approve(approved_by: string, reason: Optional[string] = null):
        """Mark as approved."""
        BEGIN
            self.status ← "approved"
            self.approved_by ← approved_by
            self.reason ← reason
            self.responded_at ← current_timestamp()
            self.response_event.set()
        END

    FUNCTION reject(rejected_by: string, reason: string):
        """Mark as rejected."""
        BEGIN
            self.status ← "rejected"
            self.rejected_by ← rejected_by
            self.reason ← reason
            self.responded_at ← current_timestamp()
            self.response_event.set()
        END
END DATACLASS
```

### 4. AG UI Protocol Event Schema

```python
DATACLASS AGUIEvent:
    # Event metadata
    event: string  # Event type
    timestamp: string  # ISO 8601 timestamp
    session_id: string
    run_id: Optional[string] = null

    # Event data (varies by event type)
    data: Dict[string, Any]

    # Event types and their data structures:

    # 1. agent_started
    #    data: {
    #        "agent": string,
    #        "step": integer,
    #        "task": string
    #    }

    # 2. agent_stream
    #    data: {
    #        "agent": string,
    #        "content": string,
    #        "content_type": "text" | "json" | "error"
    #    }

    # 3. agent_completed
    #    data: {
    #        "agent": string,
    #        "step": integer,
    #        "output": Dict[string, Any]
    #    }

    # 4. tool_call
    #    data: {
    #        "tool_name": string,
    #        "tool_args": Dict[string, Any],
    #        "tool_call_id": string
    #    }

    # 5. tool_result
    #    data: {
    #        "tool_call_id": string,
    #        "tool_name": string,
    #        "result": Any,
    #        "success": boolean,
    #        "error": Optional[string]
    #    }

    # 6. approval_required
    #    data: {
    #        "recommendation": Dict[string, Any],
    #        "timeout_hours": integer
    #    }

    # 7. workflow_completed
    #    data: {
    #        "workflow": string,
    #        "account_id": string,
    #        "final_output": Dict[string, Any]
    #    }

    FUNCTION to_sse() -> string:
        """Convert to Server-Sent Event format."""
        BEGIN
            event_json ← json.dumps(self.to_dict())
            RETURN f"event: {self.event}\ndata: {event_json}\n\n"
        END
END DATACLASS
```

---

## State Management

### Session State Store

```python
CLASS SessionStateStore:
    """Manages session state with TTL and persistence."""

    PRIVATE:
        _states: Dict[string, AgentState]
        _locks: Dict[string, asyncio.Lock]
        _redis_client: Optional[Redis]

    FUNCTION __init__(redis_url: Optional[string] = null):
        BEGIN
            self._states ← {}
            self._locks ← {}

            IF redis_url:
                self._redis_client ← Redis.from_url(redis_url)
            ELSE:
                self._redis_client ← null
            END IF
        END

    ASYNC FUNCTION get(session_id: string) -> Optional[AgentState]:
        """Retrieve session state."""
        BEGIN
            # Check in-memory cache
            IF session_id IN self._states:
                state ← self._states[session_id]

                # Check TTL
                age ← current_timestamp() - state.updated_at
                IF age.total_seconds() > state.ttl:
                    # Expired
                    DELETE self._states[session_id]
                    RETURN null
                END IF

                RETURN state
            END IF

            # Check Redis if available
            IF self._redis_client:
                state_json ← AWAIT self._redis_client.get(f"session:{session_id}")

                IF state_json:
                    state ← AgentState.from_json(state_json)

                    # Cache in memory
                    self._states[session_id] ← state

                    RETURN state
                END IF
            END IF

            RETURN null
        END

    ASYNC FUNCTION set(
        session_id: string,
        state: AgentState,
        ttl: integer = 3600
    ):
        """Store session state."""
        BEGIN
            # Acquire lock for session
            IF session_id NOT IN self._locks:
                self._locks[session_id] ← asyncio.Lock()
            END IF

            ASYNC WITH self._locks[session_id]:
                # Update timestamp and TTL
                state.updated_at ← current_timestamp()
                state.ttl ← ttl

                # Store in memory
                self._states[session_id] ← state

                # Persist to Redis if available
                IF self._redis_client:
                    state_json ← state.to_json()

                    AWAIT self._redis_client.setex(
                        f"session:{session_id}",
                        ttl,
                        state_json
                    )
                END IF
            END WITH
        END

    ASYNC FUNCTION delete(session_id: string):
        """Delete session state."""
        BEGIN
            # Remove from memory
            IF session_id IN self._states:
                DELETE self._states[session_id]
            END IF

            # Remove from Redis
            IF self._redis_client:
                AWAIT self._redis_client.delete(f"session:{session_id}")
            END IF
        END

    ASYNC FUNCTION cleanup_expired():
        """Clean up expired sessions."""
        BEGIN
            current_time ← current_timestamp()
            expired_sessions ← []

            FOR session_id, state IN self._states.items():
                age ← current_time - state.updated_at
                IF age.total_seconds() > state.ttl:
                    expired_sessions.append(session_id)
                END IF
            END FOR

            FOR session_id IN expired_sessions:
                AWAIT self.delete(session_id)
            END FOR

            LOG_INFO("cleaned_up_expired_sessions", count=len(expired_sessions))
        END
END CLASS
```

---

## Error Handling

### Retry Logic with Exponential Backoff

```python
ALGORITHM: RetryWithBackoff
INPUT:
    - operation: Callable
    - max_retries: integer = 3
    - initial_delay: float = 1.0
    - backoff_multiplier: float = 2.0
    - max_delay: float = 60.0
OUTPUT:
    - result: Any OR raises Exception

BEGIN
    attempt ← 0
    delay ← initial_delay
    last_error ← null

    WHILE attempt < max_retries:
        TRY:
            result ← AWAIT operation()
            RETURN result

        CATCH RetryableError as error:
            last_error ← error
            attempt ← attempt + 1

            IF attempt >= max_retries:
                LOG_ERROR("max_retries_exceeded", {
                    "operation": operation.__name__,
                    "attempts": attempt,
                    "error": str(error)
                })
                RAISE error
            END IF

            # Calculate next delay with exponential backoff
            current_delay ← MIN(delay, max_delay)

            LOG_WARNING("operation_failed_retrying", {
                "operation": operation.__name__,
                "attempt": attempt,
                "delay_seconds": current_delay,
                "error": str(error)
            })

            # Wait before retry
            AWAIT asyncio.sleep(current_delay)

            # Increase delay for next attempt
            delay ← delay * backoff_multiplier

        CATCH NonRetryableError as error:
            LOG_ERROR("non_retryable_error", {
                "operation": operation.__name__,
                "error": str(error)
            })
            RAISE error
        END TRY
    END WHILE
END
```

### Error Classification

```python
FUNCTION classify_error(error: Exception) -> ErrorClassification:
    """Classify error for retry logic."""
    BEGIN
        # Network errors - retryable
        IF isinstance(error, (ConnectionError, TimeoutError, HTTPException)):
            RETURN ErrorClassification(
                type="network",
                retryable=true,
                severity="warning",
                user_message="Network issue - retrying..."
            )
        END IF

        # Rate limit errors - retryable with longer delay
        IF isinstance(error, RateLimitError):
            RETURN ErrorClassification(
                type="rate_limit",
                retryable=true,
                severity="warning",
                user_message="Rate limit reached - waiting before retry...",
                suggested_delay=60.0
            )
        END IF

        # Authentication errors - not retryable
        IF isinstance(error, (AuthenticationError, PermissionError)):
            RETURN ErrorClassification(
                type="authentication",
                retryable=false,
                severity="error",
                user_message="Authentication failed - check credentials"
            )
        END IF

        # Validation errors - not retryable
        IF isinstance(error, (ValidationError, ValueError)):
            RETURN ErrorClassification(
                type="validation",
                retryable=false,
                severity="error",
                user_message="Invalid input - please check your request"
            )
        END IF

        # Agent execution errors - context-dependent
        IF isinstance(error, AgentExecutionError):
            # Check if agent supports retry
            IF error.agent_supports_retry:
                RETURN ErrorClassification(
                    type="agent_execution",
                    retryable=true,
                    severity="warning",
                    user_message=f"Agent {error.agent_name} failed - retrying..."
                )
            ELSE:
                RETURN ErrorClassification(
                    type="agent_execution",
                    retryable=false,
                    severity="error",
                    user_message=f"Agent {error.agent_name} failed: {error.message}"
                )
            END IF
        END IF

        # Unknown errors - not retryable by default
        RETURN ErrorClassification(
            type="unknown",
            retryable=false,
            severity="error",
            user_message="An unexpected error occurred"
        )
    END
```

---

## HITL Workflow

### Human-in-the-Loop Approval Algorithm

```python
ALGORITHM: RequestApproval
INPUT:
    - recommendations: List[Recommendation]
    - session_id: string
    - timeout_seconds: integer = 300
OUTPUT:
    - approval_result: ApprovalResult

BEGIN
    # Create approval request
    approval_id ← generate_uuid()

    approval_request ← ApprovalRequest(
        approval_id=approval_id,
        session_id=session_id,
        recommendation_id=recommendations[0].recommendation_id,
        recommendation=recommendations[0].to_dict(),
        status="pending",
        created_at=current_timestamp(),
        timeout_at=current_timestamp() + timedelta(seconds=timeout_seconds),
        response_event=asyncio.Event()
    )

    # Store approval request
    approval_store.set(approval_id, approval_request)

    # Emit approval required event
    emit_event("approval_required", {
        "approval_id": approval_id,
        "session_id": session_id,
        "recommendation": approval_request.recommendation,
        "timeout_seconds": timeout_seconds
    })

    LOG_INFO("approval_requested", {
        "approval_id": approval_id,
        "recommendation_id": recommendations[0].recommendation_id,
        "timeout_seconds": timeout_seconds
    })

    # Wait for response with timeout
    response_received ← AWAIT approval_request.wait_for_response(
        timeout=timeout_seconds
    )

    IF response_received:
        # Response received before timeout
        approval_result ← ApprovalResult(
            approval_id=approval_id,
            status=approval_request.status,
            approved_by=approval_request.approved_by,
            rejected_by=approval_request.rejected_by,
            reason=approval_request.reason,
            responded_at=approval_request.responded_at
        )

        # Emit approval response event
        emit_event("approval_response", {
            "approval_id": approval_id,
            "status": approval_request.status,
            "reason": approval_request.reason
        })

        LOG_INFO("approval_responded", {
            "approval_id": approval_id,
            "status": approval_request.status
        })
    ELSE:
        # Timeout occurred
        approval_result ← ApprovalResult(
            approval_id=approval_id,
            status="timeout",
            reason="Approval request timed out"
        )

        # Emit timeout event
        emit_event("approval_timeout", {
            "approval_id": approval_id,
            "timeout_seconds": timeout_seconds
        })

        LOG_WARNING("approval_timeout", {
            "approval_id": approval_id,
            "timeout_seconds": timeout_seconds
        })
    END IF

    # Clean up approval request
    approval_store.delete(approval_id)

    RETURN approval_result
END
```

### Approval Response Handling

```python
ALGORITHM: HandleApprovalResponse
INPUT:
    - approval_id: string
    - action: string  # "approve" | "reject"
    - user_id: string
    - reason: Optional[string] = null
OUTPUT:
    - success: boolean

BEGIN
    # Retrieve approval request
    approval_request ← approval_store.get(approval_id)

    IF NOT approval_request:
        LOG_ERROR("approval_not_found", approval_id=approval_id)
        RETURN false
    END IF

    # Check if already responded
    IF approval_request.status != "pending":
        LOG_WARNING("approval_already_responded", {
            "approval_id": approval_id,
            "status": approval_request.status
        })
        RETURN false
    END IF

    # Check if timed out
    IF current_timestamp() > approval_request.timeout_at:
        approval_request.status ← "timeout"
        approval_store.set(approval_id, approval_request)

        LOG_WARNING("approval_timeout_exceeded", approval_id=approval_id)
        RETURN false
    END IF

    # Apply action
    IF action == "approve":
        approval_request.approve(
            approved_by=user_id,
            reason=reason
        )

        LOG_INFO("approval_granted", {
            "approval_id": approval_id,
            "approved_by": user_id
        })
    ELSE IF action == "reject":
        approval_request.reject(
            rejected_by=user_id,
            reason=reason OR "No reason provided"
        )

        LOG_INFO("approval_rejected", {
            "approval_id": approval_id,
            "rejected_by": user_id,
            "reason": reason
        })
    ELSE:
        LOG_ERROR("invalid_approval_action", action=action)
        RETURN false
    END IF

    # Update stored request
    approval_store.set(approval_id, approval_request)

    RETURN true
END
```

---

## Function Signatures

### FastAPI Endpoint Registration

```python
FUNCTION add_fastapi_endpoint(
    app: FastAPI,
    sdk: CopilotKitSDK,
    path: string = "/copilotkit"
) -> None:
    """
    Register CopilotKit endpoint with FastAPI application.

    Args:
        app: FastAPI application instance
        sdk: Initialized CopilotKitSDK instance
        path: URL path for endpoint (default: "/copilotkit")

    Registers:
        POST {path}/chat - Main chat endpoint with streaming
        GET {path}/status - Get SDK and agent status
        POST {path}/approval/{approval_id} - Handle approval responses
    """
    BEGIN
        # Register chat endpoint
        @app.post(f"{path}/chat")
        ASYNC FUNCTION copilotkit_chat(request: ChatRequest):
            RETURN StreamingResponse(
                sdk.stream_chat(request),
                media_type="text/event-stream"
            )
        END

        # Register status endpoint
        @app.get(f"{path}/status")
        ASYNC FUNCTION copilotkit_status():
            RETURN sdk.get_status()
        END

        # Register approval endpoint
        @app.post(f"{path}/approval/{approval_id}")
        ASYNC FUNCTION handle_approval(
            approval_id: string,
            action: ApprovalAction
        ):
            success ← AWAIT HandleApprovalResponse(
                approval_id=approval_id,
                action=action.action,
                user_id=action.user_id,
                reason=action.reason
            )

            RETURN {"success": success}
        END
    END
```

### CopilotKitSDK Class Interface

```python
CLASS CopilotKitSDK:
    """
    CopilotKit SDK for managing LangGraph agents.
    """

    FUNCTION __init__(
        agents: List[LangGraphAgent],
        config: SDKConfig
    ):
        """
        Initialize SDK with agents.

        Args:
            agents: List of LangGraph agent wrappers
            config: SDK configuration
        """
        pass

    ASYNC FUNCTION stream_chat(
        request: ChatRequest
    ) -> AsyncGenerator[AGUIEvent, None]:
        """
        Stream chat responses with AG UI Protocol events.

        Args:
            request: Chat request with messages and context

        Yields:
            AG UI Protocol events
        """
        pass

    FUNCTION get_status() -> Dict[string, Any]:
        """
        Get SDK and agent status.

        Returns:
            Status dictionary with agent states
        """
        pass

    ASYNC FUNCTION invoke_agent(
        agent_name: string,
        context: Dict[string, Any],
        session_id: string
    ) -> Dict[string, Any]:
        """
        Invoke specific agent with context.

        Args:
            agent_name: Name of agent to invoke
            context: Execution context
            session_id: Session identifier

        Returns:
            Agent output
        """
        pass
```

### LangGraphAgent Wrapper Interface

```python
CLASS LangGraphAgent:
    """
    Wrapper for LangGraph agent with AG UI Protocol support.
    """

    FUNCTION __init__(
        name: string,
        description: string,
        agent: CompiledGraph
    ):
        """
        Initialize LangGraph agent wrapper.

        Args:
            name: Agent name
            description: Agent description
            agent: Compiled LangGraph graph
        """
        pass

    ASYNC FUNCTION invoke(
        context: Dict[string, Any],
        session_id: string
    ) -> Dict[string, Any]:
        """
        Invoke agent with context.

        Args:
            context: Execution context
            session_id: Session identifier

        Returns:
            Agent output
        """
        pass

    ASYNC FUNCTION stream_events(
        context: Dict[string, Any],
        session_id: string
    ) -> AsyncGenerator[AGUIEvent, None]:
        """
        Stream agent execution events.

        Args:
            context: Execution context
            session_id: Session identifier

        Yields:
            AG UI Protocol events
        """
        pass
```

### Next.js API Route Handler

```typescript
FUNCTION handler(
    req: NextApiRequest,
    res: NextApiResponse
) -> Promise<void>:
    """
    Next.js API route handler for CopilotKit proxy.

    Args:
        req: Next.js request object
        res: Next.js response object

    Proxies:
        - POST requests to FastAPI with streaming
        - GET requests for status
    """
    BEGIN
        AWAIT ProxyCopilotKitRequest(req, res)
    END
```

---

## Complexity Analysis

### Overall System Performance

**Orchestration Workflow**:
- Time Complexity: O(n) where n = number of agents (sequential execution)
- Space Complexity: O(m) where m = accumulated state size
- Target Latency: < 500ms per agent (SPARC PRD metric)

**State Management**:
- Get/Set Operations: O(1) average with hash table
- Session Cleanup: O(k) where k = number of sessions
- Memory Usage: O(s × m) where s = sessions, m = state size per session

**Event Streaming**:
- Event Emission: O(1) per event
- SSE Streaming: O(n) where n = event count
- Bandwidth: O(e × s) where e = event size, s = stream length

**Approval Workflow**:
- Request Creation: O(1)
- Wait with Timeout: O(1) (async event)
- Response Handling: O(1)

---

## Next Steps

1. **Architecture Phase**: Design detailed system architecture with deployment topology
2. **Refinement Phase**: Implement and test LangGraph wrappers
3. **Completion Phase**: Integration testing and performance validation

---

**Document Status**: Complete
**Ready for**: Architecture Phase
**Validation**: Algorithm correctness verified against existing agent implementations
