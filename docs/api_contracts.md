# API Contracts Specification

## 1. Overview

This document defines the API contracts for the Sergas Agents system, including:
- Internal API contracts between agents
- MCP tool interface specifications
- Hook event schemas
- Configuration API contracts
- External service integration contracts

All APIs follow RESTful principles with JSON payloads and use OpenAPI 3.1 specification.

## 2. Internal Agent Communication APIs

### 2.1 Agent Task Execution API

#### Execute Agent Task

```typescript
POST /api/v1/agents/{agent_id}/execute

Request:
{
  "task_description": string,
  "context": {
    "account_id"?: string,
    "session_id"?: string,
    "priority"?: "high" | "medium" | "low",
    "timeout_seconds"?: number,
    "additional_context"?: Record<string, any>
  },
  "options": {
    "streaming"?: boolean,
    "max_iterations"?: number,
    "continue_session"?: boolean,
    "parent_session_id"?: string
  }
}

Response (200 OK):
{
  "success": true,
  "message": "Task execution started",
  "data": {
    "session_id": string,
    "agent_id": string,
    "status": "active" | "queued",
    "estimated_completion_time": string (ISO 8601),
    "stream_url"?: string  // If streaming enabled
  },
  "timestamp": string (ISO 8601),
  "request_id": string
}

Response (Streaming):
Server-Sent Events (text/event-stream)
data: {"type": "text", "content": string, "session_id": string}
data: {"type": "tool_use", "tool": string, "input": object}
data: {"type": "tool_result", "tool": string, "output": any}
data: {"type": "complete", "session_id": string, "result": object}
data: {"type": "error", "error": string, "session_id": string}

Error Response (400 Bad Request):
{
  "success": false,
  "message": "Invalid request",
  "error": "Task description is required",
  "error_code": "INVALID_TASK",
  "timestamp": string (ISO 8601),
  "request_id": string
}

Error Response (429 Too Many Requests):
{
  "success": false,
  "message": "Rate limit exceeded",
  "error": "Maximum concurrent agents reached",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60,
  "timestamp": string (ISO 8601)
}
```

#### Get Agent Session Status

```typescript
GET /api/v1/agents/{agent_id}/sessions/{session_id}

Response (200 OK):
{
  "success": true,
  "data": {
    "session_id": string,
    "agent_id": string,
    "status": "active" | "completed" | "failed" | "cancelled",
    "start_time": string (ISO 8601),
    "end_time"?: string (ISO 8601),
    "duration_seconds"?: number,
    "iterations_completed": number,
    "tools_called": string[],
    "output"?: string,
    "error"?: string,
    "metrics": {
      "tokens_used": number,
      "api_calls": number,
      "tool_calls": number
    }
  }
}
```

#### Continue Agent Session

```typescript
POST /api/v1/agents/{agent_id}/sessions/{session_id}/continue

Request:
{
  "prompt": string,
  "context"?: Record<string, any>
}

Response (200 OK):
{
  "success": true,
  "data": {
    "session_id": string,
    "status": "active",
    "stream_url"?: string
  }
}
```

#### Cancel Agent Session

```typescript
DELETE /api/v1/agents/{agent_id}/sessions/{session_id}

Response (200 OK):
{
  "success": true,
  "message": "Session cancelled successfully",
  "data": {
    "session_id": string,
    "status": "cancelled"
  }
}
```

### 2.2 Agent Coordination API

#### Spawn Sub-Agent

```typescript
POST /api/v1/agents/spawn

Request:
{
  "agent_type": string,
  "parent_session_id": string,
  "task_description": string,
  "context": Record<string, any>,
  "config_override"?: {
    "max_iterations"?: number,
    "timeout_seconds"?: number,
    "allowed_tools"?: string[]
  }
}

Response (200 OK):
{
  "success": true,
  "data": {
    "agent_id": string,
    "session_id": string,
    "status": "active"
  }
}
```

#### Agent Memory Operations

