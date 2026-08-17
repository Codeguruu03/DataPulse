"""
CLI command for executing the Data Quality Gate.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from datapulse.quality.gate import DataQualityGate
from datapulse.config import settings

console = Console()


@click.command()
@click.option("--threshold", "-t", default=None, type=float, help="Minimum pass rate threshold % (default: 95.0)")
def validate(threshold: float):
    """Evaluates raw data quality, quarantines corrupted records, and enforces gate thresholds."""
    gate_threshold = threshold if threshold is not None else settings.QUALITY_THRESHOLD_PERCENT
    gate = DataQualityGate(quality_threshold=gate_threshold)

    with console.status(f"[bold cyan]Running Data Quality Gate checks (Threshold: {gate_threshold}%)..."):
        passed, summary, datasets = gate.evaluate_pipeline_batch()

    # Metric Table
    table = Table(title=f"Data Quality Gate Evaluation [{summary.run_id}]", border_style="cyan")
    table.add_column("Dataset", style="bold white")
    table.add_column("Check Name", style="cyan")
    table.add_column("Checked", justify="right")
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Pass Rate", justify="right", style="bold yellow")
    table.add_column("Status", justify="center")

    for m in summary.metrics:
        status_style = "[bold green]PASS[/bold green]" if m.status == "PASSED" else "[bold red]FAIL[/bold red]"
        table.add_row(
            m.dataset,
            m.check_name,
            f"{m.records_checked:,}",
            f"{m.records_passed:,}",
            f"{m.records_failed:,}",
            f"{m.pass_rate:.2f}%",
            status_style,
        )

    console.print(table)

    # Summary Panel
    gate_color = "green" if passed else "red"
    verdict = "[bold green]PASSED - Proceed to Spark Transformation & Warehouse[/bold green]" if passed else "[bold red]BLOCKED - Downstream Pipeline Halted[/bold red]"

    summary_text = (
        f"[bold]Batch Run ID:[/bold] {summary.run_id}\n"
        f"[bold]Total Ingested Records:[/bold] {summary.total_records_ingested:,}\n"
        f"[bold]Valid Records (Clean):[/bold] [green]{summary.total_records_valid:,}[/green]\n"
        f"[bold]Quarantined Records (Bad):[/bold] [red]{summary.total_records_quarantined:,}[/red]\n"
        f"[bold]Overall Quality Score:[/bold] [yellow]{summary.overall_quality_score:.2f}%[/yellow] (Threshold: {gate_threshold}%)\n"
        f"[bold]Quality Gate Verdict:[/bold] {verdict}"
    )

    console.print(Panel(summary_text, title="Quality Gate Summary", border_style=gate_color))
