/**
 * HttpAgent Wrapper for CopilotKit
 *
 * HttpAgent is an alternative to LangGraph for simpler agent patterns.
 * Use this when you don't need complex state management or multi-step workflows.
 *
 * Key Concepts:
 * - Direct HTTP calls to backend agents
 * - Simpler than LangGraph for basic use cases
 * - Works with any backend (Python, Node, etc.)
 * - Automatic streaming support
 *
 * Use Cases:
 * - Single-agent queries
 * - Simple data retrieval
 * - Stateless operations
 * - Quick prototyping
 *
 * When to use HttpAgent vs LangGraph:
 * - HttpAgent: Simple, stateless, single-step operations
 * - LangGraph: Complex workflows, state management, multi-step processes
 */

import { CopilotRuntime, HttpAgent } from '@copilotkit/runtime';

// ============================================================================
// HttpAgent Configuration
// ============================================================================

/**
 * Create an HttpAgent that communicates with the FastAPI backend.
 *
 * This agent makes direct HTTP calls to your backend endpoints without
 * the complexity of LangGraph state management.
 */
export function createHttpAgent() {
  return new HttpAgent({
    // Backend endpoint
    url: process.env.BACKEND_URL || 'http://localhost:8000',

    // Name for identification
    name: 'sergas-account-manager',

    // Description (used by CopilotKit for agent selection)
    description: 'Account analysis and management agent',

    // Custom headers (authentication, etc.)
    headers: {
      'Content-Type': 'application/json',
      // Add authentication if needed
      // 'Authorization': `Bearer ${process.env.API_KEY}`,
    },

    // Request transformation
    transformRequest: async (message: string) => {
      // Transform CopilotKit message format to your backend format
      return {
        query: message,
        session_id: generateSessionId(),
        agent: 'orchestrator',
      };
    },

    // Response transformation
    transformResponse: async (response: any) => {
      // Transform backend response to CopilotKit format
      if (response.error) {
        throw new Error(response.error);
      }

      return {
        content: response.message || JSON.stringify(response),
        data: response,
      };
    },
  });
}

/**
 * Create a specialized HttpAgent for Zoho data fetching.
 */
export function createZohoHttpAgent() {
  return new HttpAgent({
    url: process.env.BACKEND_URL || 'http://localhost:8000',
    name: 'zoho-data-scout',
    description: 'Fetch and analyze Zoho CRM account data',

    // Endpoint-specific configuration
    endpoint: '/api/accounts',

    transformRequest: async (message: string) => {
      // Extract account ID from message
      const accountIdMatch = message.match(/ACC-\d+/);
      const accountId = accountIdMatch ? accountIdMatch[0] : null;

      if (!accountId) {
        throw new Error('Please provide an account ID (format: ACC-XXX)');
      }

      return {
        account_id: accountId,
        action: 'fetch_snapshot',
      };
    },

    transformResponse: async (response: any) => {
      return {
        content: formatAccountSnapshot(response),
        data: response,
      };
    },
  });
}

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example 1: Basic HttpAgent Setup
 *
 * Use this in your Next.js API route:
 */
export async function basicHttpAgentExample() {
  const runtime = new CopilotRuntime();

  // Create and register agent
  const agent = createHttpAgent();
  runtime.agent(agent);

  // Handle incoming requests
  // This would typically be in your API route handler
  const response = await runtime.process({
    messages: [
      {
        role: 'user',
        content: 'Analyze account ACC-001',
      },
    ],
  });

  return response;
}

/**
 * Example 2: Multiple HttpAgents
 *
 * Register multiple agents for different tasks:
 */
export async function multipleHttpAgentsExample() {
  const runtime = new CopilotRuntime();

  // Register orchestrator agent
  runtime.agent(createHttpAgent());

  // Register Zoho-specific agent
  runtime.agent(createZohoHttpAgent());

  // CopilotKit will automatically choose the right agent based on context
}

/**
 * Example 3: HttpAgent with Streaming
 *
 * Enable real-time streaming responses:
 */
export function createStreamingHttpAgent() {
  return new HttpAgent({
    url: process.env.BACKEND_URL || 'http://localhost:8000',
    name: 'streaming-agent',
    description: 'Agent with streaming support',

    // Enable streaming
    stream: true,

    // Stream handler
    streamHandler: async function* (response: Response) {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // Parse SSE format
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              yield parsed;
            } catch {
              // Ignore parsing errors
            }
          }
        }
      }
    },
  });
}

