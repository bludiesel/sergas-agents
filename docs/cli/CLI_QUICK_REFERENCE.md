# CLI Quick Reference Card

**Sergas Account Manager CLI - Version 1.0.0**

## Installation

```bash
# Automated setup
./scripts/cli_setup.sh

# Manual install
pip install click rich httpx
alias sergas="python -m src.cli.agent_cli"
```

## Commands

### Analyze Account

```bash
sergas analyze --account-id ACC-001
```

**Options:**
- `--api-url URL` - Backend URL (default: localhost:8000)
- `--auto-approve` - Skip approval prompts
- `--workflow TYPE` - Workflow type (default: account_analysis)
- `--timeout SECS` - Request timeout (default: 300)
- `--verbose` - Detailed output

**Examples:**
```bash
# Interactive analysis
sergas analyze --account-id ACC-001

# Automated mode
sergas analyze --account-id ACC-001 --auto-approve

# Production backend
sergas analyze --account-id ACC-001 --api-url https://api.prod.com

# Debug mode
sergas analyze --account-id ACC-001 --verbose
```

### Health Check

```bash
sergas health
```

**Options:**
- `--api-url URL` - Backend URL to check
- `--verbose` - Show detailed info

**Examples:**
```bash
# Local health check
sergas health

# Production check
sergas health --api-url https://api.prod.com
```

## Event Indicators

| Symbol | Meaning |
|--------|---------|
| ✓ | Success |
| ✗ | Error |
| → | Progress |
| 🔧 | Tool call |
| ⚠ | Warning/Approval |

## Common Workflows

### 1. Before Analysis
```bash
# Check backend health
sergas health || exit 1
```

### 2. Interactive Analysis
```bash
# Analyze with approval prompts
sergas analyze --account-id ACC-001
```

### 3. Automated Analysis
```bash
# Auto-approve for scripts
sergas analyze --account-id ACC-001 --auto-approve
```

### 4. Debug Issues
```bash
# Verbose output
sergas analyze --account-id ACC-001 --verbose
```

## Troubleshooting

### Cannot connect to backend
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify URL: `sergas health`
3. Check firewall settings

### Request timeout
1. Increase timeout: `--timeout 600`
2. Check backend logs
3. Verify network stability

### Installation issues
1. Use virtual environment: `source venv/bin/activate`
2. Check Python version: `python --version` (3.8+ required)
3. Manual install: `pip install click rich httpx`

## Files

| File | Purpose |
|------|---------|
| `src/cli/agent_cli.py` | Main CLI implementation |
| `scripts/cli_setup.sh` | Automated setup |
| `docs/guides/CLI_USAGE.md` | Complete user guide |
| `examples/cli_demo.sh` | Demo script |

## Support

- **Full Documentation:** `docs/guides/CLI_USAGE.md`
- **Implementation Details:** `docs/cli/CLI_IMPLEMENTATION_SUMMARY.md`
- **Demo:** `./examples/cli_demo.sh`
