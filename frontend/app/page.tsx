'use client';

import { CopilotSidebar } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';
import { useState } from 'react';
import { ApprovalModal } from '@/components/ApprovalModal';
import { AccountAnalysisAgent } from '@/components/copilot/AccountAnalysisAgent';
import { CoAgentDashboard } from '@/components/copilot/CoAgentIntegration';

interface ApprovalRequest {
  run_id: string;
  recommendations: Array<{
    recommendation_id: string;
    category: string;
    title: string;
    description: string;
    confidence_score: number;
    priority: string;
    next_steps: string[];
  }>;
}

export default function Home() {
  const [approvalRequest, setApprovalRequest] = useState<ApprovalRequest | null>(null);
  const [activeView, setActiveView] = useState<'analysis' | 'coagent'>('analysis');

  const runtimeUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8008';

  const handleApproval = async (modified?: Record<string, unknown>) => {
    if (!approvalRequest) return;

    await fetch(`${runtimeUrl}/approval/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: approvalRequest.run_id,
        approved: true,
        modified_data: modified,
      }),
    });
    setApprovalRequest(null);
  };

  const handleRejection = async (reason: string) => {
    if (!approvalRequest) return;

    await fetch(`${runtimeUrl}/approval/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: approvalRequest.run_id,
        approved: false,
        reason,
      }),
    });
    setApprovalRequest(null);
  };

  const handleApprovalRequired = (request: { run_id: string; recommendations: unknown[] }) => {
    setApprovalRequest({
      run_id: request.run_id,
      recommendations: request.recommendations as ApprovalRequest['recommendations'],
    });
  };

  return (
    <div className="flex h-screen bg-gray-50">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              Sergas Account Manager
            </h1>
            <p className="text-gray-600">AI-powered account analysis and recommendations</p>

            {/* View Tabs */}
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setActiveView('analysis')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeView === 'analysis'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Account Analysis
              </button>
              <button
                onClick={() => setActiveView('coagent')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeView === 'coagent'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Agent Dashboard
              </button>
            </div>
          </header>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeView === 'analysis' ? (
              <AccountAnalysisAgent
                runtimeUrl={runtimeUrl}
                onApprovalRequired={handleApprovalRequired}
              />
            ) : (
              <CoAgentDashboard runtimeUrl={runtimeUrl} />
            )}
          </div>
        </div>

        {/* CopilotKit Sidebar */}
        <CopilotSidebar
          defaultOpen={true}
          clickOutsideToClose={false}
          labels={{
            title: 'Account Analysis Assistant',
            initial: 'Hello! I can help you analyze accounts, generate recommendations, and manage risk signals. What would you like to do?',
          }}
        />

        {/* Approval Modal */}
        {approvalRequest && (
          <ApprovalModal
            request={approvalRequest}
            onApprove={handleApproval}
            onReject={handleRejection}
          />
        )}
      </div>
  );
}
