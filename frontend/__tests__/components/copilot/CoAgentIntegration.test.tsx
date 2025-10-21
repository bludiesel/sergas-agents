/**
 * CoAgentIntegration Component Tests
 *
 * Tests for CoAgent state management and inter-agent communication
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CoAgentDashboard, useCoAgentState } from '@/components/copilot/CoAgentIntegration';

// Mock CopilotKit hooks
const mockUseCopilotAction = jest.fn();
const mockUseCopilotReadable = jest.fn();

jest.mock('@copilotkit/react-core', () => ({
  useCopilotAction: mockUseCopilotAction,
  useCopilotReadable: mockUseCopilotReadable,
}));

describe('CoAgentIntegration', () => {
  const mockRuntimeUrl = 'http://localhost:8008';

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCopilotAction.mockImplementation(({ handler }) => handler);
    mockUseCopilotReadable.mockImplementation(() => {});
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('useCoAgentState Hook', () => {
    it('should initialize with default state', () => {
      const TestComponent = () => {
        const { sharedState } = useCoAgentState(mockRuntimeUrl);
        return (
          <div data-testid="state-display">
            <span data-testid="current-account">{sharedState.current_account_id}</span>
            <span data-testid="analysis-in-progress">{sharedState.analysis_in_progress.toString()}</span>
            <span data-testid="agent-queue">{sharedState.agent_queue.join(',')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      expect(screen.getByTestId('current-account')).toHaveTextContent('');
      expect(screen.getByTestId('analysis-in-progress')).toHaveTextContent('false');
      expect(screen.getByTestId('agent-queue')).toHaveTextContent('');
    });

    it('should set up CopilotKit readable contexts', () => {
      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div>Test</div>;
      };

      render(<TestComponent />);

      expect(mockUseCopilotReadable).toHaveBeenCalledTimes(2); // sharedState, agentMessages
    });

    it('should register CopilotKit actions', () => {
      const TestComponent = () => {
        useCoAgentState(mockRuntimeUrl);
        return <div>Test</div>;
      };

      render(<TestComponent />);

      expect(mockUseCopilotAction).toHaveBeenCalledTimes(3); // updateSharedState, sendAgentMessage, getAgentMessages
    });

    describe('updateSharedState Action', () => {
      it('should update shared state from backend agents', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          if (handler.name === 'updateSharedState') {
            actionHandler = handler;
          }
          return handler;
        });

        const TestComponent = () => {
          const { sharedState } = useCoAgentState(mockRuntimeUrl);
          return (
            <div data-testid="state">
              <span data-testid="account">{sharedState.current_account_id}</span>
              <span data-testid="analysis">{sharedState.analysis_in_progress.toString()}</span>
            </div>
          );
        };

        render(<TestComponent />);

        const result = await actionHandler({
          stateUpdate: {
            current_account_id: 'ACC-001',
            analysis_in_progress: true,
          },
          sourceAgent: 'zoho-data-scout',
        });

        expect(result).toEqual({
          success: true,
          message: 'State updated by zoho-data-scout',
          new_state: expect.objectContaining({
            current_account_id: 'ACC-001',
            analysis_in_progress: true,
          }),
        });
      });

      it('should handle partial state updates', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          if (handler.name === 'updateSharedState') {
            actionHandler = handler;
          }
          return handler;
        });

        const TestComponent = () => {
          useCoAgentState(mockRuntimeUrl);
          return <div>Test</div>;
        };

        render(<TestComponent />);

        await actionHandler({
          stateUpdate: { agent_queue: ['agent1', 'agent2'] },
          sourceAgent: 'orchestrator',
        });

        // Should only update specified fields
        const result = await actionHandler({
          stateUpdate: { user_preferences: { auto_analyze: true } },
          sourceAgent: 'ui',
        });

        expect(result.success).toBe(true);
      });
    });

    describe('sendAgentMessage Action', () => {
      it('should send inter-agent messages', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          if (handler.name === 'sendAgentMessage') {
            actionHandler = handler;
          }
          return handler;
        });

        const TestComponent = () => {
          const { agentMessages } = useCoAgentState(mockRuntimeUrl);
          return (
            <div data-testid="messages">
              {agentMessages.map((msg, idx) => (
                <div key={idx} data-testid={`message-${idx}`}>
                  {msg.from_agent} → {msg.to_agent}
                </div>
              ))}
            </div>
          );
        };

        render(<TestComponent />);

        const result = await actionHandler({
          fromAgent: 'zoho-data-scout',
          toAgent: 'memory-analyst',
          messageType: 'data_ready',
          payload: { account_id: 'ACC-001', data_size: '1.2MB' },
        });

        expect(result).toEqual({
          success: true,
          message: 'Message sent from zoho-data-scout to memory-analyst',
          message_id: expect.any(String),
        });
      });

      it('should handle messages without payload', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          if (handler.name === 'sendAgentMessage') {
            actionHandler = handler;
          }
          return handler;
        });

        const TestComponent = () => {
          useCoAgentState(mockRuntimeUrl);
          return <div>Test</div>;
        };

        render(<TestComponent />);

        const result = await actionHandler({
          fromAgent: 'orchestrator',
          toAgent: 'all',
          messageType: 'analysis_complete',
        });

        expect(result.success).toBe(true);
      });
    });

    describe('getAgentMessages Action', () => {
      it('should retrieve messages for specific agent', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          if (handler.name === 'getAgentMessages') {
            actionHandler = handler;
          }
          return handler;
        });

        const TestComponent = () => {
          useCoAgentState(mockRuntimeUrl);
          return <div>Test</div>;
        };

        render(<TestComponent />);

        const result = await actionHandler({
          agentName: 'memory-analyst',
        });

        expect(result).toEqual({
          success: true,
          messages: [],
          count: 0,
        });
      });

      it('should filter messages by type', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          if (handler.name === 'getAgentMessages') {
            actionHandler = handler;
          }
          return handler;
        });

        const TestComponent = () => {
          useCoAgentState(mockRuntimeUrl);
          return <div>Test</div>;
        };

        render(<TestComponent />);

        const result = await actionHandler({
          agentName: 'orchestrator',
          messageType: 'data_ready',
        });

        expect(result.success).toBe(true);
        expect(result.count).toBe(0);
      });
    });
  });

  describe('CoAgentDashboard Component', () => {
    it('should render dashboard with shared state', () => {
      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      expect(screen.getByText('Shared Agent State')).toBeInTheDocument();
      expect(screen.getByText('Agent Messages (0)')).toBeInTheDocument();
      expect(screen.getByText('Current Account')).toBeInTheDocument();
      expect(screen.getByText('Analysis In Progress')).toBeInTheDocument();
    });

    it('should display default values correctly', () => {
      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      expect(screen.getByText('None')).toBeInTheDocument(); // Current Account
      expect(screen.getByText('No')).toBeInTheDocument(); // Analysis In Progress
      expect(screen.getByText('Never')).toBeInTheDocument(); // Last Analysis
      expect(screen.getByText('Empty')).toBeInTheDocument(); // Agent Queue
      expect(screen.getByText('No messages yet')).toBeInTheDocument();
    });

    it('should display user preferences', () => {
      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      expect(screen.getByText('User Preferences')).toBeInTheDocument();
      expect(screen.getByText('Auto Analyze')).toBeInTheDocument();
      expect(screen.getByText('Disabled')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('all')).toBeInTheDocument();
    });

    describe('State Updates', () => {
      it('should update shared state when changed', async () => {
        let updateHandler;
        let messageHandler;

        mockUseCopilotAction.mockImplementation(({ name, handler }) => {
          if (name === 'updateSharedState') {
            updateHandler = handler;
          } else if (name === 'sendAgentMessage') {
            messageHandler = handler;
          }
          return handler;
        });

        render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

        // Update state via action
        await updateHandler({
          stateUpdate: {
            current_account_id: 'ACC-001',
            analysis_in_progress: true,
            last_analysis_timestamp: '2024-01-15T10:30:00Z',
            agent_queue: ['zoho-data-scout', 'memory-analyst'],
          },
          sourceAgent: 'orchestrator',
        });

        // The dashboard should reflect updated state
        await waitFor(() => {
          expect(screen.getByDisplayValue(/ACC-001/)).toBeInTheDocument();
        });
      });

      it('should display new agent messages', async () => {
        let messageHandler;

        mockUseCopilotAction.mockImplementation(({ name, handler }) => {
          if (name === 'sendAgentMessage') {
            messageHandler = handler;
          }
          return handler;
        });

        render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

        // Send a message
        await messageHandler({
          fromAgent: 'zoho-data-scout',
          toAgent: 'memory-analyst',
          messageType: 'data_ready',
          payload: { account_id: 'ACC-001' },
        });

        // Should display the message
        await waitFor(() => {
          expect(screen.getByText('Agent Messages (1)')).toBeInTheDocument();
          expect(screen.getByText('zoho-data-scout')).toBeInTheDocument();
          expect(screen.getByText('memory-analyst')).toBeInTheDocument();
          expect(screen.getByText('data_ready')).toBeInTheDocument();
        });
      });

      it('should limit message display to recent messages', async () => {
        let messageHandler;

        mockUseCopilotAction.mockImplementation(({ name, handler }) => {
          if (name === 'sendAgentMessage') {
            messageHandler = handler;
          }
          return handler;
        });

        render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

        // Send multiple messages
        for (let i = 0; i < 15; i++) {
          await messageHandler({
            fromAgent: `agent-${i}`,
            toAgent: `agent-${i + 1}`,
            messageType: 'test',
            payload: { index: i },
          });
        }

        await waitFor(() => {
          expect(screen.getByText('Agent Messages (15)')).toBeInTheDocument();
          // Should only show last 10 messages
          expect(screen.getAllByTestId(/message-/).length).toBe(10);
        });
      });
    });

    describe('User Preferences', () => {
      it('should display user preferences correctly', async () => {
        let updateHandler;

        mockUseCopilotAction.mockImplementation(({ name, handler }) => {
          if (name === 'updateSharedState') {
            updateHandler = handler;
          }
          return handler;
        });

        render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

        // Update user preferences
        await updateHandler({
          stateUpdate: {
            user_preferences: {
              auto_analyze: true,
              notification_level: 'critical',
            },
          },
          sourceAgent: 'ui',
        });

        await waitFor(() => {
          expect(screen.getByText('Enabled')).toBeInTheDocument(); // Auto Analyze
          expect(screen.getByText('critical')).toBeInTheDocument(); // Notifications
        });
      });

      it('should handle different notification levels', async () => {
        let updateHandler;

        mockUseCopilotAction.mockImplementation(({ name, handler }) => {
          if (name === 'updateSharedState') {
            updateHandler = handler;
          }
          return handler;
        });

        const { rerender } = render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

        // Test each notification level
        const levels = ['all', 'critical', 'none'];

        for (const level of levels) {
          await updateHandler({
            stateUpdate: {
              user_preferences: { notification_level: level },
            },
            sourceAgent: 'test',
          });

          await waitFor(() => {
            expect(screen.getByText(level)).toBeInTheDocument();
          });
        }
      });
    });
  });

  describe('Message Display', () => {
    it('should format message timestamps correctly', async () => {
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      const testTimestamp = '2024-01-15T14:30:00.000Z';

      // Mock current time for consistent testing
      const originalNow = Date.now;
      Date.now = () => new Date(testTimestamp).getTime();

      await messageHandler({
        fromAgent: 'test-agent',
        toAgent: 'target-agent',
        messageType: 'test-message',
      });

      await waitFor(() => {
        const messageTime = screen.getByText(/2:30:00/);
        expect(messageTime).toBeInTheDocument();
      });

      // Restore Date.now
      Date.now = originalNow;
    });

    it('should truncate long payloads', async () => {
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      const longPayload = {
        data: 'x'.repeat(100), // Long string that should be truncated
        more_data: { nested: 'value' },
      };

      await messageHandler({
        fromAgent: 'sender',
        toAgent: 'receiver',
        messageType: 'payload-test',
        payload: longPayload,
      });

      await waitFor(() => {
        // Should truncate payload display
        const payloadElement = screen.getByText(/.../);
        expect(payloadElement).toBeInTheDocument();
      });
    });

    it('should handle messages without payload', async () => {
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      await messageHandler({
        fromAgent: 'sender',
        toAgent: 'receiver',
        messageType: 'simple-message',
      });

      await waitFor(() => {
        expect(screen.getByText('Agent Messages (1)')).toBeInTheDocument();
        expect(screen.getByText('simple-message')).toBeInTheDocument();
        // Should not show payload section
        expect(screen.queryByText(/.../)).not.toBeInTheDocument();
      });
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete workflow simulation', async () => {
      let updateHandler;
      let messageHandler;

      mockUseCopilotAction.mockImplementation(({ name, handler }) => {
        if (name === 'updateSharedState') {
          updateHandler = handler;
        } else if (name === 'sendAgentMessage') {
          messageHandler = handler;
        }
        return handler;
      });

      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      // 1. Start analysis
      await updateHandler({
        stateUpdate: {
          current_account_id: 'ACC-001',
          analysis_in_progress: true,
          agent_queue: ['zoho-data-scout'],
        },
        sourceAgent: 'orchestrator',
      });

      // 2. Send data ready message
      await messageHandler({
        fromAgent: 'zoho-data-scout',
        toAgent: 'memory-analyst',
        messageType: 'data_ready',
        payload: { records: 150 },
      });

      // 3. Update agent queue
      await updateHandler({
        stateUpdate: {
          agent_queue: ['memory-analyst', 'recommendation-author'],
        },
        sourceAgent: 'orchestrator',
      });

      // 4. Complete analysis
      await updateHandler({
        stateUpdate: {
          analysis_in_progress: false,
          agent_queue: [],
          last_analysis_timestamp: new Date().toISOString(),
        },
        sourceAgent: 'orchestrator',
      });

      // Verify final state
      await waitFor(() => {
        expect(screen.getByText('No')).toBeInTheDocument(); // Analysis not in progress
        expect(screen.getByText('Empty')).toBeInTheDocument(); // Agent queue empty
        expect(screen.getByText(/Agent Messages \(2\)/)).toBeInTheDocument();
      });
    });
  });
});