```typescript
// Store Memory
POST /api/v1/agents/{agent_id}/memory

Request:
{
  "session_id": string,
  "memory_type": "short_term" | "long_term" | "episodic" | "semantic",
  "memory_key": string,
  "content": Record<string, any>,
  "importance_score"?: number,  // 0-1
  "expires_at"?: string (ISO 8601),
  "tags"?: string[]
}

Response (201 Created):
{
  "success": true,
  "data": {
    "memory_id": string,
    "memory_key": string,
    "created_at": string (ISO 8601)
  }
}

// Retrieve Memory
GET /api/v1/agents/{agent_id}/memory/{memory_key}
GET /api/v1/agents/{agent_id}/memory?session_id={session_id}

Response (200 OK):
{
  "success": true,
  "data": {
    "memory_id": string,
    "memory_key": string,
    "content": Record<string, any>,
    "memory_type": string,
    "importance_score": number,
    "access_count": number,
    "created_at": string (ISO 8601),
    "last_accessed": string (ISO 8601)
  }
}

// Search Memory
POST /api/v1/agents/{agent_id}/memory/search

Request:
{
  "query": string,
  "memory_types"?: string[],
  "tags"?: string[],
  "min_importance"?: number,
  "limit"?: number
}

Response (200 OK):
{
  "success": true,
  "data": {
    "results": Array<{
      "memory_id": string,
      "memory_key": string,
      "content": Record<string, any>,
      "relevance_score": number
    }>,
    "total_count": number
  }
}
```

## 3. MCP Tool Interface Specifications

### 3.1 Zoho CRM Tools

#### zoho_query_accounts

```typescript
Tool Name: zoho_query_accounts
Description: Query Zoho CRM for account data

Input Schema:
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query or COQL query string"
    },
    "filters": {
      "type": "object",
      "properties": {
        "status": { "type": "string", "enum": ["active", "inactive"] },
        "account_type": { "type": "string" },
        "date_range": {
          "type": "object",
          "properties": {
            "start": { "type": "string", "format": "date-time" },
            "end": { "type": "string", "format": "date-time" }
          }
        }
      }
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "default": 0
    }
  },
  "required": ["query"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "accounts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "status": { "type": "string" },
          "account_type": { "type": "string" },
          "email": { "type": "string" },
          "phone": { "type": "string" },
          "annual_revenue": { "type": "number" },
          "created_at": { "type": "string", "format": "date-time" },
          "custom_fields": { "type": "object" }
        }
      }
    },
    "total_count": { "type": "integer" },
    "has_more": { "type": "boolean" }
  }
}

Error Codes:
- AUTH_FAILED: Authentication with Zoho failed
- INVALID_QUERY: Query syntax error
- RATE_LIMIT: API rate limit exceeded
- NETWORK_ERROR: Network connectivity issue
```

#### zoho_update_account

```typescript
Tool Name: zoho_update_account
Description: Update account record in Zoho CRM

Input Schema:
{
  "type": "object",
  "properties": {
    "account_id": {
      "type": "string",
      "description": "Zoho account ID"
    },
    "updates": {
      "type": "object",
      "properties": {
        "account_name": { "type": "string" },
        "status": { "type": "string" },
        "email": { "type": "string", "format": "email" },
        "phone": { "type": "string" },
        "notes": { "type": "string" },
        "custom_fields": { "type": "object" }
      }
    },
    "trigger_workflows": {
      "type": "boolean",
      "default": true,
      "description": "Whether to trigger Zoho workflows"
    }
  },
  "required": ["account_id", "updates"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "account_id": { "type": "string" },
    "updated_fields": { "type": "array", "items": { "type": "string" } },
    "updated_at": { "type": "string", "format": "date-time" },
    "version": { "type": "integer" }
  }
}
```

#### zoho_query_transactions

```typescript
Tool Name: zoho_query_transactions
Description: Query financial transactions from Zoho Books

Input Schema:
{
  "type": "object",
  "properties": {
    "account_id": {
      "type": "string",
      "description": "Filter by account ID"
    },
    "transaction_types": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["invoice", "payment", "credit_note", "refund"]
      }
    },
    "date_range": {
      "type": "object",
      "properties": {
        "start": { "type": "string", "format": "date" },
        "end": { "type": "string", "format": "date" }
      },
      "required": ["start", "end"]
    },
    "status": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["pending", "completed", "failed", "cancelled"]
      }
    },
    "min_amount": { "type": "number" },
    "max_amount": { "type": "number" },
    "limit": { "type": "integer", "default": 100 }
  }
}

Output Schema:
{
  "type": "object",
  "properties": {
    "transactions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "transaction_id": { "type": "string" },
          "account_id": { "type": "string" },
          "transaction_type": { "type": "string" },
          "transaction_number": { "type": "string" },
          "date": { "type": "string", "format": "date-time" },
          "amount": { "type": "number" },
          "currency": { "type": "string" },
          "status": { "type": "string" },
          "line_items": { "type": "array" }
        }
      }
    },
    "total_count": { "type": "integer" },
    "total_amount": { "type": "number" }
  }
}
```

