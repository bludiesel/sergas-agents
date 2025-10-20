# CopilotKit Provider Configuration

## Overview

This document describes the CopilotKit provider setup for the Sergas Account Manager frontend application. The provider wraps the entire application, enabling AI-powered features through the CopilotKit framework.

## Architecture

```
RootLayout (app/layout.tsx)
└── CopilotProvider
    ├── Backend Connection: /api/copilotkit
    ├── Agent: orchestrator
    ├── Authentication: Bearer token (optional)
    └── Children (Application Content)
```

## Components Created

### 1. CopilotProvider (`/frontend/components/copilot/CopilotProvider.tsx`)

**Purpose**: Main provider component that configures CopilotKit

**Features**:
- Backend API connection via `/api/copilotkit`
- Authentication token management from environment
- Configurable agent selection (default: orchestrator)
- Optional CopilotKit Cloud API key support

**Configuration**:
```typescript
<CopilotProvider
  agent="orchestrator"
  publicApiKey="optional-cloud-api-key"
>
  {children}
</CopilotProvider>
```

**Environment Variables**:
- `NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL`: Backend API endpoint (default: `/api/copilotkit`)
- `NEXT_PUBLIC_API_TOKEN`: Authentication token for backend
- `NEXT_PUBLIC_COPILOTKIT_API_KEY`: Optional CopilotKit Cloud API key

### 2. CopilotSidebar (`/frontend/components/copilot/CopilotSidebar.tsx`)

**Purpose**: Sidebar chat interface for AI assistant

**Features**:
- Fixed sidebar position on application edge
- Customizable title and initial message
- Configurable default open/closed state
- Click outside to close behavior

**Usage**:
```typescript
import { CopilotSidebar } from '@/components/copilot';

<CopilotSidebar
  title="Sergas Account Assistant"
  initialMessage="Ask me about accounts..."
  defaultOpen={true}
  clickOutsideToClose={false}
/>
```

### 3. CopilotPopup (`/frontend/components/copilot/CopilotPopup.tsx`)

**Purpose**: Popup chat interface (floating button)

**Features**:
- Minimizable floating chat window
- Bottom-right corner positioning
- Less intrusive than sidebar
- Customizable labels

**Usage**:
```typescript
import { CopilotPopup } from '@/components/copilot';

<CopilotPopup
  title="Sergas Account Assistant"
  initialMessage="How can I help?"
/>
```

## Integration with Application

### Layout Update

The `app/layout.tsx` file has been updated to wrap the entire application:

```typescript
import { CopilotProvider } from "@/components/copilot";

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <CopilotProvider agent="orchestrator">
          {children}
        </CopilotProvider>
      </body>
    </html>
  );
}
```

### Metadata Update

Application metadata has been updated to reflect CopilotKit integration:

```typescript
export const metadata: Metadata = {
  title: "Sergas Account Manager",
  description: "AI-powered account management with CopilotKit",
};
```

## Environment Configuration

### `.env.local.example` Created

Template file for environment variables:

```env
# CopilotKit Runtime URL (defaults to /api/copilotkit)
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=/api/copilotkit

# Optional: CopilotKit Cloud API Key
# NEXT_PUBLIC_COPILOTKIT_API_KEY=your-copilotkit-cloud-api-key

# Optional: Authentication token for backend API
# NEXT_PUBLIC_API_TOKEN=your-backend-api-token

# Anthropic API Key (required for backend)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### Setup Instructions

1. **Copy environment template**:
   ```bash
   cp .env.local.example .env.local
   ```

2. **Configure required variables**:
   - Set `ANTHROPIC_API_KEY` (required for backend)
   - Optionally set `NEXT_PUBLIC_API_TOKEN` for authentication
   - Optionally set `NEXT_PUBLIC_COPILOTKIT_API_KEY` for cloud features

3. **Verify configuration**:
   ```bash
   npm run build
   ```

## Authentication Flow

### Without Authentication Token
```typescript
// Provider sends requests to /api/copilotkit without auth headers
<CopilotProvider agent="orchestrator">
  {children}
</CopilotProvider>
```

### With Authentication Token
```typescript
// Provider automatically adds Bearer token from environment
// Headers: { Authorization: "Bearer <token>" }
<CopilotProvider agent="orchestrator">
  {children}
</CopilotProvider>
```

## Backend Connection

### API Route
- **Endpoint**: `/api/copilotkit`
- **Method**: POST (streaming)
- **Content-Type**: `application/json`, `text/event-stream`
- **Authentication**: Optional Bearer token

### Request Flow
```
Frontend Component (useCopilotChat)
    ↓
CopilotProvider (adds auth headers)
    ↓
POST /api/copilotkit
    ↓
Backend Route Handler
    ↓
Claude Agent SDK
    ↓
Streaming Response
    ↓
Frontend Component (renders messages)
```

## Using CopilotKit Hooks

Once the provider is configured, use CopilotKit hooks in any component:

### 1. useCopilotChat - Chat Interface
```typescript
import { useCopilotChat } from '@copilotkit/react-core';

