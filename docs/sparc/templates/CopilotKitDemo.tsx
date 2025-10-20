/**
 * CopilotKit React Frontend Demo
 *
 * This component demonstrates how to integrate CopilotKit React hooks
 * with the Sergas Account Manager backend.
 *
 * Key Features:
 * - CopilotKitProvider configuration
 * - useCopilotChat for AI conversations
 * - useCopilotAction for custom actions
 * - useCopilotReadable for context sharing
 * - Real-time streaming responses
 *
 * Usage:
 *   Import and use this component in your Next.js application:
 *   import { CopilotKitDemo } from '@/components/CopilotKitDemo'
 */

'use client';

import React, { useState } from 'react';
import {
  CopilotKit,
  useCopilotChat,
  useCopilotAction,
  useCopilotReadable,
} from '@copilotkit/react-core';
import { CopilotSidebar, CopilotPopup } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

// ============================================================================
// Type Definitions
// ============================================================================

interface Account {
  id: string;
  name: string;
  owner: string;
  status: string;
  risk_level: string;
}

interface AccountSnapshot {
  account_name: string;
  owner_name: string;
  status: string;
  risk_level: string;
  priority_score: number;
  needs_review: boolean;
  deal_count: number;
  total_value: number;
}

interface RiskSignal {
  signal_type: string;
  severity: string;
  description: string;
  detected_at: string;
}

// ============================================================================
// Main Application Component
// ============================================================================

export function CopilotKitDemo() {
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [accountSnapshot, setAccountSnapshot] = useState<AccountSnapshot | null>(null);
  const [riskSignals, setRiskSignals] = useState<RiskSignal[]>([]);

  return (
    <CopilotKit
      // Backend API endpoint
      runtimeUrl="/api/copilotkit"
      // Agent to use (can be dynamically switched)
      agent="orchestrator"
      // Optional: Public API key for CopilotKit Cloud features
      // publicApiKey={process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY}
    >
      <div className="flex h-screen">
        {/* Main Content Area */}
        <div className="flex-1 p-6">
          <AccountManagerUI
            selectedAccount={selectedAccount}
            setSelectedAccount={setSelectedAccount}
            accountSnapshot={accountSnapshot}
            setAccountSnapshot={setAccountSnapshot}
            riskSignals={riskSignals}
            setRiskSignals={setRiskSignals}
          />
        </div>

        {/* CopilotKit Sidebar */}
        <CopilotSidebar
          defaultOpen={true}
          clickOutsideToClose={false}
          labels={{
            title: 'Account Manager Assistant',
            initial: 'Ask me about any account...',
          }}
        />
      </div>
    </CopilotKit>
  );
}

// ============================================================================
// Account Manager UI Component (with CopilotKit Integration)
// ============================================================================

interface AccountManagerUIProps {
  selectedAccount: Account | null;
  setSelectedAccount: (account: Account | null) => void;
  accountSnapshot: AccountSnapshot | null;
  setAccountSnapshot: (snapshot: AccountSnapshot | null) => void;
  riskSignals: RiskSignal[];
  setRiskSignals: (signals: RiskSignal[]) => void;
}

