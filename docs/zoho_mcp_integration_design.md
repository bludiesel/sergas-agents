# Zoho CRM MCP Integration Design

## 1. Executive Summary

This document defines the integration architecture for connecting Sergas Super Account Manager agents to Zoho CRM via Model Context Protocol (MCP). The design prioritizes the official Zoho MCP endpoint (`npx mcp-remote`) as the primary integration point, with fallback mechanisms for resilience and comprehensive coverage of CRM operations.

**Key Design Principles:**
- **Security First**: OAuth 2.0 with token rotation, secrets management, and audit logging
- **Resilience**: Multi-layer fallback strategy (MCP → REST API → cached data)
- **Observability**: Comprehensive logging, metrics, and error tracking
- **Scalability**: Rate limiting, connection pooling, and request queuing
- **Maintainability**: Clear separation of concerns, versioned APIs, and extensibility

---

## 2. Architecture Overview

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Agent SDK Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Research    │  │   Account    │  │ Recommendation│         │
│  │   Agent      │  │   Manager    │  │    Engine     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │   MCP Integration Orchestrator       │
          │  - Tool routing                      │
          │  - Permission enforcement            │
          │  - Request/response normalization    │
          │  - Circuit breaker                   │
          └──────────┬───────────────────────────┘
                     │
          ┌──────────┴──────────┬─────────────┐
          │                     │             │
┌─────────▼─────────┐ ┌────────▼──────┐ ┌───▼──────────┐
│   Zoho MCP        │ │  REST API     │ │   Memory     │
│   Client          │ │  Fallback     │ │   Cache      │
│  (Primary)        │ │  (Secondary)  │ │  (Tertiary)  │
└─────────┬─────────┘ └───────┬───────┘ └──────────────┘
          │                   │
          └───────┬───────────┘
                  │
        ┌─────────▼──────────┐
        │   Zoho CRM API     │
        │   (OAuth 2.0)      │
        └────────────────────┘
```

### 2.2 Integration Layers

1. **Agent Layer**: Claude agents invoke tools through MCP protocol
2. **Orchestration Layer**: Routes requests, enforces policies, manages failures
3. **Client Layer**: Handles actual API communication with Zoho
4. **Data Layer**: Caching, persistence, and memory integration

---

## 3. Zoho MCP Endpoint Integration

### 3.1 Primary Integration: Official Zoho MCP

**Endpoint Configuration:**
```typescript
{
  "mcpServers": {
    "zoho-crm": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://zoho-mcp2-900114980.us-west-2.elb.amazonaws.com"
      ],
      "env": {
        "ZOHO_CLIENT_ID": "${VAULT_ZOHO_CLIENT_ID}",
        "ZOHO_CLIENT_SECRET": "${VAULT_ZOHO_CLIENT_SECRET}",
        "ZOHO_REFRESH_TOKEN": "${VAULT_ZOHO_REFRESH_TOKEN}",
        "ZOHO_REGION": "US",
        "ZOHO_API_VERSION": "v6"
      }
    }
  }
}
```

### 3.2 Tool Catalog Mapping

**Core Operations:**

| MCP Tool | Zoho Module | Agent Permissions | Rate Limit Group |
|----------|-------------|-------------------|------------------|
| `get_account` | Accounts | research, account-manager | read-single |
| `list_accounts` | Accounts | research, account-manager | read-list |
| `update_account` | Accounts | account-manager | write-single |
| `create_account` | Accounts | account-manager | write-single |
| `get_contact` | Contacts | research, account-manager | read-single |
| `list_contacts` | Contacts | research, account-manager | read-list |
| `get_deal` | Deals | research, account-manager | read-single |
| `list_deals` | Deals | research, account-manager | read-list |
| `create_deal` | Deals | account-manager | write-single |
| `update_deal` | Deals | account-manager | write-single |
| `get_notes` | Notes | research, account-manager | read-list |
| `create_note` | Notes | account-manager, recommendation | write-single |
| `list_activities` | Tasks/Events/Calls | research, account-manager | read-list |
| `create_activity` | Tasks/Events/Calls | account-manager, recommendation | write-single |
| `search_records` | Search API | research, account-manager | search |

**Extended Operations (via tool composition):**

| Composite Tool | Component Tools | Purpose |
|----------------|-----------------|---------|
| `get_account_health` | get_account, list_deals, list_activities, get_notes | Retrieve complete account context |
| `update_account_with_notes` | update_account, create_note | Atomic update with audit trail |
| `create_deal_with_activities` | create_deal, create_activity | Deal creation with follow-up tasks |

### 3.3 Tool Discovery and Registration

**Discovery Process:**
1. On startup, invoke MCP `list_tools` to retrieve available operations
2. Parse tool schemas (input parameters, return types, descriptions)
3. Register tools with orchestrator, mapping to internal permissions model
4. Cache tool catalog with 24-hour TTL, refresh on changes

**Tool Registry Schema:**
```typescript
interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: JSONSchema;
  outputSchema: JSONSchema;
  requiredScopes: string[];
  rateLimitGroup: string;
  fallbackStrategy: 'rest-api' | 'cache' | 'fail';
  timeout: number; // milliseconds
  retryPolicy: {
    maxAttempts: number;
    backoffMultiplier: number;
    initialDelay: number;
  };
}
```

---

## 4. Authentication and Token Management

### 4.1 OAuth 2.0 Flow

**Initial Authorization (One-Time Setup):**
```
1. Generate authorization URL:
   https://accounts.zoho.com/oauth/v2/auth?
     scope=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL
     &client_id={CLIENT_ID}
     &response_type=code
     &redirect_uri={REDIRECT_URI}
     &access_type=offline

