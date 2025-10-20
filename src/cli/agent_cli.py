"""Sergas Account Manager CLI - Production-Ready Terminal Interface.

Week 8 Implementation - CLI with SSE streaming and interactive approval prompts.

Features:
- Live Server-Sent Events (SSE) streaming from backend
- Rich terminal UI with colored output, tables, and progress indicators
- Interactive approval prompts with recommendation display
- Auto-approval mode for automation
- Real-time event handling and error recovery
- Health check and connection validation

Architecture Alignment:
- SPARC V3 Refinement Phase (Week 8, Day 14)
- AG UI Protocol event handling
- Orchestrator integration via SSE
- Production-ready error handling

Usage:
    # Analyze account with interactive approval
    python -m src.cli.agent_cli analyze --account-id ACC-001

    # Auto-approve all recommendations
    python -m src.cli.agent_cli analyze --account-id ACC-001 --auto-approve

    # Custom backend URL
    python -m src.cli.agent_cli analyze --account-id ACC-001 --api-url https://api.example.com

    # Health check
    python -m src.cli.agent_cli health
"""

import asyncio
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box

# Initialize Rich console for styled output
console = Console()


class EventStats:
    """Track event statistics during workflow execution."""

    def __init__(self):
        self.workflow_started = False
        self.agents_started = 0
        self.agents_completed = 0
        self.tool_calls = 0
        self.approvals_requested = 0
        self.errors = 0
        self.start_time = datetime.now()

    def get_duration(self) -> float:
        """Get workflow duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def summary(self) -> str:
        """Get summary string."""
        return (
            f"Duration: {self.get_duration():.1f}s | "
            f"Agents: {self.agents_completed}/{self.agents_started} | "
            f"Tools: {self.tool_calls} | "
            f"Errors: {self.errors}"
        )


@click.group()
@click.version_option(version="1.0.0", prog_name="Sergas Agent CLI")
def cli():
    """Sergas Account Manager CLI - AI-powered account analysis.

    \b
    Features:
    - Live event streaming from AI agents
    - Interactive approval workflows
    - Rich terminal UI with progress tracking
    - Real-time account analysis

    \b
    Examples:
        sergas analyze --account-id ACC-001
        sergas analyze --account-id ACC-001 --auto-approve
        sergas health --api-url http://localhost:8000
    """
    pass


@cli.command()
@click.option(
    '--account-id',
    required=True,
    help='Zoho CRM account ID to analyze (e.g., ACC-001)'
)
@click.option(
    '--api-url',
    default='http://localhost:8000',
    help='Backend API URL (default: http://localhost:8000)'
)
@click.option(
    '--auto-approve',
    is_flag=True,
    help='Automatically approve all recommendations without prompting'
)
@click.option(
    '--workflow',
    default='account_analysis',
    help='Workflow to execute (default: account_analysis)'
)
@click.option(
    '--timeout',
    default=300,
    type=int,
    help='Request timeout in seconds (default: 300)'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Enable verbose output with detailed event data'
)
def analyze(
    account_id: str,
    api_url: str,
    auto_approve: bool,
    workflow: str,
    timeout: int,
    verbose: bool
):
    """Analyze account with AI agents and live event streaming.

    This command starts a multi-agent workflow to analyze the specified
    account, streaming real-time progress and requesting approval for
    generated recommendations.

    \b
    The workflow includes:
    1. ZohoDataScout - Fetch and analyze CRM data
    2. MemoryAnalyst - Retrieve historical context
    3. RecommendationAuthor - Generate actionable recommendations
    4. Approval workflow - Interactive or automatic approval

    \b
    Examples:
        # Interactive analysis with approval prompts
        sergas analyze --account-id ACC-001

        # Automated analysis with auto-approval
        sergas analyze --account-id ACC-001 --auto-approve

        # Verbose output for debugging
        sergas analyze --account-id ACC-001 --verbose
    """
    # Display header
    console.print()
    console.print(Panel.fit(
        f"[bold blue]Sergas Account Analysis[/bold blue]\n"
        f"Account ID: [cyan]{account_id}[/cyan]\n"
        f"Workflow: [magenta]{workflow}[/magenta]\n"
        f"API URL: [dim]{api_url}[/dim]",
        border_style="blue"
    ))
    console.print()

    if auto_approve:
        console.print("[yellow]⚠ Auto-approve mode enabled - all recommendations will be approved automatically[/yellow]")
        console.print()

    # Run async analysis
    try:
        asyncio.run(_analyze_account(
            account_id=account_id,
            api_url=api_url,
            auto_approve=auto_approve,
            workflow=workflow,
            timeout=timeout,
            verbose=verbose
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(1)


async def _analyze_account(
    account_id: str,
    api_url: str,
    auto_approve: bool,
    workflow: str,
    timeout: int,
    verbose: bool
):
    """Execute account analysis with SSE streaming.

    Args:
        account_id: Account to analyze
        api_url: Backend API URL
        auto_approve: Auto-approve recommendations
        workflow: Workflow type
        timeout: Request timeout in seconds
        verbose: Enable verbose output
    """
    thread_id = f"cli-{account_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_id = f"run-{datetime.now().timestamp():.0f}"

    # Track statistics
    stats = EventStats()

    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[cyan]{task.fields[status]}"),
        console=console,
        transient=False
    ) as progress:

        main_task = progress.add_task(
            "[cyan]Connecting to backend...",
            total=None,
            status="Initializing"
        )

        async with httpx.AsyncClient() as client:
            try:
                # Start SSE stream
                progress.update(main_task, description="[cyan]Starting workflow...", status="Connecting")

                async with client.stream(
                    "POST",
                    f"{api_url}/api/copilotkit",
                    json={
                        "thread_id": thread_id,
                        "run_id": run_id,
                        "account_id": account_id,
                        "workflow": workflow,
                        "options": {
                            "auto_approve": auto_approve,
                            "cli_mode": True
                        }
                    },
                    headers={"Accept": "text/event-stream"},
                    timeout=timeout
                ) as response:

                    if response.status_code != 200:
                        console.print(f"[bold red]Error:[/bold red] HTTP {response.status_code}")
                        error_text = await response.aread()
                        console.print(f"[dim]{error_text.decode()}[/dim]")
                        return

                    progress.update(main_task, description="[green]Workflow active", status="Streaming")

                    # Process SSE events
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue

                        event_data = line[5:].strip()
                        if not event_data:
                            continue

                        try:
                            event = json.loads(event_data)

                            # Handle event
                            await _handle_event(
                                event=event,
                                client=client,
                                api_url=api_url,
                                run_id=run_id,
                                auto_approve=auto_approve,
                                verbose=verbose,
                                stats=stats,
                                progress=progress,
                                main_task=main_task
                            )

                        except json.JSONDecodeError as e:
                            if verbose:
                                console.print(f"[yellow]Warning: Invalid JSON event: {event_data[:100]}...[/yellow]")

                    # Update final status
                    progress.update(
                        main_task,
                        description=f"[green]✓ Workflow completed",
                        status=stats.summary()
                    )

            except httpx.TimeoutException:
                progress.update(main_task, description="[bold red]✗ Request timeout", status="Failed")
                console.print(f"[bold red]Error:[/bold red] Request timeout after {timeout}s")

            except httpx.ConnectError:
                progress.update(main_task, description="[bold red]✗ Connection failed", status="Failed")
                console.print(f"[bold red]Error:[/bold red] Cannot connect to {api_url}")
                console.print("[dim]Ensure backend is running and accessible[/dim]")

            except Exception as e:
                progress.update(main_task, description="[bold red]✗ Error", status="Failed")
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                if verbose:
                    console.print_exception()


async def _handle_event(
    event: Dict[str, Any],
    client: httpx.AsyncClient,
    api_url: str,
    run_id: str,
    auto_approve: bool,
    verbose: bool,
    stats: EventStats,
    progress: Progress,
    main_task
):
    """Handle individual SSE events.

    Args:
        event: Parsed event data
        client: HTTP client for responses
        api_url: Backend API URL
        run_id: Current run ID
        auto_approve: Auto-approve flag
        verbose: Verbose output flag
        stats: Event statistics tracker
        progress: Rich progress instance
        main_task: Main progress task ID
    """
    event_type = event.get("type") or event.get("event")
    data = event.get("data", {})

    if verbose:
        console.print(f"[dim]Event: {event_type}[/dim]")

    # Workflow started
    if event_type == "workflow_started":
        stats.workflow_started = True
        workflow_name = data.get("workflow", "unknown")
        console.print(f"[bold green]✓[/bold green] Workflow started: [cyan]{workflow_name}[/cyan]")
        progress.update(main_task, description=f"[cyan]Running {workflow_name}...", status="Active")

    # Agent started
    elif event_type == "agent_started":
        stats.agents_started += 1
        agent_id = data.get("agent_id") or data.get("agentId", "unknown")
        task = data.get("task", "Processing...")
        step = data.get("step", stats.agents_started)

        console.print(f"\n[bold cyan]→ Step {step}:[/bold cyan] {agent_id}")
        console.print(f"  [dim]{task}[/dim]")

        progress.update(main_task, description=f"[cyan]Step {step}: {agent_id}", status=f"{stats.agents_completed}/{stats.agents_started} agents")

    # Agent stream (real-time progress)
    elif event_type == "agent_stream":
        agent_id = data.get("agent_id") or data.get("agentId", "unknown")
        content = data.get("content", "")
        content_type = data.get("content_type", "text")

        if content:
            console.print(f"  [dim]→[/dim] {content}")

    # Tool call
    elif event_type == "tool_call":
        stats.tool_calls += 1
        tool_name = data.get("tool_name") or data.get("toolName", "unknown")
        console.print(f"  [yellow]🔧[/yellow] Tool: {tool_name}")

    # Tool result
    elif event_type == "tool_result":
        result_status = data.get("status", "completed")
        if result_status == "success":
            console.print(f"  [green]✓[/green] Tool completed")
        else:
            console.print(f"  [yellow]⚠[/yellow] Tool {result_status}")

    # Agent completed
    elif event_type == "agent_completed":
        stats.agents_completed += 1
        agent_id = data.get("agent_id") or data.get("agentId", "unknown")
        output = data.get("output", {})

        console.print(f"[bold green]✓[/bold green] {agent_id} completed")

        if verbose and output:
            console.print(Panel(
                json.dumps(output, indent=2),
                title=f"{agent_id} output",
                border_style="green"
            ))

        progress.update(main_task, status=f"{stats.agents_completed}/{stats.agents_started} agents")

    # Approval required
    elif event_type == "approval_required":
        stats.approvals_requested += 1
        recommendations = data.get("recommendations", [])
        recommendation = data.get("recommendation", {})

        # Handle single recommendation or list
        if not recommendations and recommendation:
            recommendations = [recommendation]

        # Display recommendations
        console.print()
        console.print("[bold yellow]⚠ APPROVAL REQUIRED[/bold yellow]")
        console.print()

        if recommendations:
            # Create table
            table = Table(
                title="Generated Recommendations",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Category", style="blue")
            table.add_column("Title", style="green")
            table.add_column("Priority", style="yellow")
            table.add_column("Confidence", justify="right", style="magenta")

            for rec in recommendations:
                rec_id = rec.get("recommendation_id", "N/A")
                category = rec.get("category") or rec.get("action_type", "N/A")
                title = rec.get("title") or rec.get("recommendation", "N/A")
                priority = rec.get("priority", "medium")
                confidence = rec.get("confidence_score", 0)

                # Truncate long titles
                if len(title) > 60:
                    title = title[:57] + "..."

                table.add_row(
                    rec_id[:12],
                    category,
                    title,
                    priority.upper(),
                    f"{confidence}%"
                )

            console.print(table)
            console.print()

            # Show detailed first recommendation
            if recommendations and verbose:
                first_rec = recommendations[0]
                details = f"""
