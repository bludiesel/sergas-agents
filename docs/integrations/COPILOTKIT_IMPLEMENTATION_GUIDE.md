# CopilotKit Integration Implementation Guide

## Phase 1: Immediate Fixes (Week 1)

### 1.1 Fix CopilotKit Route Issues

**Current Issues in `/api/copilotkit/route.ts`:**
- Limited GraphQL operation support
- No streaming for large responses
- Basic error handling
- Missing authentication integration

**Solutions:**

```typescript
// Enhanced route.ts with streaming support
import { NextRequest, NextResponse } from 'next/server';
import { streamText } from 'ai';

// Add comprehensive operation handling
const SUPPORTED_OPERATIONS = [
  'loadAgentState',
  'generateCopilotResponse',
  'executeAgentAction',
  'streamAgentResponse'
];

async function handleStreamingResponse(request: NextRequest) {
  const { messages, agent, context } = await request.json();

  // Enable streaming for long-running agent responses
  const stream = await streamText({
    model: yourGLMModel,
    messages,
    temperature: 0.3,
    onFinish: async (result) => {
      // Log completion and store results
      await storeConversationTurn(messages, result);
    }
  });

  return new NextResponse(stream.toAIStreamResponse());
}
```

### 1.2 Enhance Error Handling

```typescript
// Add comprehensive error handling
class CopilotError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message);
  }
}

function handleCopilotError(error: unknown) {
  if (error instanceof CopilotError) {
    return NextResponse.json({
      errors: [{
        message: error.message,
        code: error.code,
        extensions: { statusCode: error.statusCode }
      }]
    }, { status: error.statusCode });
  }

  // Fallback for unknown errors
  return NextResponse.json({
    errors: [{ message: 'Internal server error' }]
  }, { status: 500 });
}
```

### 1.3 Fix Authentication Integration

```typescript
// Add proper JWT token handling
async function authenticateRequest(request: NextRequest) {
  const authHeader = request.headers.get('authorization');

  if (!authHeader?.startsWith('Bearer ')) {
    throw new CopilotError('Missing or invalid authorization', 'UNAUTHORIZED', 401);
  }

  const token = authHeader.slice(7);
  try {
    const payload = await verifyJWT(token);
    return payload;
  } catch (error) {
    throw new CopilotError('Invalid or expired token', 'INVALID_TOKEN', 401);
  }
}
```

## Phase 2: Complete Frontend Integration

### 2.1 Fix useCopilotAction Implementations

**Issues in AccountAnalysisAgent.tsx:**
- Missing error boundaries
- Incomplete action handlers
- No proper loading states

**Solutions:**

```typescript
// Enhanced action handler with proper error handling
useCopilotAction({
  name: 'analyzeAccount',
  description: 'Perform comprehensive account analysis...',
  parameters: [/* ... */],
  handler: async ({ accountId }) => {
    try {
      // Add validation
      if (!accountId || typeof accountId !== 'string') {
        throw new Error('Account ID is required and must be a string');
      }

      // Add timeout handling
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Analysis timeout')), 60000)
      );

      const analysisPromise = handleAnalyzeAccount(accountId);
      const result = await Promise.race([analysisPromise, timeoutPromise]);

      return {
        success: true,
        message: `Successfully analyzed account ${accountId}`,
        data: sanitizeAnalysisResult(result),
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('[CopilotKit Action] analyzeAccount error:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        error_code: error.name || 'ANALYSIS_ERROR',
        timestamp: new Date().toISOString()
      };
    }
  },
});
```

### 2.2 Add Real-time State Synchronization

```typescript
// Add WebSocket integration for real-time updates
function useRealTimeAgentUpdates(runtimeUrl: string) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');

  useEffect(() => {
    const websocket = new WebSocket(`${runtimeUrl.replace('http', 'ws')}/agent-updates`);

    websocket.onopen = () => {
      setConnectionStatus('connected');
      console.log('Agent updates WebSocket connected');
    };

    websocket.onmessage = (event) => {
      const update = JSON.parse(event.data);

      // Update appropriate agent state
      if (update.type === 'agent_status') {
        setAgentStatus(prev => ({ ...prev, [update.agent]: update.status }));
      } else if (update.type === 'analysis_progress') {
        setAnalysisProgress(update.progress);
      }
    };

    websocket.onclose = () => {
      setConnectionStatus('disconnected');
      // Auto-reconnect after 3 seconds
      setTimeout(() => setConnectionStatus('connecting'), 3000);
    };

    setWs(websocket);

    return () => websocket.close();
  }, [runtimeUrl]);

  return { ws, connectionStatus };
}
```

### 2.3 Implement Proper Loading States

```typescript
// Enhanced loading state management
function useLoadingStates() {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [globalLoading, setGlobalLoading] = useState(false);

  const setLoading = (key: string, isLoading: boolean) => {
    setLoadingStates(prev => ({ ...prev, [key]: isLoading }));
    setGlobalLoading(Object.values({ ...loadingStates, [key]: isLoading }).some(Boolean));
  };

  return { loadingStates, globalLoading, setLoading };
}
```

## Phase 3: Backend Improvements

### 3.1 Complete Python Model Implementations