2. User authorizes and receives authorization code

3. Exchange code for tokens:
   POST https://accounts.zoho.com/oauth/v2/token
   Body:
     grant_type=authorization_code
     client_id={CLIENT_ID}
     client_secret={CLIENT_SECRET}
     redirect_uri={REDIRECT_URI}
     code={AUTH_CODE}

4. Store refresh_token in secrets vault (never expires)
   Store access_token in memory cache (1-hour TTL)
```

### 4.2 Token Refresh Strategy

**Proactive Refresh:**
```typescript
class TokenManager {
  private accessToken: string;
  private expiresAt: Date;
  private refreshToken: string;
  private refreshThreshold = 300; // 5 minutes before expiry

  async getAccessToken(): Promise<string> {
    if (this.needsRefresh()) {
      await this.refreshAccessToken();
    }
    return this.accessToken;
  }

  private needsRefresh(): boolean {
    const now = new Date();
    const threshold = new Date(this.expiresAt.getTime() - this.refreshThreshold * 1000);
    return now >= threshold;
  }

  private async refreshAccessToken(): Promise<void> {
    const response = await fetch('https://accounts.zoho.com/oauth/v2/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: await secrets.get('ZOHO_CLIENT_ID'),
        client_secret: await secrets.get('ZOHO_CLIENT_SECRET'),
        refresh_token: this.refreshToken
      })
    });

    if (!response.ok) {
      await this.handleRefreshError(response);
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    this.expiresAt = new Date(Date.now() + data.expires_in * 1000);

    // Store in memory cache for concurrent requests
    await cache.set('zoho:access_token', this.accessToken, data.expires_in);

    // Audit token refresh
    await auditLog.write({
      event: 'token_refreshed',
      timestamp: new Date(),
      expiresAt: this.expiresAt
    });
  }
}
```

### 4.3 Multi-Region Support

**Region-Specific Endpoints:**
```typescript
const ZOHO_REGIONS = {
  US: {
    api: 'https://www.zohoapis.com',
    accounts: 'https://accounts.zoho.com'
  },
  EU: {
    api: 'https://www.zohoapis.eu',
    accounts: 'https://accounts.zoho.eu'
  },
  IN: {
    api: 'https://www.zohoapis.in',
    accounts: 'https://accounts.zoho.in'
  },
  AU: {
    api: 'https://www.zohoapis.com.au',
    accounts: 'https://accounts.zoho.com.au'
  },
  CN: {
    api: 'https://www.zohoapis.com.cn',
    accounts: 'https://accounts.zoho.com.cn'
  }
};

