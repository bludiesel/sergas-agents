/**
 * AccountAnalysisAgent.tsx
 *
 * CopilotKit-powered component for AI-driven account analysis.
 * Integrates with backend agents: orchestrator, zoho_scout, memory_analyst, recommendation_author
 *
 * Features:
 * - useCopilotAction: Define custom actions for backend agent triggers
 * - useCoAgent: Bidirectional state sharing between frontend and backend
 * - useCopilotChat: Chat interface integration
 * - useCopilotReadable: Share context with AI agents
 * - HITL approval workflow support
 * - Real-time streaming updates
 */

'use client';

import React, { useState, useCallback } from 'react';
import {
  useCopilotAction,
  useCopilotReadable,
  useCopilotChat,
} from '@copilotkit/react-core';
import { CheckCircle, AlertTriangle, TrendingUp, Activity } from 'lucide-react';

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
  account_id: string;
  account_name: string;
  owner_name: string;
  status: string;
  risk_level: string;
  priority_score: number;
  needs_review: boolean;
  deal_count: number;
  total_value: number;
  last_contact_date?: string;
  engagement_score?: number;
}

interface RiskSignal {
  signal_id: string;
  signal_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  detected_at: string;
  account_id: string;
}

interface Recommendation {
  recommendation_id: string;
  category: string;
  title: string;
  description: string;
  confidence_score: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  next_steps: string[];
  supporting_evidence: string[];
}

interface AnalysisResult {
  account_snapshot: AccountSnapshot;
  risk_signals: RiskSignal[];
  recommendations: Recommendation[];
  run_id: string;
  timestamp: string;
}

interface AgentStatus {
  'zoho-data-scout': 'idle' | 'running' | 'completed' | 'error';
  'memory-analyst': 'idle' | 'running' | 'completed' | 'error';
  'recommendation-author': 'idle' | 'running' | 'completed' | 'error';
}

// ============================================================================
// Main Component
// ============================================================================

interface AccountAnalysisAgentProps {
  runtimeUrl: string;
  onApprovalRequired?: (request: {
    run_id: string;
    recommendations: unknown[];
  }) => void;
}

