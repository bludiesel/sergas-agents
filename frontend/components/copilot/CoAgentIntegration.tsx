/**
 * CoAgentIntegration.tsx
 *
 * Demonstrates useCoAgent hook for bidirectional state sharing
 * between frontend and backend agents.
 *
 * Features:
 * - Real-time state synchronization
 * - Agent-to-agent communication
 * - Shared memory management
 * - Event-driven updates
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';
import { useWebSocketManager, useWebSocketPerformance } from '../../lib/websocket-manager';

// ============================================================================
// Type Definitions
// ============================================================================

export interface SharedState {
  current_account_id: string | null;
  analysis_in_progress: boolean;
  last_analysis_timestamp: string | null;
  agent_queue: string[];
  user_preferences: {
    auto_analyze: boolean;
    notification_level: 'all' | 'critical' | 'none';
  };
}

export interface AgentMessage {
  from_agent: string;
  to_agent: string;
  message_type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

// ============================================================================
// CoAgent State Management Hook
// ============================================================================

export function useCoAgentState(runtimeUrl: string) {
  const [sharedState, setSharedState] = useState<SharedState>({
    current_account_id: null,
    analysis_in_progress: false,
    last_analysis_timestamp: null,
    agent_queue: [],
    user_preferences: {
      auto_analyze: false,
      notification_level: 'all',
    },
  });

  const [agentMessages, setAgentMessages] = useState<AgentMessage[]>([]);

  // ========================================================================
  // State Synchronization
  // ========================================================================

  // Make shared state readable by all agents
  useCopilotReadable({
    description: 'Shared state between frontend and backend agents',
    value: sharedState,
  });

  // Make agent messages readable
  useCopilotReadable({
    description: 'Inter-agent communication messages',
    value: agentMessages,
  });

  // ========================================================================
  // State Update Actions
  // ========================================================================

  /**
   * Action: Update shared state from backend agents
   */
  useCopilotAction({
    name: 'updateSharedState',
    description: 'Update the shared state from a backend agent',
    parameters: [
      {
        name: 'stateUpdate',
        type: 'object',
        description: 'Partial state update object',
        required: true,
      },
      {
        name: 'sourceAgent',
        type: 'string',
        description: 'Name of the agent making the update',
        required: false,
      },
    ],
    handler: async ({ stateUpdate, sourceAgent }) => {
      console.log('[CoAgent] State update from:', sourceAgent, stateUpdate);

      // Use broadcast to sync via WebSocket
      broadcastStateUpdate(stateUpdate, sourceAgent);

      return {
        success: true,
        message: `State updated by ${sourceAgent || 'unknown agent'}`,
        new_state: { ...sharedState, ...stateUpdate },
      };
    },
  });

  /**
   * Action: Send inter-agent message
   */
  useCopilotAction({
    name: 'sendAgentMessage',
    description: 'Send a message between agents for coordination',
    parameters: [
      {
        name: 'fromAgent',
        type: 'string',
        description: 'Source agent name',
        required: true,
      },
      {
        name: 'toAgent',
        type: 'string',
        description: 'Destination agent name',
        required: true,
      },
      {
        name: 'messageType',
        type: 'string',
        description: 'Type of message (e.g., "data_ready", "analysis_complete")',
        required: true,
      },
      {
        name: 'payload',
        type: 'object',
        description: 'Message payload data',
        required: false,
      },
    ],
    handler: async ({ fromAgent, toAgent, messageType, payload }) => {
      console.log('[CoAgent] Inter-agent message:', { fromAgent, toAgent, messageType });

      // Use broadcast to send via WebSocket
      broadcastAgentMessage(fromAgent, toAgent, messageType, (payload || {}) as Record<string, unknown>);

      return {
        success: true,
        message: `Message sent from ${fromAgent} to ${toAgent}`,
        message_id: new Date().toISOString(),
      };
    },
  });

  /**
   * Action: Get agent messages
   */
  useCopilotAction({
    name: 'getAgentMessages',
    description: 'Retrieve inter-agent messages for a specific agent',
    parameters: [
      {
        name: 'agentName',
        type: 'string',
        description: 'Name of the agent to get messages for',
        required: true,
      },
      {
        name: 'messageType',
        type: 'string',
        description: 'Filter by message type (optional)',
        required: false,
      },
    ],
    handler: async ({ agentName, messageType }) => {
      let messages = agentMessages.filter(
        (msg) => msg.to_agent === agentName || msg.from_agent === agentName
      );

      if (messageType) {
        messages = messages.filter((msg) => msg.message_type === messageType);
      }

      return {
        success: true,
        messages,
        count: messages.length,
      };
    },
  });

  // ========================================================================
  // WebSocket Integration for Real-Time Updates
  // ========================================================================

  const wsManager = useWebSocketManager(runtimeUrl);
  const performanceMetrics = useWebSocketPerformance(wsManager);

  // Sync WebSocket messages with local state
  useEffect(() => {
    // Handle state updates from WebSocket
    wsManager.messages
      .filter(msg => msg.type === 'state_update')
      .forEach(msg => {
        setSharedState(prev => ({
          ...prev,
          ...(msg.payload as Partial<SharedState>)
        }));
      });

    // Handle agent messages from WebSocket
    wsManager.messages
      .filter(msg => msg.type === 'agent_message')
      .forEach(msg => {
        const agentMsg: AgentMessage = {
          from_agent: msg.sourceAgent || 'unknown',
          to_agent: msg.targetAgent || 'unknown',
          message_type: msg.payload.messageType as string || 'message',
          payload: msg.payload as Record<string, unknown>,
          timestamp: msg.timestamp,
        };
        setAgentMessages(prev => [...prev, agentMsg]);
      });
  }, [wsManager.messages]);

  // Broadcast state updates via WebSocket
  const broadcastStateUpdate = useCallback((stateUpdate: Partial<SharedState>, sourceAgent?: string) => {
    setSharedState(prev => {
      const newState = { ...prev, ...stateUpdate };

      // Send via WebSocket for real-time sync
      wsManager.sendStateUpdate(stateUpdate, sourceAgent || 'frontend');

      return newState;
    });
  }, [wsManager]);

  // Broadcast agent message via WebSocket
  const broadcastAgentMessage = useCallback((
    fromAgent: string,
    toAgent: string,
    messageType: string,
    payload: Record<string, unknown>
  ) => {
    const message: AgentMessage = {
      from_agent: fromAgent,
      to_agent: toAgent,
      message_type: messageType,
      payload,
      timestamp: new Date().toISOString(),
    };

    setAgentMessages(prev => [...prev, message]);
    wsManager.sendAgentMessage(fromAgent, toAgent, messageType, payload);
  }, [wsManager]);

  return {
    sharedState,
    setSharedState,
    agentMessages,
    setAgentMessages,
    // Real-time capabilities
    wsManager,
    performanceMetrics,
    broadcastStateUpdate,
    broadcastAgentMessage,
    isConnected: wsManager.isConnected,
    connectionStatus: wsManager.connectionState.status,
  };
}