function getApiEndpoint(region: string): string {
  return ZOHO_REGIONS[region]?.api || ZOHO_REGIONS.US.api;
}
```

---

## 5. Rate Limiting and Quota Management

### 5.1 Zoho API Limits

**Tier-Based Limits:**
| Edition | API Calls/Day | Concurrent Connections |
|---------|---------------|------------------------|
| Free | 200 | 1 |
| Standard | 5,000 | 5 |
| Professional | 10,000 | 10 |
| Enterprise | 25,000 | 15 |
| Ultimate | 100,000 | 20 |

**Rate Limit Headers:**
- `X-RATELIMIT-LIMIT`: Total daily quota
- `X-RATELIMIT-REMAINING`: Remaining calls
- `X-RATELIMIT-RESET`: Reset time (Unix timestamp)

### 5.2 Client-Side Rate Limiting

**Token Bucket Algorithm:**
```typescript
class RateLimiter {
  private tokens: number;
  private lastRefill: Date;
  private capacity: number;
  private refillRate: number; // tokens per second

  constructor(dailyLimit: number) {
    this.capacity = dailyLimit;
    this.refillRate = dailyLimit / 86400; // spread across 24 hours
    this.tokens = this.capacity;
    this.lastRefill = new Date();
  }

  async acquire(cost: number = 1): Promise<void> {
    await this.refillTokens();

    if (this.tokens < cost) {
      const waitTime = (cost - this.tokens) / this.refillRate * 1000;
      await this.sleep(waitTime);
      await this.refillTokens();
    }

    this.tokens -= cost;
  }

