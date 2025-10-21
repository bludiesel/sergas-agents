import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
  LangGraphHttpAgent,
} from "@copilotkit/runtime";

// Use empty adapter since we're using a single HTTP agent
const serviceAdapter = new ExperimentalEmptyAdapter();

// Configure the GLM-4.6 backend as a LangGraph HTTP agent
const runtime = new CopilotRuntime({
  agents: {
    "glm-agent": new LangGraphHttpAgent({
      url: "http://localhost:8008/api/copilotkit"
    }),
  },
});

export const POST = async (req: NextRequest) => {
  try {
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
      runtime,
      serviceAdapter,
      endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
  } catch (error) {
    console.error("CopilotKit runtime error:", error);
    return new Response(
      JSON.stringify({
        error: "CopilotKit runtime error",
        message: error instanceof Error ? error.message : "Unknown error"
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
};

export async function GET() {
  return new Response(JSON.stringify({
    status: 'OK',
    message: 'CopilotKit API with GLM-4.6 integration'
  }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}