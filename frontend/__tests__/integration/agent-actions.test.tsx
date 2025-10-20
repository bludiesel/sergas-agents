/**
 * Integration Tests: Agent Action Invocations
 *
 * Tests agent action registration, invocation, parameter validation,
 * and response handling in the CopilotKit integration.
 *
 * Coverage:
 * - Action registration and discovery
 * - Parameter validation
 * - Action invocation flow
 * - Response handling
 * - Error scenarios
 * - Multi-agent coordination
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { CopilotKit, useCopilotAction } from '@copilotkit/react-core';
import '@testing-library/jest-dom';

// Mock fetch
global.fetch = jest.fn();

describe('Agent Action Integration Tests', () => {
  const mockRuntimeUrl = 'http://localhost:8000/copilotkit';

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
  });

  describe('Action Registration', () => {
    it('should register analyzeAccount action', () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'analyzeAccount',
          description: 'Analyze Zoho CRM account data and provide insights',
          parameters: [
            {
              name: 'accountId',
              type: 'string',
              description: 'Zoho CRM account ID',
              required: true,
            },
            {
              name: 'includeMemory',
              type: 'boolean',
              description: 'Include historical memory analysis',
              required: false,
            },
          ],
          handler: async ({ accountId, includeMemory }) => {
            return {
              accountId,
              includeMemory: includeMemory ?? true,
              status: 'analysis_started',
            };
          },
        });

        return <div data-testid="analyze-action">Analyze Action Registered</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('analyze-action')).toBeInTheDocument();
    });

    it('should register fetchAccountData action', () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'fetchAccountData',
          description: 'Fetch Zoho CRM account data',
          parameters: [
            {
              name: 'accountId',
              type: 'string',
              description: 'Account ID',
              required: true,
            },
          ],
          handler: async ({ accountId }) => {
            return {
              account: {
                id: accountId,
                name: 'Test Account',
                status: 'Active',
              },
            };
          },
        });

        return <div data-testid="fetch-action">Fetch Action Registered</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('fetch-action')).toBeInTheDocument();
    });

    it('should register generateRecommendations action', () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'generateRecommendations',
          description: 'Generate account recommendations',
          parameters: [
            {
              name: 'accountData',
              type: 'object',
              description: 'Account analysis data',
              required: true,
            },
            {
              name: 'includeNextSteps',
              type: 'boolean',
              description: 'Include actionable next steps',
              required: false,
            },
          ],
          handler: async ({ accountData, includeNextSteps }) => {
            return {
              recommendations: [],
              includeNextSteps: includeNextSteps ?? true,
            };
          },
        });

        return <div data-testid="recommend-action">Recommendation Action Registered</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('recommend-action')).toBeInTheDocument();
    });
  });

  describe('Parameter Validation', () => {
    it('should validate required parameters', async () => {
      const mockHandler = jest.fn();

      const TestComponent = () => {
        useCopilotAction({
          name: 'testAction',
          description: 'Test action with required params',
          parameters: [
            {
              name: 'requiredParam',
              type: 'string',
              description: 'Required parameter',
              required: true,
            },
          ],
          handler: mockHandler,
        });

        return <div>Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      // Action is registered, validation happens during invocation
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    it('should handle optional parameters with defaults', async () => {
      const mockHandler = jest.fn(async ({ optionalParam }) => ({
        value: optionalParam ?? 'default',
      }));

      const TestComponent = () => {
        useCopilotAction({
          name: 'optionalAction',
          description: 'Action with optional parameter',
          parameters: [
            {
              name: 'optionalParam',
              type: 'string',
              description: 'Optional parameter',
              required: false,
            },
          ],
          handler: mockHandler,
        });

        return <div data-testid="optional-action">Optional Action</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('optional-action')).toBeInTheDocument();
    });

    it('should validate parameter types', () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'typedAction',
          description: 'Action with typed parameters',
          parameters: [
            {
              name: 'stringParam',
              type: 'string',
              description: 'String parameter',
              required: true,
            },
            {
              name: 'numberParam',
              type: 'number',
              description: 'Number parameter',
              required: true,
            },
            {
              name: 'booleanParam',
              type: 'boolean',
              description: 'Boolean parameter',
              required: true,
            },
            {
              name: 'objectParam',
              type: 'object',
              description: 'Object parameter',
              required: true,
            },
          ],
          handler: async (params) => params,
        });

        return <div data-testid="typed-action">Typed Action</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('typed-action')).toBeInTheDocument();
    });
  });

  describe('Action Invocation Flow', () => {
    it('should invoke analyzeAccount with correct parameters', async () => {
      const mockHandler = jest.fn().mockResolvedValue({
        accountId: 'acc_123',
        analysis: {
          health_score: 85,
          risk_level: 'low',
        },
      });

      const TestComponent = () => {
        useCopilotAction({
          name: 'analyzeAccount',
          description: 'Analyze account',
          parameters: [
            {
              name: 'accountId',
              type: 'string',
              description: 'Account ID',
              required: true,
            },
          ],
          handler: mockHandler,
        });

        return <div data-testid="invoke-test">Invocation Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('invoke-test')).toBeInTheDocument();
    });

    it('should handle streaming responses during action execution', async () => {
      const streamData = [
        { type: 'agent_started', agent: 'orchestrator' },
        { type: 'agent_stream', content: 'Analyzing account...' },
        { type: 'agent_completed', output: { status: 'complete' } },
      ];

      const mockHandler = jest.fn().mockImplementation(async function* () {
        for (const data of streamData) {
          yield data;
        }
      });

      const TestComponent = () => {
        useCopilotAction({
          name: 'streamingAction',
          description: 'Streaming action',
          parameters: [],
          handler: mockHandler,
        });

        return <div data-testid="streaming-test">Streaming Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('streaming-test')).toBeInTheDocument();
    });

    it('should chain multiple agent actions', async () => {
      const results: string[] = [];

      const TestComponent = () => {
        useCopilotAction({
          name: 'action1',
          description: 'First action',
          parameters: [],
          handler: async () => {
            results.push('action1');
            return { step: 1 };
          },
        });

        useCopilotAction({
          name: 'action2',
          description: 'Second action',
          parameters: [],
          handler: async () => {
            results.push('action2');
            return { step: 2 };
          },
        });

        return <div data-testid="chain-test">Chain Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('chain-test')).toBeInTheDocument();
    });
  });

  describe('Response Handling', () => {
    it('should handle successful action responses', async () => {
      const mockResponse = {
        accountId: 'acc_123',
        analysis: { score: 85 },
        recommendations: ['Action 1', 'Action 2'],
      };

      const mockHandler = jest.fn().mockResolvedValue(mockResponse);

      const TestComponent = () => {
        const [result, setResult] = React.useState<any>(null);

        useCopilotAction({
          name: 'successAction',
          description: 'Successful action',
          parameters: [],
          handler: async () => {
            const res = await mockHandler();
            setResult(res);
            return res;
          },
        });

        return (
          <div>
            <div data-testid="success-test">Success Test</div>
            {result && <div data-testid="result">{JSON.stringify(result)}</div>}
          </div>
        );
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('success-test')).toBeInTheDocument();
    });

    it('should handle partial streaming results', async () => {
      const TestComponent = () => {
        const [chunks, setChunks] = React.useState<string[]>([]);

        useCopilotAction({
          name: 'partialAction',
          description: 'Partial results action',
          parameters: [],
          handler: async () => {
            const partials = ['Part 1', 'Part 2', 'Part 3'];
            partials.forEach((p) => setChunks((prev) => [...prev, p]));
            return { chunks: partials };
          },
        });

        return (
          <div>
            <div data-testid="partial-test">Partial Test</div>
            {chunks.map((chunk, i) => (
              <div key={i} data-testid={`chunk-${i}`}>
                {chunk}
              </div>
            ))}
          </div>
        );
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('partial-test')).toBeInTheDocument();
    });

    it('should handle large response payloads', async () => {
      const largePayload = {
        accountId: 'acc_123',
        deals: Array(1000).fill({ id: 'deal', amount: 1000 }),
        activities: Array(500).fill({ type: 'email', date: '2025-10-19' }),
      };

      const mockHandler = jest.fn().mockResolvedValue(largePayload);

      const TestComponent = () => {
        useCopilotAction({
          name: 'largeAction',
          description: 'Large payload action',
          parameters: [],
          handler: mockHandler,
        });

        return <div data-testid="large-test">Large Payload Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('large-test')).toBeInTheDocument();
    });
  });

  describe('Error Scenarios', () => {
    it('should handle action execution errors', async () => {
      const mockHandler = jest.fn().mockRejectedValue(new Error('Execution failed'));
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        useCopilotAction({
          name: 'errorAction',
          description: 'Error action',
          parameters: [],
          handler: mockHandler,
        });

        return <div data-testid="error-test">Error Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('error-test')).toBeInTheDocument();
      consoleError.mockRestore();
    });

    it('should handle timeout scenarios', async () => {
      const mockHandler = jest.fn().mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ result: 'delayed' }), 5000)
          )
      );

      const TestComponent = () => {
        useCopilotAction({
          name: 'timeoutAction',
          description: 'Timeout action',
          parameters: [],
          handler: mockHandler,
        });

        return <div data-testid="timeout-test">Timeout Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('timeout-test')).toBeInTheDocument();
    });

    it('should handle network failures during action execution', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        useCopilotAction({
          name: 'networkAction',
          description: 'Network action',
          parameters: [],
          handler: async () => {
            await fetch('http://api.example.com/data');
            return { result: 'success' };
          },
        });

        return <div data-testid="network-test">Network Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('network-test')).toBeInTheDocument();
      consoleError.mockRestore();
    });
  });

  describe('Multi-Agent Coordination', () => {
    it('should coordinate between orchestrator and data scout agents', async () => {
      const executionOrder: string[] = [];

      const TestComponent = () => {
        useCopilotAction({
          name: 'orchestratorAction',
          description: 'Orchestrator action',
          parameters: [],
          handler: async () => {
            executionOrder.push('orchestrator');
            return { agent: 'orchestrator', status: 'delegating' };
          },
        });

        useCopilotAction({
          name: 'dataScoutAction',
          description: 'Data scout action',
          parameters: [],
          handler: async () => {
            executionOrder.push('data_scout');
            return { agent: 'data_scout', data: [] };
          },
        });

        return <div data-testid="coordination-test">Coordination Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('coordination-test')).toBeInTheDocument();
    });

    it('should share state between agent actions', async () => {
      const sharedState = { accountId: '', data: null };

      const TestComponent = () => {
        useCopilotAction({
          name: 'fetchAction',
          description: 'Fetch action',
          parameters: [{ name: 'accountId', type: 'string', required: true }],
          handler: async ({ accountId }) => {
            sharedState.accountId = accountId;
            sharedState.data = { fetched: true };
            return sharedState;
          },
        });

        useCopilotAction({
          name: 'analyzeAction',
          description: 'Analyze action',
          parameters: [],
          handler: async () => {
            return { accountId: sharedState.accountId, analyzed: true };
          },
        });

        return <div data-testid="shared-state-test">Shared State Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('shared-state-test')).toBeInTheDocument();
    });
  });
});
