"""
CLI command for launching the FastAPI and Dashboard web server.
"""

import click
import uvicorn
from rich.console import Console

from datapulse.config import settings

console = Console()


@click.command()
@click.option("--host", "-h", default=None, help="Host interface to bind (default: 0.0.0.0)")
@click.option("--port", "-p", default=None, type=int, help="Port to listen on (default: 8000)")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload for development.")
def serve(host: str, port: int, reload: bool):
    """Starts the DataPulse FastAPI Serving Layer and Interactive Web Dashboard."""
    server_host = host or settings.API_HOST
    server_port = port or settings.API_PORT

    console.print(f"[bold green]Starting DataPulse API & Interactive Dashboard server on [cyan]http://{server_host}:{server_port}[/cyan][/bold green]")
    console.print(f"  - Dashboard UI: [cyan]http://localhost:{server_port}/dashboard/index.html[/cyan]")
    console.print(f"  - Swagger Docs: [cyan]http://localhost:{server_port}/docs[/cyan]")
    console.print(f"  - Redoc:        [cyan]http://localhost:{server_port}/redoc[/cyan]")

    uvicorn.run(
        "datapulse.api.app:app",
        host=server_host,
        port=server_port,
        reload=reload,
    )