function AccountManagerUI({
  selectedAccount,
  setSelectedAccount,
  accountSnapshot,
  setAccountSnapshot,
  riskSignals,
  setRiskSignals,
}: AccountManagerUIProps) {
  // ========================================================================
  // CopilotKit Hooks
  // ========================================================================

  // 1. useCopilotChat - Access chat state
  const { isLoading, messages } = useCopilotChat();

  // 2. useCopilotReadable - Share context with the AI
  //    This makes the current account data available to the agent
  useCopilotReadable({
    description: 'The currently selected account in the UI',
    value: selectedAccount
      ? {
          id: selectedAccount.id,
          name: selectedAccount.name,
          owner: selectedAccount.owner,
        }
      : null,
  });

  useCopilotReadable({
    description: 'The current account snapshot with full analysis',
    value: accountSnapshot,
  });

  // 3. useCopilotAction - Define custom actions the AI can trigger
  //    Action: Analyze Account
  useCopilotAction({
    name: 'analyzeAccount',
    description: 'Analyze a specific account and display risk signals',
    parameters: [
      {
        name: 'accountId',
        type: 'string',
        description: 'The account ID to analyze (format: ACC-XXX)',
        required: true,
      },
    ],
    handler: async ({ accountId }: { accountId: string }) => {
      console.log('Analyzing account:', accountId);

      try {
        // Call backend API to fetch account data
        const response = await fetch(`/api/accounts/${accountId}`);
        const data = await response.json();

        // Update UI state
        setAccountSnapshot(data);
        setRiskSignals(data.risk_signals || []);

        return {
          success: true,
          message: `Analyzed account ${accountId}`,
          snapshot: data,
        };
      } catch (error) {
        console.error('Analysis failed:', error);
        return {
          success: false,
          message: `Failed to analyze account: ${error}`,
        };
      }
    },
  });

  // Action: Select Account
  useCopilotAction({
    name: 'selectAccount',
    description: 'Select an account to view in the UI',
    parameters: [
      {
        name: 'accountId',
        type: 'string',
        description: 'Account ID',
        required: true,
      },
      {
        name: 'accountName',
        type: 'string',
        description: 'Account name',
        required: true,
      },
    ],
    handler: async ({ accountId, accountName }) => {
      setSelectedAccount({
        id: accountId,
        name: accountName,
        owner: 'Unknown',
        status: 'Active',
        risk_level: 'unknown',
      });

      return {
        success: true,
        message: `Selected account ${accountName}`,
      };
    },
  });

  // Action: Clear Selection
  useCopilotAction({
    name: 'clearSelection',
    description: 'Clear the currently selected account',
    parameters: [],
    handler: async () => {
      setSelectedAccount(null);
      setAccountSnapshot(null);
      setRiskSignals([]);

      return {
        success: true,
        message: 'Cleared account selection',
      };
    },
  });

  // ========================================================================
  // UI Rendering
  // ========================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-900">
          Sergas Account Manager
        </h1>
        <p className="text-gray-600 mt-2">
          AI-powered account analysis and recommendations
        </p>
      </div>

      {/* Account Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Selected Account</h2>

        {selectedAccount ? (
          <div className="space-y-2">
            <p>
              <span className="font-medium">ID:</span> {selectedAccount.id}
            </p>
            <p>
              <span className="font-medium">Name:</span> {selectedAccount.name}
            </p>
            <p>
              <span className="font-medium">Owner:</span> {selectedAccount.owner}
            </p>
            <button
              onClick={() => setSelectedAccount(null)}
              className="mt-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
            >
              Clear Selection
            </button>
          </div>
        ) : (
          <p className="text-gray-500">
            No account selected. Ask the assistant to analyze an account.
          </p>
        )}
      </div>

      {/* Account Snapshot */}
      {accountSnapshot && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Account Snapshot</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Account Name</p>
              <p className="font-medium">{accountSnapshot.account_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Owner</p>
              <p className="font-medium">{accountSnapshot.owner_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="font-medium">{accountSnapshot.status}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Risk Level</p>
              <p className={`font-medium ${getRiskLevelColor(accountSnapshot.risk_level)}`}>
                {accountSnapshot.risk_level.toUpperCase()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Priority Score</p>
              <p className="font-medium">{accountSnapshot.priority_score}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Deal Count</p>
              <p className="font-medium">{accountSnapshot.deal_count}</p>
            </div>
          </div>

          {accountSnapshot.needs_review && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <p className="text-yellow-800 font-medium">⚠️ Needs Review</p>
            </div>
          )}
        </div>
      )}

      {/* Risk Signals */}
      {riskSignals.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">
            Risk Signals ({riskSignals.length})
          </h2>

          <div className="space-y-3">
            {riskSignals.map((signal, index) => (
              <div
                key={index}
                className={`p-4 rounded border-l-4 ${getSeverityColor(signal.severity)}`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{signal.signal_type}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {signal.description}
                    </p>
                  </div>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {signal.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">🤖 AI is processing your request...</p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function getRiskLevelColor(riskLevel: string): string {
  switch (riskLevel.toLowerCase()) {
    case 'critical':
      return 'text-red-600';
    case 'high':
      return 'text-orange-600';
    case 'medium':
      return 'text-yellow-600';
    case 'low':
      return 'text-green-600';
    default:
      return 'text-gray-600';
  }
}

function getSeverityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'border-red-500 bg-red-50';
    case 'high':
      return 'border-orange-500 bg-orange-50';
    case 'medium':
      return 'border-yellow-500 bg-yellow-50';
    default:
      return 'border-gray-500 bg-gray-50';
  }
}

// ============================================================================
// Alternative: Popup Style (instead of Sidebar)
// ============================================================================

export function CopilotKitPopupDemo() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="orchestrator">
      <div className="h-screen p-6">
        <h1 className="text-3xl font-bold">Account Manager</h1>
        <p className="text-gray-600 mt-2">
          Click the chat icon in the bottom right to interact with the AI
          assistant.
        </p>
      </div>

      {/* Popup chat interface */}
      <CopilotPopup
        labels={{
          title: 'Account Assistant',
          initial: 'How can I help you today?',
        }}
      />
    </CopilotKit>
  );
}
