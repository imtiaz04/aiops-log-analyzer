#!/usr/bin/env python3
"""
AIOps CLI — AI-powered Kubernetes anomaly detection, RCA, and remediation.
"""

import sys
import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text

# Allow imports from the AIOps directory regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import SCAN_PROMPT, RCA_PROMPT, SOP_PROMPT, FIX_PROMPT

console = Console()

BANNER = """
╔═══════════════════════════════════════════════════════╗
║          AIOps — Kubernetes Intelligence CLI          ║
║   Anomaly Detection │ RCA │ Auto-Remediation │ SOPs  ║
╚═══════════════════════════════════════════════════════╝
"""


def _stream_cb(role: str, content: str):
    if role == "tool":
        console.print(f"  [dim cyan]› {content}[/dim cyan]")
    elif role == "assistant":
        pass  # Final output handled separately


def _run_agent(prompt: str, model: str, read_only: bool, title: str):
    from agent import run_agent

    console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))

    with Live(Text("  Thinking...", style="bold yellow"), refresh_per_second=4) as live:
        def cb(role, content):
            if role == "tool":
                live.update(Text(f"  › {content[:80]}...", style="dim cyan") if len(content) > 80 else Text(f"  › {content}", style="dim cyan"))

        result = run_agent(prompt, model=model, read_only=read_only, stream_callback=cb)

    console.print()
    console.print(Panel(Markdown(result), title="[bold green]Results[/bold green]", border_style="green"))
    return result


@click.group()
@click.version_option("1.0.0", prog_name="aiops")
def cli():
    """AIOps CLI — AI-powered Kubernetes anomaly detection, RCA, and remediation for kind clusters."""
    console.print(BANNER, style="bold blue")


@cli.command()
@click.option("--model", default="llama3.1:latest", show_default=True, help="Ollama model to use.")
@click.option("--read-only", is_flag=True, default=False, help="Disable fix tools (scan + RCA only, no changes).")
def scan(model: str, read_only: bool):
    """
    Full cluster scan: detect anomalies, generate RCA, suggest and apply fixes, write SOP docs.

    Runs a comprehensive analysis of the kind cluster including:
    node health, pod failures, resource pressure, events, and logs.
    """
    if read_only:
        console.print("[yellow]Read-only mode: fix tools disabled.[/yellow]")

    _run_agent(
        prompt=SCAN_PROMPT,
        model=model,
        read_only=read_only,
        title="Full Cluster Scan — Anomaly Detection + RCA + Remediation"
    )

    console.print("\n[bold green]Scan complete.[/bold green] Check [cyan]docs/[/cyan] for generated SOP documents.")


@cli.command()
@click.argument("target")
@click.option("--model", default="llama3.1:latest", show_default=True, help="Ollama model to use.")
@click.option("--read-only", is_flag=True, default=False, help="Disable fix tools.")
def rca(target: str, model: str, read_only: bool):
    """
    Generate a Root Cause Analysis for a specific pod, deployment, or namespace.

    TARGET can be:  pod/<name>   deployment/<name>   namespace/<name>   node/<name>

    Examples:
      aiops rca pod/my-app-xyz-abc -n default
      aiops rca deployment/frontend
      aiops rca namespace/monitoring
    """
    prompt = RCA_PROMPT.format(target=target)
    _run_agent(
        prompt=prompt,
        model=model,
        read_only=read_only,
        title=f"Root Cause Analysis — {target}"
    )
    console.print("\n[bold green]RCA complete.[/bold green] Check [cyan]docs/[/cyan] for the generated runbook.")


@cli.command()
@click.argument("issue")
@click.option("--model", default="llama3.1:latest", show_default=True, help="Ollama model to use.")
@click.confirmation_option(prompt="This may apply changes to the cluster. Continue?")
def fix(issue: str, model: str):
    """
    Diagnose and fix a specific Kubernetes issue.

    ISSUE is a free-text description of the problem.

    Examples:
      aiops fix "frontend pods are in CrashLoopBackOff"
      aiops fix "database PVC is stuck in Pending"
      aiops fix "worker nodes are NotReady"
    """
    prompt = FIX_PROMPT.format(issue=issue)
    _run_agent(
        prompt=prompt,
        model=model,
        read_only=False,
        title=f"Fix: {issue}"
    )
    console.print("\n[bold green]Fix attempt complete.[/bold green] Check [cyan]docs/[/cyan] for the fix runbook.")


@cli.command()
@click.option("--model", default="llama3.1:latest", show_default=True, help="Ollama model to use.")
def sop(model: str):
    """
    Generate comprehensive SOPs and a README index based on cluster state.

    Scans the cluster and writes Standard Operating Procedures covering
    common failure scenarios, recovery procedures, and runbooks to docs/.
    """
    _run_agent(
        prompt=SOP_PROMPT,
        model=model,
        read_only=True,
        title="SOP Generation — Kubernetes Runbooks"
    )
    console.print("\n[bold green]SOPs generated.[/bold green] Check [cyan]docs/[/cyan] for all runbooks and the README index.")


@cli.command()
def docs():
    """List all generated SOP documents."""
    from tools.doc_tools import DOCS_DIR
    import os

    docs_path = DOCS_DIR
    if not os.path.exists(docs_path):
        console.print("[yellow]No docs/ directory found yet. Run 'aiops scan' or 'aiops sop' first.[/yellow]")
        return

    files = sorted(f for f in os.listdir(docs_path) if f.endswith(".md"))
    if not files:
        console.print("[yellow]No SOP documents found yet.[/yellow]")
        return

    console.print(Panel(
        "\n".join(f"  [cyan]{f}[/cyan]" for f in files),
        title="[bold]Generated SOP Documents[/bold]",
        border_style="blue"
    ))
    console.print(f"\nDocuments are in: [cyan]{docs_path}[/cyan]")


@cli.command()
def chat():
    """
    Interactive AIOps chat — ask anything about your cluster.

    A free-form conversational interface to the AIOps agent.
    """
    from agent import build_agent
    from langchain_core.messages import HumanMessage, AIMessage

    console.print("[bold cyan]AIOps Chat[/bold cyan] — type 'exit' to quit\n")
    agent = build_agent()
    history = []

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if user_input.lower() in ("exit", "quit", "bye"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        if not user_input:
            continue

        history.append(HumanMessage(content=user_input))

        with console.status("[bold yellow]Thinking...[/bold yellow]"):
            try:
                response = agent.invoke({"messages": history})
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                history.pop()
                continue

        for msg in reversed(response["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                console.print(f"\n[bold blue]AIOps:[/bold blue]")
                console.print(Markdown(msg.content))
                history.append(msg)
                break

        console.print()


if __name__ == "__main__":
    cli()
