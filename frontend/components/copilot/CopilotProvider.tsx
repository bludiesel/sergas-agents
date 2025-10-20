/**
 * CopilotKit Provider Component
 *
 * Wraps the application with CopilotKit provider for AI-powered features.
 * Handles configuration, authentication, and runtime URL setup.
 *
 * Features:
 * - Backend API connection via /api/copilotkit
 * - Authentication token management
 * - Agent selection (orchestrator by default)
 * - Environment-based configuration
 */

'use client';

import React from 'react';
import { CopilotKit } from '@copilotkit/react-core';

interface CopilotProviderProps {
  children: React.ReactNode;
  agent?: string;
  publicApiKey?: string;
}

/**
 * CopilotProvider Component
 *
 * Configures CopilotKit with backend connection and authentication.
 */
export function CopilotProvider({
  children,
  agent = 'orchestrator',
  publicApiKey = 'ck_pub_e406823a48472880c136f49a521e5cf6',
}: CopilotProviderProps) {
  // Get runtime URL from environment or use default
  const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL || '/api/copilotkit';

  // Get authentication token from environment if available
  const authToken = process.env.NEXT_PUBLIC_API_TOKEN;

  // Prepare headers with authentication if token is available
  const headers: Record<string, string> = {};
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  return (
    <CopilotKit
      runtimeUrl={runtimeUrl}
      agent={agent}
      headers={Object.keys(headers).length > 0 ? headers : undefined}
      publicApiKey={publicApiKey}
    >
      {children}
    </CopilotKit>
  );
}

/**
 * Hook to access CopilotKit configuration
 */
export function useCopilotConfig() {
  return {
    runtimeUrl: process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL || '/api/copilotkit',
    agent: 'orchestrator',
    isConfigured: true,
  };
}