function MyComponent() {
  const { isLoading, messages, sendMessage } = useCopilotChat();

  return (
    <div>
      {messages.map(msg => <div>{msg.content}</div>)}
    </div>
  );
}
```

### 2. useCopilotAction - Custom Actions
```typescript
import { useCopilotAction } from '@copilotkit/react-core';

useCopilotAction({
  name: 'analyzeAccount',
  description: 'Analyze account risk',
  parameters: [
    { name: 'accountId', type: 'string', required: true }
  ],
  handler: async ({ accountId }) => {
    const data = await fetch(`/api/accounts/${accountId}`);
    return data;
  }
});
```

### 3. useCopilotReadable - Share Context
```typescript
import { useCopilotReadable } from '@copilotkit/react-core';

useCopilotReadable({
  description: 'Current account selection',
  value: selectedAccount
});
```

## Component Structure

```
/frontend/components/copilot/
├── CopilotProvider.tsx    # Main provider component
├── CopilotSidebar.tsx     # Sidebar interface
├── CopilotPopup.tsx       # Popup interface
└── index.tsx              # Public exports
```

## Build Verification

### TypeScript Compilation
```bash
cd frontend
npm run build
```

**Result**: ✓ Compiled successfully
- No TypeScript errors in provider components
- Layout updated without breaking changes
- Application builds with CopilotKit integration

### Warnings (Non-Breaking)
- Unused variables in `/app/api/copilotkit/route.ts` (lines 74, 135)
- These are in the backend route, not the provider components

## Next Steps

### 1. Add UI Components
- Import and use `CopilotSidebar` in application pages
- Or use `CopilotPopup` for less intrusive interface

### 2. Implement Actions
- Define custom actions using `useCopilotAction`
- Connect actions to backend API endpoints
- Handle account analysis, recommendations, etc.

### 3. Share Context
- Use `useCopilotReadable` to share application state
- Provide current account, filters, selections to AI

### 4. Test Integration
- Verify backend connection
- Test streaming responses
- Validate authentication flow

## Example Implementation

### Page with Sidebar
```typescript
'use client';

import { CopilotSidebar } from '@/components/copilot';

export default function AccountsPage() {
  return (
    <div className="flex h-screen">
      <main className="flex-1 p-6">
        {/* Your content */}
      </main>

      <CopilotSidebar
        title="Account Assistant"
        defaultOpen={true}
      />
    </div>
  );
}
```

### Page with Popup
```typescript
'use client';

import { CopilotPopup } from '@/components/copilot';

export default function DashboardPage() {
  return (
    <div className="h-screen p-6">
      {/* Your content */}

      <CopilotPopup
        title="AI Assistant"
        initialMessage="How can I help?"
      />
    </div>
  );
}
```

## Troubleshooting

### Provider Not Working
- Check `NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL` is set correctly
- Verify backend route at `/api/copilotkit` exists
- Check browser console for connection errors

### Authentication Errors
- Verify `NEXT_PUBLIC_API_TOKEN` is set (if using auth)
- Check backend route accepts Bearer token
- Verify token format and validity

### Sidebar/Popup Not Showing
- Ensure CopilotKit CSS is imported: `@copilotkit/react-ui/styles.css`
- Check z-index conflicts with other UI elements
- Verify component is inside CopilotProvider

### Build Errors
- Run `npm install @copilotkit/react-core @copilotkit/react-ui`
- Clear `.next` folder and rebuild
- Check TypeScript version compatibility

## Performance Considerations

### Bundle Size
- **CopilotKit Core**: ~460 KB (gzipped)
- **UI Components**: ~20 KB (gzipped)
- **Total First Load**: ~621 KB

### Optimization
- Provider is wrapped at root level (single instance)
- Streaming responses reduce perceived latency
- CSS is imported once, shared by all components

## Security

### Environment Variables
- **Never commit** `.env.local` to version control
- Use `.env.local.example` as template
- Rotate API keys regularly

### Authentication
- Use Bearer tokens for backend communication
- Validate tokens on backend route
- Implement rate limiting on API endpoints

### Data Privacy
- Sensitive data should be filtered before sending to AI
- Implement data masking for PII
- Review CopilotKit Cloud data handling policies

## Resources

- [CopilotKit Documentation](https://docs.copilotkit.ai)
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-typescript)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [Component Demo Template](/docs/sparc/templates/CopilotKitDemo.tsx)

## Summary

The CopilotKit provider is now fully configured and integrated into the Sergas Account Manager application:

✅ **Provider Component**: Created with backend connection and auth support
✅ **Sidebar Component**: Ready for fixed-position chat interface
✅ **Popup Component**: Ready for floating chat interface
✅ **Layout Integration**: Application wrapped with CopilotProvider
✅ **Environment Config**: Template created for setup
✅ **TypeScript Compilation**: Verified successfully
✅ **Documentation**: Complete setup and usage guide

The application is ready to implement CopilotKit features using hooks and UI components.
