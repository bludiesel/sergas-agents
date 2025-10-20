/**
 * Next.js API Route for CopilotKit Integration
 *
 * This route uses CopilotKit's built-in runtime with OpenAIAdapter
 * to handle AI interactions properly.
 *
 * File location: app/api/copilotkit/route.ts
 */

import { copilotRuntimeNextJSAppRouterEndpoint, OpenAIAdapter } from '@copilotkit/runtime';

// Initialize CopilotKit runtime with OpenAI adapter
const runtime = copilotRuntimeNextJSAppRouterEndpoint({
  actions: [
    // Define actions that the AI can perform
    {
      name: "analyzeAccount",
      description: "Analyze a specific account for risk assessment and recommendations",
      parameters: [
        {
          name: "accountId",
          type: "string",
          description: "The account ID to analyze",
          required: true,
        },
        {
          name: "analysisType",
          type: "string",
          description: "Type of analysis to perform",
          required: false,
        },
      ],
      handler: async ({ accountId, analysisType }) => {
        // Mock account analysis - replace with actual business logic
        return {
          accountId,
          analysisType: analysisType || "comprehensive",
          riskScore: Math.floor(Math.random() * 100),
          recommendations: [
            "Monitor transaction patterns",
            "Review credit utilization",
            "Assess payment history"
          ],
          status: "completed"
        };
      },
    },
    {
      name: "generateRecommendations",
      description: "Generate recommendations for account management",
      parameters: [
        {
          name: "accountId",
          type: "string",
          description: "The account ID",
          required: true,
        },
      ],
      handler: async ({ accountId }) => {
        return {
          accountId,
          recommendations: [
            "Increase credit limit",
            "Set up automatic payments",
            "Monitor spending patterns"
          ],
          priority: "medium"
        };
      },
    },
  ],
  adapters: [
    new OpenAIAdapter({
      model: "gpt-4",
      apiKey: process.env.OPENAI_API_KEY || "sk-dummy-key",
    }),
  ],
});

// Export the handlers from the runtime
export const GET = runtime.GET;
export const POST = runtime.POST;
export const OPTIONS = runtime.OPTIONS;
