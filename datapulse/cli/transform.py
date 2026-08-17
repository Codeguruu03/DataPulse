"""
CLI command for executing the Lakehouse Parquet Transformation Pipeline.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from datapulse.quality.gate import DataQualityGate
from datapulse.transforms.pipeline import LakehouseTransformPipeline

console = Console()


@click.command()
@click.option("--skip-gate", is_flag=True, default=False, help="Skip quality gate (not recommended for production).")
def transform(skip_gate: bool):
    """Transforms clean validated datasets into partitioned Parquet Lakehouse storage."""
    gate = DataQualityGate()

    with console.status("[bold cyan]Running Quality Gate & Transformation Pipeline..."):
        passed, gate_summary, datasets = gate.evaluate_pipeline_batch()

        if not passed and not skip_gate:
            console.print(
                f"[bold red]Quality Gate Failed ({gate_summary.overall_quality_score:.2f}% < {gate_summary.quality_threshold}%). Transformation aborted.[/bold red]"
            )
            return

        pipeline = LakehouseTransformPipeline()
        manifest = pipeline.process_and_publish_lake(datasets, run_id=gate_summary.run_id)

    # Display Parquet Publish Summary
    table = Table(title=f"Lakehouse Parquet Publication [{manifest['run_id']}]", border_style="green")
    table.add_column("Dataset Tier", style="bold white")
    table.add_column("Clean Records", justify="right", style="green")
    table.add_column("Lakehouse Target Path", style="dim cyan")

    table.add_row("Dimension Customers", f"{manifest['records_processed']['customers']:,}", manifest["paths"]["customers"])
    table.add_row("Dimension Products", f"{manifest['records_processed']['products']:,}", manifest["paths"]["products"])
    table.add_row("Fact Orders (Partitioned)", f"{manifest['records_processed']['orders']:,}", manifest["paths"]["orders"])

    console.print(table)

    summary_text = (
        f"[bold]Lakehouse Partitions Generated:[/bold] [yellow]{manifest['partitions_created']}[/yellow] partitions (year/month)\n"
        f"[bold]Data Lake Status:[/bold] [bold green]ONLINE & READY FOR WAREHOUSE INGESTION[/bold green]\n"
        f"[bold]Manifest:[/bold] [dim]{manifest['paths']['orders']}[/dim]"
    )
    console.print(Panel(summary_text, title="Lakehouse Parquet Storage", border_style="green"))
