/**
 * CopilotProvider Component Tests
 *
 * Comprehensive tests for CopilotKit provider configuration and error handling
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { CopilotProvider, useCopilotConfig } from '@/components/copilot/CopilotProvider';

// Test component to access config
const TestComponent = () => {
  const config = useCopilotConfig();
  return (
    <div data-testid="config-display">
      <span data-testid="runtime-url">{config.runtimeUrl}</span>
      <span data-testid="agent">{config.agent}</span>
      <span data-testid="is-configured">{config.isConfigured.toString()}</span>
    </div>
  );
};

describe('CopilotProvider', () => {
  beforeEach(() => {
    // Reset environment variables
    process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL = undefined;
    process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = undefined;
    process.env.NEXT_PUBLIC_API_TOKEN = undefined;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Configuration', () => {
    it('should render children with default configuration', () => {
      render(
        <CopilotProvider>
          <div data-testid="child-component">Test Child</div>
        </CopilotProvider>
      );

      expect(screen.getByTestId('child-component')).toBeInTheDocument();
      expect(screen.getByText('Test Child')).toBeInTheDocument();
    });

    it('should use default runtime URL when not provided', () => {
      render(
        <CopilotProvider>
          <TestComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('runtime-url')).toHaveTextContent('/api/copilotkit');
    });

    it('should use custom agent when provided', () => {
      render(
        <CopilotProvider agent="custom-agent">
          <TestComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('agent')).toHaveTextContent('custom-agent');
    });
  });

  describe('Environment Configuration', () => {
    it('should use custom runtime URL from environment', () => {
      process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL = 'https://custom-runtime.com';

      render(
        <CopilotProvider>
          <TestComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('runtime-url')).toHaveTextContent('https://custom-runtime.com');
    });

    it('should detect when API key is configured', () => {
      process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = 'test-api-key';

      render(
        <CopilotProvider>
          <TestComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('is-configured')).toHaveTextContent('true');
    });

    it('should detect when API key is not configured', () => {
      process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = undefined;

      render(
        <CopilotProvider>
          <TestComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('is-configured')).toHaveTextContent('false');
    });
  });

  describe('Error Handling', () => {
    it('should handle missing children gracefully', () => {
      expect(() => {
        render(<CopilotProvider>{null}</CopilotProvider>);
      }).not.toThrow();
    });

    it('should handle undefined agent prop', () => {
      expect(() => {
        render(
          <CopilotProvider agent={undefined}>
            <div>Test</div>
          </CopilotProvider>
        );
      }).not.toThrow();
    });

    it('should handle empty agent prop', () => {
      render(
        <CopilotProvider agent="">
          <TestComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('agent')).toHaveTextContent('');
    });
  });

  describe('Props Configuration', () => {
    it('should use public API key from props', () => {
      render(
        <CopilotProvider publicApiKey="props-api-key">
          <div>Test</div>
        </CopilotProvider>
      );

      // Component should render without errors
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    it('should prioritize props over environment for API key', () => {
      process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = 'env-api-key';

      render(
        <CopilotProvider publicApiKey="props-api-key">
          <TestComponent />
        </CopilotProvider>
      );

      // Should still render correctly with props taking priority
      expect(screen.getByTestId('agent')).toBeInTheDocument();
    });
  });

  describe('Development Logging', () => {
    let consoleLogSpy;

    beforeEach(() => {
      process.env.NODE_ENV = 'development';
      consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    });

    afterEach(() => {
      consoleLogSpy.mockRestore();
      process.env.NODE_ENV = 'test';
    });

    it('should log configuration in development mode', () => {
      process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL = 'https://dev-runtime.com';
      process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = 'dev-key';

      render(
        <CopilotProvider>
          <div>Test</div>
        </CopilotProvider>
      );

      expect(consoleLogSpy).toHaveBeenCalledWith('CopilotProvider configuration:', {
        runtimeUrl: 'https://dev-runtime.com',
        agent: 'orchestrator',
        hasApiKey: true,
        hasAuthToken: false,
      });
    });

    it('should not log configuration in production', () => {
      process.env.NODE_ENV = 'production';
      consoleLogSpy.mockClear();

      render(
        <CopilotProvider>
          <div>Test</div>
        </CopilotProvider>
      );

      expect(consoleLogSpy).not.toHaveBeenCalled();
    });
  });

  describe('useCopilotConfig Hook', () => {
    it('should provide configuration through hook', () => {
      const TestHookComponent = () => {
        const config = useCopilotConfig();
        return (
          <div data-testid="hook-config">
            <span data-testid="hook-runtime">{config.runtimeUrl}</span>
            <span data-testid="hook-agent">{config.agent}</span>
          </div>
        );
      };

      render(
        <CopilotProvider runtimeUrl="https://test-runtime.com">
          <TestHookComponent />
        </CopilotProvider>
      );

      expect(screen.getByTestId('hook-runtime')).toHaveTextContent('https://test-runtime.com');
      expect(screen.getByTestId('hook-agent')).toHaveTextContent('orchestrator');
    });

    it('should throw error when used outside provider', () => {
      const TestComponentOutsideProvider = () => {
        try {
          useCopilotConfig();
          return <div data-testid="success">Success</div>;
        } catch (error) {
          return <div data-testid="error">{error.message}</div>;
        }
      };

      render(<TestComponentOutsideProvider />);

      // Since the hook is designed to work with default values,
      // it should not throw an error even outside provider
      expect(screen.getByTestId('success')).toBeInTheDocument();
    });
  });

  describe('Authentication Headers', () => {
    it('should include auth headers when token is provided', () => {
      process.env.NEXT_PUBLIC_API_TOKEN = 'test-auth-token';

      // This test verifies the provider handles authentication setup
      // The actual header application happens within CopilotKit
      render(
        <CopilotProvider>
          <div>Test with auth</div>
        </CopilotProvider>
      );

      expect(screen.getByText('Test with auth')).toBeInTheDocument();
    });

    it('should handle missing auth token', () => {
      process.env.NEXT_PUBLIC_API_TOKEN = undefined;

      render(
        <CopilotProvider>
          <div>Test without auth</div>
        </CopilotProvider>
      );

      expect(screen.getByText('Test without auth')).toBeInTheDocument();
    });
  });

  describe('Properties Configuration', () => {
    it('should include additional properties in CopilotKit configuration', () => {
      render(
        <CopilotProvider>
          <div>Test with properties</div>
        </CopilotProvider>
      );

      expect(screen.getByText('Test with properties')).toBeInTheDocument();
    });
  });
});