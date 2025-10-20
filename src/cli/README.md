# Sergas CLI Module

Production-ready command-line interface for Sergas Account Manager with live SSE event streaming.

## Overview

This module provides a terminal interface for account analysis with:
- Real-time event streaming from backend agents
- Rich visual feedback with colored output and progress tracking
- Interactive approval workflows
- Comprehensive error handling and recovery

## Quick Start

### Installation

```bash
# Automated setup
./scripts/cli_setup.sh

# Or manually
pip install click rich httpx
alias sergas="python -m src.cli.agent_cli"
```

### Basic Usage

```bash
# Check backend health
sergas health

# Analyze account (interactive)
sergas analyze --account-id ACC-001

# Auto-approve mode (for automation)
sergas analyze --account-id ACC-001 --auto-approve
```

## Module Structure

```
src/cli/
├── __init__.py          # Module exports
├── agent_cli.py         # Main CLI implementation (675 lines)
└── README.md            # This file
```

## Key Features

### 1. Rich Terminal UI
- Colored output with status indicators (✓✗→🔧⚠)
- Formatted tables for recommendations
- Progress bars with live updates
- Panels and borders for visual organization
- Markdown and JSON syntax highlighting

### 2. SSE Event Streaming
- Async httpx client for Server-Sent Events
- Real-time event parsing and display
- Connection management with retry
- Configurable timeout (default 300s)

### 3. Interactive Workflows
- Display recommendations in formatted tables
- Interactive approval prompts
- Auto-approve mode for automation
- Rejection reason collection
- Backend integration for approval responses

### 4. Error Handling
- Connection failures with helpful messages
- Timeout detection and reporting
- Invalid event format recovery
- Backend errors with stack traces
- Keyboard interrupt handling

## Commands

### `analyze`

Analyze account with AI agents and live event streaming.

```bash
sergas analyze --account-id ACC-001 [OPTIONS]
```

**Options:**
- `--api-url URL` - Backend URL (default: http://localhost:8000)
- `--auto-approve` - Skip approval prompts
- `--workflow TYPE` - Workflow type (default: account_analysis)
- `--timeout SECS` - Request timeout (default: 300)
- `--verbose` - Detailed output with event data

### `health`

Check backend health and connectivity.

```bash
sergas health [OPTIONS]
```

**Options:**
- `--api-url URL` - Backend URL to check
- `--verbose` - Show detailed health info

## Integration

### Backend Requirements

The CLI integrates with these backend endpoints:

- `POST /api/copilotkit` - SSE streaming for workflow execution
- `POST /api/approval/respond` - Approval response submission
- `GET /api/copilotkit/health` - Health check

### Event Types

Supported AG UI Protocol events:

| Event | Description |
|-------|-------------|
| `workflow_started` | Workflow begins |
| `agent_started` | Agent execution starts |
| `agent_stream` | Real-time agent progress |
| `tool_call` | Tool invocation |
| `tool_result` | Tool completion |
| `agent_completed` | Agent finishes |
| `approval_required` | Approval needed |
| `workflow_completed` | Workflow finishes |
| `workflow_error` | Workflow failure |
| `agent_error` | Agent failure |

## Architecture

### Event Flow

```
CLI → POST /api/copilotkit
    ↓
FastAPI Router
    ↓
Orchestrator.execute_with_events()
    ↓
ZohoDataScout → MemoryAnalyst → RecommendationAuthor
    ↓
AGUIEventEmitter.emit_*()
    ↓
SSE Stream → CLI
    ↓
Rich Terminal Display
    ↓
User Approval (if needed)
    ↓
POST /api/approval/respond
    ↓
Continue Workflow
```

### Class Structure

```python
class EventStats:
    """Track event statistics during execution"""
    workflow_started: bool
    agents_started: int
    agents_completed: int
    tool_calls: int
    approvals_requested: int
    errors: int

@click.group()
def cli():
    """Main CLI group"""
    pass

@cli.command()
def analyze(...):
    """Analyze account command"""
    asyncio.run(_analyze_account(...))

@cli.command()
def health(...):
    """Health check command"""
    # Sync HTTP request
```

## Dependencies

```python
click>=8.1.7      # CLI framework
rich>=13.7.0      # Terminal UI
httpx>=0.25.0     # Async HTTP client
```

## Development

### Testing

```bash
# Run demo script
./examples/cli_demo.sh

# Test with local backend
python -m src.cli.agent_cli analyze --account-id ACC-001 --verbose

# Test health check
python -m src.cli.agent_cli health
```

### Adding New Commands

```python
@cli.command()
@click.option('--param', help='Parameter description')
def new_command(param: str):
    """Command description for help text."""
    # Implementation
    pass
```

### Adding Event Types

Update `_handle_event()` function in `agent_cli.py`:

```python
elif event_type == "new_event_type":
    data = event.get("data", {})
    # Handle new event
    console.print(f"New event: {data}")
```

## Documentation

- **User Guide:** `docs/guides/CLI_USAGE.md` - Complete usage documentation
- **Implementation:** `docs/cli/CLI_IMPLEMENTATION_SUMMARY.md` - Technical details
- **Quick Reference:** `docs/cli/CLI_QUICK_REFERENCE.md` - Command cheat sheet
- **Examples:** `docs/cli/CLI_OUTPUT_EXAMPLES.md` - Visual output examples

## Production Considerations

### Security
- No hardcoded credentials
- HTTPS support for production URLs
- Timeout protection
- Input validation via Click

### Observability
- Event statistics tracking
- Real-time progress display
- Error reporting with stack traces
- Verbose mode for debugging

### Reliability
- Graceful error handling
- Connection retry capability
- Keyboard interrupt handling
- Clean resource cleanup

### Usability
- Comprehensive help text
- Clear error messages
- Rich visual feedback
- Automated setup
- Detailed documentation

## Troubleshooting

### Cannot connect to backend
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify URL: `sergas health`
3. Check firewall settings

### Request timeout
1. Increase timeout: `--timeout 600`
2. Check backend logs for slow operations
3. Verify network stability

### Installation issues
1. Use virtual environment: `source venv/bin/activate`
2. Check Python version: `python --version` (3.8+ required)
3. Manual install: `pip install click rich httpx`

## Support

For issues or questions:
1. Check full documentation in `docs/guides/CLI_USAGE.md`
2. Review troubleshooting section
3. Enable verbose mode: `--verbose`
4. Check backend logs

## License

Part of Sergas Account Manager - Week 8 Implementation
