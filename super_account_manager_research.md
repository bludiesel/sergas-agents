# Super Account Manager Agent Research Dossier

## 1. Objective & Scope
- **Goal**: Build a Claude Agent SDK (Python 3.14) solution that acts as *Sergas Super Account Manager*, auditing Zoho CRM accounts, tracking updates, and recommending next actions per owner.
- **Focus Areas**: Claude Agent SDK capabilities, subagent orchestration, MCP tooling, Zoho CRM integration patterns, persistent memory/knowledge base options (Cognee et al.), security/compliance. This dossier feeds upcoming planning and PRD work.

## 2. Claude Agent SDK (Python) Findings
### 2.1 SDK Highlights
- Python package: `claude-agent-sdk`; supports Python ≥3.10 (compatible with 3.14).
- Two interaction modes: `query()` (stateless) vs. `ClaudeSDKClient` (stateful sessions with interrupts, hooks, custom tools).
- Rich toolchain (Read/Write/Grep/Bash/WebSearch, etc.), subagent definitions, context compaction, permission modes (`default`, `acceptEdits`, `bypassPermissions`, `plan`).
- Hooks allow pre/post tool logic, notifications, or external reviews.
- MCP integration lets agents call external services (HTTP/SSE/stdio servers) securely via standardized tool interface.

### 2.2 Subagent Design Best Practices
- Subagents defined via Markdown + YAML metadata or programmatically; each with own prompt, tool allowlist, context window (PubNub case study, Aug 2025).
- Recommended pipeline: orchestrator + specialized subagents (spec/research, analyst, recommender). Use hooks to manage handoffs, log outputs, enforce HITL checkpoints.
- Permission hygiene: start deny-all, explicitly allow necessary tools/MCP resources to contain risk.
- Logging/Audit: configure hooks to log queue status and subagent summaries for traceability.

### 2.3 Implications for Sergas Agent
- Orchestrator agent (main) uses `ClaudeSDKClient` for long-lived sessions, enabling iterative account reviews.
- Subagents: (1) **Zoho Researcher** (fetch latest account data), (2) **History Analyst** (query memory system), (3) **Recommendation Writer** (synthesize actions; gated by approval).
- Custom hooks to enforce “ask-first” rules before mutating CRM or sending owner notifications.

## 3. MCP Integration Landscape
### 3.1 Existing Zoho CRM MCP Server (SkanderBS2024)
- PyPI package `zoho-crm-mcp`; run via `uvx --from zoho-crm-mcp zoho-mcp` (stdio transport).
- OAuth2 support with helper `zoho-mcp-auth` to generate access/refresh tokens; environment variables required (`ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_ACCESS_TOKEN`, etc.).
- Tools exposed: contact search/create/update, deal search/create/list, fetch user info. Compatible with Claude MCP clients.
- Production considerations: move tokens to secure store (KMS/Secrets Manager), rotate regularly, implement rate monitoring (Zoho free tier 200 calls/day; higher on paid plans).
- Extension path: add modules (Accounts, Activities) by editing `zoho_mcp/zoho_tools.py` & regenerating MCP tool wrappers.

### 3.2 Custom Zoho CRM Integration Requirements
- Target Zoho API version V6+ (ref docs). Authentication via OAuth “Server-based Applications”.
- Modules relevant to Super Account Manager: Accounts, Contacts, Deals, Notes, Activities, custom modules. Need scopes `ZohoCRM.modules.ALL`, plus read/write subsets depending on allowed operations.
- Recommended patterns:
  - **Read operations**: `GET /crm/v6/Accounts`, `GET /crm/v6/Deals`, `GET /crm/v6/Notes`, `POST /crm/v6/search` (COQL queries) for filtered retrieval, `GET /crm/v6/users` for owner metadata.
  - **Change monitoring**: Notification API (webhooks) or scheduled diff via `modified_time` filters. MCP server could expose `list_recent_updates(account_id)` using COQL with `Modified_Time`.
  - **Action logging**: Use Zoho Notes API or custom module to store AI suggestions; ensure segregation between recommendations and committed CRM updates.
- MCP Security: implement allowlist of MCP tools by subagent; use `permission_mode='default'` with manual approval for mutating tools (`update_account`, `create_task`).

### 3.3 Additional MCP Servers to Consider
- **Cognee Memory MCP**: none official yet; would create custom HTTP/stdio server bridging Cognee SDK (see §4). Tools: `add_context`, `search_context`, `get_account_timeline`.
- **Analytics/BI**: If metrics stored externally (e.g., data warehouse), create dedicated MCP server for aggregated metrics.

## 4. Knowledge Base / Memory Options
### 4.1 Cognee Overview (2025)
- Purpose-built memory layer combining embeddings + knowledge graphs; Python SDK with CLI (`cognify`).
- Stores data as graph-enriched chunks with entity relationships (subject–relation–object). Supports ontologies, reasoning layer, evaluation pipelines.
- Integration pattern: ingest account histories (Zoho exports, meeting notes, emails) into Cognee workspace; agent queries via natural language to retrieve contextual insights.
- Performance: ~1 GB ingestion in 40 minutes using scaled containers (v0.3). Supports local or cloud deployment; uses LanceDB for storage, ensures workspace isolation.
- Strengths: higher reliability vs. vanilla RAG (~90% vs. ~60% success per Memgraph webinar); graph structure enables better longitudinal reasoning about accounts.
- Gaps: TypeScript SDK immature, large-scale (>TB) still roadmap; need to manage deduplication and ontology definitions manually for best results.

