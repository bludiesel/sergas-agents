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
 * - CopilotKit v1.10.6 compatibility
 */

'use client';

import React from 'react';
import { CopilotKit } from '@copilotkit/react-core';

interface CopilotProviderConfig {
  runtimeUrl: string;
  agent: string;
  headers?: Record<string, string>;
  publicApiKey?: string;
  properties?: Record<string, unknown>;
}

interface CopilotProviderProps {
  children: React.ReactNode;
  agent?: string;
  publicApiKey?: string;
  runtimeUrl?: string;
  headers?: Record<string, string>;
  properties?: Record<string, unknown>;
}

interface CopilotConfigState {
  isConfigured: boolean;
  hasRuntimeUrl: boolean;
  hasApiKey: boolean;
  hasAuthToken: boolean;
  agent: string;
  runtimeUrl: string;
}

interface CopilotError {
  code: string;
  message: string;
  details?: unknown;
}

/**
 * CopilotProvider Component
 *
 * Configures CopilotKit with backend connection and authentication.
 * Updated for CopilotKit v1.10.6 with Next.js 15.5.6 App Router compatibility.
 * Enhanced with comprehensive error handling and TypeScript types.
 */
export function CopilotProvider({
  children,
  agent = 'orchestrator',
  publicApiKey,
  runtimeUrl: runtimeUrlProp,
  headers: headersProp,
  properties: propertiesProp,
}: CopilotProviderProps) {
  // Validate configuration
  const validateConfig = (): CopilotConfigState => {
    const runtimeUrl = runtimeUrlProp || process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL || '/api/copilotkit';
    const apiKey = publicApiKey || process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY;
    const authToken = process.env.NEXT_PUBLIC_API_TOKEN;

    return {
      isConfigured: !!(runtimeUrl && apiKey),
      hasRuntimeUrl: !!runtimeUrl,
      hasApiKey: !!apiKey,
      hasAuthToken: !!authToken,
      agent,
      runtimeUrl,
    };
  };

  const config = validateConfig();

  // Error handling for invalid configuration
  const getConfigurationError = (): CopilotError | null => {
    const errors: string[] = [];

    if (!config.hasRuntimeUrl) {
      errors.push('Runtime URL is not configured');
    }

    if (!config.hasApiKey && !config.hasAuthToken) {
      errors.push('Neither API key nor auth token is configured');
    }

    if (errors.length > 0) {
      return {
        code: 'CONFIGURATION_ERROR',
        message: 'CopilotKit configuration is incomplete',
        details: errors,
      };
    }

    return null;
  };

  const configError = getConfigurationError();

  // Prepare headers with authentication
  const prepareHeaders = (): Record<string, string> | undefined => {
    const headers: Record<string, string> = {};

    // Add custom headers if provided
    if (headersProp) {
      Object.assign(headers, headersProp);
    }

    // Add authentication token if available
    const authToken = process.env.NEXT_PUBLIC_API_TOKEN;
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    // Add additional headers for better debugging
    if (process.env.NODE_ENV === 'development') {
      headers['X-Debug-Copilot-Config'] = 'true';
    }

    return Object.keys(headers).length > 0 ? headers : undefined;
  };

  const headers = prepareHeaders();

  // Prepare properties with defaults
  const properties = {
    origin: 'sergas-frontend',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    ...propertiesProp,
  };

  // Log configuration for debugging
  if (process.env.NODE_ENV === 'development') {
    console.log('CopilotProvider configuration:', {
      runtimeUrl: config.runtimeUrl,
      agent: config.agent,
      hasApiKey: config.hasApiKey,
      hasAuthToken: config.hasAuthToken,
      hasHeaders: !!headers,
      hasProperties: !!propertiesProp,
      configError: configError,
    });
  }

  // If there's a configuration error, provide fallback UI
  if (configError && process.env.NODE_ENV !== 'production') {
    return (
      <div className="min-h-screen bg-red-50 border-2 border-red-200 p-6 m-4 rounded-lg">
        <h2 className="text-xl font-bold text-red-800 mb-4">
          CopilotKit Configuration Error
        </h2>
        <p className="text-red-700 mb-2">{configError.message}</p>
        {configError.details && (
          <ul className="list-disc list-inside text-red-600">
            {(configError.details as string[]).map((detail, idx) => (
              <li key={idx}>{detail}</li>
            ))}
          </ul>
        )}
        <div className="mt-4 p-3 bg-red-100 rounded text-sm text-red-800">
          <p className="font-mono">NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL: {config.runtimeUrl}</p>
          <p className="font-mono">NEXT_PUBLIC_COPILOTKIT_API_KEY: {config.hasApiKey ? '***configured***' : 'not set'}</p>
          <p className="font-mono">NEXT_PUBLIC_API_TOKEN: {config.hasAuthToken ? '***configured***' : 'not set'}</p>
        </div>
      </div>
    );
  }

  // Error boundary for CopilotKit errors
  class CopilotKitErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean; error?: Error }
  > {
    constructor(props: { children: React.ReactNode }) {
      super(props);
      this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error) {
      return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      console.error('CopilotKit Error Boundary caught an error:', error, errorInfo);

      // In production, you might want to send this to an error reporting service
      if (process.env.NODE_ENV === 'production') {
        // Example: sendErrorToService(error, errorInfo);
      }
    }

    render() {
      if (this.state.hasError) {
        return (
          <div className="min-h-screen bg-yellow-50 border-2 border-yellow-200 p-6 m-4 rounded-lg">
            <h2 className="text-xl font-bold text-yellow-800 mb-4">
              CopilotKit Runtime Error
            </h2>
            <p className="text-yellow-700 mb-2">
              Something went wrong with the CopilotKit integration.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mt-4 p-3 bg-yellow-100 rounded">
                <p className="font-mono text-sm text-yellow-800">
                  {this.state.error.message}
                </p>
                <pre className="text-xs text-yellow-600 mt-2 whitespace-pre-wrap">
                  {this.state.error.stack}
                </pre>
              </div>
            )}
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
            >
              Reload Page
            </button>
          </div>
        );
      }

      return this.props.children;
    }
  }

  return (
    <CopilotKitErrorBoundary>
      <CopilotKit
        runtimeUrl={config.runtimeUrl}
        agent={config.agent}
        headers={headers}
        publicApiKey={publicApiKey || process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY}
        properties={properties}
      >
        {children}
      </CopilotKit>
    </CopilotKitErrorBoundary>
  );
}

