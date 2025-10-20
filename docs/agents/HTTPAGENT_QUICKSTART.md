# HttpAgent Wrapper - Quick Start Guide

Get started with HttpAgent integration in 5 minutes.

## Installation

Already installed! The HttpAgent wrapper is part of the frontend codebase.

```bash
cd frontend
npm install  # All dependencies already configured
```

## Basic Usage

### 1. Import the Hook

```typescript
import { useHttpAgent } from '@/lib/copilotkit';
```

### 2. Use in Component

```typescript
function AccountAnalysis() {
  const { query, loading, response, error } = useHttpAgent();

  const handleAnalyze = async () => {
    await query('Analyze account ACC-001');
  };

  return (
    <div>
      <button onClick={handleAnalyze} disabled={loading}>
        {loading ? 'Loading...' : 'Analyze'}
      </button>
      {error && <p>Error: {error}</p>}
      {response && <pre>{JSON.stringify(response, null, 2)}</pre>}
    </div>
  );
}
```

### 3. Run Your App

```bash
npm run dev
```

Visit `http://localhost:3000` and test!

## Common Patterns

### Pattern 1: Fetch Account Data

```typescript
import { useAccountSnapshot } from '@/lib/copilotkit';

function AccountCard({ accountId }: { accountId: string }) {
  const { snapshot, loading, fetchSnapshot } = useAccountSnapshot();

  useEffect(() => {
    fetchSnapshot(accountId);
  }, [accountId]);

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>{snapshot?.accountName}</h2>
      <p>Risk: {snapshot?.riskLevel}</p>
    </div>
  );
}
```

### Pattern 2: Get Recommendations

```typescript
import { useRecommendations } from '@/lib/copilotkit';

function RecommendationsList({ accountId }: { accountId: string }) {
  const { recommendations, fetchRecommendations } = useRecommendations();

  useEffect(() => {
    fetchRecommendations(accountId);
  }, [accountId]);

  return (
    <ul>
      {recommendations.map(rec => (
        <li key={rec.recommendationId}>
          {rec.title} - {rec.priority}
        </li>
      ))}
    </ul>
  );
}
```

### Pattern 3: Streaming Analysis

```typescript
import { useStreamingAgent } from '@/lib/copilotkit';

function StreamingAnalysis() {
  const { startStream, messages, loading } = useStreamingAgent();

  return (
    <div>
      <button onClick={() => startStream('Analyze ACC-001')}>
        Start
      </button>
      {messages.map((msg, i) => (
        <div key={i}>{msg.type}: {JSON.stringify(msg.payload)}</div>
      ))}
    </div>
  );
}
```

## Environment Setup

Create `.env.local` in `/frontend/`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TOKEN=your-token-here
```

## Available Hooks

| Hook | Purpose | Returns |
|------|---------|---------|
| `useHttpAgent` | General queries | `{ query, loading, response, error }` |
| `useStreamingAgent` | Streaming responses | `{ startStream, messages, loading }` |
| `useAccountSnapshot` | Fetch account data | `{ snapshot, loading, fetchSnapshot }` |
| `useRecommendations` | Get recommendations | `{ recommendations, loading }` |
| `useAgentStatus` | Track agent status | `{ agentStatus, updateStatus }` |
| `usePolling` | Poll for updates | `{ data, isPolling, stopPolling }` |

## Agent Types

When querying, specify the agent:

```typescript
await query('your query', {
  agent: 'orchestrator',  // or 'zoho-scout', 'memory-analyst', etc.
  context: { /* additional data */ }
});
```

Available agents:
- `orchestrator` - Coordinates all agents
- `zoho-data-scout` - Fetches Zoho CRM data
- `memory-analyst` - Analyzes historical patterns
- `recommendation-author` - Generates recommendations

## Error Handling

```typescript
const { query, error } = useHttpAgent();

try {
  await query('analyze account');
} catch (err) {
  // Error is automatically caught and set in error state
  console.error('Query failed:', error);
}

// Display errors
{error && <div className="error">{error}</div>}
```

## TypeScript Support

Full type safety included:

```typescript
import type { AccountSnapshot, Recommendation } from '@/lib/copilotkit';

const { query } = useHttpAgent<AccountSnapshot>();
await query('fetch account');
// response is typed as AccountSnapshot
```

## Testing

```bash
# Type check
npm run typecheck

# Lint
npm run lint

# Build
npm run build
```

## Next Steps

1. Check `/frontend/lib/copilotkit/examples.tsx` for complete examples
2. Read `/frontend/lib/copilotkit/README.md` for full documentation
3. Explore A2A workflows in `/frontend/lib/copilotkit/A2AMiddleware.ts`

## Troubleshooting

**Can't find module '@/lib/copilotkit'**
- Ensure you're in the frontend directory
- Check `tsconfig.json` has path mapping configured

**Request timeout**
- Check backend is running on `http://localhost:8000`
- Increase timeout in config if needed

**CORS errors**
- Ensure backend CORS is configured for `http://localhost:3000`

## Support

- Full documentation: `/frontend/lib/copilotkit/README.md`
- Integration report: `/docs/agents/HTTPAGENT_WRAPPER_INTEGRATION.md`
- Examples: `/frontend/lib/copilotkit/examples.tsx`

Happy coding! 🚀