// ============================================================================
// Next.js API Route Example
// ============================================================================

/**
 * Example Next.js API route using HttpAgent
 *
 * File: app/api/copilotkit-http/route.ts
 */
export async function httpAgentApiRoute(request: Request) {
  const runtime = new CopilotRuntime();

  // Setup agents
  runtime.agent(createHttpAgent());
  runtime.agent(createZohoHttpAgent());

  // Process request
  const { messages } = await request.json();

  const response = await runtime.process({
    messages,
    // Optional: specify agent
    // agent: 'zoho-data-scout',
  });

  return Response.json(response);
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generate a unique session ID
 */
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Format account snapshot for display
 */
function formatAccountSnapshot(snapshot: any): string {
  if (!snapshot) return 'No account data available';

  const parts = [
    `Account: ${snapshot.account_name}`,
    `Owner: ${snapshot.owner_name}`,
    `Status: ${snapshot.status}`,
    `Risk Level: ${snapshot.risk_level}`,
    `Priority Score: ${snapshot.priority_score}`,
  ];

  if (snapshot.risk_signals?.length > 0) {
    parts.push(`\nRisk Signals (${snapshot.risk_signals.length}):`);
    snapshot.risk_signals.forEach((signal: any, i: number) => {
      parts.push(`${i + 1}. [${signal.severity}] ${signal.description}`);
    });
  }

  return parts.join('\n');
}

// ============================================================================
// Complete API Route Template
// ============================================================================

/**
 * Complete Next.js API route with HttpAgent
 *
 * Copy this to: app/api/copilotkit-http/route.ts
 */

/*
import { NextRequest } from 'next/server';
import { CopilotRuntime, HttpAgent } from '@copilotkit/runtime';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const runtime = new CopilotRuntime();

  // Create HttpAgent
  const agent = new HttpAgent({
    url: BACKEND_URL,
    name: 'account-manager',
    description: 'Account analysis and management',

    transformRequest: async (message: string) => {
      return {
        query: message,
        session_id: `session_${Date.now()}`,
      };
    },

    transformResponse: async (response: any) => {
      return {
        content: response.message || JSON.stringify(response),
        data: response,
      };
    },
  });

  // Register agent
  runtime.agent(agent);

  // Process request
  const { messages } = await request.json();

  try {
    const response = await runtime.process({ messages });
    return Response.json(response);
  } catch (error) {
    console.error('HttpAgent error:', error);
    return Response.json(
      { error: 'Processing failed' },
      { status: 500 }
    );
  }
}
*/

// ============================================================================
// Comparison: HttpAgent vs LangGraph
// ============================================================================

/**
 * WHEN TO USE HTTPAGENT:
 *
 * ✅ Simple request-response patterns
 * ✅ Stateless operations
 * ✅ Direct API calls
 * ✅ Quick prototyping
 * ✅ Minimal setup required
 *
 * Example use cases:
 * - Fetch account data
 * - Search operations
 * - Data retrieval
 * - Simple analysis
 *
 *
 * WHEN TO USE LANGGRAPH:
 *
 * ✅ Complex multi-step workflows
 * ✅ State management across steps
 * ✅ Conditional branching
 * ✅ Agent coordination
 * ✅ Long-running processes
 *
 * Example use cases:
 * - Full account analysis (Zoho → Memory → Recommendations)
 * - Approval workflows
 * - Multi-agent orchestration
 * - Stateful conversations
 */

export const comparisonExamples = {
  // Simple case: HttpAgent is sufficient
  httpAgentUseCase: `
    User: "Show me account ACC-001"
    → HttpAgent makes single API call
    → Returns account data
    → Done
  `,

  // Complex case: LangGraph is better
  langGraphUseCase: `
    User: "Analyze account ACC-001 and generate recommendations"
    → LangGraph Step 1: Fetch from Zoho (ZohoDataScout)
    → LangGraph Step 2: Get history (MemoryAnalyst)
    → LangGraph Step 3: Generate recommendations (RecommendationAuthor)
    → LangGraph Step 4: Request approval
    → State maintained throughout
    → Done
  `,
};
