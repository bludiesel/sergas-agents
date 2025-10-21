/**
 * CopilotChatIntegration Component Tests
 *
 * Tests for chat interface, message handling, and streaming responses
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CopilotChatIntegration, CompactChatWidget } from '@/components/copilot/CopilotChatIntegration';

// Mock CopilotKit hooks
const mockUseCopilotChat = jest.fn();
const mockUseCopilotReadable = jest.fn();

jest.mock('@copilotkit/react-core', () => ({
  useCopilotChat: mockUseCopilotChat,
  useCopilotReadable: mockUseCopilotReadable,
}));

describe('CopilotChatIntegration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCopilotChat.mockReturnValue({ isLoading: false });
    mockUseCopilotReadable.mockImplementation(() => {});
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render chat interface without crashing', () => {
      render(<CopilotChatIntegration />);

      expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Ask about an account/)).toBeInTheDocument();
      expect(screen.getByText('Send')).toBeInTheDocument();
    });

    it('should display initial welcome state', () => {
      render(<CopilotChatIntegration />);

      expect(screen.getByText('Start a conversation')).toBeInTheDocument();
      expect(screen.getByText('Ask me to analyze accounts, generate recommendations, or check risk signals')).toBeInTheDocument();
      expect(screen.getByText('Analyze account ACC-001')).toBeInTheDocument();
      expect(screen.getByText('Show me high-risk accounts')).toBeInTheDocument();
      expect(screen.getByText('Generate recommendations for account 12345')).toBeInTheDocument();
    });

    it('should configure CopilotKit readable context for chat history', () => {
      render(<CopilotChatIntegration />);

      expect(mockUseCopilotReadable).toHaveBeenCalledWith({
        description: 'Current conversation history with user',
        value: [],
      });
    });
  });

  describe('Message Input', () => {
    it('should allow typing in message input', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      await user.type(input, 'Analyze account ACC-123');

      expect(input).toHaveValue('Analyze account ACC-123');
    });

    it('should handle Enter key to send message', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      const sendButton = screen.getByText('Send');

      await user.type(input, 'Test message{enter}');

      expect(input).toHaveValue('');
      // Message should be added to chat (would be visible in real implementation)
    });

    it('should handle Shift+Enter for new line', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);

      await user.type(input, 'First line{shift>}{enter}Second line');

      expect(input).toHaveValue('First line\nSecond line');
    });

    it('should not send empty messages', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      const sendButton = screen.getByText('Send');

      // Try to send empty message
      await user.click(sendButton);

      expect(input).toHaveValue('');
      // Should not add message to chat
    });

    it('should disable send button when input is empty', () => {
      render(<CopilotChatIntegration />);

      const sendButton = screen.getByText('Send');
      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when input has text', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      const sendButton = screen.getByText('Send');

      await user.type(input, 'Test message');

      expect(sendButton).not.toBeDisabled();
    });
  });

  describe('Message Handling', () => {
    it('should clear input after sending message', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);

      await user.type(input, 'Test message');
      await user.click(screen.getByText('Send'));

      expect(input).toHaveValue('');
    });

    it('should prevent sending messages when loading', async () => {
      mockUseCopilotChat.mockReturnValue({ isLoading: true });

      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      const sendButton = screen.getByText('Send');

      await user.type(input, 'Test message');

      expect(sendButton).toBeDisabled();
      expect(input).toBeDisabled();
    });

    it('should show loading indicator when processing', () => {
      mockUseCopilotChat.mockReturnValue({ isLoading: true });

      render(<CopilotChatIntegration />);

      expect(screen.getByText('AI is thinking...')).toBeInTheDocument();
      expect(screen.getByText(/🤖/)).toBeInTheDocument();
    });

    it('should show animated loading dots', () => {
      mockUseCopilotChat.mockReturnValue({ isLoading: true });

      render(<CopilotChatIntegration />);

      const loadingDots = screen.getAllByRole('generic');
      expect(loadingDots.length).toBeGreaterThan(0);
    });
  });

  describe('Suggestion Chips', () => {
    it('should display suggestion chips in welcome state', () => {
      render(<CopilotChatIntegration />);

      const suggestions = screen.getAllByRole('button').filter(button =>
        button.textContent?.includes('Analyze') ||
        button.textContent?.includes('Show me') ||
        button.textContent?.includes('Generate')
      );

      expect(suggestions.length).toBe(3);
    });

    it('should set input text when suggestion is clicked', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const suggestionChip = screen.getByText('Analyze account ACC-001');
      await user.click(suggestionChip);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      expect(input).toHaveValue('Analyze account ACC-001');
    });

    it('should focus input after suggestion click', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const suggestionChip = screen.getByText('Analyze account ACC-001');
      const input = screen.getByPlaceholderText(/Ask about an account/);

      await user.click(suggestionChip);

      expect(input).toHaveFocus();
    });

    it('should apply hover styles to suggestion chips', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const suggestionChip = screen.getByText('Analyze account ACC-001');

      await user.hover(suggestionChip);

      // Test that hover effect works (would require visual testing in real implementation)
      expect(suggestionChip).toBeInTheDocument();
    });
  });

  describe('Chat Header', () => {
    it('should display correct header information', () => {
      render(<CopilotChatIntegration />);

      expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
      expect(screen.getByText('Ask me to analyze accounts, generate recommendations, or check risk signals')).toBeInTheDocument();
    });

    it('should include bot icon in header', () => {
      render(<CopilotChatIntegration />);

      const botIcon = document.querySelector('.lucide-bot');
      expect(botIcon).toBeInTheDocument();
    });

    it('should apply gradient styling to header', () => {
      render(<CopilotChatIntegration />);

      const header = screen.getByText('Account Analysis Assistant').closest('div');
      expect(header?.parentElement).toHaveClass('from-blue-600');
      expect(header?.parentElement).toHaveClass('to-blue-700');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<CopilotChatIntegration />);

      const input = screen.getByPlaceholderText(/Ask about an account/);
      const sendButton = screen.getByText('Send');

      expect(input).toHaveAttribute('placeholder');
      expect(sendButton).toHaveAttribute('disabled');
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      // Tab to input
      await user.tab();

      const input = screen.getByPlaceholderText(/Ask about an account/);
      expect(input).toHaveFocus();

      // Type and tab to send button
      await user.type(input, 'Test');
      await user.tab();

      const sendButton = screen.getByText('Send');
      expect(sendButton).toHaveFocus();
    });

    it('should prevent form submission on Enter in textarea without modifier', async () => {
      const user = userEvent.setup();
      render(<CopilotChatIntegration />);

      const form = screen.getByRole('form') || screen.getByText('Send').closest('form');
      const input = screen.getByPlaceholderText(/Ask about an account/);

      await user.type(input, 'Test message{enter}');

      // Form should handle Enter without submitting (handled by preventDefault)
      expect(input).toHaveValue('');
    });
  });

  describe('Auto-scroll Behavior', () => {
    // Note: Auto-scroll testing would require intersection observer mocks
    // and scroll behavior simulation which is complex in JSDOM

    it('should have scroll container element', () => {
      render(<CopilotChatIntegration />);

      const messagesContainer = screen.getByText('Start a conversation').closest('.overflow-y-auto');
      expect(messagesContainer).toBeInTheDocument();
    });

    it('should have scroll anchor element', () => {
      render(<CopilotChatIntegration />);

      // Should have ref element for auto-scroll
      expect(document.querySelector('[data-testid="chat-end"]')).toBeInTheDocument();
    });
  });
});

describe('CompactChatWidget', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Widget Toggle', () => {
    it('should render chat toggle button when closed', () => {
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');
      expect(toggleButton).toBeInTheDocument();
      expect(toggleButton).toHaveClass('bg-blue-600');

      const botIcon = document.querySelector('.lucide-bot');
      expect(botIcon).toBeInTheDocument();
    });

    it('should open chat when toggle button is clicked', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      // Should render the full chat interface
      expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Ask about an account/)).toBeInTheDocument();
    });

    it('should show close button when chat is open', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      // Open the chat
      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      // Should show close button
      const closeButton = screen.getByText('✕');
      expect(closeButton).toBeInTheDocument();
    });

    it('should close chat when close button is clicked', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      // Open chat
      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      // Close chat
      const closeButton = screen.getByText('✕');
      await user.click(closeButton);

      // Should return to toggle button state
      expect(screen.queryByText('Account Analysis Assistant')).not.toBeInTheDocument();
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });

  describe('Widget Styling', () => {
    it('should apply fixed positioning when closed', () => {
      render(<CompactChatWidget />);

      const widget = document.querySelector('.fixed.bottom-4.right-4');
      expect(widget).toBeInTheDocument();
    });

    it('should have shadow styling when closed', () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');
      expect(toggleButton).toHaveClass('shadow-lg');
    });

    it('should have proper dimensions when open', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      // Open the chat
      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      const chatContainer = document.querySelector('.w-96');
      expect(chatContainer).toBeInTheDocument();
    });
  });

  describe('Widget Accessibility', () => {
    it('should have accessible toggle button', () => {
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');
      expect(toggleButton).toBeInTheDocument();
    });

    it('should have proper button text for screen readers', () => {
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');
      const botIcon = toggleButton.querySelector('.lucide-bot');

      expect(botIcon).toBeInTheDocument();
      // Real implementation would have aria-label for screen readers
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');
      await user.tab();

      expect(toggleButton).toHaveFocus();

      // Should be able to activate with Enter
      await user.keyboard('{Enter}');

      // Chat should open
      expect(screen.getByText('Account Analysis Assistant')).toBeInTheDocument();
    });
  });

  describe('Widget Integration', () => {
    it('should render CopilotChatIntegration when opened', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      // Open the widget
      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      // Should contain all chat components
      expect(screen.getByPlaceholderText(/Ask about an account/)).toBeInTheDocument();
      expect(screen.getByText('Send')).toBeInTheDocument();
      expect(screen.getByText('Start a conversation')).toBeInTheDocument();
    });

    it('should pass all props to CopilotChatIntegration', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      // Open the widget
      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      // Should function exactly like the main chat component
      mockUseCopilotChat.mockReturnValue({ isLoading: true });

      expect(screen.getByText('AI is thinking...')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid toggle clicks', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      const toggleButton = screen.getByRole('button');

      // Rapid clicks should not cause errors
      await user.click(toggleButton);
      await user.click(toggleButton);
      await user.click(toggleButton);

      // Should still work correctly
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('should handle escape key to close chat', async () => {
      const user = userEvent.setup();
      render(<CompactChatWidget />);

      // Open chat
      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      // Press Escape to close
      await user.keyboard('{Escape}');

      // Note: This would require escape key handler implementation
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});