### 3.2 Cognee Knowledge Graph Tools

#### cognee_search

```typescript
Tool Name: cognee_search
Description: Search Cognee knowledge graph for relevant information

Input Schema:
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Natural language search query"
    },
    "entity_types": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Filter by entity types (e.g., 'account', 'transaction')"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 10
    },
    "min_relevance": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "default": 0.7,
      "description": "Minimum relevance score (0-1)"
    }
  },
  "required": ["query"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "entity_id": { "type": "string" },
          "entity_type": { "type": "string" },
          "content": { "type": "object" },
          "relevance_score": { "type": "number" },
          "related_entities": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "entity_id": { "type": "string" },
                "relationship": { "type": "string" },
                "relevance": { "type": "number" }
              }
            }
          }
        }
      }
    },
    "total_results": { "type": "integer" },
    "query_time_ms": { "type": "number" }
  }
}
```

#### cognee_query_graph

```typescript
Tool Name: cognee_query_graph
Description: Execute graph query on Cognee knowledge graph

Input Schema:
{
  "type": "object",
  "properties": {
    "cypher_query": {
      "type": "string",
      "description": "Cypher query to execute"
    },
    "parameters": {
      "type": "object",
      "description": "Query parameters"
    },
    "timeout_ms": {
      "type": "integer",
      "default": 30000
    }
  },
  "required": ["cypher_query"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "labels": { "type": "array", "items": { "type": "string" } },
          "properties": { "type": "object" }
        }
      }
    },
    "relationships": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "type": { "type": "string" },
          "start_node": { "type": "string" },
          "end_node": { "type": "string" },
          "properties": { "type": "object" }
        }
      }
    },
    "execution_time_ms": { "type": "number" }
  }
}
```

#### cognee_add_knowledge

```typescript
Tool Name: cognee_add_knowledge
Description: Add new knowledge to Cognee graph

Input Schema:
{
  "type": "object",
  "properties": {
    "entity_type": {
      "type": "string",
      "description": "Type of entity to create"
    },
    "entity_data": {
      "type": "object",
      "description": "Entity properties"
    },
    "relationships": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target_entity_id": { "type": "string" },
          "relationship_type": { "type": "string" },
          "properties": { "type": "object" }
        }
      }
    }
  },
  "required": ["entity_type", "entity_data"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "entity_id": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "relationships_created": { "type": "integer" }
  }
}
```

### 3.3 Analysis and Validation Tools

#### validate_account_data

```typescript
Tool Name: validate_account_data
Description: Validate account data for completeness and correctness

Input Schema:
{
  "type": "object",
  "properties": {
    "account_data": {
      "type": "object",
      "description": "Account data to validate"
    },
    "validation_rules": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["required_fields", "format_validation", "business_rules", "data_consistency"]
      },
      "default": ["required_fields", "format_validation"]
    }
  },
  "required": ["account_data"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "is_valid": { "type": "boolean" },
    "validation_errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "error_type": { "type": "string" },
          "message": { "type": "string" },
          "severity": { "type": "string", "enum": ["error", "warning", "info"] }
        }
      }
    },
    "validation_warnings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "message": { "type": "string" }
        }
      }
    },
    "completeness_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Data completeness (0-1)"
    }
  }
}
```

#### generate_recommendation

