# Zoho CRM Connectivity Options for Claude-Based Agents

## 1. Overview
Connecting Claude Agent SDK workflows to Zoho CRM can be achieved through several methods, each balancing control, velocity, and governance. This document compares available approaches, highlights authentication requirements, and recommends patterns for Sergas’ Super Account Manager system.

## 2. Authentication Primer
- **OAuth 2.0 (Server-based Applications)** is the primary method for Zoho CRM API access.
  - Register an app via Zoho Developer Console to obtain `client_id`, `client_secret`, and define redirect URIs.
  - Request scopes such as `ZohoCRM.modules.ALL`, `ZohoCRM.settings.ALL`, or narrower read/write subsets.
  - Exchange authorization code for `access_token` (1 hour) and `refresh_token` (long-lived); refresh tokens must be stored securely and rotated per policy.
- **Self Client flow** is available for testing but not recommended for production automation.
- **API limits**: baseline 200 calls/day (Free plan); higher with paid editions. Monitor `X-RATELIMIT-REMAINING` headers and implement backoff.

## 3. Option A – Direct REST / SDK Integration
### Description
- Call Zoho CRM REST APIs (v6/v7/v8) from custom code running inside Claude tools (e.g., via Python `requests`) or external services.
- Zoho provides official SDKs (Java, Python, Node.js, PHP, etc.) and OpenAPI specs for generating clients.

### Pros
- Fine-grained control over endpoints, caching, retries, and error handling.
- Flexible deployment (serverless functions, microservices, CLI tools).
- Easier to support advanced operations (Bulk Read/Write, Composite API, COQL queries, webhooks).

### Cons
- Requires manual orchestration of credentials, token refresh, and rate limiting.
- Claude Agent SDK tools cannot call external HTTP APIs directly without a custom MCP server or bespoke tool.
- More engineering effort to expose safe/permissioned operations to agents.

### Implementation Notes
- Build a thin service (e.g., FastAPI) that wraps Zoho endpoints and enforces business logic.
- Use Zoho webhooks or Notification API to push change events into the system.
- Consider caching metadata (modules/fields) to reduce API consumption.

## 4. Option B – Model Context Protocol (MCP) Servers
### 4.1 Third-Party/Community Servers
- **Python-based `zoho-crm-mcp` (SkanderBS2024)**: installable via `uvx`/pip; exposes contact/deal CRUD and automatic token refresh. Good starting point; extend `zoho_mcp/zoho_tools.py` for additional modules (Accounts, Notes, etc.).
- **Node.js Docker `zohocrm-mcpserver` (whiteside-daniel)**: packaged for Claude Desktop; includes module listing and record search tools. Requires Docker and manual OAuth setup.
- **Zapier MCP Connector**: hosted MCP gateway that bridges to Zapier’s 30k+ actions, including Zoho CRM. Minimal setup but limited customization and may incur per-task costs.

-### 4.2 Zoho MCP (Official)
- Zoho’s native MCP product (limited access currently granted via `npx mcp-remote https://zoho-mcp2-900114980…`) exposes standardized tools across Zoho apps with OAuth-based scopes, playground testing, and schema-first design.
- Supports autonomous agents (watchers/triggers) and multi-app workflows. Ideal for current pilot and long-term roadmap as features expand.

### Pros of MCP Approach
- Claude Agent SDK natively understands MCP tools—no extra glue code.
- Tool permissions can be strictly allowlisted per agent/subagent.
- Token handling abstracted if using maintained server (auto refresh, error normalization).
- Encourages consistent schema and logging per MCP spec.

### Cons
- Community servers may not cover all required modules; need to fork/extend.
- Requires hosting the MCP process (stdio/HTTP/SSE) with proper secret management.
- Official Zoho MCP still in gated access; timelines may vary.

### Implementation Notes
- Fork an existing MCP server to add custom logic (e.g., `list_recent_updates`, `create_followup_task`).
- Deploy on internal infrastructure with secrets manager and TLS where applicable.
- Map MCP tool names to Claude permission settings (e.g., allow only read tools for research agents).

## 5. Option C – Middleware & Integration Platforms
- **Zoho CRM Functions & Deluge**: build serverless functions triggered by workflows; expose via REST endpoints. Useful for encapsulating business logic but Deluge-centric.
- **Zoho Flow / Integrately / Make.com**: no-code automation platforms with webhook and API connectors. Can bridge to custom HTTP endpoints but less suitable for complex agent loops.
- **Serverless APIs (AWS Lambda, GCP Cloud Functions)**: run custom Python/Node code that interacts with Zoho; pair with API Gateway. Offers scaling and centralized control.

## 6. Option D – Hybrid Architecture
- Combine MCP for agent-facing operations with backend services for heavy lifting (bulk operations, analytics).
- Use direct REST integration to sync data into Cognee/knowledge base; expose curated MCP tools for runtime lookups.
- Employ Zoho Notifications to push delta updates into memory layer without polling.

## 7. Recommendation for Sergas
1. **Short Term**: Leverage the official Zoho MCP endpoint already provisioned; document its tool catalog, wire into Claude, and enforce least-privilege usage via Claude permissions.
2. **Parallel**: Maintain/plan a backend sync pipeline that calls Zoho REST APIs directly to update Cognee memory and support operations the MCP doesn’t expose.
3. **Monitor Zoho MCP evolution**: Track new tools/scopes released on the official endpoint to reduce custom maintenance.
4. **Fallback Strategy**: Keep raw REST client capability for operations not exposed via MCP (e.g., Bulk APIs, complex COQL queries) or during outages.

## 8. Key Considerations
- **Security**: store OAuth secrets and refresh tokens in a secrets vault; audit tool usage via MCP logs.
- **Rate Management**: queue and batch requests; prefer Zoho’s incremental syncs to minimize load.
- **Compliance**: sanitize PII before logging; respect regional data residency when hosting MCP/servers.
- **Testing**: use Zoho sandbox or developer edition for integration tests; validate scopes before production rollout.

## 9. References
- Zoho CRM API Docs (v6+): https://www.zoho.com/crm/developer/docs/
- SkanderBS2024 `zoho-crm-mcp` README (Oct 2025)
- whiteside-daniel `zohocrm-mcpserver` docs (Sep 2025)
- Zoho MCP product page (2025) outlining official MCP offering
- Zapier MCP connector for Zoho CRM (2025)

---
Prepared to guide integration planning for Claude-based Sergas agents.
