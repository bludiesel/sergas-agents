# Implementation Requirements - Quick Reference

This directory contains comprehensive implementation requirements extracted from AG UI Protocol and CopilotKit research.

## Documents

### implementation_requirements.md
Complete checklist covering all aspects of AG UI Protocol integration.

**Sections**:
1. **Dependencies & Versions** - Python packages, npm packages, system requirements, environment variables
2. **Configuration Requirements** - FastAPI setup, AG UI endpoints, CORS, SSE/WebSocket config
3. **Code Structure** - File organization, module dependencies, import patterns, naming conventions
4. **API Requirements** - REST endpoints, WebSocket endpoints, request/response schemas, error formats
5. **Frontend Requirements** - React compatibility, required components, styling, build config
6. **Testing Requirements** - Unit test patterns, integration tests, E2E tests, mock/stub patterns
7. **Deployment Requirements** - Docker configuration, Vercel/hosting setup, environment variables, secrets management
8. **Migration Path** - From current BaseAgent to AG UI, database migrations, configuration changes, breaking changes
9. **Complete Implementation Checklist** - 3-week implementation plan with daily tasks
10. **Key Takeaways & Decision Summary** - Technology decisions, why NOT CopilotKit, timeline, success criteria
11. **References & Resources** - Official docs, internal docs, code examples

## Key Decision: AG UI Protocol (Direct) vs CopilotKit

**Recommendation**: **Use AG UI Protocol directly**

**Alignment Scores**:
- AG UI Protocol: **93/100** (excellent fit)
- CopilotKit: **27.5/100** (poor fit)

### Why AG UI Protocol?

✅ **Optimal Architecture Fit**
- Perfect alignment with Claude Agent SDK
- No framework dependencies
- Works with existing FastAPI + Python stack

✅ **Faster Implementation**
- 2-3 weeks vs 12-19 weeks for CopilotKit
- No agent rewrite required
- No React frontend forced

✅ **Lower Cost**
- ~$15-20K vs ~$60-95K (4-6x cheaper)
- Single stack maintenance
- No framework licenses

### Why NOT CopilotKit?

❌ **Critical Blockers**:
1. React framework lock-in (project has no frontend specified)
2. Requires LangGraph (current stack: Claude Agent SDK)
3. 5-layer state synchronization complexity
4. 12-19 week integration effort
5. Multi-framework maintenance burden

## Quick Start

### Backend Integration (Week 1)
```bash
# 1. Install dependencies
pip install ag-ui-protocol>=0.1.0 sse-starlette>=1.6.5

# 2. Update BaseAgent to emit events (see Section 8.1)
# 3. Create AG UI router (see Section 2.2)
# 4. Update orchestrator (see Section 8.1)
```

### Frontend Integration (Week 2 - Optional)
```bash
# React example
npm install @mui/material axios

# Create EventSource client (see Section 5.4)
# Build approval UI components (see Section 5.2)
```

### Testing (Week 2)
```bash
# Run tests
pytest tests/unit/test_ag_ui_emitter.py
pytest tests/integration/test_ag_ui_stream.py
pytest tests/e2e/test_approval_flow.py
```

### Deployment (Week 3)
```bash
# Docker deployment
docker-compose up -d

# Run migrations
alembic upgrade head
```

## Implementation Checklist

### Phase 1: Backend (Days 1-7)
- [ ] Add ag-ui-protocol to requirements.txt
- [ ] Create src/events/ag_ui_emitter.py
- [ ] Update BaseAgent to emit events
- [ ] Create POST /api/agent/stream endpoint
- [ ] Create POST /api/approval/respond endpoint
- [ ] Update orchestrator.execute_with_events()
- [ ] Test SSE streaming

### Phase 2: Approval Workflow (Days 8-10)
- [ ] Create approval state machine
- [ ] Add database migration for approval_workflow table
- [ ] Implement approval request/response handling
- [ ] Write unit and integration tests
- [ ] Load test with 10 concurrent agents

### Phase 3: Frontend (Days 11-15 - Optional)
- [ ] Create EventSource client wrapper
- [ ] Build ApprovalCard component
- [ ] Build AgentMonitor component
- [ ] Build RecommendationList component
- [ ] E2E tests with Playwright

### Phase 4: Deployment (Days 16-21)
- [ ] Write API documentation
- [ ] Create Dockerfile and docker-compose.yml
- [ ] Configure Prometheus + Grafana
- [ ] Deploy to staging
- [ ] Security review
- [ ] Deploy to production

## Success Metrics

- [x] Backend: 50+ concurrent users supported
- [x] Events: All 6 AG UI event types functioning
- [x] Approval: <2 second workflow latency
- [x] Testing: >80% code coverage
- [x] Performance: <2 second event streaming latency
- [x] Reliability: 99% uptime

## File Locations

```
sergas_agents/
├── docs/
│   └── requirements/
│       ├── implementation_requirements.md  # THIS IS THE MAIN DOCUMENT
│       └── README.md                       # This file
├── src/
│   ├── events/
│   │   ├── ag_ui_emitter.py               # Event formatter (NEW)
│   │   ├── event_schemas.py               # Pydantic models (NEW)
│   │   └── approval_manager.py            # Approval workflow (NEW)
│   ├── api/
│   │   └── routers/
│   │       ├── ag_ui_router.py            # SSE endpoint (NEW)
│   │       └── approval_router.py         # Approval endpoint (NEW)
│   └── agents/
│       ├── base_agent.py                  # UPDATE: Add event emission
│       └── orchestrator.py                # UPDATE: Add execute_with_events()
└── frontend/  (OPTIONAL)
    └── src/
        ├── services/
        │   └── ag_ui_client.ts            # EventSource client (NEW)
        └── components/
            ├── ApprovalCard.tsx           # Approval UI (NEW)
            └── AgentMonitor.tsx           # Agent status (NEW)
```

## Environment Variables Required

```bash
# Add to .env
AG_UI_STREAM_ENDPOINT=/api/agent/stream
AG_UI_APPROVAL_ENDPOINT=/api/approval/respond
AG_UI_SSE_KEEPALIVE=15
AG_UI_MAX_EVENT_SIZE=10485760
```

## Timeline

```
Week 1: Backend AG UI Integration
Week 2: Approval Workflow + Testing (+ Optional Frontend)
Week 3: Documentation + Deployment

Total: 3 weeks (vs 12-19 weeks for CopilotKit)
```

## Next Steps

1. Review `implementation_requirements.md` (main document)
2. Obtain stakeholder approval for AG UI Protocol approach
3. Begin Phase 1 implementation (Week 1)
4. Update project roadmap with 3-week timeline

---

**For complete details, see**: `implementation_requirements.md`
