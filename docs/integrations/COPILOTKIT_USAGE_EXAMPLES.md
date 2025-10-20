# CopilotKit Usage Examples

## Quick Start

### Basic Setup

```typescript
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';

export default function App() {
  return (
    <CopilotKit runtimeUrl="http://localhost:8000/copilotkit">
      <div className="flex h-screen">
        <div className="flex-1">
          <AccountAnalysisAgent
            runtimeUrl="http://localhost:8000"
            onApprovalRequired={(request) => console.log('Approval needed:', request)}
          />
        </div>
        <CopilotSidebar />
      </div>
    </CopilotKit>
  );
}
```

---

## Chat Interactions

### Example 1: Analyze Account
```
User: "Analyze account ACC-001"

AI Response:
"I'll analyze account ACC-001 for you..."
→ Triggers: analyzeAccount({ accountId: "ACC-001" })
→ Backend: POST /orchestrator/analyze
→ Result: Full analysis with snapshot, risks, recommendations

UI Updates:
✅ Agent status panel shows: zoho-data-scout → running
✅ Progress indicator appears
✅ Account snapshot card displays
✅ Risk signals list populates
✅ Recommendations render with confidence scores
```

### Example 2: Quick Data Fetch
```
User: "Show me quick stats for account 12345"

AI Response:
"Fetching account data..."
→ Triggers: fetchAccountData({ accountId: "12345" })
→ Backend: GET /zoho-scout/snapshot/12345
→ Result: Quick snapshot without full analysis

UI Updates:
✅ Account snapshot displays
✅ Basic metrics shown (deals, value, status)
✅ No risk analysis or recommendations
```

### Example 3: Generate Recommendations
```
User: "Give me recommendations for account ACC-001"

AI Response:
"Generating recommendations..."
→ Triggers: getRecommendations({ accountId: "ACC-001" })
→ Backend: POST /recommendation-author/generate
→ Result: Recommendations with HITL approval required

UI Updates:
✅ Approval modal appears
✅ User reviews recommendations
✅ User approves/rejects
✅ Backend receives approval decision
```

---

## Using Actions Programmatically

### Trigger Analysis from Code

```typescript
import { useCopilotAction } from '@copilotkit/react-core';

function MyComponent() {
  // This action can be called by AI or programmatically
  useCopilotAction({
    name: 'analyzeAccount',
    handler: async ({ accountId }) => {
      const response = await fetch(`${apiUrl}/orchestrator/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          include_recommendations: true,
          hitl_enabled: true
        })
      });

      const result = await response.json();
      return { success: true, data: result };
    }
  });

  // Trigger via button click (AI can also trigger)
  const handleAnalyzeClick = async () => {
    // The AI will pick up this request via chat context
    await sendMessage(`Analyze account ${selectedAccountId}`);
  };

  return <button onClick={handleAnalyzeClick}>Analyze</button>;
}
```

---

## Sharing Context with AI

### Share User Preferences

```typescript
import { useCopilotReadable } from '@copilotkit/react-core';

function UserPreferences() {
  const [preferences, setPreferences] = useState({
    auto_analyze: true,
    notification_level: 'critical',
    preferred_view: 'dashboard'
  });

  // AI can now see and reference user preferences
  useCopilotReadable({
    description: 'User preferences for account management',
    value: preferences
  });

  return (
    <div>
      {/* User preference controls */}
    </div>
  );
}
```

### Share Current Workflow State

```typescript
function WorkflowManager() {
  const [workflowState, setWorkflowState] = useState({
    step: 'data_collection',
    progress: 35,
    current_agent: 'zoho-data-scout',
    errors: []
  });

  // AI knows where we are in the workflow
  useCopilotReadable({
    description: 'Current state of the account analysis workflow',
    value: workflowState
  });

  return <WorkflowVisualization state={workflowState} />;
}
```

---

## CoAgent State Management

### Update State from Backend Agent

```typescript
// Backend agent (Python) can call this action via CopilotKit
// POST /copilotkit with action: updateSharedState

// Frontend receives and handles update
useCopilotAction({
  name: 'updateSharedState',
  handler: async ({ stateUpdate, sourceAgent }) => {
    console.log(`State update from ${sourceAgent}:`, stateUpdate);

    setSharedState(prev => ({
      ...prev,
      ...stateUpdate,
      last_updated_by: sourceAgent,
      last_update_time: new Date().toISOString()
    }));

    return {
      success: true,
      message: `State updated by ${sourceAgent}`,
      new_state: sharedState
    };
  }
});
```

### Inter-Agent Communication

```typescript
// Agent 1 sends message to Agent 2
useCopilotAction({
  name: 'sendAgentMessage',
  handler: async ({ fromAgent, toAgent, messageType, payload }) => {
    const message = {
      id: generateId(),
      from_agent: fromAgent,
      to_agent: toAgent,
      message_type: messageType,
      payload: payload || {},
      timestamp: new Date().toISOString()
    };

    // Store in message queue
    setAgentMessages(prev => [...prev, message]);

    // Optionally notify via WebSocket
    websocket?.send(JSON.stringify({ type: 'agent_message', message }));

    return {
      success: true,
      message_id: message.id
    };
  }
});
```

---

## HITL Approval Workflow

### Complete Example

```typescript
import { useState } from 'react';
import { ApprovalModal } from '@/components/ApprovalModal';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';

