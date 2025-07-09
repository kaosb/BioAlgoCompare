#!/usr/bin/env python3
"""
BioAlgoCompare - Unified CLI Entry Point

This is the main entry point for all BioAlgoCompare commands.
It provides a clean, organized interface for running algorithms,
benchmarking, analysis, and other operations.
"""

import click
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import commands
from scripts.cli.commands import run, benchmark, analyze, massive, dashboard, publish, export, reproducibility, metadata, quality, environment, standards, monitor, optimize


@click.group()
@click.version_option(version='2.0.0', prog_name='BioAlgoCompare')
def cli():
    """
    BioAlgoCompare - Bio-inspired Algorithm Evaluation Platform
    
    A comprehensive platform for rigorous statistical evaluation of bio-inspired
    algorithms on optimization problems, with focus on the Vehicle Routing Problem.
    
    Features:
    - 18 state-of-the-art bio-inspired algorithms
    - Complete reproducibility with metadata capture
    - Statistical analysis and visualization
    - Massive benchmarking capabilities (1000+ runs)
    - Real-time monitoring dashboard
    
    For detailed help on any command, use: bioalgo COMMAND --help
    """
    pass


# Add commands to the CLI group
cli.add_command(run.run)
cli.add_command(benchmark.benchmark)
cli.add_command(analyze.analyze)
cli.add_command(massive.massive)
cli.add_command(dashboard.dashboard)
cli.add_command(publish.publish)
cli.add_command(export.export)
cli.add_command(reproducibility.reproducibility)
cli.add_command(metadata.metadata)
cli.add_command(quality.quality)
cli.add_command(environment.environment)
cli.add_command(standards.standards)
cli.add_command(monitor.monitor)
cli.add_command(optimize.optimize)


# Utility commands group
@cli.group()
def tools():
    """Utility tools for maintenance and management."""
    pass


@tools.command()
@click.option('--target', type=click.Choice(['results', 'checkpoints', 'logs', 'all']), 
              default='all', help='What to clean')
@click.option('--older-than', type=int, help='Clean files older than N days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without deleting')
def clean(target, older_than, dry_run):
    """Clean temporary files and old results."""
    from scripts.tools.clean import clean_files
    clean_files(target, older_than, dry_run)


@tools.command()
@click.argument('algorithm')
@click.option('--check-only', is_flag=True, help='Only check, do not migrate')
def migrate(algorithm, check_only):
    """Migrate an algorithm to the latest version."""
    from scripts.tools.migrate_algorithm import migrate_algorithm
    migrate_algorithm(algorithm, check_only)


@tools.command()
def check_installation():
    """Verify installation and dependencies."""
    click.echo("🔍 Checking BioAlgoCompare installation...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        click.echo(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        click.echo(f"❌ Python {python_version.major}.{python_version.minor} (requires 3.8+)")
    
    # Check key dependencies
    try:
        import numpy
        click.echo(f"✅ NumPy {numpy.__version__}")
    except ImportError:
        click.echo("❌ NumPy not installed")
    
    try:
        import pandas
        click.echo(f"✅ Pandas {pandas.__version__}")
    except ImportError:
        click.echo("❌ Pandas not installed")
    
    try:
        import matplotlib
        click.echo(f"✅ Matplotlib {matplotlib.__version__}")
    except ImportError:
        click.echo("❌ Matplotlib not installed")
    
    # Check data directory
    data_dir = Path("data/vrp")
    if data_dir.exists():
        vrp_files = list(data_dir.glob("*.vrp"))
        click.echo(f"✅ VRP instances found: {len(vrp_files)}")
    else:
        click.echo("❌ VRP data directory not found")
    
    # Check if package is installed
    try:
        import bioalgocompare
        click.echo("✅ BioAlgoCompare package installed")
    except ImportError:
        click.echo("⚠️  BioAlgoCompare not installed (run: pip install -e .)")


# Info commands group
@cli.group()
def info():
    """Information and documentation commands."""
    pass


@info.command()
def algorithms():
    """List all available algorithms with details."""
    from scripts.config.algorithms import ALGORITHMS_INFO
    
    click.echo("\n🧬 Available Bio-inspired Algorithms:\n")
    click.echo(f"{'Name':<6} {'Full Name':<40} {'Year':<6} {'Version'}")
    click.echo("-" * 70)
    
    for algo, info in sorted(ALGORITHMS_INFO.items()):
        click.echo(f"{algo:<6} {info['name']:<40} {info['year']:<6} {info['version']}")
    
    click.echo(f"\nTotal: {len(ALGORITHMS_INFO)} algorithms")


@info.command()
def instances():
    """List available VRP instances."""
    from pathlib import Path
    
    data_dir = Path("data/vrp")
    if not data_dir.exists():
        click.echo("❌ VRP data directory not found")
        return
    
    instances = sorted(data_dir.glob("*.vrp"))
    
    click.echo("\n📦 Available VRP Instances:\n")
    click.echo(f"{'Instance':<20} {'Size':<15} {'Optimal'}")
    click.echo("-" * 50)
    
    from utils.benchmarking import OPTIMAL_VALUES
    
    for instance in instances:
        name = instance.stem
        size = instance.stat().st_size // 1024  # KB
        optimal = OPTIMAL_VALUES.get(name, "Unknown")
        click.echo(f"{name:<20} {f'{size} KB':<15} {optimal}")
    
    click.echo(f"\nTotal: {len(instances)} instances")


@info.command()
def config():
    """Show current configuration."""
    import json
    from pathlib import Path
    
    click.echo("\n⚙️  BioAlgoCompare Configuration:\n")
    
    # Check for config file
    config_file = Path.home() / ".bioalgocompare" / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            config_data = json.load(f)
        click.echo("Configuration file found:")
        click.echo(json.dumps(config_data, indent=2))
    else:
        click.echo("No user configuration file found (using defaults)")
    
    # Show environment variables
    click.echo("\nEnvironment variables:")
    for key, value in os.environ.items():
        if key.startswith("BIOALGO_"):
            click.echo(f"  {key}: {value}")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()