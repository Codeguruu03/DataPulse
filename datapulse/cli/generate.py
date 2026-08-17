"""
CLI command for generating synthetic enterprise dataset.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from datapulse.generator.generator import DataPulseGenerator
from datapulse.config import settings

console = Console()


@click.command()
@click.option("--orders", "-o", default=5000, help="Number of order transactions to generate.")
@click.option("--customers", "-c", default=500, help="Number of customer profiles to generate.")
@click.option("--anomaly-rate", "-a", default=0.05, help="Proportion of corrupted/anomalous records (0.0 to 1.0).")
@click.option("--output-dir", "-d", default=None, help="Custom output directory for raw CSV files.")
def generate(orders: int, customers: int, anomaly_rate: float, output_dir: str):
    """Generates synthetic e-commerce/sales datasets with realistic flaws for quality testing."""
    target_path = Path(output_dir) if output_dir else settings.RAW_DATA_PATH
    generator = DataPulseGenerator(anomaly_rate=anomaly_rate)

    with console.status(f"[bold green]Generating datasets with {anomaly_rate * 100:.1f}% anomaly rate..."):
        c_path, p_path, o_path = generator.generate_all_and_save(
            output_dir=target_path,
            num_orders=orders,
            num_customers=customers,
        )

    table = Table(title="Generated Raw Datasets", border_style="cyan")
    table.add_column("Dataset", style="bold white")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Anomaly Rate", justify="right", style="yellow")
    table.add_column("File Location", style="dim")

    table.add_row("Customers", str(customers), f"{anomaly_rate * 50:.1f}%", str(c_path))
    table.add_row("Products", "12", "0.0%", str(p_path))
    table.add_row("Orders", str(orders), f"{anomaly_rate * 100:.1f}%", str(o_path))

    console.print(table)
    console.print(f"[bold green]✔ Data successfully written to raw data zone: [cyan]{target_path}[/cyan][/bold green]")
