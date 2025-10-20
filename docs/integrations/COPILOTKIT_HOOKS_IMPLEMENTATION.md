# CopilotKit React Hooks Implementation

## Overview

This document describes the CopilotKit hooks integration implemented for the Sergas Account Manager frontend application. The integration provides AI-powered account analysis with real-time streaming, HITL approval workflows, and bidirectional state sharing.

## Components Created

### 1. AccountAnalysisAgent (`/frontend/components/copilot/AccountAnalysisAgent.tsx`)

**Purpose**: Main component for AI-driven account analysis with backend agent integration.

**CopilotKit Hooks Used**:
- `useCopilotAction`: Defines custom actions for backend agent triggers
- `useCopilotReadable`: Shares context with AI agents
- `useCopilotChat`: Accesses chat state for loading indicators

**Key Actions Implemented**:

#### analyzeAccount
```typescript
useCopilotAction({
  name: 'analyzeAccount',
  description: 'Perform comprehensive account analysis...',
  parameters: [{ name: 'accountId', type: 'string', required: true }],
  handler: async ({ accountId }) => {
    // Triggers orchestrator workflow
    // Coordinates: zoho_scout → memory_analyst → recommendation_author
    const result = await fetch(`${runtimeUrl}/orchestrator/analyze`, {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, hitl_enabled: true })
    });
    return result;
  }
});
```

**Backend Integration**:
- Calls `/orchestrator/analyze` endpoint
- Triggers full agent workflow: Zoho Data Scout → Memory Analyst → Recommendation Author
- Updates UI with real-time agent status
- Returns comprehensive analysis results

#### fetchAccountData
```typescript
useCopilotAction({
  name: 'fetchAccountData',
  description: 'Fetch account snapshot from Zoho CRM',
  parameters: [{ name: 'accountId', type: 'string', required: true }],
  handler: async ({ accountId }) => {
    const snapshot = await fetch(`${runtimeUrl}/zoho-scout/snapshot/${accountId}`);
    return snapshot;
  }
});
```

**Backend Integration**:
- Quick data retrieval without full analysis
- Calls Zoho Data Scout directly

#### getRecommendations
```typescript
useCopilotAction({
  name: 'getRecommendations',
  description: 'Generate AI recommendations with HITL approval',
  parameters: [{ name: 'accountId', type: 'string', required: true }],
  handler: async ({ accountId }) => {
    const recs = await fetch(`${runtimeUrl}/recommendation-author/generate`, {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, require_approval: true })
    });

    // Trigger HITL workflow
    if (recs.requires_approval) {
      onApprovalRequired({ run_id: recs.run_id, recommendations: recs.recommendations });
    }

    return recs;
  }
});
```

**Backend Integration**:
- Calls Recommendation Author agent
- Triggers HITL approval modal
- Supports recommendation modification before execution

**Context Sharing**:
```typescript
useCopilotReadable({
  description: 'Currently selected account in the application',
  value: selectedAccount
});

useCopilotReadable({
  description: 'Latest account analysis results...',
  value: analysisResult
});

useCopilotReadable({
  description: 'Current status of backend agents',
  value: agentStatus
});
```

**Features**:
- Real-time agent status tracking
- Account snapshot display with metrics
- Risk signals visualization
- Recommendations with confidence scores
- HITL approval workflow integration
- Error handling and user feedback

---

### 2. CoAgentIntegration (`/frontend/components/copilot/CoAgentIntegration.tsx`)

**Purpose**: Bidirectional state sharing between frontend and backend agents using shared state pattern.

**CopilotKit Hooks Used**:
- `useCopilotReadable`: Share state with backend agents
- `useCopilotAction`: Allow agents to update shared state

**Shared State Structure**:
```typescript
interface SharedState {
  current_account_id: string | null;
  analysis_in_progress: boolean;
  last_analysis_timestamp: string | null;
  agent_queue: string[];
  user_preferences: {
    auto_analyze: boolean;
    notification_level: 'all' | 'critical' | 'none';
  };
}
```

**Key Actions**:

#### updateSharedState
```typescript
useCopilotAction({
  name: 'updateSharedState',
  description: 'Update shared state from a backend agent',
  parameters: [
    { name: 'stateUpdate', type: 'object', required: true },
    { name: 'sourceAgent', type: 'string', required: false }
  ],
  handler: async ({ stateUpdate, sourceAgent }) => {
    setSharedState(prev => ({ ...prev, ...stateUpdate }));
    return { success: true, new_state: sharedState };
  }
});
```

**Use Case**: Backend agents can update UI state (e.g., when analysis starts/completes)

