# API Documentation

## Overview

The Sergas Super Account Manager provides a RESTful API for account management, analysis, and recommendations. All endpoints require authentication unless otherwise specified.

## Base URL

```
Production: https://api.sergas.com/v1
Staging:    https://staging-api.sergas.com/v1
Local:      http://localhost:8000/v1
```

## Authentication

### OAuth 2.0 Flow

```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=user@example.com&password=secret
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here"
}
```

### Using Access Token

Include the access token in the Authorization header:

```http
GET /accounts/ACC-123
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## Endpoints

### Health & Status

#### GET /health

Check API health status.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-10-19T10:00:00Z",
  "database": "connected",
  "redis": "connected",
  "zoho": "authenticated",
  "cognee": "connected"
}
```

**Status Codes:**
- `200` - Service healthy
- `503` - Service degraded or unavailable

---

### Accounts

#### POST /accounts/{account_id}/analyze

Trigger analysis for an account.

**Authentication:** Required
**Permissions:** `account:read`, `agent:execute`

**Path Parameters:**
- `account_id` (string, required) - Zoho CRM account ID

**Request Body:**
```json
{
  "priority": "high",
  "include_historical": true,
  "notification_email": "manager@example.com"
}
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "account_id": "ACC-123",
  "status": "in_progress",
  "started_at": "2024-10-19T10:00:00Z",
  "estimated_completion": "2024-10-19T10:00:30Z",
  "progress_url": "/sessions/sess_abc123"
}
```

**Status Codes:**
- `202` - Analysis started
- `400` - Invalid request
- `404` - Account not found
- `429` - Rate limit exceeded
- `503` - Service unavailable

**Example:**
```bash
curl -X POST https://api.sergas.com/v1/accounts/ACC-123/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"priority": "high", "include_historical": true}'
```

---

#### GET /accounts/{account_id}

Get account details.

**Authentication:** Required
**Permissions:** `account:read`

**Path Parameters:**
- `account_id` (string, required) - Account ID

**Query Parameters:**
- `include_activities` (boolean, optional) - Include recent activities (default: false)
- `include_recommendations` (boolean, optional) - Include active recommendations (default: false)

**Response:**
```json
{
  "id": "ACC-123",
  "name": "Acme Corporation",
  "status": "active",
  "owner": {
    "id": "USR-456",
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  "created_at": "2023-01-15T10:00:00Z",
  "updated_at": "2024-10-19T09:30:00Z",
  "last_activity": {
    "type": "email",
    "date": "2024-10-18T14:30:00Z",
    "description": "Follow-up email sent"
  },
  "health_score": 0.82,
  "risk_level": "low",
  "activities": [],
  "recommendations": []
}
```

**Status Codes:**
- `200` - Success
- `404` - Account not found
- `403` - Permission denied

---

#### GET /accounts

List accounts with filtering.

**Authentication:** Required
**Permissions:** `account:list`

**Query Parameters:**
- `owner_id` (string, optional) - Filter by owner
- `status` (string, optional) - Filter by status: `active`, `inactive`, `on_hold`
- `risk_level` (string, optional) - Filter by risk: `high`, `medium`, `low`
- `page` (integer, optional) - Page number (default: 1)
- `limit` (integer, optional) - Results per page (default: 20, max: 100)
- `sort` (string, optional) - Sort field: `name`, `updated_at`, `health_score`
- `order` (string, optional) - Sort order: `asc`, `desc`

**Response:**
```json
{
  "data": [
    {
      "id": "ACC-123",
      "name": "Acme Corporation",
      "status": "active",
      "owner_name": "Jane Smith",
      "health_score": 0.82,
      "risk_level": "low",
      "last_activity": "2024-10-18T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid query parameters

**Example:**
```bash
curl "https://api.sergas.com/v1/accounts?status=active&risk_level=high&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Recommendations

#### GET /recommendations/{recommendation_id}

Get recommendation details.

**Authentication:** Required
**Permissions:** `recommendation:read`

**Path Parameters:**
- `recommendation_id` (string, required) - Recommendation ID

**Response:**
```json
{
  "id": "rec_abc123",
  "account_id": "ACC-123",
  "account_name": "Acme Corporation",
  "type": "follow_up",
  "priority": "high",
  "confidence": 0.87,
  "status": "pending_approval",
  "action": "Schedule follow-up call",
  "rationale": "No contact in 14 days. Previous engagement pattern shows 7-day cycle.",
  "draft_content": "Hi Sarah, Following up on our last discussion...",
  "estimated_impact": "Reduces churn risk by 15%",
  "requires_approval": true,
  "created_at": "2024-10-19T10:00:30Z",
  "approved_by": null,
  "approved_at": null,
  "executed_at": null
}
```

**Status Codes:**
- `200` - Success
- `404` - Recommendation not found
- `403` - Permission denied

---

#### POST /recommendations/{recommendation_id}/approve

Approve a recommendation.

