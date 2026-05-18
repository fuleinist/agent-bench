#!/usr/bin/env python3
"""CLI for agent-bench."""

import os
import sys
from pathlib import Path

import click

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_bench import __version__
from agent_bench.adapters import ClaudeCodeAdapter, GenericCommandAdapter, get_adapter
from agent_bench.models import Task
from agent_bench.runner import Runner
from agent_bench.store import Store
from agent_bench.dashboard import Dashboard


@click.group()
@click.version_option(version=__version__)
def cli():
    """Agent-Bench: Benchmark suite for coding agents."""
    pass


@cli.command()
@click.argument("task_id", required=False)
@click.option("--all", "run_all", is_flag=True, help="Run all tasks")
@click.option("--filter", "category", default=None, help="Filter by category")
@click.option("--agent", default="generic", help="Agent to use (default: generic)")
@click.option("--timeout", default=None, type=int, help="Timeout per task in seconds")
@click.option("--verbose", "verbose", is_flag=True, help="Show detailed task output (stdout/stderr)")
def run(task_id: str, run_all: bool, category: str, agent: str, timeout: int, verbose: bool):
    """Run benchmark tasks."""
    runner = Runner()
    store = Store()

    # Load tasks
    tasks = runner.load_tasks()
    if not tasks:
        click.echo("No tasks found in tasks/ directory.", err=True)
        return

    # Filter tasks
    if category:
        tasks = [t for t in tasks if t.category == category]
    if task_id and not run_all:
        tasks = [t for t in tasks if t.id == task_id]

    if not tasks:
        click.echo("No matching tasks found.", err=True)
        return

    click.echo(f"Running {len(tasks)} task(s) with {agent}...")

    # Get adapter
    adapter = get_adapter(agent)
    if not adapter:
        click.echo(f"Unknown agent: {agent}", err=True)
        return

    if not adapter.is_available():
        click.echo(f"Agent '{agent}' is not available. Install it first.", err=True)
        return

    # Create run
    run_id = store.create_run(agent, len(tasks))
    passed = 0
    failed = 0

    for task in tasks:
        click.echo(f"\n  [{task.id}] {task.name}...", nl=False)
        result = runner.run_task(task, agent)

        store.save_result(result, run_id)

        if result.status.value == "passed":
            click.echo(f" {click.style('PASS', fg='green')}")
            passed += 1
        else:
            click.echo(f" {click.style(result.status.value.upper(), fg='red')}")
            if verbose and result.stdout:
                click.echo(f"    stdout: {result.stdout[:500]}")
            if verbose and result.stderr:
                click.echo(f"    stderr: {result.stderr[:500]}")
            if verbose and result.error:
                click.echo(f"    error: {result.error}")
            failed += 1

    # Update run summary
    duration = sum(
        r.duration for r in store.get_results_by_run(run_id)
    )
    store.update_run(run_id, passed, failed, duration)

    click.echo(f"\n{click.style('✓', fg='green')} {passed}/{len(tasks)} passed")
    if failed > 0:
        click.echo(f"{click.style('✗', fg='red')} {failed}/{len(tasks)} failed")


@cli.command()
@click.option("--category", default=None, help="Filter by category")
def list(category: str):
    """List available benchmark tasks."""
    runner = Runner()
    tasks = runner.load_tasks()

    if category:
        tasks = [t for t in tasks if t.category == category]

    if not tasks:
        click.echo("No tasks found.")
        return

    click.echo(f"{len(tasks)} task(s):\n")
    for task in tasks:
        diff_color = {"easy": "green", "medium": "yellow", "hard": "red"}.get(
            task.difficulty, "white"
        )
        click.echo(
            f"  [{task.id}] {task.name} "
            f"({click.style(task.difficulty, fg=diff_color)}, {task.category})"
        )


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
def report(fmt: str, output: str):
    """Generate benchmark report."""
    store = Store()

    if fmt == "json":
        data = store.export_json()
    else:
        data = store.export_csv()

    if output:
        Path(output).write_text(data)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(data)


@cli.command()
@click.option("--output", "-o", default="dashboard.html", help="Output file path")
def serve(output: str):
    """Generate and save HTML dashboard."""
    dashboard = Dashboard()
    path = dashboard.save(output)
    click.echo(f"Dashboard saved to {path}")
    click.echo(f"Open {path} in a browser to view results.")


@cli.command()
def agents():
    """List available agents and their status."""
    adapters = [
        ClaudeCodeAdapter(),
        GenericCommandAdapter("", "generic"),
    ]

    click.echo("Available agents:\n")
    for adapter in adapters:
        status = click.style("available", fg="green") if adapter.is_available() else click.style(
            "not installed", fg="red"
        )
        click.echo(f"  {adapter.name}: {status}")


def main():
    cli()


if __name__ == "__main__":
    main()