#### sendAgentMessage
```typescript
useCopilotAction({
  name: 'sendAgentMessage',
  description: 'Send message between agents for coordination',
  parameters: [
    { name: 'fromAgent', type: 'string', required: true },
    { name: 'toAgent', type: 'string', required: true },
    { name: 'messageType', type: 'string', required: true },
    { name: 'payload', type: 'object', required: false }
  ],
  handler: async ({ fromAgent, toAgent, messageType, payload }) => {
    const message = { from_agent: fromAgent, to_agent: toAgent, ... };
    setAgentMessages(prev => [...prev, message]);
    return { success: true, message_id: message.timestamp };
  }
});
```

**Use Case**: Inter-agent communication for workflow coordination

**CoAgentDashboard Component**:
- Displays shared state in real-time
- Shows inter-agent messages
- Visualizes agent coordination
- User preference controls

**Backend Integration**:
- Agents can read shared state via CopilotKit context
- Agents can update state by calling `updateSharedState` action
- Supports agent-to-agent messaging

---

### 3. CopilotChatIntegration (`/frontend/components/copilot/CopilotChatIntegration.tsx`)

**Purpose**: Advanced chat interface with streaming responses and tool call visualization.

**CopilotKit Hooks Used**:
- `useCopilotChat`: Manage chat state and message sending
- `useCopilotReadable`: Share chat history with agents

**Key Features**:
- Real-time message streaming
- Tool call visualization (shows when actions are executed)
- Chat history persistence
- Custom message rendering
- Suggestion chips for common queries

**Chat Flow**:
```typescript
const { isLoading, sendMessage, stopGeneration } = useCopilotChat();

const handleSendMessage = async () => {
  await sendMessage(inputMessage);
  // CopilotKit handles streaming response
  // Actions are automatically triggered based on AI response
};
```

**Tool Call Display**:
```typescript
interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
  result?: any;
  status: 'pending' | 'running' | 'completed' | 'failed';
}
```

**Suggestion Examples**:
- "Analyze account ACC-001"
- "Show me high-risk accounts"
- "Generate recommendations for account 12345"

**CompactChatWidget**:
- Floating chat button
- Expandable chat window
- Can be placed anywhere in the app

---

## Integration with Backend Agents

### Orchestrator Agent
**Endpoint**: `/orchestrator/analyze`
**Method**: POST
**Triggered by**: `analyzeAccount` action

**Request**:
```json
{
  "account_id": "ACC-001",
  "include_recommendations": true,
  "hitl_enabled": true
}
```

**Response**:
```json
{
  "run_id": "uuid",
  "account_snapshot": { ... },
  "risk_signals": [ ... ],
  "recommendations": [ ... ],
  "timestamp": "2025-10-19T..."
}
```

### Zoho Data Scout Agent
**Endpoint**: `/zoho-scout/snapshot/{account_id}`
**Method**: GET
**Triggered by**: `fetchAccountData` action

**Response**:
```json
{
  "account_id": "ACC-001",
  "account_name": "Acme Corp",
  "owner_name": "John Doe",
  "status": "Active",
  "risk_level": "medium",
  "priority_score": 75,
  "needs_review": false,
  "deal_count": 5,
  "total_value": 150000
}
```

### Memory Analyst Agent
**Integration**: Automatic via orchestrator
**Purpose**: Analyzes historical patterns and risk signals
**Output**: Risk signals array included in orchestrator response

### Recommendation Author Agent
**Endpoint**: `/recommendation-author/generate`
**Method**: POST
**Triggered by**: `getRecommendations` action

**Request**:
```json
{
  "account_id": "ACC-001",
  "require_approval": true
}
```

**Response**:
```json
{
  "run_id": "uuid",
  "requires_approval": true,
  "recommendations": [
    {
      "recommendation_id": "rec-1",
      "category": "engagement",
      "title": "Schedule Follow-up Meeting",
      "description": "...",
      "confidence_score": 85,
      "priority": "high",
      "next_steps": ["Step 1", "Step 2"],
      "supporting_evidence": ["Evidence 1", "Evidence 2"]
    }
  ]
}
```

---

## HITL (Human-in-the-Loop) Workflow

### Approval Flow

1. **Trigger**: User requests recommendations via chat or action
2. **Generation**: Recommendation Author generates recommendations
3. **Modal Display**: `ApprovalModal` component shows recommendations
4. **User Decision**: User approves or rejects
5. **Callback**: Approval endpoint called with decision
6. **Execution**: Backend executes or cancels based on approval

### Approval Modal Integration

