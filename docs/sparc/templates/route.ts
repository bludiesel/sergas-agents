/**
 * Next.js API Route for CopilotKit Integration
 *
 * This route proxies requests from the Next.js frontend to the FastAPI backend
 * with CopilotKit. It handles:
 * - Agent execution requests
 * - Streaming responses via SSE
 * - Authentication and session management
 *
 * File location: app/api/copilotkit/route.ts
 *
 * Usage:
 *   The CopilotKitProvider in the frontend will automatically use this route.
 */

import { NextRequest, NextResponse } from 'next/server';

// Backend API configuration
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const COPILOTKIT_ENDPOINT = `${BACKEND_URL}/copilotkit`;

/**
 * POST handler for CopilotKit requests
 *
 * This forwards requests from the frontend CopilotKit provider to the
 * FastAPI backend, handling streaming responses appropriately.
 */
export async function POST(request: NextRequest) {
  try {
    // Extract request body
    const body = await request.json();

    console.log('CopilotKit request received:', {
      agent: body.agent,
      session_id: body.session_id,
    });

    // Forward request to FastAPI backend
    const response = await fetch(COPILOTKIT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward authentication headers if present
        ...(request.headers.get('Authorization') && {
          Authorization: request.headers.get('Authorization')!,
        }),
      },
      body: JSON.stringify(body),
    });

    // Check response status
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);

      return NextResponse.json(
        {
          error: 'Backend request failed',
          status: response.status,
          message: errorText,
        },
        { status: response.status }
      );
    }

    // Handle streaming response (SSE - Server-Sent Events)
    const contentType = response.headers.get('content-type');

    if (contentType?.includes('text/event-stream')) {
      // Stream the response back to the client
      const stream = new ReadableStream({
        async start(controller) {
          const reader = response.body!.getReader();
          const decoder = new TextDecoder();

          try {
            while (true) {
              const { done, value } = await reader.read();

              if (done) {
                controller.close();
                break;
              }

              // Forward chunks to client
              controller.enqueue(value);
            }
          } catch (error) {
            console.error('Stream error:', error);
            controller.error(error);
          }
        },
      });

      // Return streaming response
      return new NextResponse(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
      });
    } else {
      // Return JSON response
      const data = await response.json();
      return NextResponse.json(data);
    }
  } catch (error) {
    console.error('CopilotKit route error:', error);

    return NextResponse.json(
      {
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * GET handler for health checks
 */
export async function GET() {
  try {
    // Check backend health
    const response = await fetch(`${BACKEND_URL}/health`);
    const health = await response.json();

    return NextResponse.json({
      status: 'ok',
      backend: health,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Backend unavailable',
      },
      { status: 503 }
    );
  }
}
