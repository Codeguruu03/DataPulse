"""
CLI commands for Data Lineage, Schema Evolution, and Pipeline Replay.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
import pandas as pd

from datapulse.lineage.tracker import LineageTracker
from datapulse.evolution.detector import SchemaEvolutionDetector, EvolutionVerdict
from datapulse.replay.controller import PipelineReplayController

console = Console()


@click.command("lineage")
@click.option("--target", "-t", default="v_mart_monthly_revenue", help="Target node/metric to trace upstream.")
def show_lineage(target: str):
    """Traces upstream data lineage from BI/Marts back to raw source files."""
    tracker = LineageTracker()
    try:
        nodes = tracker.trace_upstream(target)
        table = Table(title=f"Data Lineage Provenance Tree: [{target}]", border_style="cyan")
        table.add_column("Tier", style="bold yellow")
        table.add_column("Node Name", style="bold cyan")
        table.add_column("Description", style="white")
        table.add_column("Upstream Dependencies", style="dim")

        for n in nodes:
            up_str = ", ".join(n["upstream"]) if n["upstream"] else "(Raw Source Ingestion)"
            table.add_row(f"[{n['tier']}]", n["name"], n["description"], up_str)

        console.print(table)
        console.print("\n[bold green]Mermaid Diagram Definition:[/bold green]")
        console.print(Panel(tracker.generate_mermaid_diagram(target), border_style="dim"))
    except KeyError as e:
        console.print(f"[bold red]Lineage node error: {e}[/bold red]")


@click.command("evolution")
@click.option("--dataset", "-d", default="orders", help="Dataset name to test (orders, customers, products).")
@click.option("--file", "-f", default=None, help="Path to incoming CSV file to evaluate schema against baseline.")
def check_evolution(dataset: str, file: str):
    """Evaluates incoming dataset for schema drift (compatible extension vs breaking changes)."""
    from datapulse.config import settings
    detector = SchemaEvolutionDetector()
    
    target_path = Path(file) if file else settings.RAW_DATA_PATH / f"{dataset}.csv"
    if not target_path.exists():
        console.print(f"[bold yellow]File not found: {target_path}. Run 'datapulse generate' first.[/bold yellow]")
        return

    df = pd.read_csv(target_path)
    report = detector.evaluate_schema(dataset, df)


    verdict_color = "green" if report.verdict != EvolutionVerdict.BREAKING_CHANGE else "red"
    summary_text = (
        f"[bold]Dataset:[/bold] {report.dataset}\n"
        f"[bold]Verdict:[/bold] [bold {verdict_color}]{report.verdict.value}[/bold {verdict_color}]\n"
        f"[bold]Pipeline Action:[/bold] [bold {verdict_color}]{report.action}[/bold {verdict_color}]\n"
        f"[bold]Details:[/bold] {report.message}\n"
        f"[bold]Added Columns:[/bold] {report.added_columns or 'None'}\n"
        f"[bold]Missing Required Columns:[/bold] {report.missing_required_columns or 'None'}"
    )

    console.print(Panel(summary_text, title="Schema Drift & Evolution Report", border_style=verdict_color))


@click.command("replay")
@click.option("--run-id", "-r", required=True, help="Run ID to replay from validation checkpoint.")
@click.option("--threshold", "-t", default=95.0, type=float, help="Quality threshold % for replay.")
def replay_pipeline(run_id: str, threshold: float):
    """Replays data pipeline execution starting from the validation checkpoint."""
    controller = PipelineReplayController()
    with console.status(f"[bold cyan]Replaying pipeline run [{run_id}]..."):
        res = controller.replay_from_validation(replay_run_id=run_id, threshold=threshold)

    is_success = res.get("status") == "SUCCESS"
    color = "green" if is_success else "red"
    summary_text = (
        f"[bold]Replay Run ID:[/bold] {res.get('replay_run_id')}\n"
        f"[bold]Checkpoint:[/bold] {res.get('checkpoint', 'VALIDATION')}\n"
        f"[bold]Status:[/bold] [bold {color}]{res.get('status')}[/bold {color}]\n"
        f"[bold]Quality Score:[/bold] {res.get('quality_score', 0.0):.2f}%\n"
        f"[bold]Orders Replayed:[/bold] {res.get('orders_replayed', 0):,}"
    )
    console.print(Panel(summary_text, title="Pipeline Replay Result", border_style=color))