```typescript
<ApprovalModal
  request={{
    run_id: "uuid",
    recommendations: [...]
  }}
  onApprove={async (modified) => {
    await fetch(`${runtimeUrl}/approval/respond`, {
      method: 'POST',
      body: JSON.stringify({
        run_id: request.run_id,
        approved: true,
        modified_data: modified
      })
    });
  }}
  onReject={async (reason) => {
    await fetch(`${runtimeUrl}/approval/respond`, {
      method: 'POST',
      body: JSON.stringify({
        run_id: request.run_id,
        approved: false,
        reason
      })
    });
  }}
/>
```

---

## Usage Examples

### Example 1: Analyze Account via Chat
```
User: "Analyze account ACC-001"
AI: "I'll analyze that account for you..."
→ Triggers analyzeAccount action
→ Calls orchestrator endpoint
→ UI shows agent status updates
→ Results displayed in AccountAnalysisAgent component
```

### Example 2: Get Recommendations with Approval
```
User: "Generate recommendations for ACC-001"
AI: "Generating recommendations..."
→ Triggers getRecommendations action
→ Calls recommendation-author endpoint
→ Approval modal appears
→ User reviews and approves/rejects
→ Backend executes or cancels
```

### Example 3: Quick Account Snapshot
```
User: "Show me data for account ACC-001"
AI: "Fetching account data..."
→ Triggers fetchAccountData action
→ Calls zoho-scout endpoint
→ Snapshot displayed without full analysis
```

---

## File Structure

```
frontend/
├── app/
│   └── page.tsx                          # Updated with CopilotKit integration
├── components/
│   ├── ApprovalModal.tsx                 # HITL approval component
│   ├── AgentStatusPanel.tsx              # Agent status display
│   └── copilot/
│       ├── AccountAnalysisAgent.tsx      # Main analysis component
│       ├── CoAgentIntegration.tsx        # Shared state management
│       ├── CopilotChatIntegration.tsx    # Chat interface
│       └── index.ts                      # Exports
└── docs/
    └── integrations/
        └── COPILOTKIT_HOOKS_IMPLEMENTATION.md  # This file
```

---

## Type Definitions

### Core Types
```typescript
interface Account {
  id: string;
  name: string;
  owner: string;
  status: string;
  risk_level: string;
}

interface AccountSnapshot {
  account_id: string;
  account_name: string;
  owner_name: string;
  status: string;
  risk_level: string;
  priority_score: number;
  needs_review: boolean;
  deal_count: number;
  total_value: number;
}

interface RiskSignal {
  signal_id: string;
  signal_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  detected_at: string;
  account_id: string;
}

interface Recommendation {
  recommendation_id: string;
  category: string;
  title: string;
  description: string;
  confidence_score: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  next_steps: string[];
  supporting_evidence: string[];
}

interface AnalysisResult {
  account_snapshot: AccountSnapshot;
  risk_signals: RiskSignal[];
  recommendations: Recommendation[];
  run_id: string;
  timestamp: string;
}
```

---

## Testing

### Manual Testing Checklist

- [ ] Chat interface loads correctly
- [ ] Can send messages and receive responses
- [ ] analyzeAccount action triggers orchestrator
- [ ] Agent status updates in real-time
- [ ] Account snapshot displays correctly
- [ ] Risk signals render with proper styling
- [ ] Recommendations show with confidence scores
- [ ] HITL approval modal appears when expected
- [ ] Approval/rejection callbacks work
- [ ] Shared state updates correctly
- [ ] Inter-agent messages display
- [ ] Error handling works properly

### Integration Testing

```bash
# Run TypeScript compilation
cd frontend
npx tsc --noEmit

# Start development server
npm run dev

# Test in browser at http://localhost:3000
```

---

## Next Steps

1. **Backend Implementation**: Ensure all endpoints are implemented and return correct data
2. **WebSocket Integration**: Add real-time updates for agent status
3. **Error Handling**: Implement comprehensive error handling and retry logic
4. **Performance**: Add caching and optimize API calls
5. **Testing**: Write unit and integration tests
6. **Documentation**: Update API documentation with new endpoints

---

## Troubleshooting

### Issue: Actions not triggering
**Solution**: Ensure CopilotKit provider wraps the component tree and runtimeUrl is correct

### Issue: State not updating
**Solution**: Check that useCopilotReadable is called with proper dependencies

### Issue: HITL modal not appearing
**Solution**: Verify onApprovalRequired callback is passed to AccountAnalysisAgent

### Issue: TypeScript errors
**Solution**: Ensure all type definitions are exported from index.ts

---

## References

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [CopilotKit React Hooks API](https://docs.copilotkit.ai/reference/hooks/useCopilotAction)
- [Backend Agent Documentation](../agents/)
- [HITL Workflow Guide](./HITL_WORKFLOW.md)
