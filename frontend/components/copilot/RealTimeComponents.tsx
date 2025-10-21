/**
 * Real-Time Status Components for CoAgent Integration
 *
 * Provides reusable components for displaying connection status,
 * agent status, and performance metrics in real-time.
 *
 * Features:
 * - Connection status indicators with animations
 * - Agent status cards with progress bars
 * - Performance metrics display
 * - Real-time updates support
 */

'use client';

import React from 'react';

// ============================================================================
// Connection Status Indicator
// ============================================================================

interface ConnectionStatusIndicatorProps {
  status: string;
  isConnected: boolean;
  latency?: number;
}

export function ConnectionStatusIndicator({ status, isConnected, latency }: ConnectionStatusIndicatorProps) {
  const statusConfig = {
    connecting: { color: 'text-yellow-500', text: 'Connecting', icon: '⏳', bgColor: 'bg-yellow-100' },
    connected: { color: 'text-green-500', text: 'Connected', icon: '✓', bgColor: 'bg-green-100' },
    disconnected: { color: 'text-gray-500', text: 'Disconnected', icon: '✕', bgColor: 'bg-gray-100' },
    reconnecting: { color: 'text-yellow-500', text: 'Reconnecting', icon: '🔄', bgColor: 'bg-yellow-100' },
    error: { color: 'text-red-500', text: 'Error', icon: '⚠️', bgColor: 'bg-red-100' },
  };

  const config = statusConfig[status] || statusConfig.disconnected;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bgColor} ${config.color}`}>
      <span className={`text-lg ${status === 'reconnecting' ? 'animate-spin' : ''}`}>
        {config.icon}
      </span>
      <div className="flex flex-col">
        <span className="text-sm font-medium">{config.text}</span>
        {latency !== undefined && isConnected && (
          <span className={`text-xs ${latency < 100 ? 'text-green-600' : latency < 300 ? 'text-yellow-600' : 'text-red-600'}`}>
            {latency}ms latency
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Agent Status Card
// ============================================================================

interface AgentExecutionStatus {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused';
  progress?: number;
  currentTask?: string;
  startTime?: Date;
  estimatedCompletion?: Date;
  metadata?: Record<string, unknown>;
}

interface AgentStatusCardProps {
  agentId: string;
  status: AgentExecutionStatus;
  className?: string;
}

export function AgentStatusCard({ agentId, status, className = '' }: AgentStatusCardProps) {
  const statusConfig = {
    idle: { color: 'text-gray-500', bg: 'bg-gray-100', text: 'Idle', icon: '⚸' },
    running: { color: 'text-blue-500', bg: 'bg-blue-100', text: 'Running', icon: '▶️' },
    completed: { color: 'text-green-500', bg: 'bg-green-100', text: 'Completed', icon: '✓' },
    failed: { color: 'text-red-500', bg: 'bg-red-100', text: 'Failed', icon: '✕' },
    paused: { color: 'text-yellow-500', bg: 'bg-yellow-100', text: 'Paused', icon: '⏸' },
  };

  const config = statusConfig[status.status] || statusConfig.idle;
  const hasProgress = status.progress !== undefined && status.progress >= 0;

  // Calculate duration
  let duration = '';
  if (status.startTime) {
    const now = new Date();
    const diff = now.getTime() - status.startTime.getTime();
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    duration = minutes > 0 ? `${m}m ${s}s` : `${s}s`;
  }

  return (
    <div className={`border border-gray-200 rounded-lg p-4 ${className} ${
      status.status === 'running' ? 'shadow-sm shadow-blue-100' : ''
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{config.icon}</span>
          <h3 className="font-semibold text-gray-900 text-sm">{agentId}</h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${config.bg} ${config.color}`}>
          {config.text}
        </span>
      </div>

      {/* Progress Bar */}
      {hasProgress && (
        <div className="mb-3">
          <div className="flex justify-between items-center text-xs text-gray-600 mb-2">
            <span className="font-medium">Progress</span>
            <div className="flex items-center gap-2">
              <span>{status.progress}%</span>
              {status.status === 'running' && (
                <div className="flex gap-1">
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse delay-100"></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse delay-200"></div>
                </div>
              )}
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ease-out ${
                status.status === 'running' ? 'bg-blue-600' :
                status.status === 'completed' ? 'bg-green-600' :
                status.status === 'failed' ? 'bg-red-600' : 'bg-gray-600'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, status.progress))}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Task */}
      {status.currentTask && (
        <div className="mb-2">
          <p className="text-xs font-medium text-gray-600 mb-1">Current Task</p>
          <p className="text-sm text-gray-800 bg-gray-50 px-2 py-1 rounded truncate">
            {status.currentTask}
          </p>
        </div>
      )}

      {/* Timing Information */}
      <div className="flex justify-between items-center text-xs text-gray-500">
        <div>
          {status.startTime && (
            <span>Started: {status.startTime.toLocaleTimeString()}</span>
          )}
        </div>
        <div className="flex flex-col items-end">
          {duration && <span>Duration: {duration}</span>}
          {status.estimatedCompletion && (
            <span>ETA: {status.estimatedCompletion.toLocaleTimeString()}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Performance Metrics Panel
// ============================================================================

interface PerformanceMetrics {
  totalMessages: number;
  messagesPerSecond: number;
  averageLatency: number;
  connectionUptime: number;
}

interface PerformanceMetricsPanelProps {
  metrics: PerformanceMetrics;
  className?: string;
}

export function PerformanceMetricsPanel({ metrics, className = '' }: PerformanceMetricsPanelProps) {
  const getLatencyColor = (latency: number) => {
    if (latency < 100) return 'text-green-600';
    if (latency < 300) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMessagesPerSecondColor = (rate: number) => {
    if (rate > 10) return 'text-green-600';
    if (rate > 5) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h2>

      <div className="grid grid-cols-2 gap-4">
        {/* Messages */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Total Messages</span>
            <span className="text-2xl font-bold text-gray-900">
              {metrics.totalMessages.toLocaleString()}
            </span>
          </div>
          <div className="text-xs text-gray-500">All time messages</div>
        </div>

        {/* Messages per Second */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Rate</span>
            <span className={`text-2xl font-bold ${getMessagesPerSecondColor(metrics.messagesPerSecond)}`}>
              {metrics.messagesPerSecond.toFixed(1)}
            </span>
          </div>
          <div className="text-xs text-gray-500">Messages/second</div>
        </div>

        {/* Latency */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Latency</span>
            <span className={`text-2xl font-bold ${getLatencyColor(metrics.averageLatency)}`}>
              {metrics.averageLatency}
            </span>
          </div>
          <div className="text-xs text-gray-500">Average (ms)</div>
        </div>

        {/* Uptime */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Uptime</span>
            <span className="text-lg font-bold text-gray-900">
              {formatUptime(metrics.connectionUptime)}
            </span>
          </div>
          <div className="text-xs text-gray-500">Connection duration</div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Connection Status Panel
// ============================================================================

interface ConnectionStatusPanelProps {
  status: string;
  isConnected: boolean;
  latency?: number;
  lastConnected?: Date;
  reconnectAttempts: number;
  error?: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function ConnectionStatusPanel({
  status,
  isConnected,
  latency,
  lastConnected,
  reconnectAttempts,
  error,
  onConnect,
  onDisconnect
}: ConnectionStatusPanelProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'connecting': return '⏳';
      case 'connected': return '🟢';
      case 'disconnected': return '🔴';
      case 'reconnecting': return '🔄';
      case 'error': return '⚠️';
      default: return '❓';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'connecting': return 'text-yellow-600';
      case 'connected': return 'text-green-600';
      case 'disconnected': return 'text-red-600';
      case 'reconnecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Connection Status</h2>
        <div className={`flex items-center gap-2 ${getStatusColor()}`}>
          <span className="text-2xl">{getStatusIcon()}</span>
          <span className="text-sm font-medium capitalize">{status}</span>
        </div>
      </div>

      <div className="space-y-3">
        {/* Connection Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600">Status</span>
            <p className={`font-medium capitalize ${getStatusColor()}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Latency</span>
            <p className={`font-medium ${latency && latency < 100 ? 'text-green-600' : latency && latency < 300 ? 'text-yellow-600' : 'text-red-600'}`}>
              {latency ? `${latency}ms` : 'N/A'}
            </p>
          </div>
        </div>

        {/* Additional Info */}
        {lastConnected && (
          <div>
            <span className="text-sm text-gray-600">Last Connected</span>
            <p className="font-medium text-gray-900">
              {lastConnected.toLocaleString()}
            </p>
          </div>
        )}

        {reconnectAttempts > 0 && (
          <div>
            <span className="text-sm text-gray-600">Reconnect Attempts</span>
            <p className="font-medium text-gray-900">{reconnectAttempts}</p>
          </div>
        )}

        {error && (
          <div>
            <span className="text-sm text-gray-600">Error</span>
            <p className="font-medium text-red-600 text-sm">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={onConnect}
            disabled={isConnected}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium transition-colors"
          >
            Connect
          </button>
          <button
            onClick={onDisconnect}
            disabled={!isConnected}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium transition-colors"
          >
            Disconnect
          </button>
        </div>
      </div>
    </div>
  );
}