"""
CLI command group for managing DataPulse Data Warehouse operations.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from datapulse.warehouse.loader import WarehouseLoader
from datapulse.warehouse.migrations import SchemaMigrator

console = Console()


@click.group()
def warehouse():
    """Manages Star Schema Warehouse DDL, migrations, data loading, and marts."""
    pass


@warehouse.command("init")
def init_db():
    """Initializes Star Schema tables, DimDate records, and analytical mart views."""
    migrator = SchemaMigrator()
    with console.status("[bold cyan]Initializing warehouse Star Schema and views..."):
        migrator.init_schema()
    console.print("[bold green][OK] DataPulse Star Schema and Analytics Marts initialized.[/bold green]")


@warehouse.command("load")
def load_db():
    """Loads transformed Parquet Lakehouse datasets into Star Schema warehouse tables."""
    loader = WarehouseLoader()
    with console.status("[bold cyan]Loading Parquet data lakehouse into Star Schema tables..."):
        stats = loader.load_lakehouse_to_warehouse()

    table = Table(title="Warehouse Ingestion Summary", border_style="cyan")
    table.add_column("Table Name", style="bold white")
    table.add_column("Rows Loaded", justify="right", style="green")

    table.add_row("dim_customers", f"{stats['customers_loaded']:,}")
    table.add_row("dim_products", f"{stats['products_loaded']:,}")
    table.add_row("fact_orders", f"{stats['orders_loaded']:,}")
    table.add_row("data_quality_audit", f"{stats['audit_records_loaded']:,}")

    console.print(table)
    console.print("[bold green][OK] Star Schema Warehouse successfully refreshed![/bold green]")


@warehouse.command("mart")
@click.argument("name", default="monthly_revenue")
@click.option("--limit", "-l", default=10, help="Max rows to display.")
def query_mart(name: str, limit: int):
    """Queries an analytical data mart (monthly_revenue, top_products, customer_retention, quality_trends)."""
    loader = WarehouseLoader()
    try:
        df = loader.query_mart(name, limit=limit)
        if df.empty:
            console.print(f"[yellow]Mart 'v_mart_{name}' is empty. Run 'datapulse warehouse load' first.[/yellow]")
            return

        table = Table(title=f"Analytics Mart: v_mart_{name}", border_style="green")
        for col in df.columns:
            table.add_column(col, style="cyan")

        for _, row in df.iterrows():
            table.add_row(*[str(val) for val in row.values])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error querying mart '{name}': {e}[/bold red]")