```typescript
Tool Name: generate_recommendation
Description: Generate recommendation based on account analysis

Input Schema:
{
  "type": "object",
  "properties": {
    "account_id": { "type": "string" },
    "analysis_data": {
      "type": "object",
      "description": "Account analysis results"
    },
    "recommendation_types": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["upsell", "cross_sell", "retention", "engagement"]
      }
    },
    "min_confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "default": 0.7
    }
  },
  "required": ["account_id", "analysis_data"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "recommendation_id": { "type": "string" },
          "type": { "type": "string" },
          "title": { "type": "string" },
          "description": { "type": "string" },
          "confidence_score": { "type": "number" },
          "priority": { "type": "string" },
          "estimated_impact": { "type": "object" },
          "suggested_actions": { "type": "array" },
          "reasoning": { "type": "string" }
        }
      }
    },
    "generation_metadata": {
      "type": "object",
      "properties": {
        "model_version": { "type": "string" },
        "generated_at": { "type": "string", "format": "date-time" },
        "processing_time_ms": { "type": "number" }
      }
    }
  }
}
```

#### audit_log_event

```typescript
Tool Name: audit_log_event
Description: Log audit event for compliance tracking

Input Schema:
{
  "type": "object",
  "properties": {
    "event_type": {
      "type": "string",
      "enum": [
        "agent_session_start",
        "agent_session_end",
        "data_access",
        "data_modification",
        "recommendation_generated",
        "tool_execution"
      ]
    },
    "severity": {
      "type": "string",
      "enum": ["info", "warning", "error", "critical"],
      "default": "info"
    },
    "description": { "type": "string" },
    "agent_id": { "type": "string" },
    "session_id": { "type": "string" },
    "resource_affected": { "type": "string" },
    "before_state": { "type": "object" },
    "after_state": { "type": "object" },
    "compliance_tags": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["event_type", "description", "agent_id"]
}

Output Schema:
{
  "type": "object",
  "properties": {
    "event_id": { "type": "string" },
    "logged_at": { "type": "string", "format": "date-time" },
    "status": { "type": "string", "enum": ["success", "failed"] }
  }
}
```

## 4. Hook Event Schemas

### 4.1 Pre-Tool Hook

```typescript
Event: pre_tool
Description: Fired before tool execution

Payload:
{
  "hook_type": "pre_tool",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "tool_name": string,
  "tool_input": object,
  "context": {
    "iteration_number": number,
    "parent_tool": string | null,
    "user_id": string | null
  }
}

Expected Response:
{
  "allow_execution": boolean,
  "modified_input"?: object,  // Optional: modify tool input
  "deny_reason"?: string  // If allow_execution is false
}
```

### 4.2 Post-Tool Hook

```typescript
Event: post_tool
Description: Fired after tool execution completes

Payload:
{
  "hook_type": "post_tool",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "tool_name": string,
  "tool_input": object,
  "tool_output": any,
  "execution_time_ms": number,
  "status": "success" | "error",
  "error"?: {
    "message": string,
    "type": string,
    "stack"?: string
  },
  "context": {
    "iteration_number": number,
    "tokens_used": number
  }
}

Expected Response:
{
  "continue_execution": boolean,
  "modified_output"?: any,  // Optional: modify tool output
  "stop_reason"?: string  // If continue_execution is false
}
```

### 4.3 Session Lifecycle Hooks

```typescript
// Session Start Hook
Event: on_session_start
Payload:
{
  "hook_type": "on_session_start",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "task_description": string,
  "initial_context": object,
  "config": {
    "max_iterations": number,
    "timeout_seconds": number,
    "allowed_tools": string[]
  }
}

// Session End Hook
Event: on_session_end
Payload:
{
  "hook_type": "on_session_end",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "status": "completed" | "failed" | "cancelled" | "timeout",
  "duration_seconds": number,
  "iterations_completed": number,
  "tools_used": string[],
  "tool_call_count": number,
  "tokens_used": number,
  "result": {
    "output": string,
    "structured_results": object,
    "error"?: string
  }
}

// Session Error Hook
Event: on_session_error
Payload:
{
  "hook_type": "on_session_error",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "error": {
    "type": string,
    "message": string,
    "stack": string,
    "tool_name"?: string,
    "context": object
  },
  "recovery_attempted": boolean
}
```

### 4.4 Permission Hook

```typescript
Event: can_use_tool
Description: Permission check before tool execution

Payload:
{
  "hook_type": "can_use_tool",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "tool_name": string,
  "tool_input": object,
  "agent_config": {
    "allowed_tools": string[],
    "disallowed_tools": string[],
    "permission_mode": string
  }
}

Expected Response:
{
  "allowed": boolean,
  "reason"?: string,  // If not allowed
  "modified_permissions"?: {
    "tool_name": string,
    "constraints": object
  }
}
```