### 4.2 Alternatives / Complements
- **LangGraph + Cognee**: deterministic control flow + persistent memory (Cognee blog Oct 2025). Could model orchestrator with LangGraph, but Claude Agent SDK already handles planning; consider Cognee purely as memory backend.
- **Vector DB only**: e.g., LanceDB standalone, Pinecone, Weaviate. Faster to implement but lower recall for complex account histories.
- **Custom Graph DB**: Memgraph or Neo4j with bespoke ingestion; more engineering effort but full control.
- **Zoho Knowledge Base**: limited to Zoho data; lacks cross-system context (emails, docs). Use as supplemental source.

### 4.3 Recommended Approach for Sergas
- Start with the **official Zoho MCP endpoint** already provisioned (`mcp-remote https://zoho-mcp2-900114980.zohomcp.com/...`). Catalogue its tools, verify read/write coverage for Accounts, Deals, Notes, and tasks, and integrate it as the primary Claude-facing connector.
- Deploy Cognee (self-hosted) for persistent account context. Pipeline:
  1. Export relevant Zoho modules via Bulk Read API (Accounts, Deals, Notes, Activities).
  2. Normalize & enrich (map owners, segments, health metrics) before ingesting into Cognee.
  3. Implement MCP server wrapping Cognee SDK (tools: `upsert_account_snapshot`, `search_account_history`, `get_related_entities`).
  4. Schedule incremental updates via Zoho notifications or nightly sync job.
- Plan a supplemental REST/SDK layer later for gaps not covered by the Zoho MCP (bulk sync, custom modules) and keep a fallback to direct Zoho fetch if MCP or Cognee unavailable.

## 5. Proposed Agent Architecture (High-Level)
1. **Main Orchestrator (Super Account Manager)**
   - Uses `ClaudeSDKClient` with continuous session.
   - Manages workflow: queue accounts, call subagents, collate outputs, prompt user approvals.
   - Tools: limited to coordination (no direct write permissions).

2. **Subagents**
   - **Zoho Data Scout**: Allowed tools `Read`, `WebFetch` (for reports), MCP `zoho-crm` (read-only). Task: pull latest account metrics, detect status changes since last review.
   - **Memory Analyst**: Allowed MCP `cognee-memory` (search), optional analytics MCP. Task: gather historical context, highlight key events, owner interactions.
   - **Recommendation Author**: Allowed `Write` (draft note/report), optional MCP to create follow-up tasks (guarded). Produces suggested actions with rationale and risk notes.
   - Optional **Compliance Reviewer**: Ensures outputs respect policy, sanitizes sensitive data before logging.

3. **Hooks & Governance**
   - `PreToolUse`: intercept Zoho write attempts, require explicit confirmation.
   - `PostToolUse`: log retrieved data references to maintain audit trail.
   - `SessionEnd`: archive transcript, push summary to knowledge base.

4. **Storage & Telemetry**
   - Cognee for long-term memory; store structured outputs (action recommendations) for future reference.
   - Observability: capture tool usage stats, latency, cost per run (Claude usage metrics available via SDK result messages).

## 6. Security, Compliance, and Reliability Considerations
- **Authentication Secrets**: use dedicated secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault). Avoid storing tokens in plaintext `.env` beyond local dev.
- **Least Privilege**: Zoho OAuth scopes restricted to modules/verbs required. Separate client IDs for staging vs. production.
- **Rate Limits**: implement caching for static metadata; queue Zoho requests to respect daily quotas. Consider Zoho’s notification API to minimize polling.
- **Data Residency & Privacy**: confirm Cognee deployment region aligns with Sergas policies. Ensure sensitive fields (PII) handled per compliance (mask in outputs when necessary).
- **Audit Trail**: maintain logs of recommendations vs. actions taken, map to account owners for accountability.
- **Human-in-the-loop**: require manual approval before pushing updates to CRM or notifying owners; configure agent prompts accordingly.

## 7. Data & Inputs Needed from Sergas
1. Zoho CRM details: environment (production vs. sandbox), tenant domain, modules/fields critical for account health, current automation processes.
2. API credentials setup: ability to register Zoho OAuth client, redirect URI constraints.
3. Definition of “account updates”: which signals trigger review (deal stage change, inactive >30 days, support tickets, etc.).
4. Historical context sources: meeting notes, emails, support systems, spreadsheets. Format and access method.
5. Compliance/policy guidelines: sensitivity levels, approval workflows, logging requirements.
6. Desired output format: internal note, email draft, dashboard entry, etc.
7. Success metrics: detection accuracy, recommendation adoption rate, latency thresholds.

## 8. Next Steps Toward Plan & PRD
1. **Architecture Workshop**: validate proposed subagent lineup, knowledge base integration, security expectations.
2. **Technical Spike**: prototype Zoho MCP server (evaluate SkanderBS2024 vs. custom fork), confirm API scopes.
3. **Memory Pilot**: ingest limited set of accounts into Cognee; benchmark retrieval quality vs. direct Zoho queries.
4. **Implementation Plan Draft**: break down milestones (MCP setup, memory integration, agent prompts, hooks, observability).
5. **PRD Preparation**: document user stories, acceptance criteria, non-functional requirements, dependencies.

---

*This dossier aggregates current research (Anthropic SDK docs, PubNub subagent practices, Zoho CRM API v6 references, Zoho MCP server project, Cognee knowledge base insights) to support Sergas Super Account Manager planning.*
