/**
 * CopilotKit API Route Integration Tests
 *
 * Tests for /api/copilotkit route handling, error scenarios,
 * and backend integration with GLM-4.6
 */

import { NextRequest } from 'next/server';
import { POST, GET, OPTIONS } from '@/app/api/copilotkit/route';

// Mock environment variables
const originalEnv = process.env;

beforeEach(() => {
  process.env = {
    ...originalEnv,
    NEXT_PUBLIC_API_URL: 'http://localhost:8008',
  };
  fetch.mockClear();
});

afterEach(() => {
  process.env = originalEnv;
  jest.clearAllMocks();
});

describe('CopilotKit API Route', () => {
  describe('POST /api/copilotkit', () => {
    describe('loadAgentState Operation', () => {
      it('should handle loadAgentState request', async () => {
        const requestBody = {
          operationName: 'loadAgentState',
          variables: {
            data: {
              threadId: 'thread-123',
            },
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data).toEqual({
          data: {
            loadAgentState: {
              threadId: 'thread-123',
              threadExists: false,
              state: null,
              messages: [],
            },
          },
        });

        // Verify CORS headers
        expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
        expect(response.headers.get('Access-Control-Allow-Methods')).toBe('GET, POST, OPTIONS');
        expect(response.headers.get('Access-Control-Allow-Headers')).toBe('Content-Type, Authorization');
      });

      it('should generate thread ID when not provided', async () => {
        const requestBody = {
          operationName: 'loadAgentState',
          variables: {},
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.data.loadAgentState.threadId).toMatch(
          /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
        );
      });

      it('should handle malformed loadAgentState request', async () => {
        const requestBody = {
          operationName: 'loadAgentState',
          variables: null, // Invalid variables
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.data.loadAgentState.threadId).toBeDefined();
      });
    });

    describe('generateCopilotResponse Operation', () => {
      beforeEach(() => {
        // Mock successful backend response
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            data: {
              generateCopilotResponse: {
                response: 'Analysis complete for account ACC-001',
                agent: 'glm-4.6',
                metadata: {
                  model: 'glm-4.6',
                  provider: 'z.ai',
                  accountId: 'ACC-001',
                },
              },
            },
          }),
        });
      });

      it('should forward messages to GLM-4.6 backend', async () => {
        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [
              {
                content: 'Analyze account ACC-001',
                role: 'user',
              },
            ],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(fetch).toHaveBeenCalledWith(
          'http://localhost:8008/api/copilotkit',
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              messages: [{ role: 'user', content: 'Analyze account ACC-001' }],
              account_id: 'DEFAULT_ACCOUNT',
              operationName: 'generateCopilotResponse',
            }),
          })
        );

        expect(data.data.generateCopilotResponse.response).toBe('Analysis complete for account ACC-001');
        expect(data.data.generateCopilotResponse.agent).toBe('glm-4.6');
      });

      it('should extract account ID from message', async () => {
        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [
              {
                content: 'Please analyze account ACC-456 for me',
                role: 'user',
              },
            ],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        await POST(request);

        expect(fetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: expect.stringContaining('"account_id":"ACC-456"'),
          })
        );
      });

      it('should handle empty messages array', async () => {
        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(fetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: expect.stringContaining('"account_id":"DEFAULT_ACCOUNT"'),
          })
        );
      });

      it('should handle backend error gracefully', async () => {
        // Mock backend error
        fetch.mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
        });

        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [{ content: 'Test message', role: 'user' }],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200); // API should still respond with 200
        expect(data.data.generateCopilotResponse.response).toBe('Sorry, I encountered an error processing your request.');
        expect(data.data.generateCopilotResponse.agent).toBe('glm-4.6');
        expect(data.data.generateCopilotResponse.metadata.error).toBeDefined();
      });

      it('should handle network timeout/failure', async () => {
        // Mock network failure
        fetch.mockRejectedValueOnce(new Error('Network timeout'));

        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [{ content: 'Test message', role: 'user' }],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.data.generateCopilotResponse.response).toBe('Sorry, I encountered an error processing your request.');
      });

      it('should handle malformed backend response', async () => {
        // Mock malformed JSON response
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => {
            throw new Error('Invalid JSON');
          },
        });

        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [{ content: 'Test message', role: 'user' }],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.data.generateCopilotResponse.response).toBe('GLM-4.6 response received');
      });
    });

    describe('Unknown Operations', () => {
      it('should handle unknown operation gracefully', async () => {
        const requestBody = {
          operationName: 'unknownOperation',
          variables: { test: 'value' },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.data.unknownOperation).toBeDefined();
        expect(data.data.unknownOperation.threadId).toMatch(/^[0-9a-f-]+$/);
      });

      it('should handle missing operation name', async () => {
        const requestBody = {
          variables: { test: 'value' },
          // Missing operationName
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.data[undefined]).toBeDefined(); // Should create response for undefined operation
      });
    });

    describe('Request Body Parsing', () => {
      it('should handle invalid JSON', async () => {
        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: 'invalid json{',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(500);
        expect(data.errors).toBeDefined();
        expect(data.errors[0].message).toBe('Failed to process request');
      });

      it('should handle empty request body', async () => {
        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: '',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(500);
        expect(data.errors).toBeDefined();
      });

      it('should handle non-object request body', async () => {
        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify('string value'),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const response = await POST(request);
        const data = await response.json();

        expect(response.status).toBe(500);
        expect(data.errors).toBeDefined();
      });
    });

    describe('Environment Configuration', () => {
      it('should use custom backend URL from environment', async () => {
        process.env.NEXT_PUBLIC_API_URL = 'https://custom-backend.com';

        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ data: { generateCopilotResponse: { response: 'test' } } }),
        });

        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [{ content: 'Test', role: 'user' }],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        await POST(request);

        expect(fetch).toHaveBeenCalledWith(
          'https://custom-backend.com/api/copilotkit',
          expect.any(Object)
        );
      });

      it('should use default URL when environment variable not set', async () => {
        delete process.env.NEXT_PUBLIC_API_URL;

        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ data: { generateCopilotResponse: { response: 'test' } } }),
        });

        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [{ content: 'Test', role: 'user' }],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        await POST(request);

        expect(fetch).toHaveBeenCalledWith(
          'http://localhost:8008/api/copilotkit', // Default URL
          expect.any(Object)
        );
      });
    });
  });

  describe('GET /api/copilotkit', () => {
    it('should return status information', async () => {
      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'GET',
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toEqual({
        status: 'OK',
        message: 'CopilotKit API proxy for GLM-4.6',
      });

      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });
  });

  describe('OPTIONS /api/copilotkit', () => {
    it('should return CORS headers', async () => {
      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'OPTIONS',
      });

      const response = await OPTIONS();

      expect(response.status).toBe(200);
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(response.headers.get('Access-Control-Allow-Methods')).toBe('GET, POST, OPTIONS');
      expect(response.headers.get('Access-Control-Allow-Headers')).toBe('Content-Type, Authorization');
    });
  });

  describe('Header Handling', () => {
    it('should include proper Content-Type header in responses', async () => {
      const requestBody = {
        operationName: 'loadAgentState',
        variables: {},
      };

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: JSON.stringify(requestBody),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const response = await POST(request);

      expect(response.headers.get('Content-Type')).toBe('application/json');
    });

    it('should handle requests with Authorization header', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: { generateCopilotResponse: { response: 'test' } } }),
      });

      const requestBody = {
        operationName: 'generateCopilotResponse',
        variables: {
          messages: [{ content: 'Test', role: 'user' }],
        },
      };

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: JSON.stringify(requestBody),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
      });

      await POST(request);

      // Should not pass auth header to backend (for security)
      const fetchCall = fetch.mock.calls[0];
      expect(fetchCall[1].headers).not.toHaveProperty('authorization');
      expect(fetchCall[1].headers).not.toHaveProperty('Authorization');
    });
  });

  describe('Performance and Load Testing', () => {
    it('should handle concurrent requests', async () => {
      const promises = [];

      // Create multiple concurrent requests
      for (let i = 0; i < 10; i++) {
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ data: { generateCopilotResponse: { response: `Response ${i}` } } }),
        });

        const requestBody = {
          operationName: 'generateCopilotResponse',
          variables: {
            messages: [{ content: `Test ${i}`, role: 'user' }],
          },
        };

        const request = new NextRequest('http://localhost:3000/api/copilotkit', {
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: {
            'Content-Type': 'application/json',
          },
        });

        promises.push(POST(request));
      }

      const responses = await Promise.all(promises);

      expect(responses).toHaveLength(10);
      responses.forEach((response, index) => {
        expect(response.status).toBe(200);
      });

      expect(fetch).toHaveBeenCalledTimes(10);
    });

    it('should handle large message payloads', async () => {
      const largeMessage = 'x'.repeat(10000); // 10KB message

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: { generateCopilotResponse: { response: 'Large message processed' } } }),
      });

      const requestBody = {
        operationName: 'generateCopilotResponse',
        variables: {
          messages: [{ content: largeMessage, role: 'user' }],
        },
      };

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: JSON.stringify(requestBody),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const response = await POST(request);

      expect(response.status).toBe(200);
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining(largeMessage),
        })
      );
    });
  });

  describe('Security', () => {
    it('should sanitize account ID extraction', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: { generateCopilotResponse: { response: 'test' } } }),
      });

      const requestBody = {
        operationName: 'generateCopilotResponse',
        variables: {
          messages: [
            {
              content: 'account account-<script>alert("xss")</script> test',
              role: 'user',
            },
          ],
        },
      };

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: JSON.stringify(requestBody),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      await POST(request);

      // Should extract account ID safely (no XSS)
      const fetchCall = fetch.mock.calls[0];
      const requestBody = JSON.parse(fetchCall[1].body);
      expect(requestBody.account_id).not.toContain('<script>');
    });

    it('should handle malicious JSON in request body', async () => {
      const maliciousJson = JSON.stringify({
        operationName: 'generateCopilotResponse',
        variables: {
          messages: [
            {
              content: '\u0000\u0001\u0002 malicious content',
              role: 'user',
            },
          ],
        },
      });

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: maliciousJson,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const response = await POST(request);

      // Should handle control characters gracefully
      expect(response.status).toBe(200);
    });
  });

  describe('Error Recovery', () => {
    it('should handle backend service unavailability', async () => {
      fetch.mockRejectedValueOnce(new Error('ECONNREFUSED'));

      const requestBody = {
        operationName: 'generateCopilotResponse',
        variables: {
          messages: [{ content: 'Test', role: 'user' }],
        },
      };

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: JSON.stringify(requestBody),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200); // API should still respond
      expect(data.data.generateCopilotResponse.response).toContain('error processing your request');
    });

    it('should handle backend timeout', async () => {
      fetch.mockRejectedValueOnce(new Error('ETIMEDOUT'));

      const requestBody = {
        operationName: 'generateCopilotResponse',
        variables: {
          messages: [{ content: 'Test', role: 'user' }],
        },
      };

      const request = new NextRequest('http://localhost:3000/api/copilotkit', {
        method: 'POST',
        body: JSON.stringify(requestBody),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.data.generateCopilotResponse.response).toContain('error processing your request');
    });
  });
});