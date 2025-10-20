/**
 * CopilotKit Components Index
 *
 * Centralized exports for all CopilotKit integration components.
 */

export { CopilotProvider, useCopilotConfig } from './CopilotProvider';
export { CopilotSidebar } from './CopilotSidebar';
export { CopilotPopup } from './CopilotPopup';
export { AccountAnalysisAgent } from './AccountAnalysisAgent';
export { CoAgentDashboard, useCoAgentState } from './CoAgentIntegration';
export { CopilotChatIntegration, CompactChatWidget } from './CopilotChatIntegration';

// Type exports
export type { SharedState, AgentMessage } from './CoAgentIntegration';
