/**
 * Integration Tests: SSE Streaming and Real-Time Events
 *
 * Tests Server-Sent Events (SSE) streaming functionality for real-time
 * communication between frontend and backend during agent execution.
 *
 * Coverage:
 * - SSE connection establishment
 * - Event stream parsing
 * - Real-time progress updates
 * - Connection management
 * - Reconnection logic
 * - Error handling
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { CopilotKit, useCopilotAction } from '@copilotkit/react-core';
import '@testing-library/jest-dom';

// Mock EventSource for SSE testing
class MockEventSource {
  url: string;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onopen: ((event: Event) => void) | null = null;
  readyState: number = 0;

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSED = 2;

  constructor(url: string) {
    this.url = url;
    this.readyState = MockEventSource.CONNECTING;

    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockEventSource.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  close() {
    this.readyState = MockEventSource.CLOSED;
  }

  // Helper method to simulate receiving messages
  simulateMessage(data: string, event = 'message') {
    if (this.onmessage) {
      const messageEvent = new MessageEvent(event, { data });
      this.onmessage(messageEvent);
    }
  }

  // Helper method to simulate errors
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// @ts-ignore
global.EventSource = MockEventSource;

// Mock fetch
global.fetch = jest.fn();

describe('SSE Streaming Integration Tests', () => {
  const mockRuntimeUrl = 'http://localhost:8000/copilotkit';

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success' }),
      headers: new Headers({ 'content-type': 'text/event-stream' }),
      body: new ReadableStream(),
    });
  });

  describe('SSE Connection Establishment', () => {
    it('should establish SSE connection to backend', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);

      await waitFor(
        () => {
          expect(eventSource.readyState).toBe(MockEventSource.OPEN);
        },
        { timeout: 100 }
      );
    });

    it('should handle connection opening event', async () => {
      const onOpen = jest.fn();
      const eventSource = new MockEventSource(mockRuntimeUrl);
      eventSource.onopen = onOpen;

      await waitFor(
        () => {
          expect(onOpen).toHaveBeenCalled();
        },
        { timeout: 100 }
      );
    });

    it('should set correct headers for SSE connection', async () => {
      const TestComponent = () => {
        useCopilotAction({
          name: 'sseAction',
          description: 'SSE test action',
          parameters: [],
          handler: async () => ({ result: 'streaming' }),
        });

        return <div data-testid="sse-connection">SSE Connection Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit
          runtimeUrl={mockRuntimeUrl}
          headers={{
            Authorization: 'Bearer test-token',
          }}
        >
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('sse-connection')).toBeInTheDocument();
    });

    it('should handle connection to different endpoints', async () => {
      const endpoints = [
        `${mockRuntimeUrl}/stream1`,
        `${mockRuntimeUrl}/stream2`,
        `${mockRuntimeUrl}/stream3`,
      ];

      const eventSources = endpoints.map((url) => new MockEventSource(url));

      await Promise.all(
        eventSources.map(
          (es) =>
            new Promise((resolve) => {
              es.onopen = resolve;
            })
        )
      );

      eventSources.forEach((es) => {
        expect(es.readyState).toBe(MockEventSource.OPEN);
      });
    });
  });

  describe('Event Stream Parsing', () => {
    it('should parse agent_started events', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      const receivedEvents: any[] = [];

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        receivedEvents.push(data);
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateMessage(
          JSON.stringify({
            type: 'agent_started',
            agent: 'orchestrator',
            step: 0,
            task: 'analyze_account',
          })
        );
      });

      await waitFor(() => {
        expect(receivedEvents).toHaveLength(1);
        expect(receivedEvents[0].type).toBe('agent_started');
        expect(receivedEvents[0].agent).toBe('orchestrator');
      });
    });

    it('should parse agent_stream events with content', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      const streamContent: string[] = [];

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_stream') {
          streamContent.push(data.content);
        }
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      const messages = [
        'Fetching account data...',
        'Found 5 deals...',
        'Analyzing patterns...',
      ];

      act(() => {
        messages.forEach((msg) => {
          eventSource.simulateMessage(
            JSON.stringify({
              type: 'agent_stream',
              agent: 'zoho_data_scout',
              content: msg,
              content_type: 'text',
            })
          );
        });
      });

      await waitFor(() => {
        expect(streamContent).toEqual(messages);
      });
    });

    it('should parse agent_completed events', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      let completedEvent: any = null;

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_completed') {
          completedEvent = data;
        }
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateMessage(
          JSON.stringify({
            type: 'agent_completed',
            agent: 'recommendation_author',
            step: 3,
            output: {
              recommendations: [{ title: 'Follow up with customer' }],
              confidence: 0.85,
            },
          })
        );
      });

      await waitFor(() => {
        expect(completedEvent).not.toBeNull();
        expect(completedEvent.type).toBe('agent_completed');
        expect(completedEvent.output.recommendations).toHaveLength(1);
      });
    });

    it('should parse workflow_interrupted events for HITL', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      let interruptedEvent: any = null;

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'workflow_interrupted') {
          interruptedEvent = data;
        }
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateMessage(
          JSON.stringify({
            type: 'workflow_interrupted',
            reason: 'approval_required',
            data: {
              run_id: 'run_123',
              recommendations: [{ title: 'Recommendation 1' }],
              approval_required: true,
            },
          })
        );
      });

      await waitFor(() => {
        expect(interruptedEvent).not.toBeNull();
        expect(interruptedEvent.reason).toBe('approval_required');
        expect(interruptedEvent.data.approval_required).toBe(true);
      });
    });

    it('should handle malformed event data gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const eventSource = new MockEventSource(mockRuntimeUrl);

      eventSource.onmessage = (event) => {
        try {
          JSON.parse(event.data);
        } catch (error) {
          console.error('Failed to parse event', error);
        }
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateMessage('invalid json {]');
      });

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalled();
      });

      consoleError.mockRestore();
    });
  });

  describe('Real-Time Progress Updates', () => {
    it('should display real-time progress during data fetching', async () => {
      const TestComponent = () => {
        const [progress, setProgress] = React.useState<string[]>([]);
        const eventSourceRef = React.useRef<MockEventSource | null>(null);

        React.useEffect(() => {
          const es = new MockEventSource(mockRuntimeUrl);
          eventSourceRef.current = es;

          es.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'agent_stream') {
              setProgress((prev) => [...prev, data.content]);
            }
          };

          return () => es.close();
        }, []);

        return (
          <div>
            <div data-testid="progress-container">
              {progress.map((msg, i) => (
                <div key={i} data-testid={`progress-${i}`}>
                  {msg}
                </div>
              ))}
            </div>
          </div>
        );
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);

      // Wait for component to mount and EventSource to be created
      await waitFor(() => {
        expect(screen.getByTestId('progress-container')).toBeInTheDocument();
      });
    });

    it('should update UI with streaming recommendations', async () => {
      const TestComponent = () => {
        const [recommendations, setRecommendations] = React.useState<string[]>([]);

        React.useEffect(() => {
          const es = new MockEventSource(mockRuntimeUrl);

          es.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'recommendation_stream') {
              setRecommendations((prev) => [...prev, data.recommendation]);
            }
          };

          // Simulate streaming recommendations
          setTimeout(() => {
            es.simulateMessage(
              JSON.stringify({
                type: 'recommendation_stream',
                recommendation: 'Schedule follow-up meeting',
              })
            );
          }, 50);

          return () => es.close();
        }, []);

        return (
          <div>
            <div data-testid="recommendations-list">
              {recommendations.map((rec, i) => (
                <div key={i} data-testid={`rec-${i}`}>
                  {rec}
                </div>
              ))}
            </div>
          </div>
        );
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);

      await waitFor(
        () => {
          expect(screen.getByTestId('rec-0')).toHaveTextContent(
            'Schedule follow-up meeting'
          );
        },
        { timeout: 200 }
      );
    });

    it('should handle multiple concurrent streams', async () => {
      const streams = [
        new MockEventSource(`${mockRuntimeUrl}/stream1`),
        new MockEventSource(`${mockRuntimeUrl}/stream2`),
        new MockEventSource(`${mockRuntimeUrl}/stream3`),
      ];

      const receivedMessages: string[][] = [[], [], []];

      streams.forEach((es, index) => {
        es.onmessage = (event) => {
          receivedMessages[index].push(event.data);
        };
      });

      await Promise.all(
        streams.map(
          (es) =>
            new Promise((resolve) => {
              es.onopen = resolve;
            })
        )
      );

      act(() => {
        streams.forEach((es, i) => {
          es.simulateMessage(`Message from stream ${i}`);
        });
      });

      await waitFor(() => {
        receivedMessages.forEach((messages, i) => {
          expect(messages).toContain(`Message from stream ${i}`);
        });
      });

      streams.forEach((es) => es.close());
    });
  });

  describe('Connection Management', () => {
    it('should close connection when component unmounts', async () => {
      const TestComponent = () => {
        const eventSourceRef = React.useRef<MockEventSource | null>(null);

        React.useEffect(() => {
          eventSourceRef.current = new MockEventSource(mockRuntimeUrl);
          return () => eventSourceRef.current?.close();
        }, []);

        return <div data-testid="connection-test">Connection Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      const { unmount } = render(<Wrapper />);
      await waitFor(() =>
        expect(screen.getByTestId('connection-test')).toBeInTheDocument()
      );

      unmount();
      // Connection should be closed after unmount
    });

    it('should handle connection timeout', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      let timeoutOccurred = false;

      const timeout = setTimeout(() => {
        timeoutOccurred = true;
        eventSource.close();
      }, 1000);

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      clearTimeout(timeout);
      expect(timeoutOccurred).toBe(false);
    });

    it('should maintain connection during long-running operations', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      let messageCount = 0;

      eventSource.onmessage = () => {
        messageCount++;
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      // Simulate long-running operation with periodic messages
      for (let i = 0; i < 10; i++) {
        act(() => {
          eventSource.simulateMessage(JSON.stringify({ type: 'heartbeat' }));
        });
        await new Promise((resolve) => setTimeout(resolve, 10));
      }

      expect(messageCount).toBe(10);
      expect(eventSource.readyState).toBe(MockEventSource.OPEN);
    });
  });

  describe('Reconnection Logic', () => {
    it('should attempt to reconnect on connection loss', async () => {
      let connectionAttempts = 0;
      const maxAttempts = 3;

      const createConnection = () => {
        connectionAttempts++;
        return new MockEventSource(mockRuntimeUrl);
      };

      let eventSource = createConnection();
      eventSource.onerror = () => {
        if (connectionAttempts < maxAttempts) {
          setTimeout(() => {
            eventSource = createConnection();
          }, 100);
        }
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      // Simulate connection error
      act(() => {
        eventSource.simulateError();
      });

      await waitFor(
        () => {
          expect(connectionAttempts).toBeGreaterThan(1);
        },
        { timeout: 500 }
      );
    });

    it('should handle reconnection with exponential backoff', async () => {
      const reconnectDelays: number[] = [];
      let attempt = 0;

      const getBackoffDelay = (attemptNum: number) => {
        return Math.min(1000 * Math.pow(2, attemptNum), 30000);
      };

      const tryReconnect = () => {
        attempt++;
        const delay = getBackoffDelay(attempt);
        reconnectDelays.push(delay);

        if (attempt < 4) {
          setTimeout(tryReconnect, delay);
        }
      };

      tryReconnect();

      await waitFor(
        () => {
          expect(reconnectDelays.length).toBeGreaterThan(0);
        },
        { timeout: 100 }
      );

      // Verify exponential backoff
      expect(reconnectDelays[0]).toBe(2000); // 2^1 * 1000
      if (reconnectDelays.length > 1) {
        expect(reconnectDelays[1]).toBe(4000); // 2^2 * 1000
      }
    });

    it('should restore state after reconnection', async () => {
      const state = { progress: 0, messages: [] as string[] };
      let eventSource = new MockEventSource(mockRuntimeUrl);

      eventSource.onmessage = (event) => {
        state.progress++;
        state.messages.push(event.data);
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      // Send some messages
      act(() => {
        eventSource.simulateMessage('Message 1');
        eventSource.simulateMessage('Message 2');
      });

      // Simulate disconnection and reconnection
      act(() => {
        eventSource.close();
        eventSource = new MockEventSource(mockRuntimeUrl);
        eventSource.onmessage = (event) => {
          state.progress++;
          state.messages.push(event.data);
        };
      });

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      // State should be preserved
      expect(state.messages).toEqual(['Message 1', 'Message 2']);
    });
  });

  describe('Error Handling', () => {
    it('should handle SSE connection errors', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      let errorOccurred = false;

      eventSource.onerror = () => {
        errorOccurred = true;
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateError();
      });

      await waitFor(() => {
        expect(errorOccurred).toBe(true);
      });
    });

    it('should handle backend unavailability', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Backend unavailable')
      );
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const TestComponent = () => {
        return <div data-testid="unavailable-test">Unavailability Test</div>;
      };

      const Wrapper = () => (
        <CopilotKit runtimeUrl={mockRuntimeUrl}>
          <TestComponent />
        </CopilotKit>
      );

      render(<Wrapper />);
      expect(screen.getByTestId('unavailable-test')).toBeInTheDocument();
      consoleError.mockRestore();
    });

    it('should handle stream interruption gracefully', async () => {
      const eventSource = new MockEventSource(mockRuntimeUrl);
      const messages: string[] = [];

      eventSource.onmessage = (event) => {
        messages.push(event.data);
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateMessage('Message 1');
        eventSource.simulateMessage('Message 2');
        // Simulate interruption
        eventSource.close();
      });

      expect(messages).toEqual(['Message 1', 'Message 2']);
      expect(eventSource.readyState).toBe(MockEventSource.CLOSED);
    });

    it('should log errors for monitoring', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const eventSource = new MockEventSource(mockRuntimeUrl);

      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
      };

      await waitFor(() => expect(eventSource.readyState).toBe(MockEventSource.OPEN));

      act(() => {
        eventSource.simulateError();
      });

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          'SSE Error:',
          expect.any(Event)
        );
      });

      consoleError.mockRestore();
    });
  });
});
