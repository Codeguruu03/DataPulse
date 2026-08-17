"""
CLI command for triggering end-to-end DataPulse pipeline executions.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from datapulse.orchestration.runner import PipelineRunner
from datapulse.config import settings

console = Console()


@click.group()
def pipeline():
    """Manages and executes end-to-end DataPulse pipelines."""
    pass


@pipeline.command("run")
@click.option("--threshold", "-t", default=None, type=float, help="Quality threshold % (default: 95.0)")
@click.option("--anomaly-rate", "-a", default=0.05, type=float, help="Synthetic anomaly rate if generating raw data.")
@click.option("--no-gen", is_flag=True, default=False, help="Do not generate new synthetic raw data; use existing data in data/raw.")
def run_pipeline(threshold: float, anomaly_rate: float, no_gen: bool):
    """Executes the full end-to-end data engineering pipeline with quality gates."""
    gate_threshold = threshold if threshold is not None else settings.QUALITY_THRESHOLD_PERCENT
    runner = PipelineRunner(
        quality_threshold=gate_threshold,
        auto_generate=not no_gen,
        anomaly_rate=anomaly_rate,
    )

    with console.status("[bold cyan]Executing full DataPulse Data Engineering Pipeline..."):
        result = runner.run()

    # Stage Summary Table
    table = Table(title=f"Pipeline Execution Summary [{result['run_id']}]", border_style="cyan")
    table.add_column("Stage", style="bold white")
    table.add_column("Status", justify="center")
    table.add_column("Duration", justify="right", style="yellow")
    table.add_column("Details", style="dim")

    for stage_name, stage_info in result.get("stages", {}).items():
        st = stage_info.get("status", "UNKNOWN")
        st_style = "[bold green]SUCCESS[/bold green]" if "PASS" in st or "SUCC" in st else "[bold red]" + st + "[/bold red]"
        dur = f"{stage_info.get('duration_sec', 0.0)}s"

        details = ""
        if stage_name == "quality_gate":
            details = f"Score: {stage_info.get('quality_score')}% | Valid: {stage_info.get('total_valid'):,} | Quarantined: {stage_info.get('total_quarantined'):,}"
        elif stage_name == "transformation":
            details = f"Orders: {stage_info.get('orders_processed'):,} across {stage_info.get('partitions_created')} partitions"
        elif stage_name == "warehouse_load":
            stats = stage_info.get("load_stats", {})
            details = f"Customers: {stats.get('customers_loaded')}, Products: {stats.get('products_loaded')}, Orders: {stats.get('orders_loaded')}"
        elif stage_name == "ingestion":
            details = "Synthetic raw files generated and staged"

        table.add_row(stage_name.replace("_", " ").title(), st_style, dur, details)

    console.print(table)

    is_success = result["status"] == "SUCCESS"
    color = "green" if is_success else "red"
    summary_text = (
        f"[bold]Run ID:[/bold] {result['run_id']}\n"
        f"[bold]Total Execution Time:[/bold] {result.get('total_duration_sec', 0.0)} seconds\n"
        f"[bold]Final Pipeline Status:[/bold] [bold {color}]{result['status']}[/bold {color}]"
    )

    console.print(Panel(summary_text, title="DataPulse Run Result", border_style=color))