```python
# Complete account.py model
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class Account(BaseModel):
    id: str = Field(..., description="Unique account identifier")
    name: str = Field(..., min_length=1, max_length=200)
    owner: str = Field(..., min_length=1, max_length=100)
    status: AccountStatus = Field(default=AccountStatus.ACTIVE)
    risk_level: str = Field(default="unknown", regex="^(low|medium|high|critical|unknown)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AccountMetrics(BaseModel):
    account_id: str
    total_deals: int = Field(default=0, ge=0)
    total_value: float = Field(default=0.0, ge=0)
    engagement_score: float = Field(default=0.0, ge=0, le=100)
    last_contact_date: Optional[datetime] = None
    priority_score: float = Field(default=0.0, ge=0)
    needs_review: bool = Field(default=False)

class AccountSnapshot(BaseModel):
    account_id: str
    account_name: str
    owner_name: str
    status: AccountStatus
    risk_level: str
    priority_score: float = Field(ge=0)
    needs_review: bool
    deal_count: int = Field(ge=0)
    total_value: float = Field(ge=0)
    last_contact_date: Optional[datetime] = None
    engagement_score: Optional[float] = Field(ge=0, le=100)
    metrics: AccountMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

```python
# Complete recommendation.py model
class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Recommendation(BaseModel):
    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    account_id: str
    category: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    confidence_score: float = Field(..., ge=0, le=100)
    priority: RecommendationPriority
    next_steps: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    status: str = Field(default="pending", regex="^(pending|approved|rejected|implemented)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class AnalysisResult(BaseModel):
    account_snapshot: AccountSnapshot
    risk_signals: List[RiskSignal] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None
    agent_versions: Dict[str, str] = Field(default_factory=dict)
```

### 3.2 Add Comprehensive Testing

```python
# tests/test_copilotkit_integration.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

class TestCopilotKitIntegration:

    @pytest.fixture
    def client(self):
        from src.main import app
        return TestClient(app)

    def test_generate_copilot_response_success(self, client):
        """Test successful copilot response generation"""
        request_data = {
            "operationName": "generateCopilotResponse",
            "variables": {
                "messages": [
                    {"role": "user", "content": "Analyze account ACC-001"}
                ]
            }
        }

        with patch('src.agents.orchestrator.analyze_account') as mock_analyze:
            mock_analyze.return_value = {
                "account_snapshot": {
                    "account_id": "ACC-001",
                    "account_name": "Test Account",
                    "risk_level": "low"
                },
                "recommendations": [],
                "risk_signals": []
            }

            response = client.post("/api/copilotkit", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "generateCopilotResponse" in data["data"]

    def test_load_agent_state_success(self, client):
        """Test agent state loading"""
        request_data = {
            "operationName": "loadAgentState",
            "variables": {
                "data": {
                    "threadId": "test-thread-id"
                }
            }
        }

        response = client.post("/api/copilotkit", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "loadAgentState" in data["data"]
        assert "threadId" in data["data"]["loadAgentState"]

    def test_error_handling(self, client):
        """Test error handling for invalid requests"""
        response = client.post("/api/copilotkit", json={})

        assert response.status_code == 400
        data = response.json()
        assert "errors" in data
        assert len(data["errors"]) > 0
```

## Phase 4: Performance and UX Optimization

### 4.1 Add Optimistic Updates

```typescript
// Optimistic updates for better UX
function useOptimisticUpdates<T>(initialValue: T) {
  const [actualValue, setActualValue] = useState<T>(initialValue);
  const [optimisticValue, setOptimisticValue] = useState<T | null>(null);

  const setValue = async (newValue: T, updateFunction: () => Promise<T>) => {
    // Show optimistic update immediately
    setOptimisticValue(newValue);

    try {
      const result = await updateFunction();
      setActualValue(result);
      setOptimisticValue(null);
    } catch (error) {
      // Revert on error
      setOptimisticValue(null);
      throw error;
    }
  };

  return {
    value: optimisticValue ?? actualValue,
    setValue,
    isOptimistic: optimisticValue !== null
  };
}
```

### 4.2 Bundle Optimization

```javascript
// next.config.js optimizations
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: ['@copilotkit/react-core', 'lucide-react']
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
```

## Implementation Checklist

### Week 1: Foundation
- [ ] Fix CopilotKit route.ts with proper error handling
- [ ] Add authentication integration
- [ ] Implement streaming responses
- [ ] Fix useCopilotAction implementations
- [ ] Add comprehensive error boundaries

### Week 2: Features
- [ ] Complete Python model implementations
- [ ] Add real-time state synchronization
- [ ] Implement proper loading states
- [ ] Add WebSocket integration
- [ ] Complete CoAgent state management

### Week 3: Polish
- [ ] Add comprehensive testing suite
- [ ] Implement optimistic updates
- [ ] Add performance monitoring
- [ ] Optimize bundle size
- [ ] Add accessibility improvements

### Week 4: Production
- [ ] Add monitoring and logging
- [ ] Implement caching strategies
- [ ] Add health checks
- [ ] Deploy to staging environment
- [ ] Performance testing and optimization

## Success Metrics

### Technical Metrics
- API response time < 2 seconds
- WebSocket connection success rate > 99%
- Error rate < 1%
- Bundle size < 1MB

### User Experience Metrics
- Page load time < 3 seconds
- Time to interactive < 5 seconds
- Core Web Vitals scores all green
- User satisfaction score > 4.5/5

### Business Metrics
- Account analysis completion rate > 95%
- Recommendation adoption rate > 80%
- Support ticket reduction > 30%
- User engagement increase > 50%

This phased approach provides immediate value while building toward a robust, scalable solution that leverages the strengths of both your existing GLM-4.6 agents and CopilotKit's powerful frontend capabilities.