/**
 * Hook to access CopilotKit configuration and state
 */
export function useCopilotConfig(): CopilotConfigState & {
  configError: CopilotError | null;
  isProduction: boolean;
} {
  const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL || '/api/copilotkit';
  const apiKey = process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY;
  const authToken = process.env.NEXT_PUBLIC_API_TOKEN;

  const config: CopilotConfigState = {
    runtimeUrl,
    agent: 'orchestrator',
    hasRuntimeUrl: !!runtimeUrl && runtimeUrl !== '/api/copilotkit',
    hasApiKey: !!apiKey,
    hasAuthToken: !!authToken,
    isConfigured: !!(runtimeUrl && (apiKey || authToken)),
  };

  // Get configuration error
  const configError: CopilotError | null = (() => {
    const errors: string[] = [];

    if (!config.hasRuntimeUrl) {
      errors.push('Runtime URL is not configured or using default');
    }

    if (!config.hasApiKey && !config.hasAuthToken) {
      errors.push('Neither API key nor auth token is configured');
    }

    if (errors.length > 0) {
      return {
        code: 'CONFIGURATION_ERROR',
        message: 'CopilotKit configuration is incomplete',
        details: errors,
      };
    }

    return null;
  })();

  return {
    ...config,
    configError,
    isProduction: process.env.NODE_ENV === 'production',
  };
}

/**
 * Hook to validate CopilotKit runtime connection
 */
export function useCopilotRuntimeHealth() {
  const [health, setHealth] = React.useState<{
    status: 'loading' | 'healthy' | 'error';
    message?: string;
    lastChecked?: Date;
  }>({ status: 'loading' });

  const config = useCopilotConfig();

  React.useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${config.runtimeUrl}/health`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });

        if (response.ok) {
          setHealth({
            status: 'healthy',
            message: 'CopilotKit runtime is accessible',
            lastChecked: new Date(),
          });
        } else {
          setHealth({
            status: 'error',
            message: `HTTP ${response.status}: ${response.statusText}`,
            lastChecked: new Date(),
          });
        }
      } catch (error) {
        setHealth({
          status: 'error',
          message: error instanceof Error ? error.message : 'Network error',
          lastChecked: new Date(),
        });
      }
    };

    // Check health immediately
    checkHealth();

    // Set up periodic health checks
    const interval = setInterval(checkHealth, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [config.runtimeUrl]);

  return health;
}
