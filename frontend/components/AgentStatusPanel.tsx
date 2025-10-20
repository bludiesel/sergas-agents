"use client"

import React from 'react';
import { CheckCircle, Loader2, Circle } from 'lucide-react';

interface AgentStatusPanelProps {
  status: Record<string, string>;
}

export function AgentStatusPanel({ status }: AgentStatusPanelProps) {
  const agents = [
    { id: 'zoho-data-scout', name: 'Zoho Data Scout' },
    { id: 'memory-analyst', name: 'Memory Analyst' },
    { id: 'recommendation-author', name: 'Recommendation Author' },
  ];

  const getStatusIcon = (agentStatus: string) => {
    switch (agentStatus) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Circle className="h-5 w-5 text-gray-300" />;
    }
  };

  const getStatusColor = (agentStatus: string) => {
    switch (agentStatus) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-3">
      {agents.map((agent) => {
        const agentStatus = status[agent.id] || 'idle';

        return (
          <div
            key={agent.id}
            className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {getStatusIcon(agentStatus)}

            <div className="flex-1">
              <p className="font-medium text-sm">{agent.name}</p>
              <p className={`text-xs capitalize ${getStatusColor(agentStatus)}`}>
                {agentStatus}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
