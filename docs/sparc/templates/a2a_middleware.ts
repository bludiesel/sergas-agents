/**
 * Agent-to-Agent (a2a) Middleware for CopilotKit
 *
 * The a2aMiddlewareAgent enables communication between multiple AI agents,
 * allowing them to collaborate on complex tasks.
 *
 * Key Features:
 * - Inter-agent communication
 * - Message routing between agents
 * - State sharing across agents
 * - Coordinated multi-agent workflows
 *
 * Use Cases:
 * - Orchestrator coordinates specialist agents
 * - Data Scout passes results to Memory Analyst
 * - Memory Analyst informs Recommendation Author
 * - Approval workflows across agents
 *
 * Architecture:
 *   Frontend (CopilotKit)
 *        ↓
 *   a2aMiddlewareAgent (coordinator)
 *        ↓
 *   ┌─────────┬─────────────┬──────────────────┐
 *   ↓         ↓             ↓                  ↓
 * Orchestrator  ZohoScout  MemoryAnalyst  RecommendationAuthor
 */

import {
  CopilotRuntime,
  a2aMiddlewareAgent,
  HttpAgent,
} from '@copilotkit/runtime';

// ============================================================================
// Agent Definitions
// ============================================================================

/**
 * Define individual agents for the a2a middleware
 */
const agents = {
  // Orchestrator: Main coordinator
  orchestrator: new HttpAgent({
    url: process.env.BACKEND_URL || 'http://localhost:8000',
    name: 'orchestrator',
    description: 'Coordinates all specialist agents for complete account analysis',
    endpoint: '/api/orchestrator',
  }),

  // Zoho Data Scout: CRM data retrieval
  zohoScout: new HttpAgent({
    url: process.env.BACKEND_URL || 'http://localhost:8000',
    name: 'zoho-scout',
    description: 'Fetches and analyzes Zoho CRM account data',
    endpoint: '/api/zoho-scout',
  }),

  // Memory Analyst: Historical context
  memoryAnalyst: new HttpAgent({
    url: process.env.BACKEND_URL || 'http://localhost:8000',
    name: 'memory-analyst',
    description: 'Retrieves historical context and identifies patterns',
    endpoint: '/api/memory-analyst',
  }),

  // Recommendation Author: Action generation
  recommendationAuthor: new HttpAgent({
    url: process.env.BACKEND_URL || 'http://localhost:8000',
    name: 'recommendation-author',
    description: 'Generates actionable recommendations based on analysis',
    endpoint: '/api/recommendation-author',
  }),
};

// ============================================================================
// a2a Middleware Configuration
// ============================================================================

/**
 * Create the a2aMiddlewareAgent that coordinates all agents
 */
export function createA2AMiddleware() {
  return a2aMiddlewareAgent({
    // Agent registry
    agents: Object.values(agents),

    // Routing strategy
    router: async (context) => {
      const { messages, currentAgent } = context;
      const lastMessage = messages[messages.length - 1];

      // Extract user intent
      const intent = await detectIntent(lastMessage.content);

      // Route to appropriate agent based on intent
      switch (intent) {
        case 'analyze_account':
          // Full analysis: orchestrator coordinates everything
          return 'orchestrator';

        case 'fetch_account':
          // Quick data fetch: direct to Zoho Scout
          return 'zoho-scout';

        case 'get_history':
          // Historical context: direct to Memory Analyst
          return 'memory-analyst';

        case 'generate_recommendations':
          // Recommendations: direct to Recommendation Author
          return 'recommendation-author';

        default:
          // Default to orchestrator for complex queries
          return 'orchestrator';
      }
    },

    // Message transformation between agents
    transformMessage: async (message, fromAgent, toAgent) => {
      // Transform message format when passing between agents
      return {
        ...message,
        metadata: {
          ...message.metadata,
          source_agent: fromAgent,
          target_agent: toAgent,
          timestamp: new Date().toISOString(),
        },
      };
    },

    // State management across agents
    sharedState: {
      // Shared context that all agents can access
      session_id: generateSessionId(),
      account_id: null,
      workflow_status: 'initialized',
    },

    // Agent communication protocol
    protocol: {
      // How agents signal completion
      completion: {
        field: 'status',
        value: 'completed',
      },

      // How agents signal errors
      error: {
        field: 'status',
        value: 'error',
      },

      // How agents request handoff to another agent
      handoff: {
        field: 'next_agent',
      },
    },
  });
}

