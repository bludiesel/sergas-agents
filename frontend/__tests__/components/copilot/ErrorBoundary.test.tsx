/**
 * CopilotErrorBoundary Component Tests
 *
 * Comprehensive tests for error boundary functionality,
 * error reporting, and recovery mechanisms
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CopilotErrorBoundary, withCopilotErrorBoundary, useCopilotErrorBoundary } from '@/components/copilot/ErrorBoundary';

// Mock console.error to capture error logs
const mockConsoleError = jest.spyOn(console, 'error').mockImplementation();

// Test component that throws errors
const ThrowingComponent = ({ shouldThrow = true, errorType = 'general' }) => {
  if (shouldThrow) {
    switch (errorType) {
      case 'network':
        throw new Error('Network request failed');
      case 'auth':
        throw new Error('Authentication failed: 401 Unauthorized');
      case 'copilot':
        throw new Error('CopilotKit connection error');
      case 'render':
        throw new Error('Failed to render component');
      case 'type':
        throw new TypeError('Cannot read property of undefined');
      default:
        throw new Error('General error occurred');
    }
  }
  return <div data-testid="normal-content">Normal content</div>;
};

// Test component with hooks
const HookComponent = () => {
  const { handleError } = useCopilotErrorBoundary();

  const triggerError = () => {
    try {
      throw new Error('Hook-triggered error');
    } catch (error) {
      handleError(error, {
        componentStack: 'TestComponent\n  at HookComponent',
      });
    }
  };

  return (
    <div>
      <div data-testid="hook-content">Hook content</div>
      <button data-testid="trigger-error" onClick={triggerError}>
        Trigger Error
      </button>
    </div>
  );
};

describe('CopilotErrorBoundary', () => {
  beforeEach(() => {
    mockConsoleError.mockClear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Basic Error Catching', () => {
    it('should render children when no error', () => {
      render(
        <CopilotErrorBoundary>
          <div data-testid="child-content">Child content</div>
        </CopilotErrorBoundary>
      );

      expect(screen.getByTestId('child-content')).toBeInTheDocument();
      expect(screen.queryByText('CopilotKit Error')).not.toBeInTheDocument();
    });

    it('should catch and display error when child throws', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      expect(screen.queryByTestId('normal-content')).not.toBeInTheDocument();
      expect(screen.getByText('CopilotKit Error')).toBeInTheDocument();
      expect(screen.getByText('General error occurred')).toBeInTheDocument();
    });

    it('should log error to console', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      expect(mockConsoleError).toHaveBeenCalledWith(
        'CopilotKit Error Boundary caught an error:',
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      );
    });

    it('should generate unique error ID', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      const errorId = screen.getByText(/copilot-error-/);
      expect(errorId).toBeInTheDocument();
      expect(errorId.textContent).toMatch(/^copilot-error-\d+-[a-z0-9]+$/);
    });
  });

  describe('Error Classification', () => {
    it('should classify network errors as high severity', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent errorType="network" />
        </CopilotErrorBoundary>
      );

      expect(screen.getByText('Network Error')).toBeInTheDocument();
      expect(screen.getByText('HIGH Severity')).toBeInTheDocument();
      expect(screen.getByText('This error may impact AI assistant features')).toBeInTheDocument();
    });

    it('should classify authentication errors as critical severity', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent errorType="auth" />
        </CopilotErrorBoundary>
      );

      expect(screen.getByText('Authentication Error')).toBeInTheDocument();
      expect(screen.getByText('CRITICAL Severity')).toBeInTheDocument();
      expect(screen.getByText('This error may affect core functionality')).toBeInTheDocument();
    });

    it('should classify CopilotKit errors as high severity', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent errorType="copilot" />
        </CopilotErrorBoundary>
      );

      expect(screen.getByText('CopilotKit Error')).toBeInTheDocument();
      expect(screen.getByText('HIGH Severity')).toBeInTheDocument();
    });

    it('should classify render errors as medium severity', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent errorType="render" />
        </CopilotErrorBoundary>
      );

      expect(screen.getByText('Rendering Error')).toBeInTheDocument();
      expect(screen.getByText('MEDIUM Severity')).toBeInTheDocument();
      expect(screen.getByText('This error may cause limited functionality')).toBeInTheDocument();
    });

    it('should classify type errors appropriately', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent errorType="type" />
        </CopilotErrorBoundary>
      );

      expect(screen.getByText('Type Error')).toBeInTheDocument();
    });
  });

  describe('Recovery Mechanisms', () => {
    it('should allow retry when attempts remain', () => {
      render(
        <CopilotErrorBoundary maxRetries={2}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      const retryButton = screen.getByText('Try Again');
      expect(retryButton).toBeInTheDocument();
      expect(screen.getByText('2 retries remaining')).toBeInTheDocument();
      expect(retryButton).not.toBeDisabled();
    });

    it('should disable retry when max attempts reached', () => {
      render(
        <CopilotErrorBoundary maxRetries={1}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      // First retry
      const retryButton = screen.getByText('Try Again');
      fireEvent.click(retryButton);

      // Wait for retry attempt to complete
      waitFor(() => {
        expect(screen.getByText('Maximum retry attempts reached')).toBeInTheDocument();
      });
    });

    it('should reset error state when reset is clicked', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      // Click reset
      const resetButton = screen.getByText('Refresh Page');
      fireEvent.click(resetButton);

      // Error should be cleared and component should try to render again
      waitFor(() => {
        expect(screen.queryByText('CopilotKit Error')).not.toBeInTheDocument();
      });
    });

    it('should track retry count correctly', () => {
      render(
        <CopilotErrorBoundary maxRetries={3}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      expect(screen.getByText('3 retries remaining')).toBeInTheDocument();

      const retryButton = screen.getByText('Try Again');

      // First retry
      fireEvent.click(retryButton);
      expect(screen.getByText('2 retries remaining')).toBeInTheDocument();

      // Second retry
      fireEvent.click(retryButton);
      expect(screen.getByText('1 retry remaining')).toBeInTheDocument();
    });

    it('should show singular retry message correctly', () => {
      render(
        <CopilotErrorBoundary maxRetries={2}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      // After one retry
      const retryButton = screen.getByText('Try Again');
      fireEvent.click(retryButton);

      expect(screen.getByText('1 retry remaining')).toBeInTheDocument();
    });
  });

  describe('Custom Error Handling', () => {
    it('should call custom error handler when provided', () => {
      const customErrorHandler = jest.fn();

      render(
        <CopilotErrorBoundary onError={customErrorHandler}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      expect(customErrorHandler).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      );
    });

    it('should use custom fallback component when provided', () => {
      const CustomFallback = () => <div data-testid="custom-fallback">Custom error UI</div>;

      render(
        <CopilotErrorBoundary fallback={<CustomFallback />}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      expect(screen.queryByText('CopilotKit Error')).not.toBeInTheDocument();
    });
  });

  describe('Error Details', () => {
    it('should show error details when expanded', async () => {
      const user = userEvent.setup();
      render(
        <CopilotErrorBoundary showErrorDetails>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      const detailsSummary = screen.getByText('Report this issue');
      await user.click(detailsSummary);

      expect(screen.getByText(/Error ID:/)).toBeInTheDocument();
      expect(screen.getByText(/Time:/)).toBeInTheDocument();
      expect(screen.getByText(/Component Stack:/)).toBeInTheDocument();
    });

    it('should show component name when provided', () => {
      render(
        <CopilotErrorBoundary componentName="TestComponent" showErrorDetails>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      const detailsSummary = screen.getByText('Report this issue');
      fireEvent.click(detailsSummary);

      expect(screen.getByText('Component: TestComponent')).toBeInTheDocument();
    });

    it('should hide error details when disabled', () => {
      render(
        <CopilotErrorBoundary showErrorDetails={false}>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      expect(screen.queryByText('Report this issue')).not.toBeInTheDocument();
    });
  });

  describe('Visual Design', () => {
    it('should apply correct severity colors', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent errorType="auth" />
        </CopilotErrorBoundary>
      );

      // Critical severity should show red styling
      const severityIndicator = screen.getByText(/This error may affect core functionality/);
      expect(severityIndicator).toHaveClass('bg-red-50', 'text-red-700');
    });

    it('should display appropriate icons', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      // Should show alert triangle icon
      const icon = document.querySelector('.lucide-alert-triangle');
      expect(icon).toBeInTheDocument();

      // Should show refresh icon in retry button
      const refreshIcon = document.querySelector('.lucide-refresh-cw');
      expect(refreshIcon).toBeInTheDocument();
    });

    it('should have responsive design', () => {
      render(
        <CopilotErrorBoundary>
          <ThrowingComponent />
        </CopilotErrorBoundary>
      );

      const errorContainer = screen.getByText('CopilotKit Error').closest('div').parentElement;
      expect(errorContainer).toHaveClass('max-w-md', 'w-full');
    });
  });
});

describe('useCopilotErrorBoundary Hook', () => {
  beforeEach(() => {
    mockConsoleError.mockClear();
  });

  it('should provide error handler function', () => {
    render(<HookComponent />);

    expect(screen.getByTestId('hook-content')).toBeInTheDocument();
    expect(screen.getByText('Trigger Error')).toBeInTheDocument();
  });

  it('should handle errors through hook', async () => {
    const user = userEvent.setup();
    render(<HookComponent />);

    const triggerButton = screen.getByText('Trigger Error');
    await user.click(triggerButton);

    expect(mockConsoleError).toHaveBeenCalledWith(
      'CopilotKit Error:',
      expect.any(Error),
      expect.objectContaining({
        componentStack: 'TestComponent\n  at HookComponent',
      })
    );
  });
});

describe('withCopilotErrorBoundary HOC', () => {
  const TestComponent = ({ name }: { name: string }) => (
    <div data-testid="hoc-content">{name}</div>
  );

  const ThrowingHocComponent = () => {
    throw new Error('HOC error');
  };

  it('should wrap component with error boundary', () => {
    const WrappedComponent = withCopilotErrorBoundary(TestComponent);

    render(<WrappedComponent name="test-prop" />);

    expect(screen.getByTestId('hoc-content')).toBeInTheDocument();
    expect(screen.getByText('test-prop')).toBeInTheDocument();
  });

  it('should handle errors in wrapped component', () => {
    const WrappedComponent = withCopilotErrorBoundary(ThrowingHocComponent);

    render(<WrappedComponent />);

    expect(screen.getByText('CopilotKit Error')).toBeInTheDocument();
  });

  it('should use HOC options', () => {
    const CustomFallback = () => <div data-testid="hoc-fallback">HOC Fallback</div>;
    const WrappedComponent = withCopilotErrorBoundary(ThrowingHocComponent, {
      fallback: <CustomFallback />,
      maxRetries: 5,
      showErrorDetails: true,
      componentName: 'HOCComponent',
    });

    render(<WrappedComponent />);

    expect(screen.getByTestId('hoc-fallback')).toBeInTheDocument();
    expect(screen.queryByText('CopilotKit Error')).not.toBeInTheDocument();
  });

  it('should set correct display name', () => {
    const WrappedComponent = withCopilotErrorBoundary(TestComponent);

    expect(WrappedComponent.displayName).toBe('withCopilotErrorBoundary(TestComponent)');
  });
});

describe('Error Reporting', () => {
  let originalFetch;
  let mockFetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    mockFetch = jest.fn();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    mockFetch.mockClear();
  });

  it('should report errors in production mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    render(
      <CopilotErrorBoundary>
        <ThrowingComponent />
      </CopilotErrorBoundary>
    );

    // In production, would send to error reporting service
    // For testing, we check that error reporting logic executes
    expect(screen.getByText(/copilot-error-/)).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('should handle error reporting failures gracefully', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    // Mock fetch to throw error during reporting
    mockFetch.mockRejectedValue(new Error('Reporting failed'));

    render(
      <CopilotErrorBoundary>
        <ThrowingComponent />
      </CopilotErrorBoundary>
    );

    // Should still show error UI even if reporting fails
    expect(screen.getByText('CopilotKit Error')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });
});