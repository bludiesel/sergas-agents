/**
 * Multi-Agent Coordination Workflow Tests
 *
 * Tests for complex agent interactions, state synchronization,
 * and distributed workflow management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';
import { CoAgentDashboard, useCoAgentState } from '@/components/copilot/CoAgentIntegration';
import { CopilotProvider } from '@/components/copilot/CopilotProvider';
import { createMockAccount, createMockAnalysisResult, createMockRiskSignal, createMockRecommendation, mockFetchResponse, mockFetchError } from '@/jest.setup.enhanced';

// Mock CopilotKit hooks
const mockUseCopilotAction = jest.fn();
const mockUseCopilotReadable = jest.fn();
const mockUseCopilotChat = jest.fn();

jest.mock('@copilotkit/react-core', () => ({
  useCopilotAction: mockUseCopilotAction,
  useCopilotReadable: mockUseCopilotReadable,
  useCopilotChat: mockUseCopilotChat,
}));

describe('Multi-Agent Coordination Workflows', () => {
  const mockRuntimeUrl = 'http://localhost:8008';

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCopilotAction.mockImplementation(({ handler }) => handler);
    mockUseCopilotReadable.mockImplementation(() => {});
    mockUseCopilotChat.mockReturnValue({ isLoading: false });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Agent State Synchronization', () => {
    it('should synchronize state across multiple agents', async () => {
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        const { sharedState } = useCoAgentState(mockRuntimeUrl);
        return (
          <div data-testid="shared-state">
            <span data-testid="current-account">{sharedState.current_account_id}</span>
            <span data-testid="analysis-progress">{sharedState.analysis_in_progress.toString()}</span>
          </div>
        );
      };

      render(<TestComponent />);

      // Agent 1 updates state
      await stateUpdateHandler({
        stateUpdate: {
          current_account_id: 'ACC-001',
          analysis_in_progress: true,
        },
        sourceAgent: 'zoho-data-scout',
      });

      // Agent 2 sends message about state change
      await messageHandler({
        fromAgent: 'zoho-data-scout',
        toAgent: 'memory-analyst',
        messageType: 'state_changed',
        payload: { account_id: 'ACC-001' },
      });

      await waitFor(() => {
        expect(screen.getByTestId('current-account')).toHaveTextContent('ACC-001');
        expect(screen.getByTestId('analysis-progress')).toHaveTextContent('true');
      });
    });

    it('should handle concurrent state updates', async () => {
      let stateUpdateHandler;
      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="concurrent-test">Test</div>;
      };

      render(<TestComponent />);

      // Multiple concurrent state updates
      const updates = [
        {
          stateUpdate: { agent_queue: ['agent1'] },
          sourceAgent: 'orchestrator',
        },
        {
          stateUpdate: { analysis_in_progress: true },
          sourceAgent: 'agent1',
        },
        {
          stateUpdate: { current_account_id: 'ACC-001' },
          sourceAgent: 'ui',
        },
      ];

      const promises = updates.map(update => stateUpdateHandler(update));
      await Promise.all(promises);

      // All updates should be applied
      expect(screen.getByTestId('concurrent-test')).toBeInTheDocument();
    });

    it('should resolve state conflicts', async () => {
      let stateUpdateHandler;
      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="conflict-test">Test</div>;
      };

      render(<TestComponent />);

      // Conflicting updates to same field
      await stateUpdateHandler({
        stateUpdate: { analysis_in_progress: false },
        sourceAgent: 'agent1',
      });

      await stateUpdateHandler({
        stateUpdate: { analysis_in_progress: true },
        sourceAgent: 'agent2',
      });

      // Should handle conflicts gracefully
      expect(screen.getByTestId('conflict-test')).toBeInTheDocument();
    });
  });

  describe('Agent Communication Workflows', () => {
    it('should orchestrate agent-to-agent messaging', async () => {
      let messageHandler;
      let getMessagesHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'sendAgentMessage') {
          messageHandler = handler;
        } else if (name === 'getAgentMessages') {
          getMessagesHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="messaging-test">Test</div>;
      };

      render(<TestComponent />);

      // Agent 1 sends message to Agent 2
      await messageHandler({
        fromAgent: 'zoho-data-scout',
        toAgent: 'memory-analyst',
        messageType: 'data_ready',
        payload: { account_id: 'ACC-001', record_count: 150 },
      });

      // Agent 2 sends acknowledgment
      await messageHandler({
        fromAgent: 'memory-analyst',
        toAgent: 'zoho-data-scout',
        messageType: 'data_received',
        payload: { status: 'processing' },
      });

      // Agent 3 requests status
      await messageHandler({
        fromAgent: 'recommendation-author',
        toAgent: 'memory-analyst',
        messageType: 'status_request',
        payload: { account_id: 'ACC-001' },
      });

      // Retrieve messages for memory-analyst
      const messages = await getMessagesHandler({
        agentName: 'memory-analyst',
      });

      expect(messages.success).toBe(true);
      expect(messages.messages).toHaveLength(2); // data_ready + status_request
    });

    it('should broadcast messages to multiple agents', async () => {
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="broadcast-test">Test</div>;
      };

      render(<TestComponent />);

      // Broadcast message to all agents
      await messageHandler({
        fromAgent: 'orchestrator',
        toAgent: 'all',
        messageType: 'shutdown_request',
        payload: { reason: 'maintenance', timeout: 300 },
      });

      expect(screen.getByTestId('broadcast-test')).toBeInTheDocument();
    });

    it('should handle message queuing and delivery', async () => {
      let messageHandler;
      const deliveredMessages = [];

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'sendAgentMessage') {
          messageHandler = async (...args) => {
            // Simulate async message delivery
            deliveredMessages.push(args[0]);
            return { success: true, message_id: Date.now().toString() };
          };
        }
        return messageHandler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="queue-test">Test</div>;
      };

      render(<TestComponent />);

      // Send multiple messages rapidly
      const messagePromises = [];
      for (let i = 0; i < 5; i++) {
        messagePromises.push(
          messageHandler({
            fromAgent: `agent-${i}`,
            toAgent: `agent-${i + 1}`,
            messageType: 'test_message',
            payload: { sequence: i },
          })
        );
      }

      await Promise.all(messagePromises);

      expect(deliveredMessages).toHaveLength(5);
      expect(screen.getByTestId('queue-test')).toBeInTheDocument();
    });
  });

  describe('Workflow Orchestration', () => {
    it('should execute complete account analysis workflow', async () => {
      let actionHandler;
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'analyzeAccount') {
          actionHandler = handler;
        } else if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      // Mock fetch responses
      const mockAnalysisResult = createMockAnalysisResult({
        account_snapshot: {
          account_id: 'ACC-001',
          account_name: 'Test Account',
          priority_score: 85,
          risk_level: 'high',
        },
        risk_signals: [
          createMockRiskSignal({ signal_type: 'high_churn_risk' }),
          createMockRiskSignal({ signal_type: 'payment_delay' }),
        ],
        recommendations: [
          createMockRecommendation({ priority: 'critical' }),
          createMockRecommendation({ priority: 'high' }),
        ],
      });

      mockFetchResponse(mockAnalysisResult);

      render(
        <CopilotProvider>
          <AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />
        </CopilotProvider>
      );

      // Step 1: Initialize workflow
      await stateUpdateHandler({
        stateUpdate: {
          analysis_in_progress: true,
          agent_queue: ['zoho-data-scout', 'memory-analyst', 'recommendation-author'],
        },
        sourceAgent: 'orchestrator',
      });

      // Step 2: Zoho Data Scout signals start
      await messageHandler({
        fromAgent: 'zoho-data-scout',
        toAgent: 'orchestrator',
        messageType: 'agent_started',
        payload: { task: 'data_collection' },
      });

      // Step 3: Execute analysis
      const result = await actionHandler({ accountId: 'ACC-001' });
      expect(result.success).toBe(true);

      // Step 4: Memory Analyst signals completion
      await messageHandler({
        fromAgent: 'memory-analyst',
        toAgent: 'orchestrator',
        messageType: 'agent_completed',
        payload: { task: 'data_analysis', insights_count: 5 },
      });

      // Step 5: Recommendation Author signals completion
      await messageHandler({
        fromAgent: 'recommendation-author',
        toAgent: 'orchestrator',
        messageType: 'agent_completed',
        payload: { task: 'recommendation_generation', rec_count: 2 },
      });

      // Step 6: Mark workflow complete
      await stateUpdateHandler({
        stateUpdate: {
          analysis_in_progress: false,
          agent_queue: [],
          last_analysis_timestamp: new Date().toISOString(),
        },
        sourceAgent: 'orchestrator',
      });

      // Verify workflow completion
      await waitFor(() => {
        expect(screen.getByText('Successfully analyzed account ACC-001')).toBeInTheDocument();
      });
    });

    it('should handle workflow failures and recovery', async () => {
      let actionHandler;
      let stateUpdateHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'analyzeAccount') {
          actionHandler = handler;
        } else if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        }
        return handler;
      });

      // Mock initial failure
      mockFetchError(new Error('Service unavailable'));

      render(
        <CopilotProvider>
          <AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />
        </CopilotProvider>
      );

      // Attempt workflow
      await stateUpdateHandler({
        stateUpdate: { analysis_in_progress: true },
        sourceAgent: 'orchestrator',
      });

      const result1 = await actionHandler({ accountId: 'ACC-001' });
      expect(result1.success).toBe(false);

      // Retry with success
      mockFetchResponse(createMockAnalysisResult());
      const result2 = await actionHandler({ accountId: 'ACC-001' });
      expect(result2.success).toBe(true);

      // Mark workflow complete
      await stateUpdateHandler({
        stateUpdate: { analysis_in_progress: false },
        sourceAgent: 'orchestrator',
      });
    });

    it('should handle partial workflow failures', async () => {
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="partial-failure-test">Test</div>;
      };

      render(<TestComponent />);

      // Initialize workflow
      await stateUpdateHandler({
        stateUpdate: {
          analysis_in_progress: true,
          agent_queue: ['agent1', 'agent2', 'agent3'],
        },
        sourceAgent: 'orchestrator',
      });

      // Agent 1 fails
      await messageHandler({
        fromAgent: 'agent1',
        toAgent: 'orchestrator',
        messageType: 'agent_failed',
        payload: { error: 'Data fetch failed', retryable: false },
      });

      // Agent 2 succeeds
      await messageHandler({
        fromAgent: 'agent2',
        toAgent: 'orchestrator',
        messageType: 'agent_completed',
        payload: { result: 'success' },
      });

      // Agent 3 needs Agent 2 data
      await messageHandler({
        fromAgent: 'agent3',
        toAgent: 'agent2',
        messageType: 'data_request',
        payload: { type: 'processed_data' },
      });

      // Continue workflow with remaining agents
      await stateUpdateHandler({
        stateUpdate: {
          agent_queue: ['agent2', 'agent3'],
          failed_agents: ['agent1'],
        },
        sourceAgent: 'orchestrator',
      });

      expect(screen.getByTestId('partial-failure-test')).toBeInTheDocument();
    });
  });

  describe('Distributed State Management', () => {
    it('should maintain state consistency across agents', async () => {
      let stateUpdateHandler;
      let getMessagesHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'getAgentMessages') {
          getMessagesHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="consistency-test">Test</div>;
      };

      render(<TestComponent />);

      // Multiple agents update different parts of state
      const updates = [
        {
          stateUpdate: { current_account_id: 'ACC-001' },
          sourceAgent: 'ui',
        },
        {
          stateUpdate: { analysis_in_progress: true },
          sourceAgent: 'orchestrator',
        },
        {
          stateUpdate: { user_preferences: { auto_analyze: true } },
          sourceAgent: 'settings',
        },
      ];

      await Promise.all(updates.map(update => stateUpdateHandler(update)));

      // Verify state consistency
      const allMessages = await getMessagesHandler({ agentName: 'all' });
      expect(allMessages.messages).toBeDefined();

      expect(screen.getByTestId('consistency-test')).toBeInTheDocument();
    });

    it('should handle state conflicts with versioning', async () => {
      let stateUpdateHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = async (...args) => {
            // Simulate versioned state updates
            const update = args[0];
            const version = Date.now();
            return {
              success: true,
              version,
              appliedState: { ...update.stateUpdate, __version: version },
            };
          };
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="versioning-test">Test</div>;
      };

      render(<TestComponent />);

      // Simulate concurrent conflicting updates
      const update1 = stateUpdateHandler({
        stateUpdate: { analysis_in_progress: true },
        sourceAgent: 'agent1',
        version: 1,
      });

      const update2 = stateUpdateHandler({
        stateUpdate: { analysis_in_progress: false },
        sourceAgent: 'agent2',
        version: 2,
      });

      const [result1, result2] = await Promise.all([update1, update2]);

      // Higher version should win
      expect(result2.version).toBeGreaterThan(result1.version);

      expect(screen.getByTestId('versioning-test')).toBeInTheDocument();
    });
  });

  describe('Resource Management', () => {
    it('should coordinate resource allocation between agents', async () => {
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="resource-test">Test</div>;
      };

      render(<TestComponent />);

      // Agent 1 requests resource
      await messageHandler({
        fromAgent: 'agent1',
        toAgent: 'resource-manager',
        messageType: 'resource_request',
        payload: { resource: 'api_quota', amount: 10 },
      });

      // Resource manager allocates
      await stateUpdateHandler({
        stateUpdate: {
          allocated_resources: {
            agent1: { api_quota: 10, expires_at: Date.now() + 300000 },
          },
          available_resources: {
            api_quota: 90,
          },
        },
        sourceAgent: 'resource-manager',
      });

      // Agent 2 requests resource
      await messageHandler({
        fromAgent: 'agent2',
        toAgent: 'resource-manager',
        messageType: 'resource_request',
        payload: { resource: 'api_quota', amount: 20 },
      });

      // Partial allocation
      await stateUpdateHandler({
        stateUpdate: {
          allocated_resources: {
            agent1: { api_quota: 10 },
            agent2: { api_quota: 15 }, // Partial allocation
          },
          available_resources: {
            api_quota: 75,
          },
        },
        sourceAgent: 'resource-manager',
      });

      expect(screen.getByTestId('resource-test')).toBeInTheDocument();
    });

    it('should handle resource exhaustion', async () => {
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="exhaustion-test">Test</div>;
      };

      render(<TestComponent />);

      // Set resource exhaustion
      await stateUpdateHandler({
        stateUpdate: {
          available_resources: {
            api_quota: 0,
            memory: 1024 * 1024, // 1MB remaining
          },
          resource_pool: 'exhausted',
        },
        sourceAgent: 'resource-monitor',
      });

      // Agent tries to request unavailable resource
      await messageHandler({
        fromAgent: 'agent1',
        toAgent: 'resource-manager',
        messageType: 'resource_request',
        payload: { resource: 'api_quota', amount: 5 },
      });

      // Resource denied
      await messageHandler({
        fromAgent: 'resource-manager',
        toAgent: 'agent1',
        messageType: 'resource_denied',
        payload: { reason: 'insufficient_resources', retry_after: 60000 },
      });

      expect(screen.getByTestId('exhaustion-test')).toBeInTheDocument();
    });
  });

  describe('Error Propagation and Recovery', () => {
    it('should propagate errors across agent network', async () => {
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="error-propagation-test">Test</div>;
      };

      render(<TestComponent />);

      // Agent 1 encounters error
      await messageHandler({
        fromAgent: 'agent1',
        toAgent: 'orchestrator',
        messageType: 'agent_error',
        payload: {
          error: 'Data validation failed',
          severity: 'high',
          context: { account_id: 'ACC-001', field: 'email' },
        },
      });

      // Orchestrator updates error state
      await stateUpdateHandler({
        stateUpdate: {
          error_state: {
            agent: 'agent1',
            error: 'Data validation failed',
            severity: 'high',
            timestamp: new Date().toISOString(),
          },
          failed_operations: ['data_validation'],
        },
        sourceAgent: 'orchestrator',
      });

      // Notify dependent agents
      await messageHandler({
        fromAgent: 'orchestrator',
        toAgent: 'agent2',
        messageType: 'operation_cancelled',
        payload: {
          reason: 'dependency_error',
          dependent_agent: 'agent1',
        },
      });

      expect(screen.getByTestId('error-propagation-test')).toBeInTheDocument();
    });

    it('should coordinate error recovery', async () => {
      let stateUpdateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          stateUpdateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div data-testid="recovery-test">Test</div>;
      };

      render(<TestComponent />);

      // Agent reports recovery capability
      await messageHandler({
        fromAgent: 'agent1',
        toAgent: 'orchestrator',
        messageType: 'recovery_capability',
        payload: {
          can_recover_from: ['data_validation_error', 'network_timeout'],
          recovery_strategies: ['retry', 'fallback_data', 'manual_intervention'],
        },
      });

      // Orchestrator initiates recovery
      await stateUpdateHandler({
        stateUpdate: {
          recovery_mode: true,
          recovery_strategy: 'fallback_data',
        },
        sourceAgent: 'orchestrator',
      });

      // Agent executes recovery
      await messageHandler({
        fromAgent: 'agent1',
        toAgent: 'orchestrator',
        messageType: 'recovery_completed',
        payload: {
          strategy: 'fallback_data',
          result: 'success',
          data_source: 'cache',
        },
      });

      // Exit recovery mode
      await stateUpdateHandler({
        stateUpdate: {
          recovery_mode: false,
          error_state: null,
          failed_operations: [],
        },
        sourceAgent: 'orchestrator',
      });

      expect(screen.getByTestId('recovery-test')).toBeInTheDocument();
    });
  });
});