// ============================================================================
// Agent Workflow Patterns
// ============================================================================

/**
 * Pattern 1: Sequential Workflow
 *
 * Orchestrator → ZohoScout → MemoryAnalyst → RecommendationAuthor
 */
export function createSequentialWorkflow() {
  return a2aMiddlewareAgent({
    agents: Object.values(agents),

    workflow: async (context) => {
      const steps = [
        { agent: 'zoho-scout', task: 'Fetch account data' },
        { agent: 'memory-analyst', task: 'Analyze historical context' },
        { agent: 'recommendation-author', task: 'Generate recommendations' },
      ];

      // Execute steps sequentially
      for (const step of steps) {
        const result = await context.executeAgent(step.agent, {
          task: step.task,
          previousResults: context.results,
        });

        // Check for errors
        if (result.error) {
          throw new Error(`${step.agent} failed: ${result.error}`);
        }

        // Store result for next agent
        context.results[step.agent] = result;
      }

      return context.results;
    },
  });
}

/**
 * Pattern 2: Parallel Workflow
 *
 * Execute multiple agents concurrently:
 * ZohoScout + MemoryAnalyst (parallel) → RecommendationAuthor
 */
export function createParallelWorkflow() {
  return a2aMiddlewareAgent({
    agents: Object.values(agents),

    workflow: async (context) => {
      // Execute ZohoScout and MemoryAnalyst in parallel
      const [zohoResult, memoryResult] = await Promise.all([
        context.executeAgent('zoho-scout', { task: 'Fetch account data' }),
        context.executeAgent('memory-analyst', {
          task: 'Analyze historical context',
        }),
      ]);

      // Check results
      if (zohoResult.error || memoryResult.error) {
        throw new Error('Parallel execution failed');
      }

      // Pass combined results to RecommendationAuthor
      const recommendations = await context.executeAgent('recommendation-author', {
        task: 'Generate recommendations',
        zoho_data: zohoResult,
        memory_data: memoryResult,
      });

      return {
        zoho: zohoResult,
        memory: memoryResult,
        recommendations,
      };
    },
  });
}

/**
 * Pattern 3: Conditional Workflow
 *
 * Dynamic routing based on results:
 * ZohoScout → (if high risk) → MemoryAnalyst → RecommendationAuthor
 *          → (if low risk) → Done
 */
export function createConditionalWorkflow() {
  return a2aMiddlewareAgent({
    agents: Object.values(agents),

    workflow: async (context) => {
      // Step 1: Fetch account data
      const zohoResult = await context.executeAgent('zoho-scout', {
        task: 'Fetch account data',
      });

      // Check risk level
      const riskLevel = zohoResult.data?.risk_level;

      if (riskLevel === 'high' || riskLevel === 'critical') {
        // High risk: full analysis required
        const memoryResult = await context.executeAgent('memory-analyst', {
          task: 'Analyze historical context',
          account_data: zohoResult,
        });

        const recommendations = await context.executeAgent(
          'recommendation-author',
          {
            task: 'Generate recommendations',
            zoho_data: zohoResult,
            memory_data: memoryResult,
          }
        );

        return {
          risk_level: riskLevel,
          analysis_depth: 'full',
          zoho: zohoResult,
          memory: memoryResult,
          recommendations,
        };
      } else {
        // Low risk: basic response
        return {
          risk_level: riskLevel,
          analysis_depth: 'basic',
          zoho: zohoResult,
          message: 'Account appears healthy, no further analysis needed',
        };
      }
    },
  });
}

// ============================================================================
// Next.js API Route Implementation
// ============================================================================

/**
 * Complete API route with a2a middleware
 *
 * File: app/api/copilotkit-a2a/route.ts
 */
