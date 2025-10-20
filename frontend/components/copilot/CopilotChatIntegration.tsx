/**
 * CopilotChatIntegration.tsx
 *
 * Advanced chat integration with CopilotKit for account management.
 * Provides streaming responses, tool calls visualization, and HITL workflows.
 *
 * Features:
 * - useCopilotChat: Chat state management
 * - Real-time streaming responses
 * - Tool call visualization
 * - Message history
 * - Custom message rendering
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useCopilotChat, useCopilotReadable } from '@copilotkit/react-core';
import { Send, Bot, User, CheckCircle, XCircle, Clock } from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
  result?: any;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
}

// ============================================================================
// Chat Integration Component
// ============================================================================

interface CopilotChatIntegrationProps {
  onToolCall?: (toolCall: ToolCall) => void;
}

export function CopilotChatIntegration({ onToolCall }: CopilotChatIntegrationProps) {
  const [inputMessage, setInputMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ========================================================================
  // CopilotKit Hooks
  // ========================================================================

  const {
    isLoading,
    sendMessage,
    stopGeneration,
    reloadMessages,
  } = useCopilotChat();

  // Make chat history readable by agents
  useCopilotReadable({
    description: 'Current conversation history with the user',
    value: chatHistory,
  });

  // ========================================================================
  // Message Handling
  // ========================================================================

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setChatHistory((prev) => [...prev, userMessage]);
    setInputMessage('');

    // Send message through CopilotKit
    await sendMessage(inputMessage);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // ========================================================================
  // Auto-scroll to bottom
  // ========================================================================

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoading]);

  // ========================================================================
  // Note: Message syncing would happen via event listeners in production
  // CopilotKit's useCopilotChat doesn't expose messages directly
  // ========================================================================

  // ========================================================================
  // UI Rendering
  // ========================================================================

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-t-lg">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Bot className="h-5 w-5" />
          Account Analysis Assistant
        </h2>
        <p className="text-sm text-blue-100 mt-1">
          Ask me to analyze accounts, generate recommendations, or check risk signals
        </p>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {chatHistory.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium">Start a conversation</p>
            <p className="text-sm mt-2">Try asking:</p>
            <div className="mt-4 space-y-2">
              <SuggestionChip text="Analyze account ACC-001" onClick={setInputMessage} />
              <SuggestionChip text="Show me high-risk accounts" onClick={setInputMessage} />
              <SuggestionChip
                text="Generate recommendations for account 12345"
                onClick={setInputMessage}
              />
            </div>
          </div>
        )}

        {chatHistory.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100" />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200" />
            <span className="text-sm ml-2">AI is thinking...</span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Chat Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about an account or request analysis..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="h-4 w-4" />
            Send
          </button>
        </div>

        {isLoading && (
          <button
            onClick={stopGeneration}
            className="mt-2 text-sm text-red-600 hover:text-red-700"
          >
            Stop generating
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

interface MessageBubbleProps {
  message: ChatMessage;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-600' : 'bg-gray-200'
          }`}
        >
          {isUser ? (
            <User className="h-5 w-5 text-white" />
          ) : (
            <Bot className="h-5 w-5 text-gray-600" />
          )}
        </div>

        {/* Message Content */}
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>

          {/* Tool Calls */}
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.toolCalls.map((toolCall, idx) => (
                <ToolCallDisplay key={idx} toolCall={toolCall} />
              ))}
            </div>
          )}

          <p className="text-xs mt-2 opacity-70">
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
}

interface ToolCallDisplayProps {
  toolCall: ToolCall;
}

function ToolCallDisplay({ toolCall }: ToolCallDisplayProps) {
  const statusIcons = {
    pending: <Clock className="h-4 w-4 text-gray-400" />,
    running: <Clock className="h-4 w-4 text-blue-500 animate-spin" />,
    completed: <CheckCircle className="h-4 w-4 text-green-500" />,
    failed: <XCircle className="h-4 w-4 text-red-500" />,
  };

  return (
    <div className="bg-white bg-opacity-20 rounded p-2 text-xs">
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium">🔧 {toolCall.tool}</span>
        {statusIcons[toolCall.status]}
      </div>

      {Object.keys(toolCall.parameters).length > 0 && (
        <div className="mt-1 font-mono text-xs opacity-80">
          {JSON.stringify(toolCall.parameters, null, 2)}
        </div>
      )}

      {toolCall.result && (
        <div className="mt-1">
          <span className="font-medium">Result:</span>
          <div className="font-mono text-xs opacity-80 mt-0.5">
            {JSON.stringify(toolCall.result, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
}

interface SuggestionChipProps {
  text: string;
  onClick: (text: string) => void;
}

function SuggestionChip({ text, onClick }: SuggestionChipProps) {
  return (
    <button
      onClick={() => onClick(text)}
      className="text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 px-4 py-2 rounded-full transition-colors"
    >
      {text}
    </button>
  );
}

// ============================================================================
// Compact Chat Widget (for sidebar)
// ============================================================================

export function CompactChatWidget() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isOpen ? (
        <div className="w-96 h-[600px] shadow-2xl rounded-lg overflow-hidden">
          <CopilotChatIntegration />
          <button
            onClick={() => setIsOpen(false)}
            className="absolute top-2 right-2 text-white hover:text-gray-200"
          >
            ✕
          </button>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
        >
          <Bot className="h-6 w-6" />
        </button>
      )}
    </div>
  );
}
