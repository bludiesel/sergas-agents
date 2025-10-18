# Agent Configuration Templates

Pre-configured agent profiles for common roles and specializations.

## Usage

These JSON files define reusable agent configurations that can be used with the `agent_spawn` MCP tool:

```javascript
// Load configuration
const backendDevConfig = require('./backend_developer.json');

// Spawn agent with config
mcp__claude-flow__agent_spawn(backendDevConfig);
```

## Available Configurations

- `backend_developer.json` - Python/FastAPI backend specialist
- `frontend_developer.json` - React/TypeScript frontend specialist
- `database_specialist.json` - PostgreSQL database expert
- `qa_engineer.json` - Testing and quality assurance
- `security_reviewer.json` - Security audit specialist
- `zoho_specialist.json` - Zoho CRM integration expert
- `code_reviewer.json` - General code review specialist

## Customization

Copy and modify these templates for project-specific needs. Key fields:

- `type`: Agent category (coder, analyst, reviewer, etc.)
- `name`: Display name for the agent
- `capabilities`: Array of specific skills and tools
- `priority`: Default task priority level
- `resources`: Resource allocation hints