  private async refillTokens(): Promise<void> {
    const now = new Date();
    const elapsed = (now.getTime() - this.lastRefill.getTime()) / 1000;
    const newTokens = elapsed * this.refillRate;
    this.tokens = Math.min(this.capacity, this.tokens + newTokens);
    this.lastRefill = now;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

**Rate Limit Groups:**
```typescript
const RATE_LIMIT_COSTS = {
  'read-single': 1,      // GET /Accounts/{id}
  'read-list': 2,        // GET /Accounts (paginated)
  'write-single': 3,     // POST/PUT /Accounts/{id}
  'write-bulk': 10,      // Bulk write operations
  'search': 2,           // Search API
  'coql': 5,             // COQL queries
  'metadata': 1          // Module/field metadata
};
```

### 5.3 Adaptive Throttling

**Response to Rate Limit Signals:**
```typescript
async function executeWithThrottling<T>(
  fn: () => Promise<Response>,
  context: { tool: string; agent: string }
): Promise<T> {
  const response = await fn();

  // Monitor rate limit headers
  const remaining = parseInt(response.headers.get('X-RATELIMIT-REMAINING') || '0');
  const limit = parseInt(response.headers.get('X-RATELIMIT-LIMIT') || '1000');
  const utilization = 1 - (remaining / limit);

  if (utilization > 0.9) {
    // Critical: < 10% quota remaining
    metrics.gauge('zoho.rate_limit.critical', 1);
    await throttle.setMode('conservative'); // Increase delays
    await notifyOps('Rate limit critical', { remaining, limit });
  } else if (utilization > 0.75) {
    // Warning: < 25% quota remaining
    metrics.gauge('zoho.rate_limit.warning', 1);
    await throttle.setMode('moderate');
  }

  if (response.status === 429) {
    // Rate limit exceeded
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    metrics.increment('zoho.rate_limit.exceeded');
    throw new RateLimitError(`Rate limit exceeded, retry after ${retryAfter}s`);
  }

  return response.json();
}
```

### 5.4 Request Queuing and Prioritization

**Priority Queue Implementation:**
```typescript
enum Priority {
  CRITICAL = 0,   // Real-time agent interactions
  HIGH = 1,       // User-initiated actions
  MEDIUM = 2,     // Background sync
  LOW = 3         // Batch analytics
}

interface QueuedRequest {
  id: string;
  priority: Priority;
  tool: string;
  params: any;
  agent: string;
  timestamp: Date;
  resolve: (value: any) => void;
  reject: (error: Error) => void;
}

class RequestQueue {
  private queues: Map<Priority, QueuedRequest[]> = new Map();
  private processing: boolean = false;

  async enqueue<T>(request: Omit<QueuedRequest, 'resolve' | 'reject'>): Promise<T> {
    return new Promise((resolve, reject) => {
      const queuedRequest = { ...request, resolve, reject };

      if (!this.queues.has(request.priority)) {
        this.queues.set(request.priority, []);
      }

      this.queues.get(request.priority)!.push(queuedRequest);
      this.processQueue();
    });
  }

  private async processQueue(): Promise<void> {
    if (this.processing) return;
    this.processing = true;

    while (this.hasRequests()) {
      const request = this.dequeue();
      if (!request) break;

      try {
        await rateLimiter.acquire(RATE_LIMIT_COSTS[request.tool] || 1);
        const result = await this.executeRequest(request);
        request.resolve(result);
      } catch (error) {
        request.reject(error as Error);
      }
    }

    this.processing = false;
  }

  private dequeue(): QueuedRequest | undefined {
    // Dequeue by priority (0 = highest)
    for (let p = Priority.CRITICAL; p <= Priority.LOW; p++) {
      const queue = this.queues.get(p);
      if (queue && queue.length > 0) {
        return queue.shift();
      }
    }
    return undefined;
  }
}
```

---

## 6. Error Handling and Retry Patterns

### 6.1 Error Classification

**Error Categories:**
```typescript
enum ErrorCategory {
  TRANSIENT,      // Network issues, timeouts (retry)
  RATE_LIMIT,     // 429 responses (backoff + retry)
  AUTH,           // 401/403 (refresh token + retry)
  CLIENT,         // 400/422 (no retry, log + alert)
  SERVER,         // 500/503 (exponential backoff + retry)
  NOT_FOUND,      // 404 (no retry, handle gracefully)
  FORBIDDEN       // 403 scope issues (no retry, alert)
}

function classifyError(response: Response): ErrorCategory {
  switch (response.status) {
    case 401: return ErrorCategory.AUTH;
    case 403: return ErrorCategory.FORBIDDEN;
    case 404: return ErrorCategory.NOT_FOUND;
    case 422: return ErrorCategory.CLIENT;
    case 429: return ErrorCategory.RATE_LIMIT;
    case 500:
    case 502:
    case 503:
    case 504: return ErrorCategory.SERVER;
    default:
      return response.status >= 400 && response.status < 500
        ? ErrorCategory.CLIENT
        : ErrorCategory.TRANSIENT;
  }
}
```

### 6.2 Exponential Backoff with Jitter

**Retry Strategy:**
```typescript
interface RetryConfig {
  maxAttempts: number;
  initialDelay: number; // milliseconds
  maxDelay: number;
  backoffMultiplier: number;
  jitterFactor: number; // 0.0 - 1.0
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  jitterFactor: 0.2
};

async function executeWithRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < config.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      const category = classifyError(error);
      if (!shouldRetry(category, attempt)) {
        throw error;
      }

      const delay = calculateBackoff(attempt, config);
      metrics.increment('zoho.retry', { attempt, category });
      await sleep(delay);
    }
  }

  throw new MaxRetriesError(`Failed after ${config.maxAttempts} attempts`, lastError);
}

function calculateBackoff(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.initialDelay * Math.pow(config.backoffMultiplier, attempt);
  const cappedDelay = Math.min(exponentialDelay, config.maxDelay);
  const jitter = cappedDelay * config.jitterFactor * Math.random();
  return cappedDelay + jitter;
}

function shouldRetry(category: ErrorCategory, attempt: number): boolean {
  switch (category) {
    case ErrorCategory.TRANSIENT:
    case ErrorCategory.RATE_LIMIT:
    case ErrorCategory.SERVER:
      return true;
    case ErrorCategory.AUTH:
      return attempt === 0; // Retry once after token refresh
    default:
      return false;
  }
}
```

### 6.3 Circuit Breaker Pattern

**Circuit Breaker Implementation:**
```typescript
enum CircuitState {
  CLOSED,      // Normal operation
  OPEN,        // Failures exceed threshold, reject requests
  HALF_OPEN    // Test if service recovered
}

class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private successCount: number = 0;
  private lastFailureTime: Date | null = null;

  private readonly failureThreshold = 5;
  private readonly successThreshold = 2;
  private readonly timeout = 60000; // 1 minute

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new CircuitBreakerOpenError('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.successCount = 0;
        metrics.increment('zoho.circuit_breaker.closed');
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = new Date();
    this.successCount = 0;

    if (this.failureCount >= this.failureThreshold) {
      this.state = CircuitState.OPEN;
      metrics.increment('zoho.circuit_breaker.opened');
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailureTime) return false;
    const elapsed = Date.now() - this.lastFailureTime.getTime();
    return elapsed >= this.timeout;
  }
}
```

---

## 7. Fallback Mechanisms

### 7.1 Three-Tier Fallback Strategy

**Fallback Hierarchy:**
```
1. Primary: Zoho MCP endpoint
   ↓ (on failure)
2. Secondary: Direct REST API
   ↓ (on failure)
3. Tertiary: Cached data / graceful degradation
```

**Implementation:**
```typescript
class ZohoIntegrationOrchestrator {
  async executeTool<T>(
    toolName: string,
    params: any,
    context: ExecutionContext
  ): Promise<T> {
    // Attempt 1: MCP endpoint
    try {
      return await circuitBreaker.execute(() =>
        this.mcpClient.callTool(toolName, params)
      );
    } catch (mcpError) {
      metrics.increment('zoho.fallback.mcp_failed', { tool: toolName });

      // Attempt 2: REST API
      try {
        return await this.restFallback.execute(toolName, params);
      } catch (restError) {
        metrics.increment('zoho.fallback.rest_failed', { tool: toolName });

        // Attempt 3: Cache or graceful degradation
        return await this.cacheFallback.execute(toolName, params, context);
      }
    }
  }
}

class CacheFallback {
  async execute<T>(
    toolName: string,
    params: any,
    context: ExecutionContext
  ): Promise<T> {
    // Try to serve from cache
    const cacheKey = this.generateCacheKey(toolName, params);
    const cached = await cache.get<T>(cacheKey);

    if (cached && !this.isStale(cached)) {
      metrics.increment('zoho.fallback.cache_hit', { tool: toolName });
      return this.attachStalenessWarning(cached);
    }

    // No cache available - graceful degradation
    if (this.canDegrade(toolName)) {
      return this.degradeGracefully(toolName, params, context);
    }

    // Cannot serve request
    throw new ServiceUnavailableError(
      'Zoho CRM is temporarily unavailable and no cached data exists'
    );
  }

  private canDegrade(toolName: string): boolean {
    // Read operations can degrade to partial data
    // Write operations must fail-fast
    const readOnlyTools = ['get_account', 'list_accounts', 'get_notes', 'search_records'];
    return readOnlyTools.includes(toolName);
  }

  private degradeGracefully<T>(
    toolName: string,
    params: any,
    context: ExecutionContext
  ): T {
    // Return partial data with clear indicators
    return {
      data: null,
      metadata: {
        source: 'degraded',
        message: 'Zoho CRM is temporarily unavailable. This response may be incomplete.',
        timestamp: new Date(),
        suggestion: 'Retry in a few minutes or contact support if issue persists.'
      }
    } as T;
  }
}
```

### 7.2 Webhook Integration for Change Notifications

**Webhook Configuration:**
```typescript
// Register webhook with Zoho
async function setupWebhooks() {
  const webhookConfig = {
    url: 'https://agents.sergas.com/api/webhooks/zoho',
    modules: ['Accounts', 'Contacts', 'Deals', 'Notes', 'Tasks'],
    events: ['create', 'update', 'delete'],
    auth: {
      type: 'bearer',
      token: await secrets.get('WEBHOOK_AUTH_TOKEN')
    }
  };

  await zohoClient.post('/crm/v6/actions/watch', webhookConfig);
}

// Webhook handler
async function handleZohoWebhook(payload: WebhookPayload) {
  const { module, event, record } = payload;

  // Invalidate cache
  await cache.invalidate(`zoho:${module}:${record.id}`);

  // Update Cognee memory
  await cogneeClient.ingest({
    source: 'zoho_webhook',
    module,
    event,
    data: record,
    timestamp: new Date()
  });

  // Trigger dependent workflows
  if (event === 'update' && module === 'Accounts') {
    await eventBus.publish('account.updated', record);
  }

  metrics.increment('zoho.webhook.received', { module, event });
}
```

---

## 8. Observability and Monitoring

### 8.1 Metrics Collection

**Key Metrics:**
```typescript
// Request metrics
metrics.histogram('zoho.request.duration', durationMs, {
  tool: toolName,
  status: response.status,
  agent: context.agentId
});

metrics.increment('zoho.request.count', {
  tool: toolName,
  method: request.method,
  result: 'success' | 'error'
});

// Rate limiting metrics
metrics.gauge('zoho.rate_limit.remaining', remaining);
metrics.gauge('zoho.rate_limit.utilization', utilization);

// Error metrics
metrics.increment('zoho.error', {
  category: errorCategory,
  tool: toolName,
  status: response.status
});

// Circuit breaker metrics
metrics.gauge('zoho.circuit_breaker.state', {
  state: circuitState
});

// Cache metrics
metrics.increment('zoho.cache.hit' | 'zoho.cache.miss', {
  tool: toolName
});
```

### 8.2 Structured Logging

**Log Schema:**
```typescript
interface ZohoRequestLog {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  event: 'request' | 'response' | 'error' | 'fallback';
  tool: string;
  agent: string;
  request: {
    id: string;
    method: string;
    params: any; // sanitized
  };
  response?: {
    status: number;
    duration: number;
    rateLimitRemaining: number;
  };
  error?: {
    message: string;
    category: ErrorCategory;
    stack?: string;
  };
  fallback?: {
    attempted: 'rest' | 'cache';
    success: boolean;
  };
}

// Example log entry
logger.info({
  timestamp: '2025-10-18T21:00:00Z',
  event: 'request',
  tool: 'get_account',
  agent: 'research-agent-01',
  request: {
    id: 'req-abc123',
    method: 'GET',
    params: { accountId: '1234567890' }
  },
  response: {
    status: 200,
    duration: 342,
    rateLimitRemaining: 8234
  }
});
```

### 8.3 Distributed Tracing

**OpenTelemetry Integration:**
```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

async function executeToolWithTracing<T>(
  toolName: string,
  params: any
): Promise<T> {
  const tracer = trace.getTracer('zoho-integration');

  return tracer.startActiveSpan(`zoho.${toolName}`, async (span) => {
    span.setAttribute('tool.name', toolName);
    span.setAttribute('tool.params', JSON.stringify(params));

    try {
      const result = await executeTool(toolName, params);
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: (error as Error).message
      });
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

---

## 9. Security Considerations

### 9.1 Least Privilege Scopes

**Scope Mapping by Agent Type:**
```typescript
const AGENT_SCOPES = {
  'research-agent': [
    'ZohoCRM.modules.accounts.READ',
    'ZohoCRM.modules.contacts.READ',
    'ZohoCRM.modules.deals.READ',
    'ZohoCRM.modules.notes.READ',
    'ZohoCRM.modules.activities.READ'
  ],
  'account-manager-agent': [
    'ZohoCRM.modules.accounts.ALL',
    'ZohoCRM.modules.contacts.ALL',
    'ZohoCRM.modules.deals.ALL',
    'ZohoCRM.modules.notes.ALL',
    'ZohoCRM.modules.activities.ALL'
  ],
  'recommendation-agent': [
    'ZohoCRM.modules.accounts.READ',
    'ZohoCRM.modules.notes.CREATE',
    'ZohoCRM.modules.activities.CREATE'
  ]
};
```

### 9.2 Request Sanitization

**Input Validation:**
```typescript
function sanitizeParams(params: any, schema: JSONSchema): any {
  // Remove unexpected fields
  const allowedFields = Object.keys(schema.properties || {});
  const sanitized = {};

  for (const key of allowedFields) {
    if (key in params) {
      sanitized[key] = sanitizeValue(params[key], schema.properties[key]);
    }
  }

  return sanitized;
}

function sanitizeValue(value: any, schema: any): any {
  // Prevent injection attacks
  if (typeof value === 'string') {
    return value
      .replace(/<script>/gi, '')
      .replace(/javascript:/gi, '')
      .slice(0, 10000); // Limit length
  }
  return value;
}
```

### 9.3 Audit Logging

**Audit Trail:**
```typescript
interface AuditLog {
  timestamp: Date;
  agent: string;
  user?: string;
  action: string;
  resource: string;
  params: any;
  result: 'success' | 'failure';
  ipAddress?: string;
}

async function auditToolExecution(
  tool: string,
  params: any,
  context: ExecutionContext,
  result: any
) {
  await auditStore.write({
    timestamp: new Date(),
    agent: context.agentId,
    user: context.userId,
    action: tool,
    resource: `zoho:${params.module}:${params.id}`,
    params: sanitizeForAudit(params),
    result: result.success ? 'success' : 'failure',
    ipAddress: context.ipAddress
  });
}
```

---

## 10. Testing Strategy

### 10.1 Test Environments

**Environment Configuration:**
```typescript
const ENVIRONMENTS = {
  development: {
    mcpEndpoint: 'http://localhost:3000/mcp',
    zohoApiBase: 'https://sandbox.zohoapis.com',
    region: 'US'
  },
  staging: {
    mcpEndpoint: 'https://staging-mcp.sergas.com',
    zohoApiBase: 'https://sandbox.zohoapis.com',
    region: 'US'
  },
  production: {
    mcpEndpoint: 'npx mcp-remote https://zoho-mcp2-900114980...',
    zohoApiBase: 'https://www.zohoapis.com',
    region: 'US'
  }
};
```

### 10.2 Integration Tests

**Test Scenarios:**
```typescript
describe('Zoho MCP Integration', () => {
  it('should retrieve account via MCP', async () => {
    const account = await mcpClient.callTool('get_account', {
      accountId: TEST_ACCOUNT_ID
    });
    expect(account).toHaveProperty('Account_Name');
  });

  it('should fallback to REST API on MCP failure', async () => {
    // Simulate MCP failure
    mockMcpClient.callTool.mockRejectedValue(new Error('MCP unavailable'));

    const account = await orchestrator.executeTool('get_account', {
      accountId: TEST_ACCOUNT_ID
    });

    expect(account).toBeDefined();
    expect(metrics.fallbackAttempted).toBe(true);
  });

  it('should respect rate limits', async () => {
    const requests = Array(100).fill(null).map(() =>
      orchestrator.executeTool('get_account', { accountId: TEST_ACCOUNT_ID })
    );

    await expect(Promise.all(requests)).resolves.not.toThrow();
    expect(rateLimiter.throttled).toBe(true);
  });

  it('should refresh token proactively', async () => {
    // Set token to expire in 4 minutes
    tokenManager.setExpiry(Date.now() + 240000);

    await orchestrator.executeTool('get_account', { accountId: TEST_ACCOUNT_ID });

    expect(tokenManager.refreshCalled).toBe(true);
  });
});
```

---

## 11. Deployment Architecture

### 11.1 Infrastructure Components

```
┌────────────────────────────────────────────────────┐
│              Load Balancer (ALB)                    │
└────────────────────┬───────────────────────────────┘
                     │
     ┌───────────────┴──────────────┐
     │                               │
┌────▼─────┐                  ┌─────▼────┐
│  Agent   │                  │  Agent   │
│  Host 1  │                  │  Host 2  │
│          │                  │          │
│  ┌────┐  │                  │  ┌────┐  │
│  │MCP │  │                  │  │MCP │  │
│  │Orch│  │                  │  │Orch│  │
│  └────┘  │                  │  └────┘  │
└────┬─────┘                  └─────┬────┘
     │                               │
     └───────────────┬───────────────┘
                     │
        ┌────────────▼────────────┐
        │   Redis (Token Cache)   │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   Secrets Manager       │
        │   (OAuth Credentials)   │
        └─────────────────────────┘
```

### 11.2 Scaling Considerations

**Horizontal Scaling:**
- Stateless MCP orchestrator instances
- Shared token cache via Redis
- Connection pooling for Zoho API

**Vertical Scaling:**
- Increase rate limit capacity with Zoho tier upgrades
- Monitor CPU/memory for orchestrator processes

---

## 12. Runbook and Operations

### 12.1 Common Issues and Resolutions

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| Token refresh failure | 401 errors on all requests | 1. Verify refresh token in vault<br>2. Check OAuth scopes<br>3. Re-authorize if token revoked |
| Rate limit exceeded | 429 errors | 1. Check utilization dashboard<br>2. Throttle non-critical agents<br>3. Upgrade Zoho tier if sustained |
| MCP endpoint timeout | Requests hanging > 30s | 1. Check endpoint health<br>2. Activate REST fallback<br>3. Contact Zoho support |
| Circuit breaker OPEN | All requests rejected | 1. Check Zoho status page<br>2. Wait for auto-recovery<br>3. Manually reset if resolved |

### 12.2 Health Check Endpoints

**Orchestrator Health:**
```typescript
app.get('/health', async (req, res) => {
  const checks = {
    mcp: await checkMcpHealth(),
    restApi: await checkRestApiHealth(),
    cache: await checkCacheHealth(),
    secrets: await checkSecretsHealth()
  };

  const healthy = Object.values(checks).every(c => c.status === 'ok');

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'degraded',
    checks,
    timestamp: new Date()
  });
});

async function checkMcpHealth(): Promise<HealthCheck> {
  try {
    await mcpClient.callTool('get_user_info', {});
    return { status: 'ok', latency: performance.now() };
  } catch (error) {
    return { status: 'error', message: (error as Error).message };
  }
}
```

---

## 13. Future Enhancements

1. **GraphQL Gateway**: Unified query interface across Zoho and other data sources
2. **Smart Caching**: ML-powered cache invalidation based on usage patterns
3. **Predictive Rate Limiting**: Forecast quota usage and optimize request scheduling
4. **Multi-Tenant Support**: Isolate API quotas and credentials per customer
5. **Advanced Analytics**: Real-time dashboards for API usage, errors, and performance

---

## 14. References

- Zoho CRM API v6 Documentation: https://www.zoho.com/crm/developer/docs/api/v6/
- Zoho OAuth 2.0 Guide: https://www.zoho.com/crm/developer/docs/api/v6/oauth-overview.html
- MCP Specification: https://modelcontextprotocol.io/
- Claude Agent SDK: https://github.com/anthropics/claude-agent-sdk

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Author**: System Architecture Designer
**Status**: Final