**Authentication:** Required
**Permissions:** `recommendation:approve`

**Path Parameters:**
- `recommendation_id` (string, required) - Recommendation ID

**Request Body:**
```json
{
  "approved": true,
  "notes": "Approved for execution",
  "modifications": {
    "draft_content": "Modified content..."
  }
}
```

**Response:**
```json
{
  "id": "rec_abc123",
  "status": "approved",
  "approved_by": "USR-456",
  "approved_at": "2024-10-19T10:15:00Z",
  "execution_scheduled": "2024-10-19T10:16:00Z"
}
```

**Status Codes:**
- `200` - Approved successfully
- `400` - Invalid request
- `404` - Recommendation not found
- `403` - Permission denied
- `409` - Already approved/rejected

---

#### POST /recommendations/{recommendation_id}/reject

Reject a recommendation.

**Authentication:** Required
**Permissions:** `recommendation:approve`

**Request Body:**
```json
{
  "reason": "Not appropriate at this time",
  "feedback": "Account is in negotiation phase"
}
```

**Response:**
```json
{
  "id": "rec_abc123",
  "status": "rejected",
  "rejected_by": "USR-456",
  "rejected_at": "2024-10-19T10:15:00Z",
  "reason": "Not appropriate at this time"
}
```

---

#### GET /recommendations

List recommendations with filtering.

**Authentication:** Required
**Permissions:** `recommendation:list`

**Query Parameters:**
- `account_id` (string, optional) - Filter by account
- `status` (string, optional) - Filter by status: `pending`, `approved`, `rejected`, `executed`
- `priority` (string, optional) - Filter by priority: `high`, `medium`, `low`
- `type` (string, optional) - Filter by type: `follow_up`, `update_status`, `escalate`
- `page` (integer, optional) - Page number
- `limit` (integer, optional) - Results per page

**Response:**
```json
{
  "data": [
    {
      "id": "rec_abc123",
      "account_id": "ACC-123",
      "account_name": "Acme Corporation",
      "type": "follow_up",
      "priority": "high",
      "confidence": 0.87,
      "status": "pending_approval",
      "created_at": "2024-10-19T10:00:30Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

---

### Agent Sessions

#### GET /sessions/{session_id}

Get session status and progress.

**Authentication:** Required
**Permissions:** `session:read`

**Path Parameters:**
- `session_id` (string, required) - Session ID

**Response:**
```json
{
  "id": "sess_abc123",
  "account_id": "ACC-123",
  "status": "in_progress",
  "current_agent": "MemoryAnalyst",
  "progress": 0.65,
  "started_at": "2024-10-19T10:00:00Z",
  "estimated_completion": "2024-10-19T10:00:30Z",
  "steps": [
    {
      "agent": "ZohoDataScout",
      "status": "completed",
      "started_at": "2024-10-19T10:00:00Z",
      "completed_at": "2024-10-19T10:00:10Z",
      "duration_ms": 10000
    },
    {
      "agent": "MemoryAnalyst",
      "status": "in_progress",
      "started_at": "2024-10-19T10:00:10Z",
      "progress": 0.65
    }
  ],
  "error": null
}
```

**Status Codes:**
- `200` - Success
- `404` - Session not found

---

#### GET /sessions/{session_id}/stream

Stream session events via Server-Sent Events (SSE).

**Authentication:** Required
**Permissions:** `session:read`

**Path Parameters:**
- `session_id` (string, required) - Session ID

**Response (SSE Stream):**
```
event: agent_started
data: {"agent": "ZohoDataScout", "timestamp": "2024-10-19T10:00:00Z"}

event: agent_progress
data: {"agent": "ZohoDataScout", "progress": 0.5, "message": "Fetching activities..."}

event: agent_completed
data: {"agent": "ZohoDataScout", "duration_ms": 10000}

event: agent_started
data: {"agent": "MemoryAnalyst", "timestamp": "2024-10-19T10:00:10Z"}

event: recommendation_generated
data: {"type": "follow_up", "confidence": 0.87, "priority": "high"}

event: session_completed
data: {"session_id": "sess_abc123", "total_duration_ms": 30000}
```

**Event Types:**
- `agent_started` - Agent began execution
- `agent_progress` - Progress update
- `agent_completed` - Agent finished successfully
- `agent_failed` - Agent encountered error
- `recommendation_generated` - New recommendation created
- `approval_required` - Waiting for approval
- `session_completed` - Session finished
- `session_failed` - Session encountered error

**Example:**
```javascript
const eventSource = new EventSource(
  'https://api.sergas.com/v1/sessions/sess_abc123/stream',
  {headers: {Authorization: `Bearer ${token}`}}
);

