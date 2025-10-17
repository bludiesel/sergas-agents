# Claude Agent SDK – Implementation Guide & Customization Intake

## 1. Overview
- **Purpose**: Build production-ready agents sharing Claude Code’s agent harness, enabling terminal/file access, tool orchestration, and iterative workflows.
- **Available SDKs**: `@anthropic-ai/claude-agent-sdk` (TypeScript) and `claude-agent-sdk` (Python).
- **Core strengths**: Automatic context compaction, fine-grained permissions, tool ecosystem (filesystem, bash, web), Model Context Protocol (MCP) integrations, subagents, and Claude Code feature parity.

## 2. Prerequisites
1. **Anthropic API access** (Claude API key) or configured Amazon Bedrock/Vertex AI credentials.
2. **Runtime**: Node.js ≥18 or Python ≥3.10.
3. **Claude Code CLI** installed (`npm install -g @anthropic-ai/claude-code`) if relying on local CLI features.
4. **Project structure** accommodating `.claude/` config, optional MCP servers, and any domain data sources.

## 3. Installation & Setup
### TypeScript
```bash
npm install @anthropic-ai/claude-agent-sdk
```
- Import `query`, `tool`, `createSdkMcpServer`.
- Configure `Options` (model, allowed/disallowed tools, permission mode, settingSources, system prompt).
- Use async generator `query()` for streaming responses; manage subagents via `agents` map; integrate MCP servers with `mcpServers`.

### Python
```bash
pip install claude-agent-sdk
```
- Choose between `query()` (stateless per call) and `ClaudeSDKClient` (stateful session).
- Decorate tools with `@tool`, register via `create_sdk_mcp_server`.
- Configure `ClaudeAgentOptions` (system prompt, allowed tools, permission mode, hooks, MCP servers).

## 4. Key Concepts & Features
- **System prompts**: Custom string or `preset: claude_code` with optional `append`.
- **Permissions**: `allowedTools`, `disallowedTools`, `permissionMode` (`default`, `acceptEdits`, `bypassPermissions`, `plan`); custom `canUseTool` callbacks.
- **Filesystem settings**: Enable `settingSources=['project']` to load `.claude/CLAUDE.md`/settings; defaults to none for isolation.
- **Subagents**: Configure via Markdown in `.claude/agents/` or programmatically; isolate context and parallelize tasks.
- **Hooks**: Pre/post tool events, session lifecycle, prompt submission, compaction for customized behavior and auditing.
- **MCP integrations**: Connect stdio/SSE/HTTP/SKD servers for external APIs and data sources; leverage growing MCP ecosystem.
- **Session management**: `continue`, `resume`, `forkSession` flags; `ClaudeSDKClient` streaming with interrupts.
- **Tooling coverage**: Read/Write/Edit/Glob/Grep/Bash/WebFetch/WebSearch/NotebookEdit/TodoWrite, etc.

## 5. Implementation Blueprint
1. **Define agent role & loop**  
   - Instruction design (system prompt + CLAUDE.md).  
   - Feedback loop: gather context → take action → verify results (per Anthropic guidance).
2. **Permissions & security**  
   - Least-privilege tool access; sandbox directories; custom permission handler for sensitive paths.
3. **Tooling strategy**  
   - Start with SDK’s built-ins; design custom MCP tools for domain actions (e.g., CRM query, ticket creation).  
   - Provide deterministic validation/linting where possible.
4. **Context management**  
   - Organize project data for agentic search (filesystem).  
   - Introduce semantic retrieval if latency or scale demands it.  
   - Use subagents for parallel search/specialized tasks.
5. **Verification & evaluation**  
   - Add rule-based checks, automated tests, visual audits, or LLM judges depending on domain requirements.  
   - Collect transcripts to refine prompts, tools, and permission rules.
6. **Deployment considerations**  
   - Monitor sessions, usage, cost; centralize logs.  
   - Harden MCP servers (auth, rate limits).  
   - Establish human-in-the-loop or escalation paths for critical flows.

## 6. Customization Intake Checklist
Please provide:
1. **Use case & goals**: Business workflow, success criteria.
2. **Target users & access model**: Internal tool vs. end-customer; authentication needs.
3. **Preferred SDK/runtime**: TypeScript or Python; hosting environment (local, server, cloud).
4. **Required capabilities/tools**: Filesystem scope, bash actions, external APIs, MCP integrations, web search, notebook editing, etc.
5. **Data sources & storage**: Locations, formats, access methods, compliance constraints.
6. **Security constraints**: Sandboxing requirements, permission policies, audit logging expectations.
7. **Context artifacts**: Existing documentation, prompts, CLAUDE.md instructions, subagent definitions.
8. **Verification strategy**: Desired linting/tests, QA workflows, human review steps.
9. **Performance requirements**: Latency budgets, concurrency, cost thresholds.
10. **Integration points**: Existing infra (CI/CD, ticketing, chat platforms, scheduling).
11. **Deployment plan**: Environment (dev/staging/prod), monitoring stack, rollback strategy.
12. **Timeline & maintenance expectations**: SLAs, update cadence, handover plan.

---

This guide consolidates Anthropic’s SDK docs and best practices to accelerate agent development; furnish the intake details to tailor system prompts, tool choices, permissions, context strategy, and deployment workflow to your specific needs.
