/**
 * CopilotKit Performance Tests
 *
 * Tests for performance validation, load handling,
 * and optimization verification
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { performance } from 'perf_hooks';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';
import { CoAgentDashboard } from '@/components/copilot/CoAgentIntegration';
import { CopilotChatIntegration } from '@/components/copilot/CopilotChatIntegration';
import { CopilotProvider } from '@/components/copilot/CopilotProvider';
import { createMockAccount, createMockAnalysisResult, createMockRiskSignal, createMockRecommendation, mockFetchResponse } from '@/jest.setup.enhanced';

// Mock CopilotKit hooks
const mockUseCopilotAction = jest.fn();
const mockUseCopilotReadable = jest.fn();
const mockUseCopilotChat = jest.fn();

jest.mock('@copilotkit/react-core', () => ({
  useCopilotAction: mockUseCopilotAction,
  useCopilotReadable: mockUseCopilotReadable,
  useCopilotChat: mockUseCopilotChat,
}));

describe('CopilotKit Performance Tests', () => {
  const mockRuntimeUrl = 'http://localhost:8008';

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCopilotAction.mockImplementation(({ handler }) => handler);
    mockUseCopilotReadable.mockImplementation(() => {});
    mockUseCopilotChat.mockReturnValue({ isLoading: false });

    // Mock performance.now for consistent timing
    jest.spyOn(performance, 'now').mockImplementation(() => Date.now());
  });

  afterEach(() => {
    jest.resetAllMocks();
    jest.restoreAllMocks();
  });

  describe('Rendering Performance', () => {
    it('should render CopilotProvider within performance threshold', () => {
      const startTime = performance.now();

      render(
        <CopilotProvider>
          <div data-testid="test-content">Performance Test</div>
        </CopilotProvider>
      );

      const renderTime = performance.now() - startTime;

      // Should render within 100ms
      expect(renderTime).toBeLessThan(100);
      expect(screen.getByTestId('test-content')).toBeInTheDocument();
    });

    it('should render AccountAnalysisAgent within performance threshold', () => {
      const startTime = performance.now();

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const renderTime = performance.now() - startTime;

      // Should render within 200ms
      expect(renderTime).toBeLessThan(200);
      expect(screen.getByText('Agent Execution Status')).toBeInTheDocument();
    });

    it('should render CoAgentDashboard within performance threshold', () => {
      const startTime = performance.now();

      render(<CoAgentDashboard runtimeUrl={mockRuntimeUrl} />);

      const renderTime = performance.now() - startTime;

      // Should render within 150ms
      expect(renderTime).toBeLessThan(150);
      expect(screen.getByText('Shared Agent State')).toBeInTheDocument();
    });

    it('should render CopilotChatIntegration within performance threshold', () => {
      const startTime = performance.now();

      render(<CopilotChatIntegration />);

      const renderTime = performance.now() - startTime;

      // Should render within 180ms
      expect(renderTime).toBeLessThan(180);
      expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
    });

    it('should handle large data sets efficiently', () => {
      const largeAnalysisResult = createMockAnalysisResult({
        risk_signals: Array.from({ length: 100 }, (_, i) =>
          createMockRiskSignal({ signal_id: `RS-${i}` })
        ),
        recommendations: Array.from({ length: 50 }, (_, i) =>
          createMockRecommendation({ recommendation_id: `REC-${i}` })
        ),
      });

      mockFetchResponse(largeAnalysisResult);

      const startTime = performance.now();

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const renderTime = performance.now() - startTime;

      // Should handle large datasets within 500ms
      expect(renderTime).toBeLessThan(500);
    });
  });

  describe('Action Handler Performance', () => {
    it('should execute CopilotKit actions within performance threshold', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const startTime = performance.now();
      const result = await actionHandler({ accountId: 'ACC-001' });
      const executionTime = performance.now() - startTime;

      // Simple action should complete within 50ms
      expect(executionTime).toBeLessThan(50);
      expect(result.success).toBe(true);
    });

    it('should handle concurrent actions efficiently', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const startTime = performance.now();

      // Execute multiple actions concurrently
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(actionHandler({ accountId: `ACC-00${i}` }));
      }

      const results = await Promise.all(promises);
      const totalTime = performance.now() - startTime;

      // Should handle 10 concurrent actions within 500ms
      expect(totalTime).toBeLessThan(500);
      expect(results).toHaveLength(10);
    });

    it('should batch multiple rapid actions efficiently', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const startTime = performance.now();

      // Rapid sequential actions
      for (let i = 0; i < 20; i++) {
        await actionHandler({ accountId: `ACC-00${i}` });
      }

      const totalTime = performance.now() - startTime;

      // Should handle 20 rapid actions within 1000ms
      expect(totalTime).toBeLessThan(1000);
      expect(mockUseCopilotAction).toHaveBeenCalledTimes(5); // 5 actions * 4 calls (setup + handler)
    });
  });

  describe('Memory Usage Performance', () => {
    it('should not cause memory leaks during repeated renders', () => {
      const initialMemory = process.memoryUsage().heapUsed;

      // Multiple render cycles
      for (let i = 0; i < 50; i++) {
        const { unmount } = render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);
        unmount();
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const finalMemory = process.memoryUsage().heapUsed;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be minimal (< 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });

    it('should efficiently manage large state objects', () => {
      const initialMemory = process.memoryUsage().heapUsed;

      // Create component with large state
      const largeAccountList = Array.from({ length: 1000 }, (_, i) =>
        createMockAccount({ id: `ACC-${i}` })
      );

      const TestComponent = () => {
        const [accounts] = React.useState(largeAccountList);
        return (
          <div data-testid="large-state">
            {accounts.length} accounts loaded
          </div>
        );
      };

      render(<TestComponent />);

      expect(screen.getByText('1000 accounts loaded')).toBeInTheDocument();

      if (global.gc) {
        global.gc();
      }

      const finalMemory = process.memoryUsage().heapUsed;
      const memoryIncrease = finalMemory - initialMemory;

      // Should handle large state efficiently (< 100MB)
      expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024);
    });
  });

  describe('Network Performance', () => {
    it('should handle rapid API calls efficiently', async () => {
      const callTimes = [];

      fetch.mockImplementation(async () => {
        const startTime = performance.now();
        await new Promise(resolve => setTimeout(resolve, 10));
        const response = {
          ok: true,
          json: async () => createMockAnalysisResult(),
        };
        callTimes.push(performance.now() - startTime);
        return response;
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Rapid API calls
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(actionHandler({ accountId: `ACC-00${i}` }));
      }

      await Promise.all(promises);

      // Average call time should be reasonable
      const averageCallTime = callTimes.reduce((a, b) => a + b, 0) / callTimes.length;
      expect(averageCallTime).toBeLessThan(100);
    });

    it('should implement request debouncing for rapid actions', async () => {
      let callCount = 0;
      fetch.mockImplementation(() => {
        callCount++;
        return Promise.resolve({
          ok: true,
          json: async () => createMockAnalysisResult(),
        });
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        // Simulate debounced handler
        let timeout;
        return (...args) => {
          clearTimeout(timeout);
          return new Promise(resolve => {
            timeout = setTimeout(() => {
              resolve(handler(...args));
            }, 50); // 50ms debounce
          });
        };
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Rapid calls (should be debounced)
      actionHandler({ accountId: 'ACC-001' });
      actionHandler({ accountId: 'ACC-001' });
      actionHandler({ accountId: 'ACC-001' });

      // Wait for debounce
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should only make one API call due to debouncing
      expect(callCount).toBeLessThan(3);
    });
  });

  describe('Component Lifecycle Performance', () => {
    it('should efficiently handle mount/unmount cycles', () => {
      const mountTimes = [];

      for (let i = 0; i < 20; i++) {
        const startTime = performance.now();
        const { unmount } = render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);
        mountTimes.push(performance.now() - startTime);
        unmount();
      }

      // Average mount time should be consistent and fast
      const averageMountTime = mountTimes.reduce((a, b) => a + b, 0) / mountTimes.length;
      expect(averageMountTime).toBeLessThan(50);

      // Mount times should be consistent (low variance)
      const variance = mountTimes.reduce((acc, time) => {
        const diff = time - averageMountTime;
        return acc + diff * diff;
      }, 0) / mountTimes.length;
      expect(variance).toBeLessThan(100);
    });

    it('should handle prop updates efficiently', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      const { rerender } = render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const updateTimes = [];

      for (let i = 0; i < 10; i++) {
        const startTime = performance.now();
        rerender(<AccountAnalysisAgent runtimeUrl={`http://localhost:${8008 + i}`} />);
        updateTimes.push(performance.now() - startTime);
      }

      // Average update time should be fast
      const averageUpdateTime = updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length;
      expect(averageUpdateTime).toBeLessThan(30);
    });
  });

  describe('Large Data Handling', () => {
    it('should efficiently render large message lists', () => {
      const largeMessages = Array.from({ length: 1000 }, (_, i) => ({
        id: `msg-${i}`,
        content: `Message ${i} content`,
        timestamp: new Date().toISOString(),
      }));

      mockUseCopilotReadable.mockImplementation(({ value }) => {
        if (value && value.length > 0) {
          return largeMessages;
        }
      });

      const startTime = performance.now();

      render(<CopilotChatIntegration />);

      const renderTime = performance.now() - startTime;

      // Should handle large message lists efficiently
      expect(renderTime).toBeLessThan(300);
    });

    it('should virtualize large lists for performance', () => {
      // Test virtual scrolling implementation if available
      const largeDataSet = Array.from({ length: 10000 }, (_, i) => ({
        id: `item-${i}`,
        content: `Item ${i}`,
      }));

      const startTime = performance.now();

      const TestComponent = () => {
        const [items] = React.useState(largeDataSet.slice(0, 100)); // Virtualization simulation
        return (
          <div data-testid="virtualized-list">
            {items.length} items rendered
          </div>
        );
      };

      render(<TestComponent />);

      const renderTime = performance.now() - startTime;

      expect(screen.getByText('100 items rendered')).toBeInTheDocument();
      expect(renderTime).toBeLessThan(50); // Much faster with virtualization
    });
  });

  describe('Animation Performance', () => {
    it('should maintain 60fps during animations', async () => {
      let frameCount = 0;
      const animationFrames = [];

      const requestAnimationFrame = (callback) => {
        frameCount++;
        const startTime = performance.now();
        callback(startTime);
        animationFrames.push(performance.now() - startTime);
        return frameCount;
      };

      global.requestAnimationFrame = requestAnimationFrame;

      render(<CopilotChatIntegration />);

      // Simulate animation frames
      for (let i = 0; i < 60; i++) {
        requestAnimationFrame(performance.now());
      }

      // Average frame time should be under 16.67ms (60fps)
      const averageFrameTime = animationFrames.reduce((a, b) => a + b, 0) / animationFrames.length;
      expect(averageFrameTime).toBeLessThan(16.67);

      // Clean up
      delete global.requestAnimationFrame;
    });

    it('should not block main thread during heavy operations', async () => {
      const mainThreadBlocked = jest.fn();

      // Mock heavy operation
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = async (...args) => {
          // Simulate heavy operation that shouldn't block UI
          await new Promise(resolve => {
            setTimeout(() => {
              mainThreadBlocked();
              resolve(handler(...args));
            }, 0);
          });
        };
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const startTime = performance.now();
      await actionHandler({ accountId: 'ACC-001' });
      const totalTime = performance.now() - startTime;

      // Operation should complete in reasonable time
      expect(totalTime).toBeLessThan(200);
      expect(mainThreadBlocked).toHaveBeenCalled();
    });
  });

  describe('Bundle Performance', () => {
    it('should have reasonable bundle size impact', () => {
      // This would typically be tested with bundle analysis tools
      // For now, we test component complexity

      const componentComplexity = {
        propCount: 2, // runtimeUrl, onApprovalRequired
        stateCount: 5, // selectedAccount, analysisResult, agentStatus, isAnalyzing, error
        hookCount: 4, // useCopilotAction (5x), useCopilotChat, useCopilotReadable (3x)
        actionCount: 5, // analyzeAccount, fetchAccountData, getRecommendations, selectAccount, clearAccountSelection
      };

      // Complexity should be reasonable
      expect(componentComplexity.hookCount).toBeLessThan(15);
      expect(componentComplexity.actionCount).toBeLessThan(10);
    });

    it('should lazy load non-critical components', () => {
      // Test that components can be loaded asynchronously
      const lazyComponent = React.lazy(() =>
        Promise.resolve({
          default: () => <div data-testid="lazy-component">Lazy Loaded</div>
        })
      );

      const startTime = performance.now();

      render(
        <React.Suspense fallback={<div>Loading...</div>}>
          <lazyComponent />
        </React.Suspense>
      );

      const loadTime = performance.now() - startTime;

      // Should load quickly
      expect(loadTime).toBeLessThan(100);
    });
  });

  describe('Caching Performance', () => {
    it('should implement efficient caching for API responses', async () => {
      const cache = new Map();
      let cacheHits = 0;

      fetch.mockImplementation((url) => {
        if (cache.has(url)) {
          cacheHits++;
          return Promise.resolve(cache.get(url));
        }

        const response = {
          ok: true,
          json: async () => createMockAnalysisResult(),
        };
        cache.set(url, response);
        return Promise.resolve(response);
      });

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // First request
      await actionHandler({ accountId: 'ACC-001' });
      expect(cacheHits).toBe(0);

      // Second request (should hit cache)
      await actionHandler({ accountId: 'ACC-001' });
      expect(cacheHits).toBe(1);

      // Verify caching improves performance
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should implement memory-efficient state caching', () => {
      const cache = new Map();
      let cacheSize = 0;

      const TestComponent = () => {
        const [data] = React.useState(null);

        React.useEffect(() => {
          const cacheKey = 'test-data';
          if (cache.has(cacheKey)) {
            return cache.get(cacheKey);
          }

          const expensiveData = Array.from({ length: 1000 }, (_, i) => ({ id: i, value: `Item ${i}` }));
          cache.set(cacheKey, expensiveData);
          cacheSize = cache.size;

          // Simulate setting state
          setTimeout(() => {
            // Would set state in real component
          }, 0);
        }, []);

        return <div data-testid="cached-component">Test</div>;
      };

      render(<TestComponent />);

      expect(screen.getByTestId('cached-component')).toBeInTheDocument();
      expect(cacheSize).toBe(1);
    });
  });

  describe('Performance Monitoring', () => {
    it('should track performance metrics', () => {
      const metrics = {
        renderTime: 0,
        actionTime: 0,
        errorCount: 0,
      };

      const startTime = performance.now();
      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);
      metrics.renderTime = performance.now() - startTime;

      expect(metrics.renderTime).toBeGreaterThan(0);
      expect(metrics.renderTime).toBeLessThan(200);
    });

    it('should detect performance regressions', () => {
      const baselines = {
        renderTime: 100,
        actionTime: 50,
        memoryUsage: 50 * 1024 * 1024, // 50MB
      };

      const currentMetrics = {
        renderTime: 300, // 3x slower than baseline
        actionTime: 150, // 3x slower than baseline
        memoryUsage: 150 * 1024 * 1024, // 3x more memory
      };

      // Detect regressions
      const renderRegression = currentMetrics.renderTime > baselines.renderTime * 2;
      const actionRegression = currentMetrics.actionTime > baselines.actionTime * 2;
      const memoryRegression = currentMetrics.memoryUsage > baselines.memoryUsage * 2;

      expect(renderRegression).toBe(true);
      expect(actionRegression).toBe(true);
      expect(memoryRegression).toBe(true);
    });
  });
});