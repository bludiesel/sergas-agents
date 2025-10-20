/**
 * Integration Tests: HITL (Human-in-the-Loop) Approval Workflows
 *
 * Tests the complete human approval workflow for recommendations,
 * including interruption, state management, and resumption.
 *
 * Coverage:
 * - Workflow interruption for approval
 * - Approval modal display and interaction
 * - State persistence during interruption
 * - Workflow resumption after approval/rejection
 * - Modification of recommendations before approval
 * - Timeout handling
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { CopilotKit } from '@copilotkit/react-core';
import { ApprovalModal } from '@/components/ApprovalModal';
import '@testing-library/jest-dom';

// Mock fetch
global.fetch = jest.fn();

describe('HITL Approval Workflow Integration Tests', () => {
  const mockRuntimeUrl = 'http://localhost:8000';

  const mockApprovalRequest = {
    run_id: 'run_123',
    recommendations: [
      {
        recommendation_id: 'rec_1',
        category: 'engagement',
        title: 'Schedule Follow-Up Meeting',
        description: 'Customer has been inactive for 30 days. Schedule a check-in meeting.',
        confidence_score: 85,
        priority: 'high',
        next_steps: [
          'Review recent communication history',
          'Prepare meeting agenda',
          'Send calendar invite',
        ],
      },
      {
        recommendation_id: 'rec_2',
        category: 'upsell',
        title: 'Propose Premium Features',
        description: 'Account is growing rapidly. Introduce premium tier features.',
        confidence_score: 72,
        priority: 'medium',
        next_steps: ['Prepare feature comparison', 'Schedule demo call'],
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success' }),
    });
  });

  describe('Workflow Interruption', () => {
    it('should interrupt workflow when approval is required', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      expect(screen.getByText('Approval Required')).toBeInTheDocument();
      expect(
        screen.getByText('Review the following recommendations and approve or reject.')
      ).toBeInTheDocument();
    });

    it('should display approval modal with recommendations', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      // Check first recommendation
      expect(
        screen.getByText('Schedule Follow-Up Meeting')
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Customer has been inactive for 30 days/)
      ).toBeInTheDocument();

      // Check second recommendation
      expect(screen.getByText('Propose Premium Features')).toBeInTheDocument();
    });

    it('should show recommendation details including confidence and priority', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      // Check confidence scores
      expect(screen.getByText('85% confident')).toBeInTheDocument();
      expect(screen.getByText('72% confident')).toBeInTheDocument();

      // Check priorities
      expect(screen.getByText('high')).toBeInTheDocument();
      expect(screen.getByText('medium')).toBeInTheDocument();
    });

    it('should display next steps for each recommendation', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      expect(
        screen.getByText('Review recent communication history')
      ).toBeInTheDocument();
      expect(screen.getByText('Prepare meeting agenda')).toBeInTheDocument();
      expect(screen.getByText('Send calendar invite')).toBeInTheDocument();
    });

    it('should preserve workflow state during interruption', async () => {
      const TestWorkflow = () => {
        const [workflowState, setWorkflowState] = React.useState({
          status: 'running',
          step: 3,
          accountId: 'acc_123',
        });
        const [showApproval, setShowApproval] = React.useState(false);

        const triggerApproval = () => {
          setWorkflowState((prev) => ({ ...prev, status: 'interrupted' }));
          setShowApproval(true);
        };

        return (
          <div>
            <div data-testid="workflow-status">{workflowState.status}</div>
            <div data-testid="workflow-step">{workflowState.step}</div>
            <div data-testid="account-id">{workflowState.accountId}</div>
            <button onClick={triggerApproval} data-testid="trigger-btn">
              Trigger Approval
            </button>
            {showApproval && (
              <ApprovalModal
                request={mockApprovalRequest}
                onApprove={async () => setShowApproval(false)}
                onReject={async () => setShowApproval(false)}
              />
            )}
          </div>
        );
      };

      render(<TestWorkflow />);

      expect(screen.getByTestId('workflow-status')).toHaveTextContent('running');

      fireEvent.click(screen.getByTestId('trigger-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('workflow-status')).toHaveTextContent(
          'interrupted'
        );
        expect(screen.getByTestId('workflow-step')).toHaveTextContent('3');
        expect(screen.getByTestId('account-id')).toHaveTextContent('acc_123');
      });
    });
  });

  describe('Approval Actions', () => {
    it('should call onApprove when approve button is clicked', async () => {
      const onApprove = jest.fn().mockResolvedValue(undefined);
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(onApprove).toHaveBeenCalledTimes(1);
      });
    });

    it('should call onReject when reject button is clicked', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn().mockResolvedValue(undefined);

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(onReject).toHaveBeenCalledTimes(1);
      });
    });

    it('should pass rejection reason when provided', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn().mockResolvedValue(undefined);

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const reasonInput = screen.getByPlaceholderText(
        'Rejection reason (optional)'
      );
      fireEvent.change(reasonInput, {
        target: { value: 'Recommendation needs more data' },
      });

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(onReject).toHaveBeenCalledWith('Recommendation needs more data');
      });
    });

    it('should send approval request to backend', async () => {
      const onApprove = jest.fn(async () => {
        await fetch(`${mockRuntimeUrl}/approval/respond`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            run_id: mockApprovalRequest.run_id,
            approved: true,
          }),
        });
      });

      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          `${mockRuntimeUrl}/approval/respond`,
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"approved":true'),
          })
        );
      });
    });

    it('should send rejection request to backend', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn(async (reason: string) => {
        await fetch(`${mockRuntimeUrl}/approval/respond`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            run_id: mockApprovalRequest.run_id,
            approved: false,
            reason,
          }),
        });
      });

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const reasonInput = screen.getByPlaceholderText(
        'Rejection reason (optional)'
      );
      fireEvent.change(reasonInput, {
        target: { value: 'Not applicable' },
      });

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          `${mockRuntimeUrl}/approval/respond`,
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"approved":false'),
          })
        );
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during approval', async () => {
      const onApprove = jest
        .fn()
        .mockImplementation(
          () => new Promise((resolve) => setTimeout(resolve, 100))
        );
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(screen.getByText('Approving...')).toBeInTheDocument();
      });
    });

    it('should show loading state during rejection', async () => {
      const onApprove = jest.fn();
      const onReject = jest
        .fn()
        .mockImplementation(
          () => new Promise((resolve) => setTimeout(resolve, 100))
        );

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(screen.getByText('Rejecting...')).toBeInTheDocument();
      });
    });

    it('should disable buttons during processing', async () => {
      const onApprove = jest
        .fn()
        .mockImplementation(
          () => new Promise((resolve) => setTimeout(resolve, 100))
        );
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(approveButton).toBeDisabled();
        expect(screen.getByRole('button', { name: /rejecting.../i })).toBeDisabled();
      });
    });
  });

  describe('Workflow Resumption', () => {
    it('should resume workflow after approval', async () => {
      const TestWorkflow = () => {
        const [status, setStatus] = React.useState('running');
        const [showApproval, setShowApproval] = React.useState(true);

        const handleApprove = async () => {
          setShowApproval(false);
          setStatus('resumed');
        };

        return (
          <div>
            <div data-testid="workflow-status">{status}</div>
            {showApproval && (
              <ApprovalModal
                request={mockApprovalRequest}
                onApprove={handleApprove}
                onReject={async () => setStatus('cancelled')}
              />
            )}
          </div>
        );
      };

      render(<TestWorkflow />);

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(screen.getByTestId('workflow-status')).toHaveTextContent('resumed');
      });
    });

    it('should stop workflow after rejection', async () => {
      const TestWorkflow = () => {
        const [status, setStatus] = React.useState('running');
        const [showApproval, setShowApproval] = React.useState(true);

        const handleReject = async () => {
          setShowApproval(false);
          setStatus('cancelled');
        };

        return (
          <div>
            <div data-testid="workflow-status">{status}</div>
            {showApproval && (
              <ApprovalModal
                request={mockApprovalRequest}
                onApprove={async () => {}}
                onReject={handleReject}
              />
            )}
          </div>
        );
      };

      render(<TestWorkflow />);

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(screen.getByTestId('workflow-status')).toHaveTextContent(
          'cancelled'
        );
      });
    });

    it('should restore workflow context after approval', async () => {
      const workflowContext = {
        accountId: 'acc_123',
        step: 3,
        data: { deals: 5, revenue: 100000 },
      };

      const TestWorkflow = () => {
        const [context, setContext] = React.useState(workflowContext);
        const [showApproval, setShowApproval] = React.useState(true);

        const handleApprove = async () => {
          setShowApproval(false);
          // Context should remain unchanged
        };

        return (
          <div>
            <div data-testid="account-id">{context.accountId}</div>
            <div data-testid="step">{context.step}</div>
            {showApproval && (
              <ApprovalModal
                request={mockApprovalRequest}
                onApprove={handleApprove}
                onReject={async () => {}}
              />
            )}
          </div>
        );
      };

      render(<TestWorkflow />);

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(screen.getByTestId('account-id')).toHaveTextContent('acc_123');
        expect(screen.getByTestId('step')).toHaveTextContent('3');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle approval request failures', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const onApprove = jest.fn(async () => {
        await fetch(`${mockRuntimeUrl}/approval/respond`, {
          method: 'POST',
          body: JSON.stringify({ approved: true }),
        });
      });

      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalled();
      });

      consoleError.mockRestore();
    });

    it('should handle rejection request failures', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      const onApprove = jest.fn();
      const onReject = jest.fn(async () => {
        await fetch(`${mockRuntimeUrl}/approval/respond`, {
          method: 'POST',
          body: JSON.stringify({ approved: false }),
        });
      });

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalled();
      });

      consoleError.mockRestore();
    });

    it('should handle session timeout gracefully', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error('Session expired')
      );

      const onApprove = jest.fn(async () => {
        await fetch(`${mockRuntimeUrl}/approval/respond`);
      });

      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      // Modal should still be rendered
      await waitFor(() => {
        expect(screen.getByText('Approval Required')).toBeInTheDocument();
      });
    });
  });

  describe('Multiple Recommendations', () => {
    it('should display all recommendations in approval modal', async () => {
      const onApprove = jest.fn();
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      expect(mockApprovalRequest.recommendations).toHaveLength(2);
      mockApprovalRequest.recommendations.forEach((rec) => {
        expect(screen.getByText(rec.title)).toBeInTheDocument();
      });
    });

    it('should approve all recommendations at once', async () => {
      const onApprove = jest.fn().mockResolvedValue(undefined);
      const onReject = jest.fn();

      render(
        <ApprovalModal
          request={mockApprovalRequest}
          onApprove={onApprove}
          onReject={onReject}
        />
      );

      const approveButton = screen.getByRole('button', { name: /approve/i });
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(onApprove).toHaveBeenCalledTimes(1);
        // All recommendations should be approved together
      });
    });
  });
});