**Reasoning:** {first_rec.get('reasoning', 'N/A')}

**Expected Impact:** {first_rec.get('expected_impact', 'N/A')}

**Next Steps:** {first_rec.get('next_steps', 'Review and implement')}
"""
                console.print(Panel(
                    Markdown(details),
                    title="Recommendation Details",
                    border_style="yellow"
                ))
                console.print()

        # Get approval
        approved = False
        reason = ""

        if auto_approve:
            approved = True
            console.print("[green]✓ Auto-approving recommendations...[/green]")
        else:
            # Interactive prompt
            approved = click.confirm(
                "Do you approve these recommendations?",
                default=True
            )

            if not approved:
                reason = click.prompt(
                    "Please provide a reason for rejection (optional)",
                    default="User rejected",
                    show_default=False
                )

        # Send approval response
        try:
            response = await client.post(
                f"{api_url}/api/approval/respond",
                json={
                    "run_id": run_id,
                    "approved": approved,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10.0
            )

            if response.status_code == 200:
                if approved:
                    console.print("[bold green]✓[/bold green] Recommendations approved")
                else:
                    console.print(f"[bold red]✗[/bold red] Recommendations rejected: {reason}")
            else:
                console.print(f"[yellow]⚠ Warning: Approval response failed (HTTP {response.status_code})[/yellow]")

        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Failed to send approval response: {str(e)}[/yellow]")

        console.print()

    # Workflow completed
    elif event_type == "workflow_completed":
        output = data.get("output") or data.get("final_output", {})
        status = output.get("status", "completed")

        console.print()
        console.print("[bold green]✓ WORKFLOW COMPLETED[/bold green]")
        console.print()

        # Display summary
        summary_panel = f"""
