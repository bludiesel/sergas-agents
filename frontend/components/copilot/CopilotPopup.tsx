/**
 * CopilotKit Popup Component
 *
 * Provides a popup chat interface for AI assistant interaction.
 * Displays as a floating button in the bottom-right corner.
 *
 * Features:
 * - Minimizable popup interface
 * - Floating button when closed
 * - Customizable labels and title
 * - Less intrusive than sidebar
 */

'use client';

import React from 'react';
import { CopilotPopup as CopilotKitPopup } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

interface CopilotPopupProps {
  title?: string;
  initialMessage?: string;
}

/**
 * CopilotPopup Component
 *
 * Renders the CopilotKit popup interface with custom configuration.
 */
export function CopilotPopup({
  title = 'Sergas Account Assistant',
  initialMessage = 'How can I help you today?',
}: CopilotPopupProps) {
  return (
    <CopilotKitPopup
      labels={{
        title,
        initial: initialMessage,
      }}
    />
  );
}
