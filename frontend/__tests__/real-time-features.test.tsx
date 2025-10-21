/**
 * Real-Time Features Test Suite
 *
 * Comprehensive tests for WebSocket, SSE, and performance optimization features.
 * Validates connection management, streaming, and real-time updates.
 *
 * Features Tested:
 * - WebSocket connection management
 * - Server-Sent Events streaming
 * - Performance optimization utilities
 * - Real-time UI components
 * - Error handling and recovery
 */

import React from 'react';
import { renderHook, act, render, screen, waitFor, fireEvent } from '@testing-library/react';
import { jest } from '@jest/globals';

// Mock WebSocket and EventSource
global.WebSocket = jest.fn(() => ({
  readyState: WebSocket.OPEN,
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
})) as any;

global.EventSource = jest.fn(() => ({
  readyState: EventSource.OPEN,
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
})) as any;

// Mock performance API
Object.defineProperty(global, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    memory: {
      usedJSHeapSize: 25000000, // 25MB
      jsHeapSizeLimit: 50000000, // 50MB
    },
  },
  writable: true,
});

// Import components and hooks to test
import {
  useWebSocketManager,
  useWebSocketPerformance,
} from '../../lib/websocket-manager';

import {
  useSSEStream,
  useCopilotStreaming,
} from '../../lib/sse-streaming';

import {
  usePerformanceMonitor,
  useOptimizedState,
  useWebSocketOptimization,
  useMemoryManagement,
} from '../../lib/performance-optimization';

import {
  ConnectionStatusIndicator,
  AgentStatusCard,
  PerformanceMetricsPanel,
  ConnectionStatusPanel,
} from '../../components/copilot/RealTimeComponents';

