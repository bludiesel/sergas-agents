/**
 * CopilotKit Sidebar Component
 *
 * Provides a sidebar chat interface for AI assistant interaction.
 * Displays on the side of the application for continuous access.
 *
 * Features:
 * - Customizable labels and title
 * - Default open/closed state
 * - Click outside to close behavior
 * - Integrated with CopilotKit chat state
 */

'use client';

import React from 'react';
import { CopilotSidebar as CopilotKitSidebar } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

interface CopilotSidebarProps {
  title?: string;
  initialMessage?: string;
  defaultOpen?: boolean;
  clickOutsideToClose?: boolean;
}

/**
 * CopilotSidebar Component
 *
 * Renders the CopilotKit sidebar interface with custom configuration.
 */
export function CopilotSidebar({
  title = 'Sergas Account Assistant',
  initialMessage = 'Ask me about accounts, deals, or recommendations...',
  defaultOpen = true,
  clickOutsideToClose = false,
}: CopilotSidebarProps) {
  return (
    <CopilotKitSidebar
      defaultOpen={defaultOpen}
      clickOutsideToClose={clickOutsideToClose}
      labels={{
        title,
        initial: initialMessage,
      }}
    />
  );
}
