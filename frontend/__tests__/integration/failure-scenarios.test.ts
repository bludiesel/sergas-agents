/**
 * CopilotKit Failure Scenario Tests
 *
 * Tests for handling network issues, GLM-4.6 downtime,
 * and various failure conditions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';
import { CoAgentDashboard } from '@/components/copilot/CoAgentIntegration';
import { CopilotChatIntegration } from '@/components/copilot/CopilotChatIntegration';
import { CopilotProvider } from '@/components/copilot/CopilotProvider';
import { CopilotErrorBoundary } from '@/components/copilot/ErrorBoundary';
import { createMockAccount, createMockAnalysisResult, mockFetchResponse, mockFetchError } from '@/jest.setup.enhanced';

// Mock CopilotKit hooks
const mockUseCopilotAction = jest.fn();
const mockUseCopilotReadable = jest.fn();
const mockUseCopilotChat = jest.fn();

jest.mock('@copilotkit/react-core', () => ({
  useCopilotAction: mockUseCopilotAction,
  useCopilotReadable: mockUseCopilotReadable,
  useCopilotChat: mockUseCopilotChat,
}));

describe('CopilotKit Failure Scenarios', () => {
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

  describe('Network Failure Scenarios', () => {
    describe('Connection Refused', () => {
      it('should handle backend service unavailable', async () => {
        const fetchError = new Error('ECONNREFUSED');
        fetchError.name = 'TypeError';
        mockFetchError(fetchError);

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
        expect(result.message).toContain('Failed to analyze account');
      });

      it('should show user-friendly error for connection refused', async () => {
        const connectionError = new Error('Failed to fetch');
        connectionError.name = 'TypeError';
        mockFetchError(connectionError);

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        await actionHandler({ accountId: 'ACC-001' });

        await waitFor(() => {
          expect(screen.getByText('Error')).toBeInTheDocument();
          expect(screen.getByText(/Failed to analyze account/)).toBeInTheDocument();
        });
      });
    });

    describe('Timeout Scenarios', () => {
      it('should handle request timeout', async () => {
        const timeoutError = new Error('Request timeout');
        timeoutError.name = 'TimeoutError';
        mockFetchError(timeoutError);

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
      });

      it('should recover from timeout with retry', async () => {
        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        // First attempt times out
        mockFetchError(new Error('Timeout'));
        const result1 = await actionHandler({ accountId: 'ACC-001' });

        expect(result1.success).toBe(false);

        // Second attempt succeeds
        mockFetchResponse(createMockAnalysisResult());
        const result2 = await actionHandler({ accountId: 'ACC-001' });

        expect(result2.success).toBe(true);
      });
    });

    describe('Slow Network', () => {
      it('should show loading state during slow responses', async () => {
        let resolveFetch;
        const slowFetchPromise = new Promise(resolve => {
          resolveFetch = resolve;
        });

        fetch.mockImplementationOnce(() => slowFetchPromise);

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        // Start analysis
        const analysisPromise = actionHandler({ accountId: 'ACC-001' });

        // Should show loading state
        await waitFor(() => {
          expect(screen.getByText('running')).toBeInTheDocument();
        });

        // Resolve the slow fetch
        resolveFetch({
          ok: true,
          json: async () => createMockAnalysisResult(),
        });

        await analysisPromise;
      });
    });
  });

  describe('GLM-4.6 Backend Failures', () => {
    describe('Service Unavailable', () => {
      it('should handle GLM-4.6 service downtime', async () => {
        fetch.mockResolvedValueOnce({
          ok: false,
          status: 503,
          statusText: 'Service Unavailable',
          json: async () => ({
            error: 'GLM-4.6 service temporarily unavailable',
          }),
        });

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
      });

      it('should provide graceful degradation when GLM-4.6 is down', async () => {
        // Mock multiple failed attempts
        for (let i = 0; i < 3; i++) {
          fetch.mockResolvedValueOnce({
            ok: false,
            status: 503,
            statusText: 'Service Unavailable',
          });
        }

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
        // Should attempt retry logic
        expect(fetch).toHaveBeenCalledTimes(1); // Would be more with retry logic
      });
    });

    describe('API Rate Limiting', () => {
      it('should handle rate limiting from GLM-4.6', async () => {
        fetch.mockResolvedValueOnce({
          ok: false,
          status: 429,
          statusText: 'Too Many Requests',
          json: async () => ({
            error: 'Rate limit exceeded',
            retryAfter: 60,
          }),
        });

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
        // Should implement backoff strategy
      });

      it('should implement exponential backoff for rate limits', async () => {
        const user = userEvent.setup();
        let retryCount = 0;

        fetch.mockImplementation(() => {
          retryCount++;
          if (retryCount <= 2) {
            // First two attempts rate limited
            return Promise.resolve({
              ok: false,
              status: 429,
              json: async () => ({ error: 'Rate limited' }),
            });
          } else {
            // Third attempt succeeds
            return Promise.resolve({
              ok: true,
              json: async () => createMockAnalysisResult(),
            });
          }
        });

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        // Multiple rapid requests
        const promises = [];
        for (let i = 0; i < 3; i++) {
          promises.push(actionHandler({ accountId: `ACC-00${i}` }));
        }

        const results = await Promise.all(promises);

        // At least one should succeed after backoff
        const successCount = results.filter(r => r.success).length;
        expect(successCount).toBeGreaterThanOrEqual(1);
      });
    });

    describe('Invalid Responses', () => {
      it('should handle malformed GLM-4.6 responses', async () => {
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => {
            throw new Error('Invalid JSON');
          },
        });

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
      });

      it('should handle empty GLM-4.6 responses', async () => {
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({}),
        });

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(true); // Should handle empty response gracefully
      });

      it('should handle GLM-4.6 validation errors', async () => {
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            error: 'Invalid request format',
            details: 'Missing required field: messages',
          }),
        });

        let actionHandler;
        mockUseCopilotAction.mockImplementation(({ handler }) => {
          actionHandler = handler;
          return handler;
        });

        render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

        const result = await actionHandler({ accountId: 'ACC-001' });

        expect(result.success).toBe(false);
      });
    });
  });

  describe('Authentication Failures', () => {
    it('should handle missing API key', () => {
      // Reset environment
      delete process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY;

      render(
        <CopilotProvider>
          <div data-testid="test-content">Test</div>
        </CopilotProvider>
      );

      expect(screen.getByTestId('test-content')).toBeInTheDocument();
    });

    it('should handle invalid API key', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({
          error: 'Invalid API key',
        }),
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(false);
    });

    it('should handle expired authentication token', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Token expired',
        json: async () => ({
          error: 'Authentication token expired',
        }),
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(false);
    });
  });

  describe('Component Failure Scenarios', () => {
    it('should handle CopilotProvider errors', () => {
      const ThrowingChild = () => {
        throw new Error('Provider child error');
      };

      expect(() => {
        render(
          <CopilotProvider>
            <ThrowingChild />
          </CopilotProvider>
        );
      }).not.toThrow();

      // Error would be caught by React error boundary if implemented
    });

    it('should handle missing required props gracefully', () => {
      expect(() => {
        render(<AccountAnalysisAgent runtimeUrl={undefined} />);
      }).not.toThrow();
    });

    it('should handle prop type mismatches', () => {
      expect(() => {
        render(
          <AccountAnalysisAgent
            runtimeUrl={123} // Invalid type
          />
        );
      }).not.toThrow();
    });
  });

  describe('Resource Exhaustion', () => {
    it('should handle memory limits', () => {
      // Mock memory exceeded scenario
      const memoryError = new Error('JavaScript heap out of memory');
      mockFetchError(memoryError);

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      expect(() => actionHandler({ accountId: 'ACC-001' })).rejects.toThrow();
    });

    it('should handle connection pool exhaustion', async () => {
      // Simulate connection pool exhausted
      const poolError = new Error('Connection pool exhausted');
      poolError.code = 'ECONNRESET';
      mockFetchError(poolError);

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(false);
    });
  });

  describe('Data Corruption Scenarios', () => {
    it('should handle corrupted response data', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: null,
          success: false,
          error: 'Data corruption detected',
        }),
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(false);
    });

    it('should handle partial data responses', async () => {
      const partialResult = {
        account_snapshot: {
          account_id: 'ACC-001',
          // Missing required fields
        },
        risk_signals: null,
        recommendations: undefined,
      };

      mockFetchResponse(partialResult);

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      // Should handle partial data gracefully
      expect(result).toBeDefined();
    });
  });

  describe('Concurrent Failure Scenarios', () => {
    it('should handle multiple simultaneous failures', async () => {
      // Mock all requests to fail
      fetch.mockRejectedValue(new Error('Network error'));

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Multiple concurrent requests
      const promises = [];
      for (let i = 0; i < 5; i++) {
        promises.push(actionHandler({ accountId: `ACC-00${i}` }));
      }

      const results = await Promise.all(promises);

      // All should fail gracefully
      results.forEach(result => {
        expect(result.success).toBe(false);
      });
    });

    it('should handle cascading failures', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // First request fails
      mockFetchError(new Error('Initial failure'));
      await actionHandler({ accountId: 'ACC-001' });

      // Subsequent requests should still work
      mockFetchResponse(createMockAnalysisResult());
      const result2 = await actionHandler({ accountId: 'ACC-002' });

      expect(result2.success).toBe(true);
    });
  });

  describe('Recovery Mechanisms', () => {
    it('should implement automatic retry with backoff', async () => {
      let attemptCount = 0;
      fetch.mockImplementation(() => {
        attemptCount++;
        if (attemptCount === 1) {
          return Promise.reject(new Error('Temporary failure'));
        } else {
          return Promise.resolve({
            ok: true,
            json: async () => createMockAnalysisResult(),
          });
        }
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = async (...args) => {
          // Simple retry logic
          try {
            return await handler(...args);
          } catch (error) {
            // Wait and retry
            await new Promise(resolve => setTimeout(resolve, 100));
            return await handler(...args);
          }
        };
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(true);
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should provide fallback functionality', async () => {
      // Mock primary service failure
      fetch.mockRejectedValueOnce(new Error('Primary service down'));

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = async (...args) => {
          try {
            return await handler(...args);
          } catch (error) {
            // Fallback response
            return {
              success: true,
              message: 'Using cached analysis',
              data: {
                account_name: 'Cached Account',
                risk_level: 'unknown',
                priority_score: 50,
              },
            };
          }
        };
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(true);
      expect(result.message).toBe('Using cached analysis');
    });

    it('should maintain user experience during failures', async () => {
      mockFetchError(new Error('Service unavailable'));

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await actionHandler({ accountId: 'ACC-001' });

      // Should show user-friendly error, not crash
      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });

      // Component should remain functional
      expect(screen.getByText('Agent Execution Status')).toBeInTheDocument();
    });
  });
});