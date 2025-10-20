# Sergas Account Manager - Frontend

Next.js frontend application with CopilotKit integration for the Sergas Account Manager system.

## Features

- **CopilotKit Integration**: Real-time agent communication via SSE
- **Approval Workflow**: Interactive approval modal for recommendations
- **Agent Status Tracking**: Live status panel for all agents
- **Tool Call Visualization**: Display agent tool invocations and results
- **Responsive Design**: Mobile-first design with Tailwind CSS

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CopilotKit React UI (Presentation Layer)                  │
│  - <CopilotChat>, <CopilotSidebar>, <CopilotTextarea>     │
└─────────────────────────────────────────────────────────────┘
                           ↓
              AG-UI Protocol (SSE/EventSource)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (Bridge Layer)                             │
│  - /copilotkit endpoint                                     │
│  - Emits AG-UI events via SSE                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Claude Agent SDK (Orchestration Layer)                     │
│  - BaseAgent, Memory Analyst, Data Scout                   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI primitives + shadcn/ui patterns
- **Icons**: Lucide React
- **AI Integration**: CopilotKit
- **Backend Communication**: Server-Sent Events (SSE) via AG-UI Protocol

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend FastAPI server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your API URL and token
```

### Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TOKEN=your-auth-token-here
```

### Development

```bash
# Start development server
npm run dev

# Open browser
# Navigate to http://localhost:3000
```

### Build

```bash
# Production build
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Main page with CopilotKit
├── components/
│   ├── ui/                 # shadcn/ui components
│   │   ├── dialog.tsx
│   │   ├── button.tsx
│   │   ├── badge.tsx
│   │   └── card.tsx
│   ├── ApprovalModal.tsx   # Recommendation approval UI
│   ├── ToolCallCard.tsx    # Tool invocation display
│   └── AgentStatusPanel.tsx # Live agent status
├── lib/
│   └── utils.ts            # Utility functions
├── .env.local              # Environment variables
└── package.json
```

## Components

### ApprovalModal

Interactive modal for reviewing and approving/rejecting agent recommendations.

**Props**:
- `request`: Recommendation data with run_id and recommendations array
- `onApprove`: Callback for approval action
- `onReject`: Callback for rejection action

**Features**:
- Display multiple recommendations
- Priority badges (critical, high, medium, low)
- Confidence score display
- Next steps visualization
- Optional rejection reason input

### ToolCallCard

Displays agent tool invocations with arguments and results.

**Props**:
- `toolCall`: Tool call data with tool_call_id, tool_name, arguments, result

**Features**:
- Tool name display with icon
- Formatted JSON arguments
- Formatted JSON results
- Syntax highlighting

### AgentStatusPanel

Live status tracking for all agents in the system.

**Props**:
- `status`: Record of agent IDs to status strings

**Features**:
- Status indicators (idle, running, completed, error)
- Animated loading states
- Color-coded status
- Hover effects

## AG-UI Protocol Integration

The frontend communicates with the backend via the AG-UI Protocol:

### Event Types Handled

- `workflowStarted`: Workflow begins
- `agentStarted`: Individual agent starts
- `agentStream`: Agent streaming output
- `agentCompleted`: Agent finishes
- `approvalRequired`: User approval needed
- `workflowCompleted`: Workflow finishes
- `workflowError`: Error occurred

### Example Request

```typescript
POST /api/copilotkit
{
  "account_id": "ACC-123",
  "workflow": "account_analysis",
  "thread_id": "thread_abc123",
  "run_id": "run_xyz789"
}
```

### Example Response Stream

```
data: {"type":"workflowStarted","workflow":"account_analysis",...}

data: {"type":"agentStarted","agentId":"zoho_scout",...}

data: {"type":"agentStream","agentId":"zoho_scout","content":"Fetching..."}

data: {"type":"agentCompleted","agentId":"zoho_scout",...}

data: {"type":"approvalRequired","recommendationId":"REC-456",...}

data: {"type":"workflowCompleted","workflow":"account_analysis",...}
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t sergas-frontend .

# Run container
docker run -p 3000:3000 sergas-frontend
```

### Environment Variables for Production

Set these in your deployment platform:

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_API_TOKEN`: Authentication token

## Resources

- **CopilotKit Docs**: https://docs.copilotkit.ai
- **AG-UI Protocol**: https://docs.ag-ui.com
- **Next.js Docs**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs

## License

Proprietary - Sergas Account Manager System
