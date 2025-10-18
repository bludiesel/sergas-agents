---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
license: MIT
---

# MCP Builder - Building High-Quality MCP Servers

Comprehensive guide for creating production-ready MCP servers that integrate external services with Claude and other LLMs through the Model Context Protocol.

## When to Use

- Building MCP integrations for external APIs (Zoho, Salesforce, etc.)
- Creating custom tool servers for specialized workflows
- Wrapping existing APIs for LLM consumption
- Enhancing existing MCP servers with new capabilities
- Developing enterprise MCP integrations
- Testing and validating MCP server implementations

## Four-Phase Development Process

### Phase 1: Deep Research & Planning

**Objective**: Thoroughly understand the target API and design agent-centric tools.

**Research Checklist**:
- [ ] Read complete API documentation
- [ ] Identify authentication mechanisms
- [ ] Map core API endpoints and data models
- [ ] Understand rate limits and constraints
- [ ] Review API best practices
- [ ] Identify common use cases and workflows
- [ ] Study existing integrations or SDKs

**Design Principles**:

**Agent-Centric Design**:
- Design tools for AI agents, not human developers
- Optimize for LLM token efficiency
- Provide clear, structured responses
- Include rich context in tool descriptions
- Make tools composable and chainable

**Tool Granularity**:
- Create focused, single-purpose tools
- Avoid overly complex multi-step tools
- Enable tool chaining for complex workflows
- Provide both high-level and low-level tools

**Error Handling**:
- Return structured error messages
- Include actionable error guidance
- Provide fallback options
- Log errors for debugging

**Planning Outputs**:
1. **Tool Inventory**: List of tools to implement
2. **Data Models**: Core entities and their relationships
3. **Authentication Flow**: How auth will be handled
4. **Error Scenarios**: Common failures and handling
5. **Integration Points**: How tools compose together

### Phase 2: Implementation with Best Practices

**Objective**: Build robust, well-structured MCP server code.

#### Python (FastMCP) Implementation

**Basic Server Structure**:
```python
from fastmcp import FastMCP
from typing import Optional, List
import httpx

# Initialize MCP server
mcp = FastMCP("service-name")

# Configuration
class Config:
    API_BASE_URL = "https://api.service.com"
    API_VERSION = "v1"
    TIMEOUT = 30

# Authentication
class AuthManager:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None

    async def get_access_token(self) -> str:
        """Get or refresh access token"""
        if self.access_token:
            return self.access_token

        # Token acquisition logic
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.API_BASE_URL}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                }
            )
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token

# API Client
class APIClient:
    def __init__(self, auth: AuthManager):
        self.auth = auth
        self.client = httpx.AsyncClient(
            base_url=Config.API_BASE_URL,
            timeout=Config.TIMEOUT
        )

    async def get_headers(self) -> dict:
        token = await self.auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def get(self, endpoint: str, params: dict = None):
        headers = await self.get_headers()
        response = await self.client.get(
            endpoint,
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: dict):
        headers = await self.get_headers()
        response = await self.client.post(
            endpoint,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

# Initialize client
auth = AuthManager(api_key="key", api_secret="secret")
client = APIClient(auth)

# Tool definitions
@mcp.tool()
async def search_records(
    module: str,
    query: str,
    fields: Optional[List[str]] = None,
    limit: int = 10
) -> dict:
    """
    Search for records in specified module.

    Args:
        module: Module to search (Accounts, Contacts, Deals)
        query: Search query string
        fields: Optional list of fields to return
        limit: Maximum number of results (default 10, max 200)

    Returns:
        Dictionary with search results and metadata
    """
    try:
        params = {
            "criteria": query,
            "fields": ",".join(fields) if fields else None,
            "per_page": min(limit, 200)
        }

        result = await client.get(f"/crm/{module}/search", params=params)

        return {
            "success": True,
            "module": module,
            "count": len(result.get("data", [])),
            "records": result.get("data", []),
            "has_more": result.get("info", {}).get("more_records", False)
        }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}",
            "message": str(e),
            "suggestion": "Check query syntax and module name"
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "message": str(e)
        }

@mcp.tool()
async def get_record(
    module: str,
    record_id: str,
    fields: Optional[List[str]] = None
) -> dict:
    """
    Get detailed information for a specific record.

    Args:
        module: Module name (Accounts, Contacts, Deals)
        record_id: Unique identifier for the record
        fields: Optional list of specific fields to retrieve

    Returns:
        Dictionary with record details
    """
    try:
        params = {"fields": ",".join(fields)} if fields else {}
        result = await client.get(f"/crm/{module}/{record_id}", params=params)

        return {
            "success": True,
            "module": module,
            "record_id": record_id,
            "data": result.get("data", [{}])[0]
        }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}",
            "message": "Record not found" if e.response.status_code == 404 else str(e)
        }

# Resource providers
@mcp.resource("config://settings")
def get_settings():
    """MCP server configuration and settings"""
    return {
        "api_version": Config.API_VERSION,
        "base_url": Config.API_BASE_URL,
        "timeout": Config.TIMEOUT
    }

# Prompt templates
@mcp.prompt()
def analyze_account_template(account_data: dict):
    """Template for analyzing account health"""
    return f"""Analyze this account data and provide insights:

Account: {account_data.get('name')}
Industry: {account_data.get('industry')}
ARR: ${account_data.get('arr', 0):,.2f}
Last Activity: {account_data.get('last_activity_time')}

Provide:
1. Health score assessment
2. Risk factors
3. Growth opportunities
4. Recommended actions
"""

# Run server
if __name__ == "__main__":
    mcp.run()
```