**Status:** {status.upper()}
**Account ID:** {output.get('account_id', 'N/A')}
**Workflow:** {output.get('workflow', 'N/A')}
**Duration:** {stats.get_duration():.1f}s

**Execution Summary:**
- Agents completed: {stats.agents_completed}
- Tool calls: {stats.tool_calls}
- Approvals: {stats.approvals_requested}
"""

        if "execution_summary" in output:
            exec_summary = output["execution_summary"]
            summary_panel += f"""
**Results:**
- Zoho data fetched: {'✓' if exec_summary.get('zoho_data_fetched') else '✗'}
- Historical context: {'✓' if exec_summary.get('historical_context_retrieved') else '✗'}
- Recommendations: {exec_summary.get('recommendations_generated', 0)}
- Risk level: {exec_summary.get('risk_level', 'N/A')}
"""

        console.print(Panel(
            Markdown(summary_panel),
            title="Workflow Summary",
            border_style="green",
            box=box.DOUBLE
        ))

        # Display full output in verbose mode
        if verbose:
            console.print()
            console.print(Panel(
                Syntax(json.dumps(output, indent=2), "json", theme="monokai"),
                title="Complete Output",
                border_style="dim"
            ))

    # Workflow error
    elif event_type == "workflow_error" or event_type == "agent_error":
        stats.errors += 1
        error = data.get("error") or data.get("error_message", "Unknown error")
        error_type = data.get("error_type", "UnknownError")

        console.print()
        console.print(f"[bold red]✗ ERROR:[/bold red] {error_type}")
        console.print(f"[red]{error}[/red]")

        if verbose and "stack_trace" in data:
            console.print()
            console.print(Panel(
                data["stack_trace"],
                title="Stack Trace",
                border_style="red"
            ))

        console.print()
        progress.update(main_task, description="[red]✗ Workflow failed", status="Error")


@cli.command()
@click.option(
    '--api-url',
    default='http://localhost:8000',
    help='Backend API URL (default: http://localhost:8000)'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Show detailed health information'
)
def health(api_url: str, verbose: bool):
    """Check backend health status and connectivity.

    Verifies that the backend API is running and accessible.
    Useful for troubleshooting connection issues.

    \b
    Examples:
        sergas health
        sergas health --api-url https://api.example.com
        sergas health --verbose
    """
    console.print()
    console.print(f"[cyan]Checking health of:[/cyan] {api_url}")
    console.print()

    try:
        response = httpx.get(
            f"{api_url}/api/copilotkit/health",
            timeout=5.0
        )

        if response.status_code == 200:
            data = response.json()

            console.print("[bold green]✓ Backend is healthy[/bold green]")
            console.print()

            if verbose:
                table = Table(show_header=False, box=box.SIMPLE)
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Status", data.get("status", "unknown"))
                table.add_row("Service", data.get("service", "unknown"))
                table.add_row("Timestamp", data.get("timestamp", "unknown"))

                console.print(table)
                console.print()
        else:
            console.print(f"[bold red]✗ Backend returned HTTP {response.status_code}[/bold red]")
            if verbose:
                console.print(f"[dim]{response.text}[/dim]")

    except httpx.ConnectError:
        console.print(f"[bold red]✗ Cannot connect to backend[/bold red]")
        console.print(f"[dim]URL: {api_url}[/dim]")
        console.print()
        console.print("[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Ensure backend is running")
        console.print("  2. Check URL is correct")
        console.print("  3. Verify firewall settings")
        sys.exit(1)

    except httpx.TimeoutException:
        console.print(f"[bold red]✗ Request timeout[/bold red]")
        console.print("[dim]Backend did not respond within 5 seconds[/dim]")
        sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    cli()