function AccountManager() {
  const [approvalRequest, setApprovalRequest] = useState(null);

  const handleApprovalRequired = (request) => {
    console.log('Approval required for run:', request.run_id);
    setApprovalRequest(request);
  };

  const handleApprove = async (modifiedData) => {
    console.log('User approved recommendations');

    // Send approval to backend
    await fetch(`${apiUrl}/approval/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: approvalRequest.run_id,
        approved: true,
        modified_data: modifiedData, // User can modify recommendations
        approved_by: currentUser.id,
        timestamp: new Date().toISOString()
      })
    });

    setApprovalRequest(null);
  };

  const handleReject = async (reason) => {
    console.log('User rejected recommendations:', reason);

    await fetch(`${apiUrl}/approval/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: approvalRequest.run_id,
        approved: false,
        reason: reason,
        rejected_by: currentUser.id,
        timestamp: new Date().toISOString()
      })
    });

    setApprovalRequest(null);
  };

  return (
    <>
      <AccountAnalysisAgent
        runtimeUrl={apiUrl}
        onApprovalRequired={handleApprovalRequired}
      />

      {approvalRequest && (
        <ApprovalModal
          request={approvalRequest}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </>
  );
}
```

---

## Custom Actions

### Create Domain-Specific Action

```typescript
import { useCopilotAction } from '@copilotkit/react-core';

function RiskManagement() {
  useCopilotAction({
    name: 'calculateRiskScore',
    description: 'Calculate a risk score for an account based on various factors',
    parameters: [
      {
        name: 'accountId',
        type: 'string',
        description: 'Account ID to analyze',
        required: true
      },
      {
        name: 'factors',
        type: 'object',
        description: 'Risk factors to consider (engagement, revenue, activity)',
        required: false
      }
    ],
    handler: async ({ accountId, factors }) => {
      // Custom risk calculation logic
      const riskData = await fetchRiskData(accountId);

      const score = calculateWeightedScore({
        engagement: riskData.engagement_score,
        revenue: riskData.revenue_trend,
        activity: riskData.activity_level,
        ...factors
      });

      return {
        success: true,
        account_id: accountId,
        risk_score: score,
        risk_level: getRiskLevel(score),
        factors_used: Object.keys(factors || {})
      };
    }
  });
}
```

---

## Error Handling

### Robust Action with Error Handling

```typescript
useCopilotAction({
  name: 'analyzeAccount',
  handler: async ({ accountId }) => {
    try {
      // Validate input
      if (!accountId || typeof accountId !== 'string') {
        return {
          success: false,
          error: 'Invalid account ID provided',
          code: 'INVALID_INPUT'
        };
      }

      // Set loading state
      setIsAnalyzing(true);
      setError(null);

      // Make API call with timeout
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);

      const response = await fetch(`${apiUrl}/orchestrator/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: accountId }),
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();

      // Update UI
      setAnalysisResult(result);
      setIsAnalyzing(false);

      return {
        success: true,
        data: result,
        message: `Successfully analyzed account ${accountId}`
      };

    } catch (error) {
      setIsAnalyzing(false);

      if (error.name === 'AbortError') {
        setError('Request timed out. Please try again.');
        return {
          success: false,
          error: 'Request timeout',
          code: 'TIMEOUT'
        };
      }

      setError(error.message);
      return {
        success: false,
        error: error.message,
        code: 'ANALYSIS_FAILED'
      };
    }
  }
});
```

---

## Real-Time Updates

### WebSocket Integration for Agent Status

```typescript
import { useEffect, useState } from 'react';
import { useCopilotReadable } from '@copilotkit/react-core';

function AgentStatusMonitor() {
  const [agentStatus, setAgentStatus] = useState({});
  const [websocket, setWebsocket] = useState(null);

  useEffect(() => {
    // Connect to WebSocket for real-time agent updates
    const ws = new WebSocket('ws://localhost:8000/ws/agents');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      if (update.type === 'agent_status') {
        setAgentStatus(prev => ({
          ...prev,
          [update.agent_id]: update.status
        }));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWebsocket(ws);

    return () => ws.close();
  }, []);

  // Share agent status with AI
  useCopilotReadable({
    description: 'Real-time status of all backend agents',
    value: agentStatus
  });

  return (
    <div>
      {Object.entries(agentStatus).map(([agentId, status]) => (
        <div key={agentId}>
          {agentId}: {status}
        </div>
      ))}
    </div>
  );
}
```

---

## Testing Examples

### Manual Testing Checklist

```typescript
// 1. Test basic chat interaction
// User input: "Hello"
// Expected: AI responds with greeting

// 2. Test account analysis
// User input: "Analyze account ACC-001"
// Expected:
// - analyzeAccount action triggered
// - Loading indicator appears
// - Agent status updates
// - Results display

// 3. Test error handling
// User input: "Analyze account INVALID"
// Expected:
// - Error message displays
// - UI remains functional
// - Can retry

// 4. Test HITL workflow
// User input: "Generate recommendations for ACC-001"
// Expected:
// - Approval modal appears
// - Recommendations are editable
// - Approve/reject buttons work
// - Backend receives decision

// 5. Test state sharing
// Action: Select account in UI
// Expected:
// - AI is aware of selection
// - Can reference in conversation
// - Context persists across messages
```

### Integration Test Example

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';

describe('AccountAnalysisAgent', () => {
  it('should trigger analysis and display results', async () => {
    const mockRuntimeUrl = 'http://localhost:8000';

    render(
      <AccountAnalysisAgent
        runtimeUrl={mockRuntimeUrl}
        onApprovalRequired={jest.fn()}
      />
    );

    // Simulate action trigger
    const analysisButton = screen.getByText('Analyze');
    analysisButton.click();

    // Wait for API call
    await waitFor(() => {
      expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    });

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/account snapshot/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});
```

---

## Performance Optimization

### Memoization for Large Datasets

```typescript
import { useMemo } from 'react';
import { useCopilotReadable } from '@copilotkit/react-core';

function PerformanceOptimizedComponent() {
  const [accounts, setAccounts] = useState([]);

  // Memoize expensive calculations
  const accountSummary = useMemo(() => {
    return {
      total_count: accounts.length,
      high_risk_count: accounts.filter(a => a.risk_level === 'high').length,
      avg_priority: accounts.reduce((sum, a) => sum + a.priority_score, 0) / accounts.length,
      needs_attention: accounts.filter(a => a.needs_review).length
    };
  }, [accounts]);

  // Only share summary, not full dataset
  useCopilotReadable({
    description: 'Summary statistics of all accounts',
    value: accountSummary
  });

  return <div>{/* UI */}</div>;
}
```

---

## Advanced Patterns

### Conditional Action Registration

```typescript
function ConditionalActions({ userRole }) {
  // Only admin users can approve high-value recommendations
  if (userRole === 'admin') {
    useCopilotAction({
      name: 'approveHighValueRecommendation',
      description: 'Approve recommendations over $10,000',
      handler: async ({ recommendationId }) => {
        // Admin-only approval logic
        return { success: true };
      }
    });
  }

  // All users can view recommendations
  useCopilotAction({
    name: 'viewRecommendations',
    description: 'View recommendations for an account',
    handler: async ({ accountId }) => {
      // Public viewing logic
      return { success: true };
    }
  });
}
```

---

## Troubleshooting

### Debug Mode

```typescript
import { useCopilotAction } from '@copilotkit/react-core';

function DebugMode() {
  const [debugLogs, setDebugLogs] = useState([]);

  useCopilotAction({
    name: 'debugAction',
    handler: async (params) => {
      const log = {
        timestamp: new Date().toISOString(),
        action: 'debugAction',
        parameters: params,
        result: null
      };

      try {
        // Your action logic
        const result = await performAction(params);
        log.result = result;
        setDebugLogs(prev => [...prev, log]);
        return result;
      } catch (error) {
        log.error = error.message;
        setDebugLogs(prev => [...prev, log]);
        throw error;
      }
    }
  });

  return (
    <div>
      <h3>Debug Logs</h3>
      {debugLogs.map((log, idx) => (
        <pre key={idx}>{JSON.stringify(log, null, 2)}</pre>
      ))}
    </div>
  );
}
```

---

## Summary

These examples demonstrate:
- Basic CopilotKit setup
- Chat-based interactions
- Programmatic action triggers
- Context sharing with AI
- HITL approval workflows
- Error handling
- Real-time updates
- Performance optimization
- Testing strategies
- Advanced patterns

For more details, see the full documentation:
- `/docs/integrations/COPILOTKIT_HOOKS_IMPLEMENTATION.md`
- `/docs/sparc/templates/CopilotKitDemo.tsx`