export async function a2aApiRoute(request: Request) {
  try {
    // Create runtime
    const runtime = new CopilotRuntime();

    // Setup a2a middleware
    const middleware = createA2AMiddleware();
    runtime.agent(middleware);

    // Process request
    const { messages, workflow = 'sequential' } = await request.json();

    // Select workflow type
    let workflowMiddleware;
    switch (workflow) {
      case 'parallel':
        workflowMiddleware = createParallelWorkflow();
        break;
      case 'conditional':
        workflowMiddleware = createConditionalWorkflow();
        break;
      default:
        workflowMiddleware = createSequentialWorkflow();
    }

    // Execute workflow
    const response = await runtime.process({
      messages,
      agent: workflowMiddleware,
    });

    return Response.json(response);
  } catch (error) {
    console.error('a2a middleware error:', error);
    return Response.json(
      {
        error: 'Workflow execution failed',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

// ============================================================================
// Advanced: Agent Communication Patterns
// ============================================================================

/**
 * Pattern: Agent Handoff
 *
 * One agent can explicitly hand off to another agent.
 */
export function createHandoffPattern() {
  return a2aMiddlewareAgent({
    agents: Object.values(agents),

    messageHandler: async (message, context) => {
      // Check if current agent is requesting handoff
      if (message.next_agent) {
        // Hand off to specified agent
        return {
          agent: message.next_agent,
          message: message.handoff_message,
          context: message.handoff_context,
        };
      }

      // Normal processing
      return null;
    },
  });
}

/**
 * Pattern: Agent Collaboration
 *
 * Multiple agents work together on the same task.
 */
export function createCollaborationPattern() {
  return a2aMiddlewareAgent({
    agents: Object.values(agents),

    collaboration: {
      // Agents can contribute to shared workspace
      workspace: new Map(),

      // Agent contributions
      contribute: async (agentName, contribution) => {
        const workspace = this.collaboration.workspace;
        workspace.set(agentName, contribution);
      },

      // Synthesize final result
      synthesize: async () => {
        const workspace = this.collaboration.workspace;
        return {
          zoho_data: workspace.get('zoho-scout'),
          historical_context: workspace.get('memory-analyst'),
          recommendations: workspace.get('recommendation-author'),
        };
      },
    },
  });
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Detect user intent from message
 */
async function detectIntent(message: string): Promise<string> {
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes('analyze')) {
    return 'analyze_account';
  } else if (lowerMessage.includes('fetch') || lowerMessage.includes('get account')) {
    return 'fetch_account';
  } else if (lowerMessage.includes('history') || lowerMessage.includes('past')) {
    return 'get_history';
  } else if (lowerMessage.includes('recommend')) {
    return 'generate_recommendations';
  }

  return 'analyze_account'; // default
}

/**
 * Generate unique session ID
 */
function generateSessionId(): string {
  return `a2a_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================================================
// Usage Example in Frontend
// ============================================================================

/**
 * Frontend component using a2a middleware
 */
export const a2aFrontendExample = `
import { CopilotKit } from '@copilotkit/react-core';

function App() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit-a2a"
      // Specify workflow type
      runtimeConfig={{
        workflow: 'conditional' // or 'sequential', 'parallel'
      }}
    >
      <YourApp />
    </CopilotKit>
  );
}
`;

// ============================================================================
// Monitoring and Debugging
// ============================================================================

/**
 * Add logging to track agent communication
 */
export function createLoggingMiddleware() {
  return a2aMiddlewareAgent({
    agents: Object.values(agents),

    onAgentStart: (agentName, input) => {
      console.log(`[a2a] Starting ${agentName}`, input);
    },

    onAgentComplete: (agentName, output) => {
      console.log(`[a2a] Completed ${agentName}`, output);
    },

    onAgentError: (agentName, error) => {
      console.error(`[a2a] Error in ${agentName}`, error);
    },

    onHandoff: (fromAgent, toAgent, context) => {
      console.log(`[a2a] Handoff: ${fromAgent} → ${toAgent}`, context);
    },
  });
}
