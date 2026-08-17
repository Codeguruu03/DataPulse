"""
Main CLI entrypoint for DataPulse platform.
"""

import click
from rich.console import Console
from rich.panel import Panel
from datapulse import __version__
from datapulse.config import settings

console = Console()


def print_banner():
    banner_text = (
        f"[bold cyan]DataPulse[/bold cyan] [green]v{__version__}[/green]\n"
        "[dim]Data Quality-Aware Cloud Data Engineering Platform[/dim]\n"
        f"[yellow]Mode: {settings.DEPLOYMENT_MODE.upper()}[/yellow] | "
        f"[yellow]Storage: {settings.STORAGE_BACKEND.upper()}[/yellow] | "
        f"[yellow]Engine: {settings.PROCESSING_ENGINE.upper()}[/yellow]"
    )
    console.print(Panel(banner_text, border_style="cyan"))


@click.group()
@click.version_option(version=__version__)
def cli():
    """DataPulse Data Engineering Platform CLI."""
    pass


from datapulse.cli.generate import generate
from datapulse.cli.validate import validate
from datapulse.cli.transform import transform
from datapulse.cli.warehouse import warehouse
cli.add_command(generate)
cli.add_command(validate)
cli.add_command(transform)
cli.add_command(warehouse)


@cli.command()
def info():
    """Displays platform configuration and runtime status."""
    print_banner()
    console.print("[bold green]System Paths:[/bold green]")
    console.print(f"  - Base Dir: [cyan]{settings.BASE_DIR}[/cyan]")
    console.print(f"  - Raw Zone: [cyan]{settings.RAW_DATA_PATH}[/cyan]")
    console.print(f"  - Processed Lake: [cyan]{settings.PROCESSED_DATA_PATH}[/cyan]")
    console.print(f"  - Quarantine Zone: [cyan]{settings.QUARANTINE_DATA_PATH}[/cyan]")
    console.print("\n[bold green]Thresholds:[/bold green]")
    console.print(f"  - Quality Gate Min Pass Rate: [yellow]{settings.QUALITY_THRESHOLD_PERCENT}%[/yellow]")
    console.print(f"  - Max Duplicate Rate: [yellow]{settings.MAX_DUPLICATE_RATE * 100}%[/yellow]")


if __name__ == "__main__":
    cli()
