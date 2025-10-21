/**
 * CopilotErrorBoundary.tsx
 *
 * Comprehensive error boundary for CopilotKit operations.
 * Provides graceful degradation and detailed error reporting.
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Bug, Wifi, WifiOff } from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

interface CopilotErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
  retryCount: number;
}

interface CopilotErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  maxRetries?: number;
  showRetry?: boolean;
  isolateErrors?: boolean;
}

interface CopilotErrorInfo {
  type: 'runtime' | 'network' | 'configuration' | 'timeout' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  recoverable: boolean;
  suggestions: string[];
  technicalDetails?: string;
}

// ============================================================================
// Error Classification and Analysis
// ============================================================================

function classifyError(error: Error): CopilotErrorInfo {
  const message = error.message.toLowerCase();

  // Network errors
  if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
    return {
      type: 'network',
      severity: 'medium',
      recoverable: true,
      suggestions: [
        'Check your internet connection',
        'Verify the CopilotKit runtime is running',
        'Try refreshing the page'
      ],
      technicalDetails: error.stack
    };
  }

  // Timeout errors
  if (message.includes('timeout') || message.includes('timed out')) {
    return {
      type: 'timeout',
      severity: 'medium',
      recoverable: true,
      suggestions: [
        'The request took too long. Try again.',
        'Check if the server is responding slowly',
        'Try with a simpler request'
      ],
      technicalDetails: error.stack
    };
  }

  // Configuration errors
  if (message.includes('configuration') || message.includes('configured') || message.includes('api key')) {
    return {
      type: 'configuration',
      severity: 'high',
      recoverable: false,
      suggestions: [
        'Check your environment variables',
        'Ensure CopilotKit API key is set',
        'Verify runtime URL configuration'
      ],
      technicalDetails: error.stack
    };
  }

  // Runtime errors (from CopilotKit)
  if (message.includes('copilot') || message.includes('agent') || message.includes('action')) {
    return {
      type: 'runtime',
      severity: 'high',
      recoverable: true,
      suggestions: [
        'Try reloading the page',
        'Clear your browser cache',
        'Check browser console for details'
      ],
      technicalDetails: error.stack
    };
  }

  // Default unknown error
  return {
    type: 'unknown',
    severity: 'high',
    recoverable: false,
    suggestions: [
      'Try reloading the page',
      'Contact support if the issue persists',
      'Check browser console for more details'
    ],
    technicalDetails: error.stack
  };
}

// ============================================================================
// Main Error Boundary Component
// ============================================================================

export class CopilotErrorBoundary extends Component<CopilotErrorBoundaryProps, CopilotErrorBoundaryState> {
  private retryTimeoutId?: NodeJS.Timeout;

  constructor(props: CopilotErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<CopilotErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error for debugging
    console.error('CopilotErrorBoundary caught an error:', {
      error,
      errorInfo,
      retryCount: this.state.retryCount,
      timestamp: new Date().toISOString()
    });

    // In production, send to error reporting service
    if (process.env.NODE_ENV === 'production') {
      this.reportError(error, errorInfo);
    }
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  private reportError = (error: Error, errorInfo: React.ErrorInfo) => {
    // Send to error reporting service (sentry, logrocket, etc.)
    try {
      // Example integration - replace with your actual error reporting
      if (window.gtag) {
        window.gtag('event', 'exception', {
          description: error.message,
          fatal: false,
          custom_map: {
            component: 'CopilotErrorBoundary',
            stack_trace: error.stack
          }
        });
      }
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private handleRetry = () => {
    const { maxRetries = 3 } = this.props;

    if (this.state.retryCount >= maxRetries) {
      console.warn('Max retries reached for CopilotKit error boundary');
      return;
    }

    this.setState(prevState => ({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      retryCount: prevState.retryCount + 1
    }));

    // Add a small delay before retry to avoid immediate re-error
    this.retryTimeoutId = setTimeout(() => {
      // Force a re-render by updating state
      this.forceUpdate();
    }, 1000);
  };

  private getErrorIcon = (errorInfo: CopilotErrorInfo) => {
    switch (errorInfo.type) {
      case 'network':
        return <WifiOff className="h-6 w-6 text-red-600" />;
      case 'configuration':
        return <Bug className="h-6 w-6 text-red-600" />;
      case 'timeout':
        return <RefreshCw className="h-6 w-6 text-orange-600" />;
      default:
        return <AlertTriangle className="h-6 w-6 text-red-600" />;
    }
  };

  private getErrorColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'text-yellow-800 bg-yellow-50 border-yellow-200';
      case 'medium':
        return 'text-orange-800 bg-orange-50 border-orange-200';
      case 'high':
        return 'text-red-800 bg-red-50 border-red-200';
      case 'critical':
        return 'text-red-900 bg-red-100 border-red-300';
      default:
        return 'text-gray-800 bg-gray-50 border-gray-200';
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const errorInfo = classifyError(this.state.error);
      const { showRetry = true, maxRetries = 3, isolateErrors = false } = this.props;

      // Use custom fallback if provided
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      const canRetry = showRetry && errorInfo.recoverable && this.state.retryCount < maxRetries;
      const errorColor = this.getErrorColor(errorInfo.severity);

      return (
        <div className={`min-h-screen ${errorColor} border-2 p-6 m-4 rounded-lg`}>
          <div className="max-w-4xl mx-auto">
            {/* Error Header */}
            <div className="flex items-center gap-4 mb-6">
              {this.getErrorIcon(errorInfo)}
              <div>
                <h1 className="text-2xl font-bold mb-2">
                  CopilotKit Error
                </h1>
                <p className="text-lg opacity-90">
                  {errorInfo.type === 'network' ? 'Connection Error' :
                   errorInfo.type === 'configuration' ? 'Configuration Error' :
                   errorInfo.type === 'timeout' ? 'Request Timeout' :
                   'Runtime Error'}
                </p>
              </div>
            </div>

            {/* Error Message */}
            <div className={`mb-6 p-4 rounded-lg ${isolateErrors ? 'bg-white bg-opacity-50' : ''}`}>
              <p className="text-lg mb-2">{this.state.error.message}</p>
              {errorInfo.recoverable && (
                <p className="text-sm opacity-80">
                  This error is recoverable. You may try the suggested solutions below.
                </p>
              )}
            </div>

            {/* Suggestions */}
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                💡 Suggested Solutions
              </h2>
              <ul className="space-y-2">
                {errorInfo.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">✓</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Retry Button */}
            {canRetry && (
              <div className="mb-6">
                <button
                  onClick={this.handleRetry}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Retry ({maxRetries - this.state.retryCount} attempts left)
                </button>
              </div>
            )}

            {/* Technical Details */}
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-6 p-4 bg-black bg-opacity-10 rounded-lg">
                <h3 className="font-semibold mb-2 text-sm">Technical Details (Development)</h3>
                <div className="text-xs space-y-2">
                  <div>
                    <strong>Error Type:</strong> {errorInfo.type}
                  </div>
                  <div>
                    <strong>Severity:</strong> {errorInfo.severity}
                  </div>
                  <div>
                    <strong>Recoverable:</strong> {errorInfo.recoverable ? 'Yes' : 'No'}
                  </div>
                  <div>
                    <strong>Retry Count:</strong> {this.state.retryCount}/{maxRetries}
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre className="mt-1 text-xs bg-white bg-opacity-50 p-2 rounded overflow-auto max-h-32">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                  {errorInfo.technicalDetails && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="mt-1 text-xs bg-white bg-opacity-50 p-2 rounded overflow-auto max-h-48">
                        {errorInfo.technicalDetails}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Contact Support */}
            <div className="text-sm opacity-80">
              <p>
                If this error persists, please contact support with the error details above.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// ============================================================================
// Functional Error Boundary Hook
// ============================================================================

export function useCopilotErrorHandler() {
  const [errors, setErrors] = React.useState<Array<{
    id: string;
    error: Error;
    timestamp: Date;
    recovered: boolean;
  }>>([]);

  const handleError = React.useCallback((error: Error) => {
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    setErrors(prev => [...prev, {
      id: errorId,
      error,
      timestamp: new Date(),
      recovered: false
    }]);

    // Log error
    console.error('Copilot error:', error);

    // Report error in production
    if (process.env.NODE_ENV === 'production') {
      // Send to error reporting service
      if (window.gtag) {
        window.gtag('event', 'exception', {
          description: error.message,
          fatal: false,
          custom_map: {
            component: 'useCopilotErrorHandler',
            error_id: errorId
          }
        });
      }
    }
  }, []);

  const recoverFromError = React.useCallback((errorId: string) => {
    setErrors(prev => prev.map(err =>
      err.id === errorId ? { ...err, recovered: true } : err
    ));
  }, []);

  const clearErrors = React.useCallback(() => {
    setErrors([]);
  }, []);

  const activeErrors = errors.filter(err => !err.recovered);

  return {
    errors: activeErrors,
    handleError,
    recoverFromError,
    clearErrors,
    hasErrors: activeErrors.length > 0
  };
}