export function AccountAnalysisAgent({
  runtimeUrl,
  onApprovalRequired,
}: AccountAnalysisAgentProps) {
  // ========================================================================
  // State Management
  // ========================================================================

  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({
    'zoho-data-scout': 'idle',
    'memory-analyst': 'idle',
    'recommendation-author': 'idle',
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ========================================================================
  // CopilotKit Hooks
  // ========================================================================

  // Access chat state for loading indicators
  const { isLoading } = useCopilotChat();

  // Share current account context with AI
  useCopilotReadable({
    description: 'Currently selected account in the application',
    value: selectedAccount
      ? {
          id: selectedAccount.id,
          name: selectedAccount.name,
          owner: selectedAccount.owner,
          status: selectedAccount.status,
          risk_level: selectedAccount.risk_level,
        }
      : null,
  });

  // Share analysis results with AI
  useCopilotReadable({
    description: 'Latest account analysis results including snapshot, risk signals, and recommendations',
    value: analysisResult,
  });

  // Share agent execution status
  useCopilotReadable({
    description: 'Current status of backend agents (zoho-data-scout, memory-analyst, recommendation-author)',
    value: agentStatus,
  });

  // ========================================================================
  // Action Handlers
  // ========================================================================

  /**
   * Analyze a specific account by triggering the full orchestrator workflow
   */
  const handleAnalyzeAccount = useCallback(
    async (accountId: string): Promise<AnalysisResult> => {
      // Validate input
      if (!accountId || accountId.trim() === '') {
        throw new Error('Account ID is required');
      }

      setIsAnalyzing(true);
      setError(null);

      // Reset and update agent statuses
      setAgentStatus({
        'zoho-data-scout': 'running',
        'memory-analyst': 'idle',
        'recommendation-author': 'idle',
      });

      try {
        // Add timeout configuration
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        // Call orchestrator endpoint with better error handling
        const response = await fetch(`${runtimeUrl}/orchestrator/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            account_id: accountId.trim(),
            include_recommendations: true,
            hitl_enabled: true,
            request_timestamp: new Date().toISOString(),
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Handle different HTTP status codes
        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = `Analysis failed: ${response.statusText}`;

          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.message || errorData.error || errorMessage;
          } catch {
            errorMessage = `Analysis failed: ${response.statusText} - ${errorText}`;
          }

          throw new Error(errorMessage);
        }

        // Validate response data
        const result: AnalysisResult = await response.json();

        if (!result || !result.account_snapshot) {
          throw new Error('Invalid analysis response received from server');
        }

        // Update statuses as agents complete with more realistic timing
        setAgentStatus({
          'zoho-data-scout': 'completed',
          'memory-analyst': 'running',
          'recommendation-author': 'idle',
        });

        // Simulate memory analyst completion with variable timing
        setTimeout(() => {
          setAgentStatus((prev) => ({
            ...prev,
            'memory-analyst': 'completed',
            'recommendation-author': 'running',
          }));
        }, 800 + Math.random() * 1200);

        // Simulate recommendation author completion
        setTimeout(() => {
          setAgentStatus((prev) => ({
            ...prev,
            'recommendation-author': 'completed',
          }));
        }, 1500 + Math.random() * 2000);

        setAnalysisResult(result);
        setIsAnalyzing(false);

        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        console.error('Account analysis failed:', err);

        setError(errorMessage);
        setAgentStatus({
          'zoho-data-scout': 'error',
          'memory-analyst': 'error',
          'recommendation-author': 'error',
        });
        setIsAnalyzing(false);

        // Re-throw for calling components to handle
        throw err;
      }
    },
    [runtimeUrl]
  );

  /**
   * Fetch account snapshot without full analysis
   */
  const handleFetchAccountData = useCallback(
    async (accountId: string): Promise<AccountSnapshot> => {
      // Validate input
      if (!accountId || accountId.trim() === '') {
        throw new Error('Account ID is required');
      }

      try {
        // Add timeout for fetch operations
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

        const response = await fetch(`${runtimeUrl}/zoho-scout/snapshot/${accountId.trim()}`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = `Failed to fetch account data: ${response.statusText}`;

          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.message || errorData.error || errorMessage;
          } catch {
            errorMessage = `Failed to fetch account data: ${response.statusText} - ${errorText}`;
          }

          throw new Error(errorMessage);
        }

        const snapshot: AccountSnapshot = await response.json();

        // Validate response data
        if (!snapshot || !snapshot.account_id) {
          throw new Error('Invalid account snapshot received from server');
        }

        return snapshot;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        console.error('Failed to fetch account data:', err);
        setError(errorMessage);
        throw err;
      }
    },
    [runtimeUrl]
  );

  /**
   * Generate recommendations for an account
   */
  const handleGetRecommendations = useCallback(
    async (accountId: string): Promise<Recommendation[]> => {
      // Validate input
      if (!accountId || accountId.trim() === '') {
        throw new Error('Account ID is required');
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout

        const response = await fetch(`${runtimeUrl}/recommendation-author/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            account_id: accountId.trim(),
            require_approval: true,
            request_timestamp: new Date().toISOString(),
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = `Failed to generate recommendations: ${response.statusText}`;

          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.message || errorData.error || errorMessage;
          } catch {
            errorMessage = `Failed to generate recommendations: ${response.statusText} - ${errorText}`;
          }

          throw new Error(errorMessage);
        }

        const data = await response.json();

        // Validate response data
        if (!data || !Array.isArray(data.recommendations)) {
          throw new Error('Invalid recommendations data received from server');
        }

        // Trigger HITL approval workflow if callback provided
        if (onApprovalRequired && data.requires_approval && data.run_id) {
          try {
            onApprovalRequired({
              run_id: data.run_id,
              recommendations: data.recommendations,
            });
          } catch (approvalError) {
            console.error('Approval callback failed:', approvalError);
            // Don't throw error here, just log it
          }
        }

        return data.recommendations;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        console.error('Failed to generate recommendations:', err);
        setError(errorMessage);
        throw err;
      }
    },
    [runtimeUrl, onApprovalRequired]
  );

  // ========================================================================
  // CopilotKit Actions
  // ========================================================================

  /**
   * Action: Analyze Account
   * Triggers full orchestrator workflow with all agents
   */
  useCopilotAction({
    name: 'analyzeAccount',
    description:
      'Perform comprehensive account analysis using Zoho Data Scout, Memory Analyst, and Recommendation Author agents. Returns account snapshot, risk signals, and recommendations.',
    parameters: [
      {
        name: 'accountId',
        type: 'string',
        description: 'The account ID to analyze (format: ACC-XXXX or numeric ID)',
        required: true,
      },
    ],
    handler: async ({ accountId }) => {
      console.log('[CopilotKit Action] analyzeAccount called:', accountId);

      // Validate input
      if (!accountId || typeof accountId !== 'string') {
        return {
          success: false,
          message: 'Valid account ID is required for analysis',
          error: 'INVALID_ACCOUNT_ID',
        };
      }

      try {
        // Show loading state via the component's isAnalyzing state
        // The handleAnalyzeAccount function already manages this
        const result = await handleAnalyzeAccount(accountId);

        return {
          success: true,
          message: `Successfully analyzed account ${result.account_snapshot.account_name}`,
          data: {
            account_name: result.account_snapshot.account_name,
            risk_level: result.account_snapshot.risk_level,
            priority_score: result.account_snapshot.priority_score,
            risk_signals_count: result.risk_signals.length,
            recommendations_count: result.recommendations.length,
            analysis_timestamp: result.timestamp,
            run_id: result.run_id,
          },
          full_result: result,
          metadata: {
            action: 'analyzeAccount',
            timestamp: new Date().toISOString(),
            duration: Date.now() - new Date(result.timestamp).getTime(),
          }
        };
      } catch (error) {
        console.error('[CopilotKit Action] analyzeAccount error:', error);

        // Handle different error types
        let errorMessage = 'Failed to analyze account';
        let errorCode = 'ANALYSIS_FAILED';

        if (error instanceof Error) {
          if (error.message.includes('Account ID is required')) {
            errorMessage = 'Account ID is required for analysis';
            errorCode = 'MISSING_ACCOUNT_ID';
          } else if (error.message.includes('timeout')) {
            errorMessage = 'Analysis request timed out. Please try again.';
            errorCode = 'TIMEOUT';
          } else if (error.message.includes('network')) {
            errorMessage = 'Network error occurred. Please check your connection.';
            errorCode = 'NETWORK_ERROR';
          } else {
            errorMessage = error.message;
          }
        }

        return {
          success: false,
          message: errorMessage,
          error: errorCode,
          details: error instanceof Error ? error.stack : 'Unknown error details',
          metadata: {
            action: 'analyzeAccount',
            timestamp: new Date().toISOString(),
            account_id: accountId,
          }
        };
      }
    },
  });

  /**
   * Action: Fetch Account Data
   * Quick snapshot retrieval without full analysis
   */
  useCopilotAction({
    name: 'fetchAccountData',
    description: 'Fetch a quick snapshot of account data from Zoho CRM without running full analysis.',
    parameters: [
      {
        name: 'accountId',
        type: 'string',
        description: 'The account ID to fetch',
        required: true,
      },
    ],
    handler: async ({ accountId }) => {
      console.log('[CopilotKit Action] fetchAccountData called:', accountId);

      // Validate input
      if (!accountId || typeof accountId !== 'string') {
        return {
          success: false,
          message: 'Valid account ID is required',
          error: 'INVALID_ACCOUNT_ID',
        };
      }

      try {
        const snapshot = await handleFetchAccountData(accountId);

        return {
          success: true,
          message: `Retrieved snapshot for ${snapshot.account_name}`,
          data: {
            account_id: snapshot.account_id,
            account_name: snapshot.account_name,
            owner_name: snapshot.owner_name,
            status: snapshot.status,
            risk_level: snapshot.risk_level,
            priority_score: snapshot.priority_score,
            deal_count: snapshot.deal_count,
            total_value: snapshot.total_value,
            engagement_score: snapshot.engagement_score,
            needs_review: snapshot.needs_review,
          },
          full_snapshot: snapshot,
          metadata: {
            action: 'fetchAccountData',
            timestamp: new Date().toISOString(),
          }
        };
      } catch (error) {
        console.error('[CopilotKit Action] fetchAccountData error:', error);

        let errorMessage = 'Failed to fetch account data';
        let errorCode = 'FETCH_FAILED';

        if (error instanceof Error) {
          if (error.message.includes('Account ID is required')) {
            errorMessage = 'Account ID is required';
            errorCode = 'MISSING_ACCOUNT_ID';
          } else if (error.message.includes('timeout')) {
            errorMessage = 'Request timed out. Please try again.';
            errorCode = 'TIMEOUT';
          } else if (error.message.includes('network')) {
            errorMessage = 'Network error occurred. Please check your connection.';
            errorCode = 'NETWORK_ERROR';
          } else {
            errorMessage = error.message;
          }
        }

        return {
          success: false,
          message: errorMessage,
          error: errorCode,
          details: error instanceof Error ? error.stack : 'Unknown error details',
          metadata: {
            action: 'fetchAccountData',
            timestamp: new Date().toISOString(),
            account_id: accountId,
          }
        };
      }
    },
  });

  /**
   * Action: Get Recommendations
   * Generate AI recommendations with HITL approval
   */
  useCopilotAction({
    name: 'getRecommendations',
    description:
      'Generate AI-powered recommendations for an account. Triggers Human-in-the-Loop (HITL) approval workflow.',
    parameters: [
      {
        name: 'accountId',
        type: 'string',
        description: 'The account ID to generate recommendations for',
        required: true,
      },
    ],
    handler: async ({ accountId }) => {
      console.log('[CopilotKit Action] getRecommendations called:', accountId);

      // Validate input
      if (!accountId || typeof accountId !== 'string') {
        return {
          success: false,
          message: 'Valid account ID is required',
          error: 'INVALID_ACCOUNT_ID',
        };
      }

      try {
        const recommendations = await handleGetRecommendations(accountId);

        // Calculate recommendation statistics
        const priorityCounts = recommendations.reduce((acc, rec) => {
          acc[rec.priority] = (acc[rec.priority] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);

        const avgConfidence = recommendations.reduce((sum, rec) => sum + rec.confidence_score, 0) / recommendations.length;

        return {
          success: true,
          message: `Generated ${recommendations.length} recommendations for account ${accountId}`,
          data: {
            recommendations_count: recommendations.length,
            recommendations: recommendations.map(rec => ({
              recommendation_id: rec.recommendation_id,
              category: rec.category,
              title: rec.title,
              description: rec.description,
              priority: rec.priority,
              confidence_score: rec.confidence_score,
              next_steps: rec.next_steps,
            })),
            priority_distribution: priorityCounts,
            average_confidence: Math.round(avgConfidence),
            categories: [...new Set(recommendations.map(rec => rec.category))],
          },
          full_recommendations: recommendations,
          requires_approval: true,
          metadata: {
            action: 'getRecommendations',
            timestamp: new Date().toISOString(),
            account_id: accountId,
          }
        };
      } catch (error) {
        console.error('[CopilotKit Action] getRecommendations error:', error);

        let errorMessage = 'Failed to generate recommendations';
        let errorCode = 'RECOMMENDATION_FAILED';

        if (error instanceof Error) {
          if (error.message.includes('Account ID is required')) {
            errorMessage = 'Account ID is required';
            errorCode = 'MISSING_ACCOUNT_ID';
          } else if (error.message.includes('timeout')) {
            errorMessage = 'Request timed out. Please try again.';
            errorCode = 'TIMEOUT';
          } else if (error.message.includes('network')) {
            errorMessage = 'Network error occurred. Please check your connection.';
            errorCode = 'NETWORK_ERROR';
          } else {
            errorMessage = error.message;
          }
        }

        return {
          success: false,
          message: errorMessage,
          error: errorCode,
          details: error instanceof Error ? error.stack : 'Unknown error details',
          metadata: {
            action: 'getRecommendations',
            timestamp: new Date().toISOString(),
            account_id: accountId,
          }
        };
      }
    },
  });

  /**
   * Action: Select Account
   * Update UI state to select an account
   */
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
      {
        name: 'owner',
        type: 'string',
        description: 'Account owner name',
        required: false,
      },
    ],
    handler: async ({ accountId, accountName, owner }) => {
      console.log('[CopilotKit Action] selectAccount called:', accountId);

      setSelectedAccount({
        id: accountId,
        name: accountName,
        owner: owner || 'Unknown',
        status: 'Active',
        risk_level: 'unknown',
      });

      return {
        success: true,
        message: `Selected account: ${accountName}`,
      };
    },
  });

  /**
   * Action: Clear Selection
   * Reset UI state
   */
  useCopilotAction({
    name: 'clearAccountSelection',
    description: 'Clear the currently selected account and analysis results',
    parameters: [],
    handler: async () => {
      console.log('[CopilotKit Action] clearAccountSelection called');

      setSelectedAccount(null);
      setAnalysisResult(null);
      setError(null);
      setAgentStatus({
        'zoho-data-scout': 'idle',
        'memory-analyst': 'idle',
        'recommendation-author': 'idle',
      });

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
      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900">Error</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Selected Account */}
      {selectedAccount && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Selected Account</h2>
            <button
              onClick={() => setSelectedAccount(null)}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Clear
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Account ID</p>
              <p className="font-medium text-gray-900">{selectedAccount.id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Account Name</p>
              <p className="font-medium text-gray-900">{selectedAccount.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Owner</p>
              <p className="font-medium text-gray-900">{selectedAccount.owner}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="font-medium text-gray-900">{selectedAccount.status}</p>
            </div>
          </div>
        </div>
      )}

      {/* Agent Status */}
      {isAnalyzing && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 animate-pulse" />
            Agent Execution Status
          </h3>

          <div className="space-y-3">
            {Object.entries(agentStatus).map(([agent, status]) => (
              <div key={agent} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  {agent.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </span>
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : status === 'running'
                      ? 'bg-blue-100 text-blue-700'
                      : status === 'error'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <>
          {/* Account Snapshot */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Snapshot</h2>

            <div className="grid grid-cols-3 gap-4">
              <MetricCard
                label="Priority Score"
                value={analysisResult.account_snapshot.priority_score.toString()}
                icon={<TrendingUp className="h-5 w-5 text-blue-600" />}
              />
              <MetricCard
                label="Risk Level"
                value={analysisResult.account_snapshot.risk_level.toUpperCase()}
                icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
                valueColor={getRiskLevelColor(analysisResult.account_snapshot.risk_level)}
              />
              <MetricCard
                label="Deal Count"
                value={analysisResult.account_snapshot.deal_count.toString()}
                icon={<CheckCircle className="h-5 w-5 text-green-600" />}
              />
            </div>

            {analysisResult.account_snapshot.needs_review && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-yellow-800 font-medium">⚠️ This account needs review</p>
              </div>
            )}
          </div>

          {/* Risk Signals */}
          {analysisResult.risk_signals.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Risk Signals ({analysisResult.risk_signals.length})
              </h2>

              <div className="space-y-3">
                {analysisResult.risk_signals.map((signal) => (
                  <RiskSignalCard key={signal.signal_id} signal={signal} />
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {analysisResult.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Recommendations ({analysisResult.recommendations.length})
              </h2>

              <div className="space-y-4">
                {analysisResult.recommendations.map((rec) => (
                  <RecommendationCard key={rec.recommendation_id} recommendation={rec} />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Loading Indicator */}
      {isLoading && !isAnalyzing && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">🤖 AI is processing your request...</p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  valueColor?: string;
}

function MetricCard({ label, value, icon, valueColor = 'text-gray-900' }: MetricCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">{icon}</div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
    </div>
  );
}

interface RiskSignalCardProps {
  signal: RiskSignal;
}

function RiskSignalCard({ signal }: RiskSignalCardProps) {
  const severityColors = {
    critical: 'border-red-500 bg-red-50',
    high: 'border-orange-500 bg-orange-50',
    medium: 'border-yellow-500 bg-yellow-50',
    low: 'border-blue-500 bg-blue-50',
  };

  return (
    <div className={`p-4 rounded border-l-4 ${severityColors[signal.severity]}`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className="font-medium text-gray-900">{signal.signal_type}</p>
          <p className="text-sm text-gray-600 mt-1">{signal.description}</p>
          <p className="text-xs text-gray-500 mt-2">
            Detected: {new Date(signal.detected_at).toLocaleString()}
          </p>
        </div>
        <span className="text-xs bg-white px-2 py-1 rounded font-medium uppercase">
          {signal.severity}
        </span>
      </div>
    </div>
  );
}

interface RecommendationCardProps {
  recommendation: Recommendation;
}

function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const priorityColors = {
    critical: 'bg-red-100 text-red-700',
    high: 'bg-orange-100 text-orange-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-blue-100 text-blue-700',
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{recommendation.title}</h3>
        <div className="flex gap-2">
          <span className={`text-xs px-2 py-1 rounded font-medium ${priorityColors[recommendation.priority]}`}>
            {recommendation.priority}
          </span>
          <span className="text-xs bg-gray-100 px-2 py-1 rounded font-medium">
            {recommendation.confidence_score}% confident
          </span>
        </div>
      </div>

      <p className="text-gray-700 mb-3">{recommendation.description}</p>

      <div className="bg-gray-50 rounded p-3">
        <p className="text-sm font-medium text-gray-900 mb-2">Next Steps:</p>
        <ul className="list-disc list-inside space-y-1">
          {recommendation.next_steps.map((step, idx) => (
            <li key={idx} className="text-sm text-gray-700">
              {step}
            </li>
          ))}
        </ul>
      </div>

      {recommendation.supporting_evidence.length > 0 && (
        <div className="mt-3 text-xs text-gray-600">
          <p className="font-medium mb-1">Supporting Evidence:</p>
          <ul className="list-disc list-inside space-y-0.5">
            {recommendation.supporting_evidence.map((evidence, idx) => (
              <li key={idx}>{evidence}</li>
            ))}
          </ul>
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
