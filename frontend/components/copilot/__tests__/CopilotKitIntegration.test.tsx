/**
 * CopilotKit Integration Tests
 *
 * Comprehensive tests for all CopilotKit frontend components.
 * Tests message sending, state synchronization, error handling, and action handlers.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CopilotProvider } from '../CopilotProvider';
import { CopilotChatIntegration } from '../CopilotChatIntegration';
import { AccountAnalysisAgent } from '../AccountAnalysisAgent';
import { CoAgentDashboard } from '../CoAgentIntegration';
import { CopilotErrorBoundary } from '../CopilotErrorBoundary';

// ============================================================================
// Mock CopilotKit
// ============================================================================

// Mock CopilotKit hooks
jest.mock('@copilotkit/react-core', () => ({
  useCopilotChat: jest.fn(() => ({
    isLoading: false,
    visibleMessages: [],
    appendMessage: jest.fn(),
    setMessages: jest.fn(),
    deleteMessage: jest.fn(),
    reloadMessages: jest.fn(),
  })),
  useCopilotAction: jest.fn(),
  useCopilotReadable: jest.fn(),
  CopilotKit: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock fetch for API calls
global.fetch = jest.fn() as jest.Mock;

// ============================================================================
// Test Utilities
// ============================================================================

const mockFetch = (response: any, ok = true, status = 200) => {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok,
    status,
    json: () => Promise.resolve(response),
    text: () => Promise.resolve(JSON.stringify(response)),
  });
};

const defaultProps = {
  runtimeUrl: 'http://localhost:8008',
};

// ============================================================================
// CopilotProvider Tests
// ============================================================================

describe('CopilotProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NODE_ENV = 'test';
  });

  it('renders children when configuration is valid', () => {
    process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL = 'http://localhost:8008';
    process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = 'test-key';

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <div>Test Content</div>
      </CopilotProvider>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('shows configuration error in development', () => {
    process.env.NODE_ENV = 'development';
    delete process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY;

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <div>Test Content</div>
      </CopilotProvider>
    );

    expect(screen.getByText('CopilotKit Configuration Error')).toBeInTheDocument();
    expect(screen.getByText(/API key nor auth token is configured/)).toBeInTheDocument();
  });

  it('provides correct configuration via hook', () => {
    process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL = 'http://localhost:8008';
    process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = 'test-key';

    const { result } = require('react').renderHook(() =>
      require('../CopilotProvider').useCopilotConfig()
    );

    expect(result.current.isConfigured).toBe(true);
    expect(result.current.hasApiKey).toBe(true);
    expect(result.current.runtimeUrl).toBe('http://localhost:8008');
  });
});

// ============================================================================
// CopilotChatIntegration Tests
// ============================================================================

describe('CopilotChatIntegration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders chat interface correctly', () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CopilotChatIntegration />
      </CopilotProvider>
    );

    expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask about an account or request analysis...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('displays suggestion chips when chat is empty', () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CopilotChatIntegration />
      </CopilotProvider>
    );

    expect(screen.getByText('Analyze account ACC-001')).toBeInTheDocument();
    expect(screen.getByText('Show me high-risk accounts')).toBeInTheDocument();
    expect(screen.getByText('Generate recommendations for account 12345')).toBeInTheDocument();
  });

  it('handles message sending correctly', async () => {
    const mockAppendMessage = jest.fn();
    jest.doMock('@copilotkit/react-core', () => ({
      useCopilotChat: () => ({
        isLoading: false,
        visibleMessages: [],
        appendMessage: mockAppendMessage,
        setMessages: jest.fn(),
        deleteMessage: jest.fn(),
        reloadMessages: jest.fn(),
      }),
      useCopilotReadable: jest.fn(),
    }));

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CopilotChatIntegration />
      </CopilotProvider>
    );

    const input = screen.getByPlaceholderText('Ask about an account or request analysis...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockAppendMessage).toHaveBeenCalledWith('Test message');
      expect(input).toHaveValue('');
    });
  });

  it('prevents sending empty messages', () => {
    const mockAppendMessage = jest.fn();
    jest.doMock('@copilotkit/react-core', () => ({
      useCopilotChat: () => ({
        isLoading: false,
        visibleMessages: [],
        appendMessage: mockAppendMessage,
        setMessages: jest.fn(),
        deleteMessage: jest.fn(),
        reloadMessages: jest.fn(),
      }),
      useCopilotReadable: jest.fn(),
    }));

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CopilotChatIntegration />
      </CopilotProvider>
    );

    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    expect(mockAppendMessage).not.toHaveBeenCalled();
  });

  it('shows loading state during message sending', async () => {
    jest.doMock('@copilotkit/react-core', () => ({
      useCopilotChat: () => ({
        isLoading: true,
        visibleMessages: [],
        appendMessage: jest.fn(),
        setMessages: jest.fn(),
        deleteMessage: jest.fn(),
        reloadMessages: jest.fn(),
      }),
      useCopilotReadable: jest.fn(),
    }));

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CopilotChatIntegration />
      </CopilotProvider>
    );

    expect(screen.getByText('AI is thinking...')).toBeInTheDocument();
  });

  it('displays character count', () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CopilotChatIntegration />
      </CopilotProvider>
    );

    const input = screen.getByPlaceholderText('Ask about an account or request analysis...');
    fireEvent.change(input, { target: { value: 'Test message' } });

    expect(screen.getByText('12 characters')).toBeInTheDocument();
  });
});

// ============================================================================
// AccountAnalysisAgent Tests
// ============================================================================

describe('AccountAnalysisAgent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders account analysis interface', () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <AccountAnalysisAgent {...defaultProps} />
      </CopilotProvider>
    );

    expect(screen.getByText('Account Analysis Agent')).toBeInTheDocument();
  });

  it('handles analyze account action correctly', async () => {
    const mockResponse = {
      account_snapshot: {
        account_id: 'ACC-001',
        account_name: 'Test Account',
        risk_level: 'medium',
        priority_score: 75,
      },
      risk_signals: [],
      recommendations: [],
      run_id: 'test-run-123',
      timestamp: new Date().toISOString(),
    };

    mockFetch(mockResponse);

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <AccountAnalysisAgent {...defaultProps} />
      </CopilotProvider>
    );

    // Simulate calling the action
    const actionHandler = require('@copilotkit/react-core').useCopilotAction.mock.calls[0][0].handler;
    const result = await actionHandler({ accountId: 'ACC-001' });

    expect(result.success).toBe(true);
    expect(result.data.account_name).toBe('Test Account');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8008/orchestrator/analyze',
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('ACC-001'),
      })
    );
  });

  it('handles API errors gracefully', async () => {
    mockFetch({ error: 'Server error' }, false, 500);

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <AccountAnalysisAgent {...defaultProps} />
      </CopilotProvider>
    );

    const actionHandler = require('@copilotkit/react-core').useCopilotAction.mock.calls[0][0].handler;
    const result = await actionHandler({ accountId: 'ACC-001' });

    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    expect(result.message).toContain('Failed to analyze account');
  });

  it('validates input parameters', async () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <AccountAnalysisAgent {...defaultProps} />
      </CopilotProvider>
    );

    const actionHandler = require('@copilotkit/react-core').useCopilotAction.mock.calls[0][0].handler;
    const result = await actionHandler({ accountId: '' });

    expect(result.success).toBe(false);
    expect(result.error).toBe('INVALID_ACCOUNT_ID');
  });

  it('shows loading states during analysis', async () => {
    mockFetch({}); // Will return empty object

    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <AccountAnalysisAgent {...defaultProps} />
      </CopilotProvider>
    );

    const actionHandler = require('@copilotkit/react-core').useCopilotAction.mock.calls[0][0].handler;

    // Start analysis
    const analysisPromise = actionHandler({ accountId: 'ACC-001' });

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/zoho-data-scout.*running/i)).toBeInTheDocument();
    });

    await analysisPromise;
  });
});

// ============================================================================
// CoAgentIntegration Tests
// ============================================================================

describe('CoAgentDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders agent dashboard correctly', () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CoAgentDashboard runtimeUrl="http://localhost:8008" />
      </CopilotProvider>
    );

    expect(screen.getByText('Shared Agent State')).toBeInTheDocument();
    expect(screen.getByText('Agent Messages')).toBeInTheDocument();
    expect(screen.getByText('Current Account')).toBeInTheDocument();
    expect(screen.getByText('None')).toBeInTheDocument(); // Default account state
  });

  it('displays agent state correctly', () => {
    render(
      <CopilotProvider runtimeUrl="http://localhost:8008">
        <CoAgentDashboard runtimeUrl="http://localhost:8008" />
      </CopilotProvider>
    );

    expect(screen.getByText('Analysis In Progress')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument(); // Default state
    expect(screen.getByText('Empty')).toBeInTheDocument(); // Agent queue
  });
});

// ============================================================================
// CopilotErrorBoundary Tests
// ============================================================================

describe('CopilotErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Component that throws an error
  const ThrowErrorComponent: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = false }) => {
    if (shouldThrow) {
      throw new Error('Test error for boundary');
    }
    return <div>No error</div>;
  };

  it('renders children when there is no error', () => {
    render(
      <CopilotErrorBoundary>
        <ThrowErrorComponent />
      </CopilotErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('catches and displays error information', () => {
    render(
      <CopilotErrorBoundary>
        <ThrowErrorComponent shouldThrow={true} />
      </CopilotErrorBoundary>
    );

    expect(screen.getByText('CopilotKit Error')).toBeInTheDocument();
    expect(screen.getByText('Test error for boundary')).toBeInTheDocument();
    expect(screen.getByText(/Suggested Solutions/)).toBeInTheDocument();
  });

  it('classifies network errors correctly', () => {
    const networkError = new Error('Network connection failed');
    const errorInfo = require('../CopilotErrorBoundary').classifyError(networkError);

    expect(errorInfo.type).toBe('network');
    expect(errorInfo.severity).toBe('medium');
    expect(errorInfo.recoverable).toBe(true);
    expect(errorInfo.suggestions).toContain('Check your internet connection');
  });

  it('shows retry button for recoverable errors', () => {
    render(
      <CopilotErrorBoundary maxRetries={3} showRetry={true}>
        <ThrowErrorComponent shouldThrow={true} />
      </CopilotErrorBoundary>
    );

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    expect(screen.getByText(/2 attempts left/)).toBeInTheDocument();
  });

  it('limits retry attempts', () => {
    render(
      <CopilotErrorBoundary maxRetries={1} showRetry={true}>
        <ThrowErrorComponent shouldThrow={true} />
      </CopilotErrorBoundary>
    );

    // Should show retry button
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();

    // Click retry
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    // Should not show retry button after max retries
    expect(screen.queryByText(/0 attempts left/)).not.toBeInTheDocument();
  });
});

// ============================================================================
// Integration Tests
// ============================================================================

describe('CopilotKit Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('works end-to-end with all components', async () => {
    mockFetch({
      account_snapshot: {
        account_id: 'ACC-001',
        account_name: 'Test Account',
        risk_level: 'low',
        priority_score: 85,
        deal_count: 5,
        total_value: 100000,
      },
      risk_signals: [],
      recommendations: [],
    });

    const TestComponent = () => (
      <div>
        <CopilotChatIntegration />
        <AccountAnalysisAgent {...defaultProps} />
        <CoAgentDashboard runtimeUrl="http://localhost:8008" />
      </div>
    );

    render(
      <CopilotErrorBoundary>
        <CopilotProvider runtimeUrl="http://localhost:8008">
          <TestComponent />
        </CopilotProvider>
      </CopilotErrorBoundary>
    );

    // Verify all components rendered
    expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
    expect(screen.getByText('Account Analysis Agent')).toBeInTheDocument();
    expect(screen.getByText('Shared Agent State')).toBeInTheDocument();

    // Test message flow
    const input = screen.getByPlaceholderText('Ask about an account or request analysis...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Analyze account ACC-001' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
  });

  it('handles network errors gracefully', async () => {
    mockFetch({ error: 'Network error' }, false, 0);

    const TestComponent = () => (
      <CopilotChatIntegration />
    );

    render(
      <CopilotErrorBoundary>
        <CopilotProvider runtimeUrl="http://localhost:8008">
          <TestComponent />
        </CopilotProvider>
      </CopilotErrorBoundary>
    );

    // Simulate network error during message send
    const input = screen.getByPlaceholderText('Ask about an account or request analysis...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });
});