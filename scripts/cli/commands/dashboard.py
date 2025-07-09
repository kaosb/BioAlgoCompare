#!/usr/bin/env python3
"""
Dashboard command for BioAlgoCompare.

Provides real-time monitoring and visualization of running experiments.
"""

import click
from pathlib import Path


@click.command()
@click.option('--port', '-p', default=8050, type=int,
              help='Port for dashboard server')
@click.option('--host', '-h', default='127.0.0.1',
              help='Host for dashboard server')
@click.option('--debug/--no-debug', default=False,
              help='Run in debug mode')
def dashboard(port, host, debug):
    """Launch real-time monitoring dashboard."""
    click.echo(f"🖥️  Launching dashboard on {host}:{port}")
    
    try:
        from scripts.tools.run_dashboard import main as run_dashboard
        run_dashboard(host=host, port=port, debug=debug)
    except ImportError:
        click.echo("Dashboard functionality will be implemented")
        click.echo("Features:")
        click.echo("- Real-time algorithm progress")
        click.echo("- Live convergence plots")
        click.echo("- Resource usage monitoring")
        click.echo("- Result comparison")