describe('Real-Time Features', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // ============================================================================
  // WebSocket Manager Tests
  // ============================================================================

  describe('useWebSocketManager', () => {
    test('should initialize with disconnected status', () => {
      const { result } = renderHook(() => useWebSocketManager('ws://localhost:7007'));

      expect(result.current.connectionState.status).toBe('disconnected');
      expect(result.current.isConnected).toBe(false);
      expect(result.current.agents.size).toBe(0);
      expect(result.current.messages).toEqual([]);
    });

    test('should connect successfully', async () => {
      const mockWS = {
        readyState: WebSocket.CONNECTING,
        send: jest.fn(),
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.WebSocket as jest.Mock).mockImplementation(() => mockWS);

      const { result } = renderHook(() => useWebSocketManager('ws://localhost:7007'));

      // Simulate WebSocket open
      act(() => {
        mockWS.readyState = WebSocket.OPEN;
        const openEvent = new Event('open');
        mockWS.addEventListener.mock.calls[0][1](openEvent);
      });

      expect(result.current.connectionState.status).toBe('connected');
      expect(result.current.isConnected).toBe(true);
    });

    test('should handle reconnection with backoff', async () => {
      const mockWS = {
        readyState: WebSocket.CONNECTING,
        send: jest.fn(),
        close: jest.fn().mockImplementation(() => {
          mockWS.readyState = WebSocket.CLOSED;
        }),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.WebSocket as jest.Mock).mockImplementation(() => mockWS);

      const { result } = renderHook(() => useWebSocketManager('ws://localhost:7007'));

      // Simulate connection failure
      act(() => {
        mockWS.readyState = WebSocket.CLOSED;
        const closeEvent = new CloseEvent('close', { code: 1006 });
        mockWS.addEventListener.mock.calls[0][1](closeEvent);
      });

      expect(result.current.connectionState.status).toBe('reconnecting');
      expect(result.current.connectionState.reconnectAttempts).toBeGreaterThan(0);
    });

    test('should send and receive messages', async () => {
      const mockWS = {
        readyState: WebSocket.OPEN,
        send: jest.fn(),
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.WebSocket as jest.Mock).mockImplementation(() => mockWS);

      const { result } = renderHook(() => useWebSocketManager('ws://localhost:7007'));

      // Simulate WebSocket open
      act(() => {
        mockWS.readyState = WebSocket.OPEN;
        const openEvent = new Event('open');
        mockWS.addEventListener.mock.calls[0][1](openEvent);
      });

      // Send a message
      act(() => {
        result.current.sendStateUpdate({ test: 'value' }, 'test-agent');
      });

      expect(mockWS.send).toHaveBeenCalled();

      // Simulate receiving a message
      act(() => {
        const messageEvent = new MessageEvent('message', {
          data: JSON.stringify({
            type: 'state_update',
            payload: { test: 'updated' },
            timestamp: new Date().toISOString(),
            messageId: 'test-message-id'
          })
        });
        mockWS.addEventListener.mock.calls.find(call => call[0] === 'message')[1](messageEvent);
      });

      expect(result.current.messages.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // SSE Streaming Tests
  // ============================================================================

  describe('useSSEStream', () => {
    test('should initialize with disconnected status', () => {
      const { result } = renderHook(() => useSSEStream({
        endpoint: '/api/copilotkit?protocol=sse'
      }));

      expect(result.current.streamState.isConnected).toBe(false);
      expect(result.current.events).toEqual([]);
      expect(result.current.agentData.size).toBe(0);
    });

    test('should connect to SSE endpoint', async () => {
      const mockES = {
        readyState: EventSource.OPEN,
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.EventSource as jest.Mock).mockImplementation(() => mockES);

      const { result } = renderHook(() => useSSEStream({
        endpoint: '/api/copilotkit?protocol=sse',
        autoReconnect: true
      }));

      expect(global.EventSource).toHaveBeenCalledWith('/api/copilotkit?protocol=sse');
    });

    test('should parse SSE messages correctly', async () => {
      const mockES = {
        readyState: EventSource.OPEN,
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.EventSource as jest.Mock).mockImplementation(() => mockES);

      const { result } = renderHook(() => useSSEStream({
        endpoint: '/api/copilotkit?protocol=sse'
      }));

      // Simulate receiving a message
      act(() => {
        const messageEvent = new MessageEvent('message', {
          data: 'data: {"event":"agent_update","data":{"agentId":"test-agent","status":"running","progress":50}}'
        });
        mockES.addEventListener.mock.calls.find(call => call[0] === 'message')[1](messageEvent);
      });

      expect(result.current.agentData.has('test-agent')).toBe(true);
      const agentData = result.current.agentData.get('test-agent');
      expect(agentData?.status).toBe('running');
      expect(agentData?.progress).toBe(50);
    });

    test('should filter events when specified', async () => {
      const mockES = {
        readyState: EventSource.OPEN,
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.EventSource as jest.Mock).mockImplementation(() => mockES);

      const { result } = renderHook(() => useSSEStream({
        endpoint: '/api/copilotkit?protocol=sse',
        eventFilter: ['agent_update']
      }));

      // Simulate receiving different event types
      act(() => {
        const agentUpdateEvent = new MessageEvent('message', {
          data: 'data: {"event":"agent_update","data":{"agentId":"test"}}'
        });
        const otherEvent = new MessageEvent('message', {
          data: 'data: {"event":"other_event","data":{"test":true}}'
        });

        mockES.addEventListener.mock.calls.find(call => call[0] === 'message')[1](agentUpdateEvent);
        mockES.addEventListener.mock.calls.find(call => call[0] === 'message')[1](otherEvent);
      });

      // Should only have agent_update events
      const agentUpdateEvents = result.current.events.filter(e => e.event === 'agent_update');
      const otherEvents = result.current.events.filter(e => e.event === 'other_event');

      expect(agentUpdateEvents.length).toBe(1);
      expect(otherEvents.length).toBe(0);
    });
  });

  // ============================================================================
  // Performance Optimization Tests
  // ============================================================================

  describe('usePerformanceMonitor', () => {
    test('should track performance metrics', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      expect(result.current.metrics.updateFrequency).toBe(0);
      expect(result.current.metrics.averageUpdateTime).toBe(0);
      expect(result.current.metrics.memoryUsage).toBe(25); // 25MB from mock
    });

    test('should calculate update frequency correctly', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      // Simulate multiple updates
      act(() => {
        for (let i = 0; i < 5; i++) {
          result.current.trackUpdate();
        }
      });

      expect(result.current.metrics.updateFrequency).toBeGreaterThan(0);
    });

    test('should determine health status correctly', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      // Set healthy metrics
      act(() => {
        result.current.metrics.updateFrequency = 50;
        result.current.metrics.averageUpdateTime = 10;
        result.current.metrics.memoryUsage = 30;
        result.current.metrics.droppedFrames = 2;
      });

      expect(result.current.isHealthy()).toBe(true);

      // Set unhealthy metrics
      act(() => {
        result.current.metrics.updateFrequency = 150;
        result.current.metrics.averageUpdateTime = 25;
        result.current.metrics.memoryUsage = 120;
        result.current.metrics.droppedFrames = 10;
      });

      expect(result.current.isHealthy()).toBe(false);
    });
  });

  describe('useOptimizedState', () => {
    test('should batch state updates', () => {
      const initialState = { counter: 0 };
      const { result } = renderHook(() => useOptimizedState(initialState, {
        debounceMs: 50,
        batchSize: 3,
        enableBatching: true
      }));

      // Trigger multiple rapid updates
      act(() => {
        for (let i = 1; i <= 5; i++) {
          result.current.setState({ counter: i }, 'medium');
        }
      });

      // Should not update immediately due to batching
      jest.advanceTimersByTime(50);

      expect(result.current.state.counter).toBeGreaterThan(0);
    });

    test('should debounce updates when enabled', () => {
      const initialState = { value: '' };
      const { result } = renderHook(() => useOptimizedState(initialState, {
        debounceMs: 100,
        enableDebouncing: true
      }));

      // Trigger rapid updates
      act(() => {
        result.current.setState({ value: 'update1' });
        result.current.setState({ value: 'update2' });
        result.current.setState({ value: 'update3' });
      });

      // Should not update immediately
      expect(result.current.state.value).toBe('');

      // Advance time and update
      jest.advanceTimersByTime(100);
      expect(result.current.state.value).toBe('update3');
    });

    test('should handle priority updates correctly', () => {
      const initialState = { data: [] };
      const { result } = renderHook(() => useOptimizedState(initialState, {
        maxQueueSize: 5
      }));

      // Fill queue with mixed priorities
      act(() => {
        result.current.setState({ data: ['low1'] }, 'low');
        result.current.setState({ data: ['medium1'] }, 'medium');
        result.current.setState({ data: ['high1'] }, 'high');
        result.current.setState({ data: ['critical1'] }, 'critical');
        result.current.setState({ data: ['low2'] }, 'low');
        result.current.setState({ data: ['low3'] }, 'low'); // Should be dropped
      });

      // Process batch
      act(() => {
        result.current.flush();
      });

      // Critical should be processed first, low priority dropped
      expect(result.current.state.data).toContain('critical1');
    });
  });

  describe('useWebSocketOptimization', () => {
    test('should batch messages for sending', () => {
      const { result } = renderHook(() => useWebSocketOptimization());

      // Queue multiple messages
      act(() => {
        result.current.optimizedSend({ type: 'test1' }, 'low');
        result.current.optimizedSend({ type: 'test2' }, 'medium');
        result.current.optimizedSend({ type: 'test3' }, 'high');
        result.current.optimizedSend({ type: 'test4' }, 'critical');
      });

      // Get batched messages
      const batched = result.current.getBatchedMessages(3);

      expect(batched.length).toBeLessThanOrEqual(3);
      expect(batched[0].priority).toBe('critical');
      expect(batched[1].priority).toBe('high');
    });

    test('should track connection health', () => {
      const { result } = renderHook(() => useWebSocketOptimization());

      // Simulate high latency
      act(() => {
        result.current.trackSend(1500);
      });

      expect(result.current.connectionHealth.status).toBe('degraded');

      // Simulate more issues
      act(() => {
        result.current.trackReconnect();
        result.current.trackReconnect();
        result.current.trackReconnect();
      });

      expect(result.current.connectionHealth.status).toBe('critical');
    });
  });

  describe('useMemoryManagement', () => {
    test('should monitor memory usage', () => {
      const { result } = renderHook(() => useMemoryManagement(50));

      expect(result.current.memoryStatus.used).toBe(25);
      expect(result.current.memoryStatus.percentage).toBe(50);
      expect(result.current.isHealthy).toBe(true);
    });

    test('should manage cache correctly', () => {
      const { result } = renderHook(() => useMemoryManagement());

      // Cache data
      act(() => {
        result.current.cache('key1', 'value1', 5000);
        result.current.cache('key2', 'value2', 1000);
      });

      // Retrieve cached data
      expect(result.current.getCached('key1')).toBe('value1');
      expect(result.current.getCached('key2')).toBe('value2');

      // Expire cache entry
      jest.advanceTimersByTime(1500);
      expect(result.current.getCached('key2')).toBeNull();
      expect(result.current.getCached('key1')).toBe('value1');
    });

    test('should trigger cleanup when threshold exceeded', () => {
      const cleanupCallback = jest.fn();
      const { result } = renderHook(() => useMemoryManagement(10));

      act(() => {
        result.current.registerCleanup(cleanupCallback);
      });

      // Mock high memory usage
      (global.performance as any).memory.usedJSHeapSize = 15000000; // 15MB

      // Trigger cleanup
      jest.advanceTimersByTime(5000);

      expect(cleanupCallback).toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Real-Time UI Component Tests
  // ============================================================================

  describe('ConnectionStatusIndicator', () => {
    test('should display connected status', () => {
      render(
        <ConnectionStatusIndicator
          status="connected"
          isConnected={true}
          latency={50}
        />
      );

      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('50ms latency')).toBeInTheDocument();
    });

    test('should display connecting status with animation', () => {
      render(
        <ConnectionStatusIndicator
          status="reconnecting"
          isConnected={false}
        />
      );

      expect(screen.getByText('Reconnecting')).toBeInTheDocument();
    });
  });

  describe('AgentStatusCard', () => {
    test('should display agent status with progress', () => {
      const status = {
        status: 'running' as const,
        progress: 75,
        currentTask: 'Processing data...',
        startTime: new Date(),
      };

      render(
        <AgentStatusCard
          agentId="test-agent"
          status={status}
        />
      );

      expect(screen.getByText('test-agent')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('Processing data...')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
    });

    test('should display completed status', () => {
      const status = {
        status: 'completed' as const,
        progress: 100,
        startTime: new Date(),
      };

      render(
        <AgentStatusCard
          agentId="test-agent"
          status={status}
        />
      );

      expect(screen.getByText('Completed')).toBeInTheDocument();
    });
  });

  describe('PerformanceMetricsPanel', () => {
    test('should display performance metrics', () => {
      const metrics = {
        totalMessages: 1250,
        messagesPerSecond: 15.5,
        averageLatency: 85,
        connectionUptime: 3600,
      };

      render(
        <PerformanceMetricsPanel
          metrics={metrics}
        />
      );

      expect(screen.getByText('1,250')).toBeInTheDocument(); // Total messages
      expect(screen.getByText('15.5')).toBeInTheDocument(); // Messages/sec
      expect(screen.getByText('85ms')).toBeInTheDocument(); // Latency
      expect(screen.getByText('1h 0m')).toBeInTheDocument(); // Uptime
    });
  });

  describe('ConnectionStatusPanel', () => {
    test('should display connection controls', () => {
      const mockConnect = jest.fn();
      const mockDisconnect = jest.fn();

      render(
        <ConnectionStatusPanel
          status="connected"
          isConnected={true}
          latency={45}
          lastConnected={new Date()}
          reconnectAttempts={0}
          onConnect={mockConnect}
          onDisconnect={mockDisconnect}
        />
      );

      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('45ms')).toBeInTheDocument();

      const disconnectButton = screen.getByText('Disconnect');
      fireEvent.click(disconnectButton);

      expect(mockDisconnect).toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Integration Tests
  // ============================================================================

  describe('Integration Tests', () => {
    test('should handle WebSocket reconnection with state recovery', async () => {
      const mockWS = {
        readyState: WebSocket.OPEN,
        send: jest.fn(),
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.WebSocket as jest.Mock).mockImplementation(() => mockWS);

      const { result } = renderHook(() => useWebSocketManager('ws://localhost:7007'));

      // Initial connection
      act(() => {
        mockWS.readyState = WebSocket.OPEN;
        const openEvent = new Event('open');
        mockWS.addEventListener.mock.calls[0][1](openEvent);
      });

      // Send some state
      act(() => {
        result.current.sendStateUpdate({ test: 'value1' }, 'agent1');
      });

      // Simulate disconnection
      act(() => {
        mockWS.readyState = WebSocket.CLOSED;
        const closeEvent = new CloseEvent('close', { code: 1006 });
        mockWS.addEventListener.mock.calls.find(call => call[0] === 'close')[1](closeEvent);
      });

      expect(result.current.connectionState.status).toBe('reconnecting');

      // Simulate reconnection
      act(() => {
        jest.advanceTimersByTime(2000); // Wait for reconnection
        mockWS.readyState = WebSocket.OPEN;
        const openEvent = new Event('open');
        mockWS.addEventListener.mock.calls[0][1](openEvent);
      });

      expect(result.current.connectionState.status).toBe('connected');
    });

    test('should maintain performance during high-frequency updates', async () => {
      const { result: perfResult } = renderHook(() => usePerformanceMonitor());
      const { result: stateResult } = renderHook(() => useOptimizedState({ counter: 0 }, {
        debounceMs: 50,
        enableBatching: true
      }));

      // Simulate high-frequency updates
      for (let i = 0; i < 20; i++) {
        act(() => {
          perfResult.current.trackUpdate();
          stateResult.current.setState({ counter: i });
        });
      }

      jest.advanceTimersByTime(50);

      // Performance should remain healthy
      expect(perfResult.current.isHealthy()).toBe(true);

      // State should be updated (batched)
      expect(stateResult.current.state.counter).toBe(19); // Last update
    });

    test('should handle concurrent WebSocket and SSE streams', async () => {
      const mockWS = {
        readyState: WebSocket.OPEN,
        send: jest.fn(),
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      const mockES = {
        readyState: EventSource.OPEN,
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.WebSocket as jest.Mock).mockImplementation(() => mockWS);
      (global.EventSource as jest.Mock).mockImplementation(() => mockES);

      const wsResult = renderHook(() => useWebSocketManager('ws://localhost:7007'));
      const sseResult = renderHook(() => useSSEStream({
        endpoint: '/api/copilotkit?protocol=sse'
      }));

      // Connect both
      act(() => {
        mockWS.readyState = WebSocket.OPEN;
        mockES.readyState = EventSource.OPEN;

        const wsOpenEvent = new Event('open');
        const esOpenEvent = new Event('open');

        mockWS.addEventListener.mock.calls[0][1](wsOpenEvent);
        mockES.addEventListener.mock.calls[0][1](esOpenEvent);
      });

      expect(wsResult.current.isConnected).toBe(true);
      expect(sseResult.current.streamState.isConnected).toBe(true);

      // Send messages via WebSocket
      act(() => {
        wsResult.current.sendAgentMessage('agent1', 'agent2', 'test', {});
      });

      expect(mockWS.send).toHaveBeenCalled();

      // Receive events via SSE
      act(() => {
        const messageEvent = new MessageEvent('message', {
          data: 'data: {"event":"agent_update","data":{"agentId":"agent2","status":"running"}}'
        });
        mockES.addEventListener.mock.calls.find(call => call[0] === 'message')[1](messageEvent);
      });

      expect(sseResult.current.agentData.has('agent2')).toBe(true);
    });
  });

  // ============================================================================
  // Error Handling Tests
  // ============================================================================

  describe('Error Handling', () => {
    test('should handle WebSocket connection errors', async () => {
      const mockWS = {
        readyState: WebSocket.CLOSED,
        send: jest.fn(),
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.WebSocket as jest.Mock).mockImplementation(() => mockWS);

      const { result } = renderHook(() => useWebSocketManager('ws://invalid-url'));

      expect(result.current.connectionState.status).toBe('error');
      expect(result.current.connectionState.error).toBeDefined();
    });

    test('should handle SSE parsing errors', async () => {
      const mockES = {
        readyState: EventSource.OPEN,
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      };

      (global.EventSource as jest.Mock).mockImplementation(() => mockES);

      const { result } = renderHook(() => useSSEStream({
        endpoint: '/api/copilotkit?protocol=sse'
      }));

      // Send malformed data
      act(() => {
        const messageEvent = new MessageEvent('message', {
          data: 'data: {invalid json}'
        });
        mockES.addEventListener.mock.calls.find(call => call[0] === 'message')[1](messageEvent);
      });

      // Should not crash, just ignore malformed data
      expect(result.current.events.length).toBe(0);
    });

    test('should handle memory threshold exceeded', async () => {
      const cleanupCallback = jest.fn();
      const { result } = renderHook(() => useMemoryManagement(10));

      act(() => {
        result.current.registerCleanup(cleanupCallback);
      });

      // Mock memory threshold exceeded
      (global.performance as any).memory.usedJSHeapSize = 15000000; // 15MB > 10MB threshold

      jest.advanceTimersByTime(5000);

      expect(cleanupCallback).toHaveBeenCalled();
      expect(result.current.memoryStatus.status).toBe('warning');
    });
  });

  // ============================================================================
  // Performance Benchmarks
  // ============================================================================

  describe('Performance Benchmarks', () => {
    test('should meet performance targets', () => {
      const { result } = renderHook(() => usePerformanceMonitor());

      // Simulate good performance
      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.trackUpdate();
        }
        jest.advanceTimersByTime(200); // 200ms for 10 updates = 50 updates/sec
      });

      expect(result.current.metrics.updateFrequency).toBeLessThan(120); // < 120 updates/sec
      expect(result.current.metrics.averageUpdateTime).toBeLessThan(16); // < 16ms average
    });

    test('should optimize memory usage', () => {
      const { result } = renderHook(() => useMemoryManagement(50));

      // Cache some data
      act(() => {
        for (let i = 0; i < 100; i++) {
          result.current.cache(`key${i}`, `value${i}`, 300000); // 5 minutes TTL
        }
      });

      // Check memory is managed
      expect(result.current.memoryStatus.used).toBeLessThan(50); // Below 50MB threshold
    });
  });
});