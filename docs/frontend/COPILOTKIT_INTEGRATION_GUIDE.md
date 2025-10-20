# CopilotKit Integration Guide

**Project:** Sergas Super Account Manager
**Framework:** Next.js 15 + React 19 + CopilotKit 1.10.6
**Last Updated:** 2025-10-19

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [Component Guide](#component-guide)
5. [API Reference](#api-reference)
6. [Usage Examples](#usage-examples)
7. [HITL Workflows](#hitl-workflows)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

This guide covers the complete CopilotKit integration in the Sergas Account Manager frontend. CopilotKit enables AI-powered conversational interfaces that connect React components to backend LangGraph agents.

### What is CopilotKit?

CopilotKit is a framework that allows you to:
- Define custom actions that AI can trigger
- Share application state with AI (useCopilotReadable)
- Create conversational interfaces with useCopilotChat
- Coordinate backend agents from frontend components

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ React Components                                            │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ CopilotProvider  │  │ AccountAnalysis  │               │
│  │                  │→ │ Agent            │               │
│  └──────────────────┘  └──────────────────┘               │
│           │                      │                          │
│           │              ┌───────┴────────┐                │
│           │              │ useCopilotAction│               │
│           │              │ useCopilotReadable             │
│           │              └────────────────┘                │
└───────────┼───────────────────┼────────────────────────────┘
            │                   │
            ↓                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Next.js API Route                                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ /app/api/copilotkit/route.ts                         │  │
│  │ - POST handler (request forwarding)                  │  │
│  │ - GET handler (health check)                         │  │
│  │ - SSE streaming support                              │  │
│  │ - Authentication propagation                         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────┼─────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ CopilotKit SDK (/copilotkit endpoint)                │  │
│  │                                                       │  │
│  │ ┌─────────────────────────────────────────────────┐ │  │
│  │ │ LangGraph Agents:                               │ │  │
│  │ │ - orchestrator_wrapper                          │ │  │
│  │ │ - zoho_scout_wrapper                            │ │  │
│  │ │ - memory_analyst_wrapper                        │ │  │
│  │ │ - recommendation_author_wrapper                 │ │  │
│  │ └─────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Component Hierarchy

```
app/
├── layout.tsx                    (Root layout - NOT wrapped yet)
├── page.tsx                      (Home page - uses CopilotKit)
│
components/
├── copilot/
│   ├── CopilotProvider.tsx       (CopilotKit context provider)
│   ├── AccountAnalysisAgent.tsx  (Main agent component)
│   ├── CopilotSidebar.tsx        (Chat sidebar)
│   ├── CopilotPopup.tsx          (Chat popup)
│   └── index.tsx                 (Exports)
│
├── ui/                           (Shadcn/UI components)
│   ├── button.tsx
│   ├── dialog.tsx
│   ├── card.tsx
│   └── badge.tsx
│
├── AgentStatusPanel.tsx          (Agent status display)
├── ApprovalModal.tsx             (HITL approval UI)
└── ToolCallCard.tsx              (Tool execution display)
```

### Data Flow

1. **User Action** → User chats with AI or triggers action
2. **CopilotKit** → AI interprets intent and selects action
3. **useCopilotAction** → Handler executes (calls backend)
4. **Next.js Route** → Proxies request to FastAPI
5. **FastAPI** → CopilotKit SDK routes to LangGraph agent
6. **LangGraph** → Executes agent workflow
7. **Response** → Returns to frontend via Next.js route
8. **State Update** → Component updates UI

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install @copilotkit/react-core @copilotkit/react-ui @copilotkit/react-textarea
npm install @radix-ui/react-dialog @radix-ui/react-slot
npm install class-variance-authority clsx tailwind-merge lucide-react
```

### 2. Configure Environment Variables

Create `.env.local`:

```env
# Backend API URL (Next.js server or FastAPI)
NEXT_PUBLIC_API_URL=http://localhost:8008

# CopilotKit runtime URL (points to Next.js API route)
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=/api/copilotkit

# Authentication token (optional)
NEXT_PUBLIC_API_TOKEN=your-token-here

# CopilotKit public API key (optional)
NEXT_PUBLIC_COPILOTKIT_API_KEY=your-key-here
```

### 3. Verify Backend is Running

```bash
# In project root
source venv312/bin/activate
uvicorn src.main:app --reload --port 8008

# Test health endpoint
curl http://localhost:8008/health
```

### 4. Start Frontend

```bash
cd frontend
npm run dev

# Open http://localhost:3000
```

---

## Component Guide

### CopilotProvider

Wraps your application with CopilotKit context.

**Usage:**

```tsx
import { CopilotProvider } from '@/components/copilot';

export default function MyApp({ children }) {
  return (
    <CopilotProvider agent="orchestrator">
      {children}
    </CopilotProvider>
  );
}
```

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | ReactNode | - | Child components |
| `agent` | string | 'orchestrator' | Backend agent to use |
| `publicApiKey` | string | undefined | CopilotKit API key |

**Environment Configuration:**

- `NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL` - API endpoint
- `NEXT_PUBLIC_API_TOKEN` - Auth token
- `NEXT_PUBLIC_COPILOTKIT_API_KEY` - CopilotKit key

---

### AccountAnalysisAgent

Main component with CopilotKit actions for account analysis.

**Usage:**

```tsx
import { AccountAnalysisAgent } from '@/components/copilot';

export default function Dashboard() {
  const handleApproval = (request) => {
    console.log('Approval required:', request);
    // Handle HITL approval
  };

  return (
    <AccountAnalysisAgent
      runtimeUrl="/api/copilotkit"
      onApprovalRequired={handleApproval}
    />
  );
}
```

**Props:**

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `runtimeUrl` | string | Yes | Backend API URL |
| `onApprovalRequired` | function | No | HITL approval callback |

**Available Actions:**

1. **analyzeAccount** - Full account analysis
2. **fetchAccountData** - Quick snapshot
3. **getRecommendations** - Generate recommendations
4. **selectAccount** - Select account for viewing
5. **clearAccountSelection** - Reset state

---

### CopilotChat Components

#### CopilotSidebar

Fixed sidebar with chat interface.

```tsx
import { CopilotSidebar } from '@copilotkit/react-ui';

<CopilotSidebar
  labels={{
    title: "Account Assistant",
    initial: "How can I help analyze accounts?"
  }}
/>
```

#### CopilotPopup

Floating popup chat window.

```tsx
import { CopilotPopup } from '@copilotkit/react-ui';

<CopilotPopup
  labels={{
    title: "AI Assistant",
    initial: "Ask me anything about accounts"
  }}
/>
```

---

## API Reference

### useCopilotAction

Define custom actions that AI can trigger.

**Signature:**

```typescript
useCopilotAction({
  name: string;
  description: string;
  parameters: Parameter[];
  handler: (args: Record<string, any>) => Promise<any>;
});
```

**Example:**

```tsx
import { useCopilotAction } from '@copilotkit/react-core';

useCopilotAction({
  name: 'analyzeAccount',
  description: 'Perform comprehensive account analysis',
  parameters: [
    {
      name: 'accountId',
      type: 'string',
      description: 'Account ID to analyze',
      required: true
    }
  ],
  handler: async ({ accountId }) => {
    const response = await fetch('/api/copilotkit/analyze', {
      method: 'POST',
      body: JSON.stringify({ accountId })
    });

    const result = await response.json();

    return {
      success: true,
      data: result
    };
  }
});
```

**Parameter Types:**

- `string` - Text input
- `number` - Numeric input
- `boolean` - True/false
- `object` - JSON object
- `array` - Array of values

---

### useCopilotReadable

Share application state with AI.

**Signature:**

```typescript
useCopilotReadable({
  description: string;
  value: any;
});
```

**Example:**

```tsx
import { useCopilotReadable } from '@copilotkit/react-core';

const [selectedAccount, setSelectedAccount] = useState(null);

useCopilotReadable({
  description: 'Currently selected account in the application',
  value: selectedAccount ? {
    id: selectedAccount.id,
    name: selectedAccount.name,
    status: selectedAccount.status
  } : null
});
```

**Best Practices:**

- ✅ Keep descriptions clear and concise
- ✅ Only share relevant data
- ✅ Handle null/undefined states
- ✅ Use structured data (objects, not strings)
- ❌ Don't share sensitive data (passwords, tokens)

---

### useCopilotChat

Access chat state and messages.

**Signature:**

```typescript
const {
  isLoading: boolean;
  messages: Message[];
  sendMessage: (text: string) => void;
} = useCopilotChat();
```

**Example:**

```tsx
import { useCopilotChat } from '@copilotkit/react-core';

const { isLoading, messages } = useCopilotChat();

return (
  <div>
    {isLoading && <p>AI is thinking...</p>}
    {messages.map(msg => (
      <div key={msg.id}>{msg.content}</div>
    ))}
  </div>
);
```

---

## Usage Examples

### Example 1: Analyze Account

**User Chat:**
```
"Analyze account ACC-12345"
```

**Flow:**
1. AI detects `analyzeAccount` action
2. Extracts accountId: "ACC-12345"
3. Calls action handler
4. Handler fetches data from backend
5. Backend orchestrates: ZohoDataScout → MemoryAnalyst → RecommendationAuthor
6. Returns results to frontend
7. UI updates with snapshot, risk signals, recommendations

**Code:**

```tsx
useCopilotAction({
  name: 'analyzeAccount',
  description: 'Analyze an account comprehensively',
  parameters: [
    { name: 'accountId', type: 'string', required: true }
  ],
  handler: async ({ accountId }) => {
    const result = await handleAnalyzeAccount(accountId);
    return {
      success: true,
      message: `Analyzed ${result.account_snapshot.account_name}`,
      data: result
    };
  }
});
```

---

### Example 2: Quick Snapshot

**User Chat:**
```
"Show me quick details for account XYZ Corp"
```

**Flow:**
1. AI uses `fetchAccountData` action
2. Calls ZohoDataScout directly (no full analysis)
3. Returns snapshot quickly

**Code:**

```tsx
useCopilotAction({
  name: 'fetchAccountData',
  description: 'Get quick account snapshot',
  parameters: [
    { name: 'accountId', type: 'string', required: true }
  ],
  handler: async ({ accountId }) => {
    const snapshot = await handleFetchAccountData(accountId);
    return {
      success: true,
      snapshot
    };
  }
});
```

---

### Example 3: HITL Approval Workflow

**User Chat:**
```
"Generate recommendations for account ACC-100"
```

**Flow:**
1. AI triggers `getRecommendations` action
2. Backend generates recommendations
3. `onApprovalRequired` callback triggered
4. ApprovalModal displays
5. User approves/rejects
6. Backend receives decision
7. Workflow continues or stops

**Code:**

```tsx
const [approvalRequest, setApprovalRequest] = useState(null);

const handleApprovalRequired = (request) => {
  setApprovalRequest(request);
};

const handleApprove = async (modified) => {
  await fetch('/api/approval/respond', {
    method: 'POST',
    body: JSON.stringify({
      run_id: approvalRequest.run_id,
      approved: true,
      modified_data: modified
    })
  });
  setApprovalRequest(null);
};

return (
  <>
    <AccountAnalysisAgent
      runtimeUrl="/api/copilotkit"
      onApprovalRequired={handleApprovalRequired}
    />

    {approvalRequest && (
      <ApprovalModal
        request={approvalRequest}
        onApprove={handleApprove}
        onReject={(reason) => handleReject(reason)}
      />
    )}
  </>
);
```

---

## HITL Workflows

### Approval Request Flow

```
1. User triggers action (e.g., "Generate recommendations")
   ↓
2. Backend agent executes workflow
   ↓
3. Agent reaches approval node
   ↓
4. LangGraph interrupts execution
   ↓
5. Backend sends approval request to frontend
   ↓
6. Frontend displays ApprovalModal
   ↓
7. User reviews and approves/rejects
   ↓
8. Frontend sends decision to backend
   ↓
9. LangGraph resumes execution
   ↓
10. Workflow completes
```

### Approval Request Structure

```typescript
interface ApprovalRequest {
  run_id: string;
  recommendations: Recommendation[];
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
```

### Approval Response

```typescript
// Approve
{
  run_id: "abc-123",
  approved: true,
  modified_data: { /* optional modifications */ }
}

// Reject
{
  run_id: "abc-123",
  approved: false,
  reason: "User rejected: insufficient data"
}
```

---

## Troubleshooting

### Issue 1: "Failed to connect to backend"

**Symptoms:**
- CopilotKit actions fail
- Network errors in console
- 503 Service Unavailable

**Diagnosis:**

```bash
# Check backend is running
curl http://localhost:8008/health

# Check Next.js route
curl http://localhost:3000/api/copilotkit
```

**Solutions:**

1. Start backend server
   ```bash
   uvicorn src.main:app --reload --port 8008
   ```

2. Verify environment variables
   ```bash
   cat frontend/.env.local
   ```

3. Check CORS settings in FastAPI

---

### Issue 2: "Actions not triggering"

**Symptoms:**
- AI doesn't recognize actions
- Actions defined but not called

**Diagnosis:**

1. Check action descriptions are clear
2. Verify parameters are properly typed
3. Check console for errors

**Solutions:**

1. Improve action descriptions
   ```tsx
   // ❌ Vague
   description: 'Do analysis'

   // ✅ Clear
   description: 'Perform comprehensive account analysis using Zoho Data Scout, Memory Analyst, and Recommendation Author agents'
   ```

2. Ensure parameters match what AI expects
   ```tsx
   parameters: [
     {
       name: 'accountId',  // Not 'account_id' or 'id'
       type: 'string',      // Match expected type
       description: 'The account ID to analyze (format: ACC-XXXX)',
       required: true
     }
   ]
   ```

---

### Issue 3: "SSE streaming not working"

**Symptoms:**
- No real-time updates
- All data arrives at once
- Timeouts on long operations

**Diagnosis:**

```bash
# Check Content-Type header
curl -i http://localhost:3000/api/copilotkit

# Should include:
# Content-Type: text/event-stream
```

**Solutions:**

1. Verify route.ts SSE implementation
2. Check backend sends proper SSE format
3. Ensure no buffering middleware

---

### Issue 4: "TypeError: Cannot read property..."

**Symptoms:**
- Runtime errors
- Null reference errors
- Undefined properties

**Solutions:**

1. Add null checks
   ```tsx
   // ❌ Unsafe
   <p>{analysisResult.account_snapshot.name}</p>

   // ✅ Safe
   {analysisResult && (
     <p>{analysisResult.account_snapshot.name}</p>
   )}
   ```

2. Use optional chaining
   ```tsx
   <p>{analysisResult?.account_snapshot?.name ?? 'N/A'}</p>
   ```

3. Provide default values
   ```tsx
   const [status, setStatus] = useState<AgentStatus>({
     'zoho-data-scout': 'idle',
     'memory-analyst': 'idle',
     'recommendation-author': 'idle'
   });
   ```

---

## Best Practices

### 1. Action Design

✅ **DO:**
- Use clear, descriptive action names
- Write detailed descriptions (AI uses these)
- Define all required parameters
- Return structured data
- Handle errors gracefully

❌ **DON'T:**
- Use vague names like "doThing"
- Omit parameter descriptions
- Return raw strings
- Ignore errors
- Create too many similar actions

### 2. State Management

✅ **DO:**
- Share relevant context with useCopilotReadable
- Keep state updates immutable
- Use TypeScript for type safety
- Handle loading and error states
- Reset state when needed

❌ **DON'T:**
- Share entire app state
- Mutate state directly
- Ignore TypeScript errors
- Forget loading indicators
- Leave stale data in state

### 3. Error Handling

✅ **DO:**
- Use try/catch in handlers
- Display user-friendly errors
- Log errors for debugging
- Retry failed requests
- Provide fallbacks

❌ **DON'T:**
- Silently fail
- Show technical error messages to users
- Skip error logging
- Give up after first failure
- Crash the app on errors

### 4. Performance

✅ **DO:**
- Use useCallback for handlers
- Memoize expensive computations
- Implement loading states
- Cancel pending requests
- Optimize re-renders

❌ **DON'T:**
- Create handlers inline
- Recalculate on every render
- Block UI during operations
- Leave requests hanging
- Render everything always

### 5. Security

✅ **DO:**
- Validate all inputs
- Use environment variables for secrets
- Sanitize user input
- Implement authentication
- Use HTTPS in production

❌ **DON'T:**
- Trust user input blindly
- Hardcode API keys
- Allow XSS vulnerabilities
- Skip authentication
- Use HTTP in production

---

## Advanced Topics

### Custom Streaming

```tsx
useCopilotAction({
  name: 'streamAnalysis',
  description: 'Stream account analysis results',
  parameters: [{ name: 'accountId', type: 'string', required: true }],
  handler: async function* ({ accountId }) {
    // Yield intermediate results
    yield { status: 'fetching_data' };

    const data = await fetchData(accountId);
    yield { status: 'analyzing', data };

    const analysis = await analyze(data);
    yield { status: 'complete', analysis };
  }
});
```

### Multi-Agent Coordination

```tsx
useCopilotAction({
  name: 'coordinateAgents',
  description: 'Coordinate multiple backend agents',
  parameters: [
    { name: 'accountId', type: 'string', required: true },
    { name: 'agents', type: 'array', required: true }
  ],
  handler: async ({ accountId, agents }) => {
    const results = {};

    for (const agent of agents) {
      const result = await callAgent(agent, accountId);
      results[agent] = result;

      // Update readable context
      setAgentResults(results);
    }

    return { success: true, results };
  }
});
```

### Context Sharing Patterns

```tsx
// Pattern 1: Current Selection
useCopilotReadable({
  description: 'Currently selected account',
  value: selectedAccount
});

// Pattern 2: Application State
useCopilotReadable({
  description: 'Application state including filters and preferences',
  value: {
    filters: currentFilters,
    sortBy: sortPreference,
    view: viewMode
  }
});

// Pattern 3: User Context
useCopilotReadable({
  description: 'Current user and permissions',
  value: {
    userId: user.id,
    role: user.role,
    permissions: user.permissions
  }
});
```

---

## Additional Resources

### Official Documentation
- [CopilotKit Docs](https://docs.copilotkit.ai)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph)
- [Next.js Docs](https://nextjs.org/docs)

### Project Files
- `/frontend/components/copilot/` - CopilotKit components
- `/frontend/app/api/copilotkit/route.ts` - API route
- `/docs/sparc/` - SPARC documentation
- `/docs/sparc/implementation_logs/WEEK2_COMPLETION_REPORT.md` - Week 2 report

### Support
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Last Updated:** 2025-10-19
**Version:** 1.0
**Maintainer:** Development Team
