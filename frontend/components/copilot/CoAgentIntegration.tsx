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

import React, { useState, useEffect } from 'react';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';

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
  payload: any;
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

      setSharedState((prev) => ({
        ...prev,
        ...stateUpdate,
      }));

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
      const message: AgentMessage = {
        from_agent: fromAgent,
        to_agent: toAgent,
        message_type: messageType,
        payload: payload || {},
        timestamp: new Date().toISOString(),
      };

      console.log('[CoAgent] Inter-agent message:', message);

      setAgentMessages((prev) => [...prev, message]);

      return {
        success: true,
        message: `Message sent from ${fromAgent} to ${toAgent}`,
        message_id: message.timestamp,
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

  useEffect(() => {
    // In production, connect to WebSocket for real-time agent updates
    // const ws = new WebSocket(`${runtimeUrl.replace('http', 'ws')}/ws/coagent`);

    // ws.onmessage = (event) => {
    //   const update = JSON.parse(event.data);
    //   if (update.type === 'state_update') {
    //     setSharedState(prev => ({ ...prev, ...update.state }));
    //   } else if (update.type === 'agent_message') {
    //     setAgentMessages(prev => [...prev, update.message]);
    //   }
    // };

    // return () => ws.close();
  }, [runtimeUrl]);

  return {
    sharedState,
    setSharedState,
    agentMessages,
    setAgentMessages,
  };
}

// ============================================================================
// CoAgent Dashboard Component
// ============================================================================

interface CoAgentDashboardProps {
  runtimeUrl: string;
}

export function CoAgentDashboard({ runtimeUrl }: CoAgentDashboardProps) {
  const { sharedState, agentMessages } = useCoAgentState(runtimeUrl);

  return (
    <div className="space-y-6">
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