### 4.5 Context Compaction Hook

```typescript
Event: on_context_compaction
Description: Fired when context window needs compaction

Payload:
{
  "hook_type": "on_context_compaction",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "current_token_count": number,
  "max_token_limit": number,
  "context_summary": {
    "messages_count": number,
    "tool_results_count": number,
    "file_contents_count": number
  }
}

Expected Response:
{
  "compaction_strategy": "summarize" | "drop_oldest" | "semantic_compression",
  "preserve_messages": string[],  // Message IDs to preserve
  "summary_instructions"?: string
}
```

## 5. Configuration API

### 5.1 Agent Configuration

```typescript
// Get Agent Configuration
GET /api/v1/config/agents/{agent_id}

Response (200 OK):
{
  "success": true,
  "data": {
    "agent_id": string,
    "agent_name": string,
    "system_prompt": string,
    "allowed_tools": string[],
    "disallowed_tools": string[],
    "permission_mode": string,
    "max_iterations": number,
    "timeout_seconds": number,
    "enable_hooks": boolean,
    "mcp_servers": string[]
  }
}

// Update Agent Configuration
PUT /api/v1/config/agents/{agent_id}

Request:
{
  "system_prompt"?: string,
  "allowed_tools"?: string[],
  "max_iterations"?: number,
  "timeout_seconds"?: number,
  "config_updates": object
}

Response (200 OK):
{
  "success": true,
  "message": "Configuration updated",
  "data": {
    "agent_id": string,
    "updated_fields": string[],
    "updated_at": string (ISO 8601)
  }
}
```

### 5.2 System Configuration

```typescript
// Get System Configuration
GET /api/v1/config/system

Response (200 OK):
{
  "success": true,
  "data": {
    "environment": string,
    "version": string,
    "log_level": string,
    "max_concurrent_agents": number,
    "enable_metrics": boolean,
    "enable_audit_logging": boolean,
    "features": {
      "hooks_enabled": boolean,
      "memory_enabled": boolean,
      "streaming_enabled": boolean
    }
  }
}

// Health Check
GET /api/v1/health

Response (200 OK):
{
  "status": "healthy" | "degraded" | "unhealthy",
  "timestamp": string (ISO 8601),
  "version": string,
  "services": {
    "database": { "status": "up" | "down", "latency_ms": number },
    "redis": { "status": "up" | "down", "latency_ms": number },
    "anthropic_api": { "status": "up" | "down", "latency_ms": number },
    "zoho_api": { "status": "up" | "down", "latency_ms": number },
    "cognee": { "status": "up" | "down", "latency_ms": number }
  },
  "metrics": {
    "active_sessions": number,
    "total_requests_today": number,
    "error_rate": number
  }
}
```

## 6. External Service Integration Contracts

### 6.1 Zoho API Integration

```typescript
// Authentication
POST https://accounts.zoho.com/oauth/v2/token

Request:
{
  "grant_type": "refresh_token",
  "client_id": string,
  "client_secret": string,
  "refresh_token": string
}

Response:
{
  "access_token": string,
  "expires_in": number,
  "api_domain": string,
  "token_type": "Bearer"
}

// Rate Limits
X-Rate-Limit-Limit: 200 requests per minute
X-Rate-Limit-Remaining: number
X-Rate-Limit-Reset: timestamp

// Error Response Format
{
  "code": string,
  "message": string,
  "details": object
}
```

### 6.2 Cognee API Integration

```typescript
// Authentication
Authorization: Bearer {api_key}

// Rate Limits
X-RateLimit-Limit: 1000 requests per hour
X-RateLimit-Remaining: number
X-RateLimit-Reset: timestamp

// Search Endpoint
POST /api/v1/search
Content-Type: application/json

// Graph Query Endpoint
POST /api/v1/graph/query
Content-Type: application/json

// Error Response Format
{
  "error": {
    "code": string,
    "message": string,
    "type": string
  }
}
```

## 7. WebSocket API for Real-Time Updates

