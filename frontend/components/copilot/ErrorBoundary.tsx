/**
 * CopilotKit Error Boundary Component
 *
 * Provides comprehensive error handling for CopilotKit components
 * with fallback UI, error reporting, and recovery mechanisms
 */

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Bug } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  maxRetries?: number;
  showErrorDetails?: boolean;
  componentName?: string;
}

export class CopilotErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private readonly maxRetries: number;

  constructor(props: ErrorBoundaryProps) {
    super(props);

    this.maxRetries = props.maxRetries || 3;

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: this.generateErrorId(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error for debugging
    console.error('CopilotKit Error Boundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report error to monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      this.reportError(error, errorInfo);
    }
  }

  private generateErrorId = (): string => {
    return `copilot-error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // In production, send to error reporting service
    try {
      const errorReport = {
        errorId: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        componentName: this.props.componentName || 'Unknown',
      };

      // Example: Send to error reporting service
      // fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorReport),
      // });

      console.log('Error report:', errorReport);
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
    });
  };

  private canRetry = (): boolean => {
    return this.state.retryCount < this.maxRetries;
  };

  private getErrorSeverity = (): 'critical' | 'high' | 'medium' | 'low' => {
    if (!this.state.error) return 'medium';

    const error = this.state.error;

    // Network-related errors
    if (error.message.includes('fetch') ||
        error.message.includes('network') ||
        error.message.includes('timeout')) {
      return 'high';
    }

    // Authentication errors
    if (error.message.includes('auth') ||
        error.message.includes('unauthorized') ||
        error.message.includes('401')) {
      return 'critical';
    }

    // CopilotKit-specific errors
    if (error.message.includes('CopilotKit') ||
        error.message.includes('useCopilot') ||
        error.message.includes('copilot')) {
      return 'high';
    }

    // Default
    return 'medium';
  };

  private getErrorCategory = (): string => {
    if (!this.state.error) return 'Unknown';

    const error = this.state.error.message.toLowerCase();

    if (error.includes('network') || error.includes('fetch') || error.includes('timeout')) {
      return 'Network';
    }

    if (error.includes('auth') || error.includes('unauthorized') || error.includes('401')) {
      return 'Authentication';
    }

    if (error.includes('copilotkit') || error.includes('usecopilot')) {
      return 'CopilotKit';
    }

    if (error.includes('render') || error.includes('component')) {
      return 'Rendering';
    }

    if (error.includes('type') || error.includes('undefined') || error.includes('null')) {
      return 'Type Error';
    }

    return 'General';
  };

  private getRetryMessage = (): string => {
    if (!this.canRetry()) {
      return 'Maximum retry attempts reached';
    }

    const attemptsLeft = this.maxRetries - this.state.retryCount;
    return attemptsLeft === 1 ? '1 retry remaining' : `${attemptsLeft} retries remaining`;
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback component if provided
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      // Default error UI
      const severity = this.getErrorSeverity();
      const category = this.getErrorCategory();
      const canRetry = this.canRetry();

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg border border-red-200 p-6">
            {/* Error Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 rounded-full ${
                severity === 'critical' ? 'bg-red-100' :
                severity === 'high' ? 'bg-orange-100' :
                'bg-yellow-100'
              }`}>
                <AlertTriangle className={`w-6 h-6 ${
                  severity === 'critical' ? 'text-red-600' :
                  severity === 'high' ? 'text-orange-600' :
                  'text-yellow-600'
                }`} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  CopilotKit Error
                </h3>
                <p className="text-sm text-gray-600">
                  {category} Error • {severity.toUpperCase()} Severity
                </p>
              </div>
            </div>

            {/* Error Message */}
            <div className="mb-4">
              <p className="text-gray-700 mb-2">
                Something went wrong with the AI assistant functionality.
              </p>
              {this.state.error && (
                <div className="bg-gray-50 rounded p-3 mb-3">
                  <p className="text-sm font-mono text-gray-800">
                    {this.state.error.message}
                  </p>
                </div>
              )}
            </div>

            {/* Error Actions */}
            <div className="space-y-3">
              {canRetry && (
                <button
                  onClick={this.handleRetry}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                  <span className="text-sm opacity-75">
                    ({this.getRetryMessage()})
                  </span>
                </button>
              )}

              <button
                onClick={this.handleReset}
                className="w-full flex items-center justify-center gap-2 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Refresh Page
              </button>

              {/* Report Issue */}
              {this.props.showErrorDetails !== false && (
                <details className="text-left">
                  <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-700 flex items-center gap-2">
                    <Bug className="w-4 h-4" />
                    Report this issue
                  </summary>
                  <div className="mt-3 p-3 bg-gray-50 rounded text-xs">
                    <div className="space-y-2">
                      <div>
                        <strong>Error ID:</strong> {this.state.errorId}
                      </div>
                      {this.props.componentName && (
                        <div>
                          <strong>Component:</strong> {this.props.componentName}
                        </div>
                      )}
                      <div>
                        <strong>Time:</strong> {new Date().toLocaleString()}
                      </div>
                      {this.state.errorInfo && (
                        <div>
                          <strong>Component Stack:</strong>
                          <pre className="mt-1 overflow-x-auto bg-gray-100 p-2 rounded text-xs">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </details>
              )}
            </div>

            {/* Severity Indicator */}
            <div className={`mt-4 p-3 rounded text-center text-sm ${
              severity === 'critical' ? 'bg-red-50 text-red-700' :
              severity === 'high' ? 'bg-orange-50 text-orange-700' :
              'bg-yellow-50 text-yellow-700'
            }`}>
              {severity === 'critical' && 'This error may affect core functionality'}
              {severity === 'high' && 'This error may impact AI assistant features'}
              {severity === 'medium' && 'This error may cause limited functionality'}
              {severity === 'low' && 'This error has minimal impact'}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for easier error boundary usage
export function useCopilotErrorBoundary() {
  const handleError = React.useCallback((error: Error, errorInfo: ErrorInfo) => {
    // Custom error handling logic
    console.error('CopilotKit Error:', error, errorInfo);

    // You can add custom error reporting here
    // Example: send to analytics, error tracking, etc.
  }, []);

  return { handleError };
}

// Higher-order component for wrapping CopilotKit components
export function withCopilotErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  options: {
    fallback?: ReactNode;
    maxRetries?: number;
    showErrorDetails?: boolean;
    componentName?: string;
  } = {}
) {
  const WrappedComponent = (props: P) => (
    <CopilotErrorBoundary
      fallback={options.fallback}
      maxRetries={options.maxRetries}
      showErrorDetails={options.showErrorDetails}
      componentName={options.componentName || Component.name}
    >
      <Component {...props} />
    </CopilotErrorBoundary>
  );

  WrappedComponent.displayName = `withCopilotErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}