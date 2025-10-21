/**
 * AccountAnalysisAgent Component Tests
 *
 * Comprehensive tests for account analysis workflow and CopilotKit integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';
import { createMockAccount, createMockAnalysisResult, createMockRiskSignal, createMockRecommendation, mockFetchResponse, mockFetchError } from '@/jest.setup.enhanced';

// Mock CopilotKit hooks
const mockUseCopilotAction = jest.fn();
const mockUseCopilotReadable = jest.fn();
const mockUseCopilotChat = jest.fn(() => ({ isLoading: false }));

jest.mock('@copilotkit/react-core', () => ({
  useCopilotAction: mockUseCopilotAction,
  useCopilotReadable: mockUseCopilotReadable,
  useCopilotChat: mockUseCopilotChat,
}));

describe('AccountAnalysisAgent', () => {
  const mockRuntimeUrl = 'http://localhost:8008';
  const mockApprovalRequired = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseCopilotAction.mockImplementation(({ handler }) => handler);
    mockUseCopilotReadable.mockImplementation(() => {});
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render without crashing', () => {
      render(
        <AccountAnalysisAgent
          runtimeUrl={mockRuntimeUrl}
          onApprovalRequired={mockApprovalRequired}
        />
      );

      expect(screen.getByText('Agent Execution Status')).toBeInTheDocument();
    });

    it('should display initial empty state', () => {
      render(
        <AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />
      );

      // Should show status section but no analysis results
      expect(screen.getByText('Agent Execution Status')).toBeInTheDocument();
      expect(screen.queryByText('Account Snapshot')).not.toBeInTheDocument();
    });

    it('should configure CopilotKit readable contexts', () => {
      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      expect(mockUseCopilotReadable).toHaveBeenCalledTimes(3); // selectedAccount, analysisResult, agentStatus
    });
  });

  describe('CopilotKit Actions', () => {
    it('should register all required CopilotKit actions', () => {
      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      expect(mockUseCopilotAction).toHaveBeenCalledTimes(5); // analyzeAccount, fetchAccountData, getRecommendations, selectAccount, clearAccountSelection
    });

    it('should configure analyzeAccount action correctly', () => {
      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const analyzeCall = mockUseCopilotAction.mock.calls.find(call => call[0].name === 'analyzeAccount');
      expect(analyzeCall).toBeDefined();
      expect(analyzeCall[0].description).toContain('comprehensive account analysis');
      expect(analyzeCall[0].parameters).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'accountId',
            type: 'string',
            required: true,
          }),
        ])
      );
    });

    it('should configure fetchAccountData action correctly', () => {
      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const fetchCall = mockUseCopilotAction.mock.calls.find(call => call[0].name === 'fetchAccountData');
      expect(fetchCall).toBeDefined();
      expect(fetchCall[0].description).toContain('quick snapshot');
    });

    it('should configure getRecommendations action correctly', () => {
      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const recommendationsCall = mockUseCopilotAction.mock.calls.find(call => call[0].name === 'getRecommendations');
      expect(recommendationsCall).toBeDefined();
      expect(recommendationsCall[0].description).toContain('HITL approval');
    });
  });

  describe('Account Analysis Action', () => {
    it('should handle successful account analysis', async () => {
      const mockAnalysisResult = createMockAnalysisResult({
        account_snapshot: {
          ...createMockAnalysisResult().account_snapshot,
          priority_score: 85,
          risk_level: 'high',
        },
      });

      mockFetchResponse(mockAnalysisResult);

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result).toEqual({
        success: true,
        message: 'Successfully analyzed account ACC-001',
        data: {
          account_name: 'Test Account',
          risk_level: 'high',
          priority_score: 85,
          risk_signals_count: 0,
          recommendations_count: 0,
        },
        full_result: mockAnalysisResult,
      });
    });

    it('should handle analysis failure', async () => {
      const analysisError = new Error('Analysis failed');
      mockFetchError(analysisError);

      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result).toEqual({
        success: false,
        message: 'Failed to analyze account: Analysis failed',
      });
    });

    it('should update agent status during analysis', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      const { rerender } = render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Start analysis
      const analysisPromise = actionHandler({ accountId: 'ACC-001' });

      // Check that status updates to running
      await waitFor(() => {
        expect(screen.getByText('zoho data scout')).toBeInTheDocument();
        expect(screen.getByText('running')).toBeInTheDocument();
      });

      // Complete the analysis
      mockFetchResponse(createMockAnalysisResult());
      await analysisPromise;

      // Check final status
      expect(screen.getByText('completed')).toBeInTheDocument();
    });
  });

  describe('Account Selection', () => {
    it('should display selected account information', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        if (handler.name === 'selectAccount') {
          actionHandler = handler;
        }
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Select an account via action
      await actionHandler({
        accountId: 'ACC-001',
        accountName: 'Test Account Company',
        owner: 'John Doe'
      });

      // Verify account information is displayed
      await waitFor(() => {
        expect(screen.getByText('Selected Account')).toBeInTheDocument();
        expect(screen.getByText('ACC-001')).toBeInTheDocument();
        expect(screen.getByText('Test Account Company')).toBeInTheDocument();
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });

    it('should clear account selection', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        if (handler.name === 'clearAccountSelection') {
          actionHandler = handler;
        }
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // First select an account
      const selectHandler = mockUseCopilotAction.mock.calls.find(call => call[0].name === 'selectAccount')[0].handler;
      await selectHandler({ accountId: 'ACC-001', accountName: 'Test' });

      // Then clear selection
      await actionHandler();

      expect(screen.queryByText('Selected Account')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when analysis fails', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      mockFetchError(new Error('Network timeout'));

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByText('Network timeout')).toBeInTheDocument();
      });
    });

    it('should handle malformed API response', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      // Mock invalid response
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'ACC-001' });

      expect(result.success).toBe(false);
      expect(result.message).toContain('Analysis failed');
    });

    it('should handle fetch with invalid JSON', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      // Mock invalid JSON response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await expect(actionHandler({ accountId: 'ACC-001' })).rejects.toThrow();
    });
  });

  describe('Analysis Results Display', () => {
    it('should display account snapshot with metrics', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      const mockResult = createMockAnalysisResult({
        account_snapshot: {
          account_id: 'ACC-001',
          account_name: 'Test Account',
          owner_name: 'John Doe',
          status: 'Active',
          risk_level: 'medium',
          priority_score: 75,
          needs_review: true,
          deal_count: 10,
          total_value: 100000,
        },
        risk_signals: [],
        recommendations: [],
      });

      mockFetchResponse(mockResult);

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(screen.getByText('Account Snapshot')).toBeInTheDocument();
        expect(screen.getByText('75')).toBeInTheDocument(); // Priority Score
        expect(screen.getByText('MEDIUM')).toBeInTheDocument(); // Risk Level
        expect(screen.getByText('10')).toBeInTheDocument(); // Deal Count
        expect(screen.getByText('This account needs review')).toBeInTheDocument();
      });
    });

    it('should display risk signals when present', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      const mockResult = createMockAnalysisResult({
        risk_signals: [
          createMockRiskSignal({
            signal_type: 'high_churn_risk',
            severity: 'high',
            description: 'Account showing signs of potential churn',
          }),
          createMockRiskSignal({
            signal_type: 'payment_delay',
            severity: 'medium',
            description: 'Recent payment delay detected',
          }),
        ],
      });

      mockFetchResponse(mockResult);

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(screen.getByText('Risk Signals (2)')).toBeInTheDocument();
        expect(screen.getByText('high_churn_risk')).toBeInTheDocument();
        expect(screen.getByText('payment_delay')).toBeInTheDocument();
        expect(screen.getByText('HIGH')).toBeInTheDocument();
        expect(screen.getByText('MEDIUM')).toBeInTheDocument();
      });
    });

    it('should display recommendations when present', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      const mockResult = createMockAnalysisResult({
        recommendations: [
          createMockRecommendation({
            title: 'Increase Customer Engagement',
            confidence_score: 90,
            priority: 'critical',
          }),
        ],
      });

      mockFetchResponse(mockResult);

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(screen.getByText('Recommendations (1)')).toBeInTheDocument();
        expect(screen.getByText('Increase Customer Engagement')).toBeInTheDocument();
        expect(screen.getByText('90% confident')).toBeInTheDocument();
        expect(screen.getByText('CRITICAL')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading indicator during chat processing', () => {
      mockUseCopilotChat.mockReturnValue({ isLoading: true });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      expect(screen.getByText('🤖 AI is processing your request...')).toBeInTheDocument();
    });

    it('should show agent status during analysis', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Start analysis to trigger loading state
      const analysisPromise = actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(screen.getByText('Agent Execution Status')).toBeInTheDocument();
        expect(screen.getByText('zoho data scout')).toBeInTheDocument();
      });

      // Clean up
      mockFetchResponse(createMockAnalysisResult());
      await analysisPromise;
    });
  });

  describe('HITL Approval Workflow', () => {
    it('should call approval callback when recommendations require approval', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        if (handler.name === 'getRecommendations') {
          actionHandler = handler;
        }
        return handler;
      });

      // Mock response requiring approval
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          requires_approval: true,
          run_id: 'run-123',
          recommendations: [createMockRecommendation()],
        }),
      });

      render(
        <AccountAnalysisAgent
          runtimeUrl={mockRuntimeUrl}
          onApprovalRequired={mockApprovalRequired}
        />
      );

      await actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(mockApprovalRequired).toHaveBeenCalledWith({
          run_id: 'run-123',
          recommendations: [createMockRecommendation()],
        });
      });
    });

    it('should handle recommendations without approval requirement', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        if (handler.name === 'getRecommendations') {
          actionHandler = handler;
        }
        return handler;
      });

      // Mock response not requiring approval
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          requires_approval: false,
          recommendations: [createMockRecommendation()],
        }),
      });

      render(
        <AccountAnalysisAgent
          runtimeUrl={mockRuntimeUrl}
          onApprovalRequired={mockApprovalRequired}
        />
      );

      await actionHandler({ accountId: 'ACC-001' });

      // Should not call approval callback
      expect(mockApprovalRequired).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing approval callback gracefully', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        if (handler.name === 'getRecommendations') {
          actionHandler = handler;
        }
        return handler;
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          requires_approval: true,
          run_id: 'run-123',
          recommendations: [],
        }),
      });

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      // Should not throw error even without approval callback
      await expect(actionHandler({ accountId: 'ACC-001' })).resolves.toBeDefined();
    });

    it('should handle empty analysis results', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      const emptyResult = createMockAnalysisResult({
        risk_signals: [],
        recommendations: [],
      });

      mockFetchResponse(emptyResult);

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      await actionHandler({ accountId: 'ACC-001' });

      await waitFor(() => {
        expect(screen.getByText('Risk Signals (0)')).toBeInTheDocument();
        expect(screen.getByText('Recommendations (0)')).toBeInTheDocument();
      });
    });

    it('should handle invalid account ID format', async () => {
      let actionHandler;
      mockUseCopilotAction.mockImplementation(({ handler }) => {
        actionHandler = handler;
        return handler;
      });

      mockFetchError(new Error('Invalid account ID format'));

      render(<AccountAnalysisAgent runtimeUrl={mockRuntimeUrl} />);

      const result = await actionHandler({ accountId: 'invalid-format' });

      expect(result.success).toBe(false);
      expect(result.message).toContain('Failed to analyze account');
    });
  });
});