```typescript
WebSocket: ws://api.sergas.com/v1/ws

// Connection
{
  "type": "connect",
  "auth_token": string,
  "subscribe_to": string[]  // ["agents", "sessions", "audit"]
}

// Agent Status Updates
{
  "type": "agent_status",
  "timestamp": string (ISO 8601),
  "agent_id": string,
  "session_id": string,
  "status": string,
  "data": object
}

// Real-time Audit Events
{
  "type": "audit_event",
  "timestamp": string (ISO 8601),
  "event": object
}

// System Alerts
{
  "type": "system_alert",
  "timestamp": string (ISO 8601),
  "severity": "info" | "warning" | "error" | "critical",
  "message": string,
  "data": object
}
```

## 8. Error Handling Standards

### 8.1 Error Response Format

```typescript
{
  "success": false,
  "error": string,
  "error_code": string,
  "error_details": {
    "field": string,
    "constraint": string,
    "provided_value": any
  },
  "timestamp": string (ISO 8601),
  "request_id": string,
  "documentation_url": string
}
```

### 8.2 Standard Error Codes

```typescript
// Authentication & Authorization (4xx)
AUTH_REQUIRED: "Authentication required"
AUTH_FAILED: "Authentication failed"
AUTH_EXPIRED: "Authentication token expired"
PERMISSION_DENIED: "Permission denied"
INVALID_API_KEY: "Invalid API key"

// Request Errors (4xx)
INVALID_REQUEST: "Invalid request format"
MISSING_PARAMETER: "Required parameter missing"
INVALID_PARAMETER: "Invalid parameter value"
RESOURCE_NOT_FOUND: "Resource not found"
RESOURCE_CONFLICT: "Resource conflict"

// Rate Limiting (429)
RATE_LIMIT_EXCEEDED: "Rate limit exceeded"
QUOTA_EXCEEDED: "API quota exceeded"

// Server Errors (5xx)
INTERNAL_ERROR: "Internal server error"
SERVICE_UNAVAILABLE: "Service temporarily unavailable"
TIMEOUT: "Request timeout"
EXTERNAL_SERVICE_ERROR: "External service error"

// Business Logic Errors
INVALID_STATE: "Invalid state for operation"
BUSINESS_RULE_VIOLATION: "Business rule violation"
DATA_VALIDATION_FAILED: "Data validation failed"
```

## 9. Authentication and Security

### 9.1 API Authentication

```typescript
// API Key Authentication
Authorization: Bearer {api_key}

// JWT Authentication (for internal services)
Authorization: Bearer {jwt_token}

// OAuth 2.0 (for third-party integrations)
Authorization: Bearer {oauth_access_token}
```

### 9.2 Request Signing

```typescript
// HMAC Request Signature
X-Signature: HMAC-SHA256(secret_key, request_body + timestamp)
X-Timestamp: Unix timestamp
X-Client-ID: string
```

### 9.3 Rate Limiting Headers

```typescript
X-RateLimit-Limit: Maximum requests per window
X-RateLimit-Remaining: Remaining requests in current window
X-RateLimit-Reset: Timestamp when limit resets
X-RateLimit-Window: Time window in seconds
```

## 10. Versioning and Deprecation

### 10.1 API Versioning

```
Base URL: https://api.sergas.com/v1
Version Header: X-API-Version: 1.0
Accept Header: application/vnd.sergas.v1+json
```

### 10.2 Deprecation Notice

```typescript
// Deprecated Endpoint Response
{
  "success": true,
  "data": object,
  "deprecation_notice": {
    "deprecated": true,
    "sunset_date": string (ISO 8601),
    "migration_guide_url": string,
    "replacement_endpoint": string
  }
}
```

---

## Summary

This API contracts specification provides comprehensive definitions for:

1. **Internal Agent APIs**: Task execution, session management, memory operations
2. **MCP Tool Interfaces**: Zoho, Cognee, analysis, and validation tools
3. **Hook Event Schemas**: Lifecycle hooks, permission checks, context management
4. **Configuration APIs**: Agent and system configuration management
5. **External Integrations**: Zoho and Cognee API contracts
6. **Real-time Updates**: WebSocket API for live monitoring
7. **Error Handling**: Standard error formats and codes
8. **Security**: Authentication, authorization, and rate limiting
9. **Versioning**: API versioning and deprecation strategies

All contracts follow RESTful principles, use JSON for data exchange, include comprehensive error handling, and provide clear documentation for implementation.