// ============================================================================
// CoAgent Dashboard Component
// ============================================================================

interface CoAgentDashboardProps {
  runtimeUrl: string;
}

export function CoAgentDashboard({ runtimeUrl }: CoAgentDashboardProps) {
  const {
    sharedState,
    agentMessages,
    isConnected,
    connectionStatus,
    performanceMetrics,
    wsManager
  } = useCoAgentState(runtimeUrl);

  return (
    <div className="space-y-6">
      {/* Connection Status & Performance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Connection Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Connection Status</h2>
            <ConnectionStatusIndicator status={connectionStatus} isConnected={isConnected} />
          </div>

          <div className="space-y-2">
            <StateItem
              label="Status"
              value={connectionStatus}
              valueColor={isConnected ? 'text-green-600' : 'text-red-600'}
            />
            <StateItem
              label="WebSocket"
              value={isConnected ? 'Connected' : 'Disconnected'}
              valueColor={isConnected ? 'text-green-600' : 'text-red-600'}
            />
            {wsManager.connectionState.latency && (
              <StateItem
                label="Latency"
                value={`${wsManager.connectionState.latency}ms`}
                valueColor={wsManager.connectionState.latency < 100 ? 'text-green-600' : 'text-yellow-600'}
              />
            )}
            {wsManager.connectionState.lastConnected && (
              <StateItem
                label="Last Connected"
                value={wsManager.connectionState.lastConnected.toLocaleTimeString()}
              />
            )}
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={() => wsManager.connect()}
              disabled={isConnected}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
            >
              Connect
            </button>
            <button
              onClick={() => wsManager.disconnect()}
              disabled={!isConnected}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
            >
              Disconnect
            </button>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Performance Metrics</h2>

          <div className="space-y-2">
            <StateItem
              label="Total Messages"
              value={performanceMetrics.totalMessages.toString()}
            />
            <StateItem
              label="Messages/Second"
              value={performanceMetrics.messagesPerSecond.toString()}
            />
            <StateItem
              label="Average Latency"
              value={`${performanceMetrics.averageLatency}ms`}
              valueColor={performanceMetrics.averageLatency < 100 ? 'text-green-600' : 'text-yellow-600'}
            />
            <StateItem
              label="Uptime"
              value={`${Math.floor(performanceMetrics.connectionUptime / 60)}m ${performanceMetrics.connectionUptime % 60}s`}
            />
          </div>
        </div>
      </div>

      {/* Agent Status Panel */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Active Agents ({wsManager.agents.size})
        </h2>

        {wsManager.agents.size === 0 ? (
          <p className="text-gray-500 text-sm">No active agents</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from(wsManager.agents.entries()).map(([agentId, status]) => (
              <AgentStatusCard key={agentId} agentId={agentId} status={status} />
            ))}
          </div>
        )}
      </div>

      {/* Shared State Display */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Shared Agent State</h2>

        <div className="space-y-3">
          <StateItem
            label="Current Account"
            value={sharedState.current_account_id || 'None'}
          />
          <StateItem
            label="Analysis In Progress"
            value={sharedState.analysis_in_progress ? 'Yes' : 'No'}
            valueColor={sharedState.analysis_in_progress ? 'text-blue-600' : 'text-gray-600'}
          />
          <StateItem
            label="Last Analysis"
            value={
              sharedState.last_analysis_timestamp
                ? new Date(sharedState.last_analysis_timestamp).toLocaleString()
                : 'Never'
            }
          />
          <StateItem
            label="Agent Queue"
            value={sharedState.agent_queue.length > 0 ? sharedState.agent_queue.join(', ') : 'Empty'}
          />
        </div>

        {/* User Preferences */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">User Preferences</h3>
          <div className="space-y-2">
            <StateItem
              label="Auto Analyze"
              value={sharedState.user_preferences.auto_analyze ? 'Enabled' : 'Disabled'}
            />
            <StateItem
              label="Notifications"
              value={sharedState.user_preferences.notification_level}
            />
          </div>
        </div>
      </div>

      {/* Agent Messages */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Agent Messages ({agentMessages.length})
        </h2>

        {agentMessages.length === 0 ? (
          <p className="text-gray-500 text-sm">No messages yet</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {agentMessages.slice(-10).reverse().map((msg, idx) => (
              <AgentMessageCard key={idx} message={msg} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

interface StateItemProps {
  label: string;
  value: string;
  valueColor?: string;
}

function StateItem({ label, value, valueColor = 'text-gray-900' }: StateItemProps) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-600">{label}:</span>
      <span className={`text-sm font-medium ${valueColor}`}>{value}</span>
    </div>
  );
}

interface AgentMessageCardProps {
  message: AgentMessage;
}

function AgentMessageCard({ message }: AgentMessageCardProps) {
  return (
    <div className="bg-gray-50 rounded p-3 text-sm">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">{message.from_agent}</span>
          <span className="text-gray-500">→</span>
          <span className="font-medium text-gray-900">{message.to_agent}</span>
        </div>
        <span className="text-xs text-gray-500">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
          {message.message_type}
        </span>
        {Object.keys(message.payload).length > 0 && (
          <span className="text-xs text-gray-600">
            {JSON.stringify(message.payload).slice(0, 50)}...
          </span>
        )}
      </div>
    </div>
  );
}