eventSource.addEventListener('agent_progress', (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.agent}: ${data.progress * 100}%`);
});

eventSource.addEventListener('session_completed', (event) => {
  eventSource.close();
  console.log('Analysis complete');
});
```

---

### Webhooks

#### POST /webhooks/zoho

Receive Zoho CRM webhook events.

**Authentication:** HMAC signature verification
**Headers:**
- `X-Zoho-Signature` - HMAC-SHA256 signature

**Request Body:**
```json
{
  "event": "account.updated",
  "account_id": "ACC-123",
  "timestamp": "2024-10-19T10:00:00Z",
  "changes": {
    "status": {
      "old": "active",
      "new": "on_hold"
    }
  },
  "changed_by": "USR-456"
}
```

**Response:**
```json
{
  "received": true,
  "event_id": "evt_abc123",
  "processed": false,
  "queued_at": "2024-10-19T10:00:01Z"
}
```

**Status Codes:**
- `200` - Webhook received
- `400` - Invalid payload
- `401` - Invalid signature
- `409` - Duplicate event (already processed)

---

### Users

#### POST /users

Create a new user.

**Authentication:** Required
**Permissions:** `user:create`

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "account_executive",
  "permissions": ["account:read", "account:analyze", "recommendation:approve"]
}
```

**Response:**
```json
{
  "id": "USR-789",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "account_executive",
  "status": "active",
  "created_at": "2024-10-19T10:00:00Z"
}
```

**Status Codes:**
- `201` - User created
- `400` - Invalid request
- `409` - Email already exists
- `403` - Permission denied

---

## Error Responses

### Error Format

All errors follow this format:

```json
{
  "error": {
    "code": "ACCOUNT_NOT_FOUND",
    "message": "Account with ID ACC-999 not found",
    "details": {
      "account_id": "ACC-999"
    },
    "request_id": "req_abc123",
    "timestamp": "2024-10-19T10:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `ACCOUNT_NOT_FOUND` | 404 | Account not found in Zoho CRM |
| `ZOHO_API_ERROR` | 502 | Zoho API error |
| `SESSION_EXPIRED` | 401 | Session expired |
| `APPROVAL_REQUIRED` | 403 | Action requires approval |
| `INVALID_SIGNATURE` | 401 | Invalid webhook signature |

---

## Rate Limiting

### Limits

- **Default**: 60 requests per minute per IP
- **Authenticated**: 120 requests per minute per user
- **Burst**: Up to 20 requests allowed in burst

### Headers

Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697720400
```

### Exceeded Limit

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
}
```

---

## Pagination

### Query Parameters

- `page` - Page number (starts at 1)
- `limit` - Results per page (max 100)

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": true,
    "next_page": 3,
    "prev_page": 1
  }
}
```

---

## Filtering & Sorting

### Filter Syntax

```
GET /accounts?status=active&risk_level=high
```

### Sort Syntax

```
GET /accounts?sort=name&order=asc
GET /accounts?sort=updated_at&order=desc
```

### Advanced Filtering

```
GET /accounts?owner_id=USR-456&status=active,on_hold&health_score_min=0.7
```

---

## Versioning

The API uses URL-based versioning:

```
https://api.sergas.com/v1/accounts
https://api.sergas.com/v2/accounts  (future)
```

### Deprecation

Deprecated endpoints include a header:

```http
Deprecation: true
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Link: <https://docs.sergas.com/migration/v2>; rel="sunset"
```

---

## SDK Examples

### Python

```python
from sergas_sdk import SergasClient

client = SergasClient(
    api_key="your_api_key",
    base_url="https://api.sergas.com/v1"
)

# Analyze account
session = client.accounts.analyze("ACC-123", priority="high")
print(f"Session ID: {session.id}")

# Stream progress
for event in client.sessions.stream(session.id):
    if event.type == "agent_progress":
        print(f"{event.agent}: {event.progress * 100}%")

# Get recommendations
recommendations = client.recommendations.list(
    account_id="ACC-123",
    status="pending"
)

# Approve recommendation
client.recommendations.approve(
    recommendations[0].id,
    notes="Approved for execution"
)
```

### JavaScript

```javascript
import { SergasClient } from '@sergas/sdk';

const client = new SergasClient({
  apiKey: 'your_api_key',
  baseURL: 'https://api.sergas.com/v1'
});

// Analyze account
const session = await client.accounts.analyze('ACC-123', {
  priority: 'high'
});

// Stream progress
const stream = client.sessions.stream(session.id);
stream.on('agent_progress', (event) => {
  console.log(`${event.agent}: ${event.progress * 100}%`);
});

// Get recommendations
const recommendations = await client.recommendations.list({
  accountId: 'ACC-123',
  status: 'pending'
});

// Approve recommendation
await client.recommendations.approve(recommendations[0].id, {
  notes: 'Approved for execution'
});
```

---

## OpenAPI Specification

Complete OpenAPI 3.0 specification available at:

```
GET /openapi.json
GET /openapi.yaml
```

Interactive documentation:

```
GET /docs     (Swagger UI)
GET /redoc    (ReDoc)
```

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**API Version**: v1
**Maintained by**: Sergas API Team
