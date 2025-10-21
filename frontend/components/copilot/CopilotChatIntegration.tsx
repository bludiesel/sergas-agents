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
  parameters: Record<string, unknown>;
  result?: unknown;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
}

// ============================================================================
// Chat Integration Component
// ============================================================================

export function CopilotChatIntegration() {
  const [inputMessage, setInputMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ========================================================================
  // CopilotKit Hooks
  // ========================================================================

  const {
    isLoading,
    visibleMessages,
    appendMessage,
    setMessages,
    deleteMessage,
    reloadMessages,
  } = useCopilotChat({
    // Additional configuration for better chat handling
    instructions: "You are an AI assistant for account analysis and management. Help users analyze accounts, understand risk signals, and provide actionable recommendations based on the available data.",
    labels: {
      initial: "Start a conversation about account analysis",
      placeholder: "Ask about accounts, risk analysis, or recommendations...",
    }
  });

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

    // Clear any existing errors
    setError(null);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    try {
      // Clear input immediately for better UX
      setInputMessage('');

      // Append message to CopilotKit chat
      await appendMessage(inputMessage);

      // Update local chat history for immediate UI update
      setChatHistory((prev) => [...prev, userMessage]);

      // Add a temporary assistant message while processing
      const processingMessage: ChatMessage = {
        id: `assistant-processing-${Date.now()}`,
        role: 'assistant',
        content: 'Processing your request...',
        timestamp: new Date(),
      };

      setChatHistory((prev) => [...prev, processingMessage]);

    } catch (error) {
      console.error('Failed to send message:', error);

      // Add error message to chat history
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error sending your message. Please try again.',
        timestamp: new Date(),
        toolCalls: [{
          tool: 'error_handler',
          parameters: { error: error instanceof Error ? error.message : 'Unknown error' },
          status: 'failed'
        }]
      };

      setChatHistory((prev) => [...prev, errorMessage]);

      // Restore input message for retry
      setInputMessage(inputMessage);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // ========================================================================
  // Sync with CopilotKit messages
  // ========================================================================

  useEffect(() => {
    // Sync local chat history with CopilotKit's visible messages
    if (visibleMessages && visibleMessages.length > 0) {
      const copilotMessages: ChatMessage[] = visibleMessages.map((msg, idx) => ({
        id: msg.id || `copilot-${idx}`,
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content || '',
        timestamp: new Date(msg.createdAt || Date.now()),
        toolCalls: msg.toolCalls?.map((tool: any) => ({
          tool: tool.name,
          parameters: tool.arguments || {},
          result: tool.result,
          status: tool.result ? 'completed' : 'pending'
        }))
      }));

      // Update chat history, but keep user messages that might not be in visibleMessages yet
      setChatHistory((prev) => {
        const existingUserMessages = prev.filter(m => m.role === 'user');
        const mergedMessages = [...existingUserMessages, ...copilotMessages];

        // Remove duplicates and keep latest version of each message
        const uniqueMessages = mergedMessages.filter((message, index, array) =>
          array.findIndex(m => m.id === message.id) === index
        );

        return uniqueMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
      });
    }
  }, [visibleMessages]);

  // ========================================================================
  // Auto-scroll to bottom
  // ========================================================================

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoading]);

  // ========================================================================
  // Message History Management
  // ========================================================================

  const clearChatHistory = () => {
    setChatHistory([]);
    setMessages([]);
  };

  const retryLastMessage = () => {
    const lastUserMessage = chatHistory
      .filter(m => m.role === 'user')
      .pop();

    if (lastUserMessage) {
      setInputMessage(lastUserMessage.content);
    }
  };

  // ========================================================================
  // UI Rendering
  // ========================================================================

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Account Analysis Assistant
            </h2>
            <p className="text-sm text-blue-100 mt-1">
              Ask me to analyze accounts, generate recommendations, or check risk signals
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={retryLastMessage}
              className="p-2 hover:bg-blue-500 rounded transition-colors"
              title="Retry last message"
              disabled={chatHistory.length === 0}
            >
              ↻
            </button>
            <button
              onClick={clearChatHistory}
              className="p-2 hover:bg-blue-500 rounded transition-colors"
              title="Clear chat"
            >
              ✕
            </button>
          </div>
        </div>
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
        {/* Loading indicator for streaming responses */}
        {isLoading && (
          <div className="mb-3 flex items-center gap-2 text-sm text-blue-600 bg-blue-50 px-3 py-2 rounded-lg">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100" />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200" />
            <span className="ml-2">AI is thinking...</span>
          </div>
        )}

        {/* Error display for connection issues */}
        {error && (
          <div className="mb-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="text-red-500 hover:text-red-700 ml-2"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isLoading ? "Waiting for response..." : "Ask about an account or request analysis..."}
            className={`flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
              isLoading
                ? 'border-gray-300 bg-gray-100 cursor-not-allowed'
                : 'border-gray-300 focus:ring-blue-500'
            }`}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={`px-6 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              !inputMessage.trim() || isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Sending...</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>Send</span>
              </>
            )}
          </button>
        </div>

        {/* Character count and send shortcut hint */}
        <div className="mt-2 text-xs text-gray-500 flex justify-between">
          <span>{inputMessage.length} characters</span>
          <span>Press Enter to send, Shift+Enter for new line</span>
        </div>
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

      {toolCall.result ? (
        <div className="mt-1">
          <span className="font-medium">Result:</span>
          <div className="font-mono text-xs opacity-80 mt-0.5">
            {String(JSON.stringify(toolCall.result, null, 2))}
          </div>
        </div>
      ) : null}
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
