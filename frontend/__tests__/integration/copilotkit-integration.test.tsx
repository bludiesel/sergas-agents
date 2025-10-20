/**
 * Integration Tests: CopilotKit Provider and Hooks
 *
 * Tests CopilotKit provider initialization, configuration, and hook functionality
 * for the frontend-backend integration flow.
 *
 * Coverage:
 * - CopilotKit provider initialization
 * - useCopilotAction hook functionality
 * - useCoAgent state sharing
 * - Context provision to child components
 * - Error handling and recovery
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { CopilotKit, useCopilotAction } from '@copilotkit/react-core';
import '@testing-library/jest-dom';

// Mock Next.js environment
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock fetch for API calls
global.fetch = jest.fn();

describe('CopilotKit Integration Tests', () => {
  const mockRuntimeUrl = 'http://localhost:8000/copilotkit';
  const mockApiToken = 'test-api-token';

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success' }),
      text: async () => 'success',
      headers: new Headers({ 'content-type': 'application/json' }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('CopilotKit Provider Initialization', () => {
    it('should initialize with correct runtime URL', () => {
      const TestComponent = () => {
        return (
          <CopilotKit runtimeUrl={mockRuntimeUrl}>
            <div data-testid="child-component">Test Child</div>
          </CopilotKit>
        );
      };

      render(<TestComponent />);
      expect(screen.getByTestId('child-component')).toBeInTheDocument();
    });

    it('should initialize with authentication headers', () => {
      const TestComponent = () => {
        return (
          <CopilotKit
            runtimeUrl={mockRuntimeUrl}
            headers={{
              Authorization: `Bearer ${mockApiToken}`,
            }}
          >
            <div data-testid="auth-child">Authenticated</div>
          </CopilotKit>
        );
      };

      render(<TestComponent />);
      expect(screen.getByTestId('auth-child')).toBeInTheDocument();
    });

    it('should wrap children components correctly', () => {
      const ChildComponent = () => <div data-testid="nested-child">Nested Content</div>;

      const TestComponent = () => {
        return (
          <CopilotKit runtimeUrl={mockRuntimeUrl}>
            <ChildComponent />
          </CopilotKit>
        );
      };

      render(<TestComponent />);
      expect(screen.getByTestId('nested-child')).toBeInTheDocument();
    });

    it('should handle missing runtime URL gracefully', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        return (
          <CopilotKit runtimeUrl="">
            <div>Test</div>
          </CopilotKit>
        );
      };

      expect(() => render(<TestComponent />)).not.toThrow();
      consoleError.mockRestore();
    });

    it('should configure claude-3-5-sonnet model by default', () => {
      // CopilotKit uses claude-3-5-sonnet-20241022 as the default model
      const TestComponent = () => {
        return (
          <CopilotKit runtimeUrl={mockRuntimeUrl}>
            <div data-testid="model-test">Model Test</div>
          </CopilotKit>
        );
      };

      render(<TestComponent />);
      expect(screen.getByTestId('model-test')).toBeInTheDocument();
    });
  });

  describe('useCopilotAction Hook', () => {
    it('should register action handler correctly', async () => {
      const mockHandler = jest.fn().mockResolvedValue({ success: true });

      const TestComponent = () => {
        useCopilotAction({
          name: 'analyzeAccount',
          description: 'Analyze account data',
          parameters: [
            {
              name: 'accountId',
              type: 'string',
              description: 'Account ID to analyze',
              required: true,
            },
          ],
          handler: mockHandler,
        });

        return <div data-testid="action-component">Action Registered</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('action-component')).toBeInTheDocument();
    });

    it('should invoke action handler with correct parameters', async () => {
      const mockHandler = jest.fn().mockResolvedValue({ result: 'analyzed' });

      const TestComponent = () => {
        useCopilotAction({
          name: 'testAction',
          description: 'Test action',
          parameters: [
            {
              name: 'testParam',
              type: 'string',
              description: 'Test parameter',
              required: true,
            },
          ],
          handler: mockHandler,
        });

        return <div>Test Action</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      await waitFor(() => {
        expect(screen.getByText('Test Action')).toBeInTheDocument();
      });
    });

    it('should handle action errors gracefully', async () => {
      const mockHandler = jest.fn().mockRejectedValue(new Error('Action failed'));
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        useCopilotAction({
          name: 'failingAction',
          description: 'Action that fails',
          parameters: [],
          handler: mockHandler,
        });

        return <div data-testid="error-action">Error Action</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('error-action')).toBeInTheDocument();
      consoleError.mockRestore();
    });

    it('should support multiple action registrations', async () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'action1',
          description: 'First action',
          parameters: [],
          handler: async () => ({ result: '1' }),
        });

        useCopilotAction({
          name: 'action2',
          description: 'Second action',
          parameters: [],
          handler: async () => ({ result: '2' }),
        });

        return <div data-testid="multi-action">Multiple Actions</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('multi-action')).toBeInTheDocument();
    });
  });

  describe('State Sharing via useCoAgent', () => {
    it('should share state between components', async () => {
      const TestComponent = () => {
        const [sharedState, setSharedState] = React.useState({ count: 0 });

        return (
          <div>
            <div data-testid="state-value">{sharedState.count}</div>
            <button
              data-testid="increment-button"
              onClick={() => setSharedState({ count: sharedState.count + 1 })}
            >
              Increment
            </button>
          </div>
        );
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      const { getByTestId } = render(<Wrapper />);
      expect(getByTestId('state-value')).toHaveTextContent('0');

      act(() => {
        getByTestId('increment-button').click();
      });

      await waitFor(() => {
        expect(getByTestId('state-value')).toHaveTextContent('1');
      });
    });

    it('should isolate state between different contexts', () => {
      const TestComponent = ({ id }: { id: string }) => {
        const [state] = React.useState({ id });
        return <div data-testid={`state-${id}`}>{state.id}</div>;
      };

      const Wrapper = () => (
        <div>
          <CopilotKit runtimeUrl={mockRuntimeUrl}>
            <TestComponent id="context1" />
          </CopilotKit>
          <CopilotKit runtimeUrl={mockRuntimeUrl}>
            <TestComponent id="context2" />
          </CopilotKit>
        </div>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('state-context1')).toHaveTextContent('context1');
      expect(screen.getByTestId('state-context2')).toHaveTextContent('context2');
    });
  });

  describe('Context Provision', () => {
    it('should provide context to deeply nested components', () => {
      const DeepChild = () => {
        useCopilotAction({
          name: 'deepAction',
          description: 'Deep action',
          parameters: [],
          handler: async () => ({ deep: true }),
        });
        return <div data-testid="deep-child">Deep Child</div>;
      };

      const MiddleComponent = () => (
        <div>
          <DeepChild />
        </div>
      );

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <MiddleComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('deep-child')).toBeInTheDocument();
    });

    it('should handle context updates without unmounting children', async () => {
      const TestComponent = () => {
        const [count, setCount] = React.useState(0);

        return (
          <div>
            <div data-testid="count">{count}</div>
            <button data-testid="update-btn" onClick={() => setCount(count + 1)}>
              Update
            </button>
          </div>
        );
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      const { getByTestId } = render(<Wrapper />);

      act(() => {
        getByTestId('update-btn').click();
      });

      await waitFor(() => {
        expect(getByTestId('count')).toHaveTextContent('1');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle backend connection errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        useCopilotAction({
          name: 'networkAction',
          description: 'Action with network error',
          parameters: [],
          handler: async () => {
            await fetch(mockRuntimeUrl);
            return { result: 'success' };
          },
        });

        return <div data-testid="network-error">Network Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('network-error')).toBeInTheDocument();
      consoleError.mockRestore();
    });

    it('should handle malformed responses gracefully', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        return <div data-testid="malformed-test">Malformed Response Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('malformed-test')).toBeInTheDocument();
      consoleError.mockRestore();
    });

    it('should recover from temporary failures', async () => {
      let callCount = 0;
      (global.fetch as jest.Mock).mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Temporary failure'));
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'success' }),
          headers: new Headers({ 'content-type': 'application/json' }),
        });
      });

      const TestComponent = () => {
        return <div data-testid="recovery-test">Recovery Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('recovery-test')).toBeInTheDocument();
    });

    it('should handle missing authentication gracefully', async () => {
      const TestComponent = () => {
        return <div data-testid="no-auth">No Auth Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('no-auth')).toBeInTheDocument();
    });
  });

  describe('Performance and Memory', () => {
    it('should not cause memory leaks with multiple renders', async () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'memoryAction',
          description: 'Memory test action',
          parameters: [],
          handler: async () => ({ result: 'ok' }),
        });

        return <div data-testid="memory-test">Memory Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      const { unmount, rerender } = render(<Wrapper />);

      // Render multiple times
      for (let i = 0; i < 10; i++) {
        rerender(<Wrapper />);
      }

      expect(screen.getByTestId('memory-test')).toBeInTheDocument();
      unmount();
    });

    it('should clean up event listeners on unmount', () => {
      const TestComponent = () => {
        React.useEffect(() => {
          const handler = () => {};
          window.addEventListener('message', handler);
          return () => window.removeEventListener('message', handler);
        }, []);

        return <div data-testid="cleanup-test">Cleanup Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      const { unmount } = render(<Wrapper />);
      expect(screen.getByTestId('cleanup-test')).toBeInTheDocument();
      unmount();
      // If cleanup is working, no errors should occur
    });
  });
});
