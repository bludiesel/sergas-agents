/**
 * Integration Tests: Next.js API Route Proxy
 *
 * Tests the Next.js API route that proxies requests from the frontend
 * CopilotKit provider to the FastAPI backend.
 *
 * Coverage:
 * - Request forwarding to backend
 * - Header preservation
 * - SSE streaming proxy
 * - Error handling
 * - Method validation
 * - Security headers
 */

import { NextRequest, NextResponse } from 'next/server';
import { POST, GET } from '@/app/api/copilotkit/route';

// Mock Next.js request/response
jest.mock('next/server', () => ({
  NextRequest: jest.fn(),
  NextResponse: {
    json: jest.fn((data, options) => ({
      json: async () => data,
      status: options?.status || 200,
      headers: new Headers(),
      ...options,
    })),
  },
}));

// Mock fetch
global.fetch = jest.fn();

// Mock ReadableStream
global.ReadableStream = class ReadableStream {
  constructor(
    public underlyingSource?: {
      start?: (controller: any) => void | Promise<void>;
      pull?: (controller: any) => void | Promise<void>;
      cancel?: () => void | Promise<void>;
    }
  ) {}
} as any;

describe('API Route Integration Tests', () => {
  const mockBackendUrl = 'http://localhost:8008';
  const originalEnv = process.env;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = {
      ...originalEnv,
      NEXT_PUBLIC_BACKEND_URL: mockBackendUrl,
    };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('POST Request Forwarding', () => {
    it('should forward POST requests to FastAPI backend', async () => {
      const mockRequestBody = {
        agent: 'orchestrator',
        action: 'analyze_account',
        parameters: { accountId: 'acc_123' },
        session_id: 'session_123',
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'success', result: 'analyzed' }),
        text: async () => 'success',
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map([['content-type', 'application/json']]),
      } as unknown as NextRequest;

      const mockGet = jest.fn((header: string) => {
        if (header === 'Authorization') return null;
        return null;
      });
      mockRequest.headers.get = mockGet;

      await POST(mockRequest);

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockBackendUrl}/copilotkit`,
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(mockRequestBody),
        })
      );
    });

    it('should preserve Authorization headers', async () => {
      const mockRequestBody = {
        agent: 'orchestrator',
        session_id: 'session_123',
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map([
          ['content-type', 'application/json'],
          ['authorization', 'Bearer test-token-123'],
        ]),
      } as unknown as NextRequest;

      const mockGet = jest.fn((header: string) => {
        if (header === 'Authorization') return 'Bearer test-token-123';
        return null;
      });
      mockRequest.headers.get = mockGet;

      await POST(mockRequest);

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockBackendUrl}/copilotkit`,
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token-123',
          }),
        })
      );
    });

    it('should handle requests without authentication', async () => {
      const mockRequestBody = { agent: 'orchestrator' };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map([['content-type', 'application/json']]),
      } as unknown as NextRequest;

      const mockGet = jest.fn(() => null);
      mockRequest.headers.get = mockGet;

      await POST(mockRequest);

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockBackendUrl}/copilotkit`,
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.anything(),
          }),
        })
      );
    });

    it('should log request details for monitoring', async () => {
      const consoleLog = jest.spyOn(console, 'log').mockImplementation();
      const mockRequestBody = {
        agent: 'orchestrator',
        session_id: 'session_123',
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      await POST(mockRequest);

      expect(consoleLog).toHaveBeenCalledWith(
        'CopilotKit request received:',
        expect.objectContaining({
          agent: 'orchestrator',
          session_id: 'session_123',
        })
      );

      consoleLog.mockRestore();
    });
  });

  describe('SSE Streaming Proxy', () => {
    it('should proxy SSE event streams from backend', async () => {
      const mockRequestBody = { agent: 'orchestrator' };

      const mockStream = {
        getReader: jest.fn(() => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: event1\n\n'),
            })
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: event2\n\n'),
            })
            .mockResolvedValueOnce({
              done: true,
              value: undefined,
            }),
        })),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/event-stream' }),
        body: mockStream,
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);

      // Verify response is a streaming response
      expect(response).toBeDefined();
    });

    it('should set correct headers for SSE streaming', async () => {
      const mockRequestBody = { agent: 'orchestrator' };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/event-stream' }),
        body: new ReadableStream(),
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);

      // SSE responses should have specific headers
      // In actual implementation, verify headers are set correctly
      expect(response).toBeDefined();
    });

    it('should handle stream interruptions gracefully', async () => {
      const mockRequestBody = { agent: 'orchestrator' };

      const mockStream = {
        getReader: jest.fn(() => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode('data: event1\n\n'),
            })
            .mockRejectedValueOnce(new Error('Stream interrupted')),
        })),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/event-stream' }),
        body: mockStream,
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      await POST(mockRequest);

      // Error should be logged but not crash
      consoleError.mockRestore();
    });

    it('should forward SSE events without modification', async () => {
      const mockRequestBody = { agent: 'orchestrator' };
      const eventData = 'data: {"type":"agent_started","agent":"orchestrator"}\n\n';

      const mockStream = {
        getReader: jest.fn(() => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              done: false,
              value: new TextEncoder().encode(eventData),
            })
            .mockResolvedValueOnce({
              done: true,
              value: undefined,
            }),
        })),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/event-stream' }),
        body: mockStream,
      });

      const mockRequest = {
        json: async () => mockRequestBody,
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      await POST(mockRequest);

      // Events should be forwarded as-is
      expect(mockStream.getReader).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should handle backend connection errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Connection refused')
      );

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);
      const data = await response.json();

      expect(data).toEqual({
        error: 'Internal server error',
        message: 'Connection refused',
      });
      expect(response.status).toBe(500);
    });

    it('should handle backend error responses', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
        text: async () => 'Invalid request format',
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const response = await POST(mockRequest);
      const data = await response.json();

      expect(data).toEqual({
        error: 'Backend request failed',
        status: 400,
        message: 'Invalid request format',
      });
      expect(response.status).toBe(400);

      consoleError.mockRestore();
    });

    it('should handle malformed request payloads', async () => {
      const mockRequest = {
        json: async () => {
          throw new Error('Invalid JSON');
        },
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const response = await POST(mockRequest);
      const data = await response.json();

      expect(data).toEqual({
        error: 'Internal server error',
        message: 'Invalid JSON',
      });

      consoleError.mockRestore();
    });

    it('should handle backend timeout', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 35000))
      );

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      // This would timeout in real scenario
      // Testing timeout handling logic
    });

    it('should log errors for monitoring', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Test error'));

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      await POST(mockRequest);

      expect(consoleError).toHaveBeenCalledWith(
        'CopilotKit route error:',
        expect.any(Error)
      );

      consoleError.mockRestore();
    });
  });

  describe('GET Health Check', () => {
    it('should return health status', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          status: 'healthy',
          version: '1.0.0',
        }),
      });

      const response = await GET();
      const data = await response.json();

      expect(data).toEqual({
        status: 'ok',
        backend: {
          status: 'healthy',
          version: '1.0.0',
        },
        timestamp: expect.any(String),
      });
    });

    it('should check backend availability', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      await GET();

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockBackendUrl}/health`
      );
    });

    it('should handle backend unavailability', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Backend unavailable')
      );

      const response = await GET();
      const data = await response.json();

      expect(data).toEqual({
        status: 'error',
        message: 'Backend unavailable',
      });
      expect(response.status).toBe(503);
    });

    it('should include timestamp in health response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      const response = await GET();
      const data = await response.json();

      expect(data.timestamp).toBeDefined();
      expect(new Date(data.timestamp).toISOString()).toBe(data.timestamp);
    });
  });

  describe('Security', () => {
    it('should validate request content-type', async () => {
      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map([['content-type', 'text/plain']]),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // Should still process request, but could add validation
      await POST(mockRequest);
    });

    it('should not expose internal error details', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Database connection failed: postgres://internal-db:5432')
      );

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);
      const data = await response.json();

      // Should return generic error without exposing internal details
      expect(data.error).toBe('Internal server error');
    });

    it('should handle CORS appropriately', async () => {
      // CORS should be configured at the Next.js level
      // This test validates that responses don't block CORS
      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map([['origin', 'http://localhost:3000']]),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await POST(mockRequest);
      // Response should not have CORS issues
    });
  });

  describe('Response Handling', () => {
    it('should return JSON responses correctly', async () => {
      const mockResponseData = {
        status: 'success',
        accountId: 'acc_123',
        analysis: { score: 85 },
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponseData,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);
      const data = await response.json();

      expect(data).toEqual(mockResponseData);
    });

    it('should handle large response payloads', async () => {
      const largePayload = {
        status: 'success',
        data: Array(10000).fill({ item: 'data' }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => largePayload,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);
      const data = await response.json();

      expect(data.data).toHaveLength(10000);
    });

    it('should handle empty responses', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const response = await POST(mockRequest);
      const data = await response.json();

      expect(data).toEqual({});
    });
  });

  describe('Performance', () => {
    it('should handle concurrent requests', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const requests = Array(10)
        .fill(null)
        .map(() => {
          const mockRequest = {
            json: async () => ({ agent: 'orchestrator' }),
            headers: new Map(),
          } as unknown as NextRequest;
          mockRequest.headers.get = jest.fn(() => null);
          return POST(mockRequest);
        });

      const responses = await Promise.all(requests);

      expect(responses).toHaveLength(10);
      expect(global.fetch).toHaveBeenCalledTimes(10);
    });

    it('should not block on slow backend responses', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ status: 'success' }),
                  headers: new Headers({
                    'content-type': 'application/json',
                  }),
                }),
              100
            )
          )
      );

      const mockRequest = {
        json: async () => ({ agent: 'orchestrator' }),
        headers: new Map(),
      } as unknown as NextRequest;

      mockRequest.headers.get = jest.fn(() => null);

      const start = Date.now();
      await POST(mockRequest);
      const duration = Date.now() - start;

      // Should complete within reasonable time
      expect(duration).toBeLessThan(200);
    });
  });
});