#### TypeScript (MCP SDK) Implementation

**Basic Server Structure**:
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";

interface ServerConfig {
  apiBaseUrl: string;
  apiVersion: string;
  timeout: number;
}

const config: ServerConfig = {
  apiBaseUrl: "https://api.service.com",
  apiVersion: "v1",
  timeout: 30000,
};

class AuthManager {
  private accessToken: string | null = null;

  constructor(
    private apiKey: string,
    private apiSecret: string
  ) {}

  async getAccessToken(): Promise<string> {
    if (this.accessToken) {
      return this.accessToken;
    }

    const response = await fetch(`${config.apiBaseUrl}/oauth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grant_type: "client_credentials",
        client_id: this.apiKey,
        client_secret: this.apiSecret,
      }),
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    return this.accessToken;
  }
}

class APIClient {
  constructor(private auth: AuthManager) {}

  async getHeaders(): Promise<Record<string, string>> {
    const token = await this.auth.getAccessToken();
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  async get(endpoint: string, params?: Record<string, any>): Promise<any> {
    const headers = await this.getHeaders();
    const url = new URL(`${config.apiBaseUrl}${endpoint}`);

    if (params) {
      Object.keys(params).forEach(key =>
        params[key] && url.searchParams.append(key, params[key])
      );
    }

    const response = await fetch(url.toString(), { headers });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }
}

// Initialize
const auth = new AuthManager(
  process.env.API_KEY || "",
  process.env.API_SECRET || ""
);
const client = new APIClient(auth);

// Define tools
const tools: Tool[] = [
  {
    name: "search_records",
    description: "Search for records in specified module",
    inputSchema: {
      type: "object",
      properties: {
        module: {
          type: "string",
          description: "Module to search (Accounts, Contacts, Deals)",
        },
        query: {
          type: "string",
          description: "Search query string",
        },
        fields: {
          type: "array",
          items: { type: "string" },
          description: "Optional list of fields to return",
        },
        limit: {
          type: "number",
          description: "Maximum number of results (default 10, max 200)",
          default: 10,
        },
      },
      required: ["module", "query"],
    },
  },
  {
    name: "get_record",
    description: "Get detailed information for a specific record",
    inputSchema: {
      type: "object",
      properties: {
        module: {
          type: "string",
          description: "Module name (Accounts, Contacts, Deals)",
        },
        record_id: {
          type: "string",
          description: "Unique identifier for the record",
        },
        fields: {
          type: "array",
          items: { type: "string" },
          description: "Optional list of specific fields to retrieve",
        },
      },
      required: ["module", "record_id"],
    },
  },
];

// Create server
const server = new Server(
  {
    name: "service-name-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools,
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "search_records": {
        const { module, query, fields, limit = 10 } = args as any;
        const params = {
          criteria: query,
          fields: fields?.join(","),
          per_page: Math.min(limit, 200),
        };

        const result = await client.get(`/crm/${module}/search`, params);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                success: true,
                module,
                count: result.data?.length || 0,
                records: result.data || [],
                has_more: result.info?.more_records || false,
              }, null, 2),
            },
          ],
        };
      }

      case "get_record": {
        const { module, record_id, fields } = args as any;
        const params = fields ? { fields: fields.join(",") } : {};

        const result = await client.get(`/crm/${module}/${record_id}`, params);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                success: true,
                module,
                record_id,
                data: result.data?.[0] || {},
              }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            success: false,
            error: error.message,
            suggestion: "Check parameters and try again",
          }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main().catch(console.error);
```

### Phase 3: Review & Refinement

**Objective**: Ensure code quality, security, and usability.

**Code Review Checklist**:

**Functionality**:
- [ ] All tools work as documented
- [ ] Error handling covers edge cases
- [ ] Authentication works correctly
- [ ] Rate limiting is implemented
- [ ] Pagination works for large datasets

**Code Quality**:
- [ ] Code follows language conventions
- [ ] Functions have clear docstrings
- [ ] Type hints/types are comprehensive
- [ ] No hardcoded credentials
- [ ] Consistent naming conventions

**Security**:
- [ ] Credentials stored securely (env vars)
- [ ] API keys not exposed in logs
- [ ] Input validation prevents injection
- [ ] HTTPS used for all connections
- [ ] Token refresh implemented

**Usability**:
- [ ] Tool descriptions are clear
- [ ] Parameters have helpful descriptions
- [ ] Error messages are actionable
- [ ] Examples provided in documentation
- [ ] Installation instructions complete

**Performance**:
- [ ] Async/await used properly
- [ ] Connection pooling implemented
- [ ] Responses are efficiently structured
- [ ] Large payloads handled correctly
- [ ] Timeouts configured appropriately

### Phase 4: Evaluation & Testing

**Objective**: Create comprehensive evaluation harness and validate implementation.

**Evaluation Harness**:

Create 10+ test scenarios covering:
1. **Basic Operations**: Simple tool calls with valid inputs
2. **Error Handling**: Invalid inputs, missing parameters, API errors
3. **Authentication**: Token acquisition, refresh, expiration
4. **Edge Cases**: Empty results, large datasets, rate limits
5. **Integration**: Tool chaining, complex workflows
6. **Performance**: Response times, concurrent requests
7. **Security**: Credential handling, data validation
8. **Documentation**: Tool descriptions, parameter guidance
9. **Real-world Scenarios**: Actual use cases
10. **Failure Recovery**: Network errors, timeouts, retries

**Test Template**:
```python
# test_mcp_server.py
import pytest
import asyncio
from fastmcp.testing import MCPTestClient

@pytest.fixture
async def client():
    """Create test client"""
    from your_mcp_server import mcp
    async with MCPTestClient(mcp) as client:
        yield client

@pytest.mark.asyncio
async def test_search_records_success(client):
    """Test successful record search"""
    result = await client.call_tool(
        "search_records",
        module="Accounts",
        query="Annual_Revenue>100000",
        limit=5
    )

    assert result["success"] is True
    assert "records" in result
    assert len(result["records"]) <= 5

@pytest.mark.asyncio
async def test_search_records_invalid_module(client):
    """Test error handling for invalid module"""
    result = await client.call_tool(
        "search_records",
        module="InvalidModule",
        query="test"
    )

    assert result["success"] is False
    assert "error" in result
    assert "suggestion" in result

@pytest.mark.asyncio
async def test_get_record_not_found(client):
    """Test handling of non-existent record"""
    result = await client.call_tool(
        "get_record",
        module="Accounts",
        record_id="999999999999999"
    )

    assert result["success"] is False
    assert "not found" in result["message"].lower()

@pytest.mark.asyncio
async def test_authentication_token_refresh(client):
    """Test token refresh after expiration"""
    # Simulate token expiration
    # Make call that triggers refresh
    # Verify new token obtained
    pass

@pytest.mark.asyncio
async def test_rate_limit_handling(client):
    """Test graceful handling of rate limits"""
    # Make rapid successive calls
    # Verify rate limit handling
    pass
```

**Manual Testing Checklist**:
- [ ] Test with Claude Desktop or Claude Code
- [ ] Verify tool discovery works
- [ ] Test each tool individually
- [ ] Test tool chaining scenarios
- [ ] Verify error messages are helpful
- [ ] Check performance with real data
- [ ] Validate authentication flow
- [ ] Test with different configurations

## Best Practices

### Tool Design

✅ **Do**:
- Use clear, descriptive tool names
- Provide comprehensive parameter descriptions
- Return structured, consistent responses
- Include success/error indicators
- Add helpful suggestions in errors
- Use semantic versioning
- Document all tools thoroughly

❌ **Don't**:
- Create overly complex multi-step tools
- Return unstructured text responses
- Use technical jargon in descriptions
- Hardcode configuration values
- Ignore error scenarios
- Break backward compatibility
- Skip input validation

### Authentication

✅ **Do**:
- Store credentials in environment variables
- Implement token refresh logic
- Handle authentication errors gracefully
- Support multiple auth methods if needed
- Log authentication events (without exposing secrets)
- Use secure token storage
- Implement retry logic for auth failures

❌ **Don't**:
- Hardcode API keys or secrets
- Log access tokens
- Store tokens in plaintext files
- Expose credentials in error messages
- Skip token validation
- Ignore token expiration
- Use basic auth over HTTP

### Error Handling

✅ **Do**:
- Return structured error objects
- Include actionable error messages
- Provide suggestions for resolution
- Log errors for debugging
- Handle network timeouts
- Validate inputs before API calls
- Catch and handle all exceptions

❌ **Don't**:
- Let exceptions crash the server
- Return generic "error occurred" messages
- Expose internal error details
- Skip validation of inputs
- Ignore rate limit errors
- Return inconsistent error formats
- Log sensitive data in errors

### Performance

✅ **Do**:
- Use async/await for I/O operations
- Implement connection pooling
- Add request timeouts
- Cache frequently accessed data
- Paginate large result sets
- Batch similar requests when possible
- Monitor response times

❌ **Don't**:
- Use blocking synchronous calls
- Create new connections for each request
- Fetch entire datasets without pagination
- Skip timeout configurations
- Ignore memory usage
- Make redundant API calls
- Return massive JSON payloads

## Quality Checklists

### Pre-Release Checklist

**Code Quality**:
- [ ] All tools tested and working
- [ ] Error handling comprehensive
- [ ] Code follows best practices
- [ ] Type hints/types complete
- [ ] Docstrings for all functions
- [ ] No hardcoded values
- [ ] Logging implemented

**Documentation**:
- [ ] README with installation instructions
- [ ] Tool reference documentation
- [ ] Configuration guide
- [ ] Example usage scenarios
- [ ] Troubleshooting guide
- [ ] API changelog
- [ ] License file included

**Security**:
- [ ] No exposed credentials
- [ ] Input validation complete
- [ ] HTTPS enforced
- [ ] Rate limiting implemented
- [ ] Security scan passed
- [ ] Dependencies up to date
- [ ] Vulnerability scan passed

**Testing**:
- [ ] Unit tests written
- [ ] Integration tests passed
- [ ] Error scenarios tested
- [ ] Manual testing complete
- [ ] Performance tested
- [ ] Edge cases covered
- [ ] Test coverage >80%

**Deployment**:
- [ ] Package published
- [ ] Claude Desktop config documented
- [ ] Environment setup guide
- [ ] Version tagged
- [ ] Release notes published
- [ ] Example repository available
- [ ] Support channels defined

## Integration with SERGAS Project

### Enhancing Zoho CRM MCP Server

**Current State**: Basic Zoho CRM integration exists

**Enhancement Opportunities**:
1. Add account health analysis tools
2. Implement batch operations
3. Add relationship mapping tools
4. Create report generation tools
5. Add predictive analytics tools
6. Implement webhook handlers
7. Add bulk data import/export

**Example Enhancement**:
```python
@mcp.tool()
async def analyze_account_health(
    account_id: str,
    include_history: bool = True,
    timeframe_days: int = 90
) -> dict:
    """
    Analyze account health with comprehensive metrics.

    Args:
        account_id: Zoho CRM account ID
        include_history: Include historical health scores
        timeframe_days: Analysis timeframe in days

    Returns:
        Comprehensive health analysis with score, trends, and recommendations
    """
    # Implementation using existing Zoho client
    # Combine with Cognee memory for historical context
    # Return structured health analysis
    pass
```

## Common Patterns

### Pagination Pattern

```python
@mcp.tool()
async def list_records_paginated(
    module: str,
    page: int = 1,
    per_page: int = 20,
    filters: Optional[dict] = None
) -> dict:
    """List records with pagination support"""
    params = {
        "page": page,
        "per_page": min(per_page, 200),
        **(filters or {})
    }

    result = await client.get(f"/crm/{module}", params=params)

    return {
        "success": True,
        "page": page,
        "per_page": per_page,
        "total": result["info"]["count"],
        "has_next": result["info"]["more_records"],
        "records": result["data"]
    }
```

### Batch Operations Pattern

```python
@mcp.tool()
async def batch_update_records(
    module: str,
    updates: List[dict]
) -> dict:
    """Update multiple records in a single API call"""
    # Validate batch size
    if len(updates) > 100:
        return {
            "success": False,
            "error": "Batch size exceeds limit",
            "max_batch_size": 100
        }

    # Execute batch update
    result = await client.post(
        f"/crm/{module}/batch",
        data={"data": updates}
    )

    return {
        "success": True,
        "updated": len(result["data"]),
        "details": result["data"]
    }
```

### Resource Caching Pattern

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedResource:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str, ttl_seconds: int = 300):
        """Get cached value if not expired"""
        if key in self._cache:
            timestamp = self._timestamps[key]
            if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                return self._cache[key]
        return None

    def set(self, key: str, value: any):
        """Cache value with timestamp"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

cache = CachedResource()

@mcp.tool()
async def get_account_with_cache(account_id: str) -> dict:
    """Get account data with caching"""
    # Check cache first
    cached = cache.get(f"account_{account_id}", ttl_seconds=300)
    if cached:
        return {"success": True, "cached": True, "data": cached}

    # Fetch from API
    result = await client.get(f"/crm/Accounts/{account_id}")

    # Cache result
    cache.set(f"account_{account_id}", result["data"][0])

    return {"success": True, "cached": False, "data": result["data"][0]}
```

## Troubleshooting

**Tools not appearing in Claude**:
→ Check MCP server is configured in claude_desktop_config.json
→ Verify server starts without errors
→ Check tool schemas are valid
→ Restart Claude Desktop

**Authentication failures**:
→ Verify credentials in environment variables
→ Check token expiration and refresh logic
→ Validate API endpoint URLs
→ Review authentication logs

**Slow performance**:
→ Implement connection pooling
→ Add response caching
→ Use pagination for large datasets
→ Optimize API queries
→ Check network latency

**Inconsistent responses**:
→ Validate response structure consistency
→ Check error handling coverage
→ Review edge case handling
→ Add response validation

## Resources

- FastMCP Documentation: https://github.com/jlowin/fastmcp
- MCP SDK Documentation: https://github.com/modelcontextprotocol/sdk
- MCP Specification: https://modelcontextprotocol.io
- Claude MCP Guide: https://docs.anthropic.com/claude/docs/mcp
- Example Servers: https://github.com/modelcontextprotocol/servers

## Related Skills

- **skill-creator**: Meta-skill for creating new skills
- **zoho-crm-integration**: Existing Zoho integration to enhance
- **webapp-testing**: Testing MCP server functionality
- **cognee-memory-management**: Storing MCP server state and history
