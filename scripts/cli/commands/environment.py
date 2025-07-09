"""
Environment management commands for BioAlgoCompare.
"""

import click
import subprocess
import sys
import os
import platform
import shutil
from pathlib import Path
import json
from datetime import datetime


@click.group()
def environment():
    """Development environment management commands."""
    pass


@environment.command()
@click.option('--minimal', is_flag=True, help='Minimal setup (no optional tools)')
@click.option('--docker', is_flag=True, help='Setup for Docker development')
@click.option('--force', is_flag=True, help='Force reinstall everything')
def setup(minimal, docker, force):
    """
    Setup development environment.
    
    Configures a complete development environment with all necessary
    tools, dependencies, and configurations.
    
    Examples:
    
        # Full setup
        bioalgo environment setup
        
        # Minimal setup (faster)
        bioalgo environment setup --minimal
        
        # Setup for Docker development
        bioalgo environment setup --docker
    """
    from scripts.setup_environment import EnvironmentSetup
    
    click.echo("🚀 Setting up BioAlgoCompare development environment...")
    
    setup_manager = EnvironmentSetup()
    
    if force:
        click.echo("⚠️  Force mode: reinstalling everything")
    
    # Run setup
    success = setup_manager.setup()
    
    if success:
        click.echo("\n✅ Environment setup complete!")
        click.echo("\n📚 Next steps:")
        click.echo("  1. Activate virtual environment:")
        if platform.system() == "Windows":
            click.echo("     .\\venv\\Scripts\\activate")
        else:
            click.echo("     source venv/bin/activate")
        click.echo("  2. Run quality checks:")
        click.echo("     bioalgo quality check")
        click.echo("  3. Start developing!")
    else:
        click.echo("\n❌ Setup failed. Check errors above.", err=True)
        sys.exit(1)


@environment.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
def info(format):
    """
    Show environment information.
    
    Displays detailed information about the current development
    environment including Python version, installed packages,
    and system details.
    """
    info_data = {
        'timestamp': datetime.now().isoformat(),
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        },
        'python': {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'executable': sys.executable,
            'prefix': sys.prefix
        },
        'environment': {
            'virtual_env': os.environ.get('VIRTUAL_ENV', 'Not in virtual environment'),
            'pythonpath': os.environ.get('PYTHONPATH', 'Not set'),
            'bioalgo_env': os.environ.get('BIOALGO_ENV', 'Not set')
        },
        'paths': {
            'cwd': os.getcwd(),
            'project_root': str(Path(__file__).parent.parent.parent.parent),
            'data_path': str(Path('data').absolute()) if Path('data').exists() else 'Not found',
            'results_path': str(Path('results').absolute()) if Path('results').exists() else 'Not found'
        }
    }
    
    if format == 'json':
        click.echo(json.dumps(info_data, indent=2))
    else:
        click.echo("\n🔍 BioAlgoCompare Environment Information\n")
        click.echo("=" * 60)
        
        click.echo("\n📊 System:")
        click.echo(f"  OS: {info_data['platform']['system']} {info_data['platform']['release']}")
        click.echo(f"  Machine: {info_data['platform']['machine']}")
        
        click.echo("\n🐍 Python:")
        click.echo(f"  Version: {info_data['python']['version']}")
        click.echo(f"  Implementation: {info_data['python']['implementation']}")
        click.echo(f"  Executable: {info_data['python']['executable']}")
        
        click.echo("\n🌍 Environment:")
        for key, value in info_data['environment'].items():
            click.echo(f"  {key}: {value}")
        
        click.echo("\n📁 Paths:")
        for key, value in info_data['paths'].items():
            click.echo(f"  {key}: {value}")
        
        # Check installed packages
        click.echo("\n📦 Key Packages:")
        packages = ['numpy', 'pandas', 'matplotlib', 'ruff', 'pytest', 'click']
        for package in packages:
            try:
                __import__(package)
                module = sys.modules[package]
                version = getattr(module, '__version__', 'installed')
                click.echo(f"  ✅ {package}: {version}")
            except ImportError:
                click.echo(f"  ❌ {package}: not installed")


@environment.command()
@click.option('--check', is_flag=True, help='Only check, do not install')
def dependencies(check):
    """
    Manage project dependencies.
    
    Installs or checks all required dependencies for the project.
    """
    click.echo("📦 Managing dependencies...")
    
    requirements_files = [
        'requirements.txt',
        'requirements-dev.txt'
    ]
    
    if check:
        # Check dependencies
        click.echo("\nChecking installed packages...")
        
        for req_file in requirements_files:
            if Path(req_file).exists():
                click.echo(f"\n📄 {req_file}:")
                with open(req_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            package = line.split('>=')[0].split('==')[0]
                            try:
                                __import__(package.replace('-', '_'))
                                click.echo(f"  ✅ {package}")
                            except ImportError:
                                click.echo(f"  ❌ {package}")
    else:
        # Install dependencies
        for req_file in requirements_files:
            if Path(req_file).exists():
                click.echo(f"\n📥 Installing from {req_file}...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', req_file],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    click.echo(f"✅ {req_file} installed successfully")
                else:
                    click.echo(f"❌ Error installing {req_file}", err=True)
                    click.echo(result.stderr, err=True)


@environment.command()
@click.option('--service', type=click.Choice(['dev', 'jupyter', 'test', 'quality', 'all']), 
              default='dev', help='Service to start')
@click.option('--build', is_flag=True, help='Build images first')
def docker(service, build):
    """
    Manage Docker development environment.
    
    Start, stop, or manage Docker containers for development.
    
    Examples:
    
        # Start development container
        bioalgo environment docker
        
        # Start Jupyter server
        bioalgo environment docker --service jupyter
        
        # Build and start all services
        bioalgo environment docker --service all --build
    """
    if not shutil.which('docker-compose'):
        click.echo("❌ docker-compose not found. Please install Docker.", err=True)
        sys.exit(1)
    
    if build:
        click.echo("🔨 Building Docker images...")
        subprocess.run(['docker-compose', 'build'])
    
    services_map = {
        'dev': ['bioalgo-dev'],
        'jupyter': ['bioalgo-jupyter'],
        'test': ['bioalgo-test'],
        'quality': ['bioalgo-quality'],
        'all': []  # Empty means all services
    }
    
    services = services_map.get(service, [])
    
    click.echo(f"🐳 Starting {service} services...")
    cmd = ['docker-compose', 'up', '-d'] + services
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        click.echo("✅ Services started successfully")
        
        if service == 'jupyter' or service == 'all':
            click.echo("\n📓 Jupyter Lab: http://localhost:8888 (token: bioalgo2024)")
        if service == 'all':
            click.echo("📚 Documentation: http://localhost:8080")
            click.echo("🗄️  PostgreSQL: localhost:5432")
            click.echo("📦 Redis: localhost:6379")
    else:
        click.echo("❌ Failed to start services", err=True)


@environment.command()
def shell():
    """
    Open interactive Python shell with project context.
    
    Starts an IPython shell with commonly used modules pre-imported.
    """
    click.echo("🐚 Starting BioAlgoCompare shell...")
    
    # Create startup script
    startup_code = """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Import algorithms
from algorithms import ALGORITHMS
from algorithms.hoa import HOA
from algorithms.foa import FOA
from algorithms.egto import EGTO

# Import problem
from problems.vrp import VRPProblem

# Import utilities
from utils.benchmarking import run_benchmark
from utils.visualization import plot_convergence
from utils.results import ResultsManager

print("\\n🚀 BioAlgoCompare shell ready!")
print("Available algorithms:", list(ALGORITHMS.keys()))
print("\\nExample usage:")
print("  problem = VRPProblem('E-n22-k4')")
print("  algo = HOA(problem, population_size=30, max_iterations=100, seed=42)")
print("  result = algo.run()")
print("  print(f'Best fitness: {result[\"best_fitness\"]}')")
print()
"""
    
    # Try to use IPython if available
    try:
        from IPython import start_ipython
        start_ipython(argv=[], user_ns={}, banner1="", exit_msg="👋 Goodbye!")
        # Execute startup code in IPython
        get_ipython().exec_lines(startup_code.split('\n'))
    except ImportError:
        # Fall back to standard Python
        import code
        import readline
        import rlcompleter
        
        # Enable tab completion
        readline.parse_and_bind("tab: complete")
        
        # Create namespace
        namespace = {}
        exec(startup_code, namespace)
        
        # Start interactive console
        console = code.InteractiveConsole(namespace)
        console.interact(banner="🐚 BioAlgoCompare shell (standard Python)")


@environment.command()
@click.option('--output', '-o', default='environment_report.md', help='Output file')
def report(output):
    """
    Generate environment setup report.
    
    Creates a detailed report of the current environment setup
    including all configurations, installed packages, and potential issues.
    """
    click.echo(f"📊 Generating environment report...")
    
    report_content = f"""# BioAlgoCompare Environment Report

Generated: {datetime.now().isoformat()}

## System Information

- **OS**: {platform.system()} {platform.release()}
- **Machine**: {platform.machine()}
- **Processor**: {platform.processor()}
- **Python**: {platform.python_version()} ({platform.python_implementation()})

## Environment Variables

"""
    
    # Add relevant environment variables
    env_vars = ['PYTHONPATH', 'BIOALGO_ENV', 'VIRTUAL_ENV', 'PATH']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        if var == 'PATH':
            # Truncate PATH for readability
            paths = value.split(os.pathsep)
            value = f"{len(paths)} entries (first: {paths[0] if paths else 'empty'})"
        report_content += f"- **{var}**: {value}\n"
    
    # Check project structure
    report_content += "\n## Project Structure\n\n"
    
    required_dirs = ['algorithms', 'problems', 'utils', 'scripts', 'tests', 'data']
    for dir_name in required_dirs:
        path = Path(dir_name)
        if path.exists():
            file_count = len(list(path.rglob('*.py')))
            report_content += f"- ✅ **{dir_name}/**: {file_count} Python files\n"
        else:
            report_content += f"- ❌ **{dir_name}/**: Missing\n"
    
    # Check key files
    report_content += "\n## Configuration Files\n\n"
    
    config_files = [
        '.pre-commit-config.yaml',
        'pyproject.toml',
        'requirements.txt',
        'requirements-dev.txt',
        'Dockerfile',
        'docker-compose.yml',
        'Makefile',
        '.env'
    ]
    
    for file_name in config_files:
        path = Path(file_name)
        if path.exists():
            size = path.stat().st_size
            report_content += f"- ✅ **{file_name}**: {size:,} bytes\n"
        else:
            report_content += f"- ❌ **{file_name}**: Not found\n"
    
    # Check installed packages
    report_content += "\n## Installed Packages\n\n"
    
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=json'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        packages = json.loads(result.stdout)
        key_packages = ['numpy', 'pandas', 'matplotlib', 'click', 'ruff', 'pytest', 'mypy', 'pre-commit']
        
        for package_name in key_packages:
            found = next((p for p in packages if p['name'] == package_name), None)
            if found:
                report_content += f"- ✅ **{package_name}**: {found['version']}\n"
            else:
                report_content += f"- ❌ **{package_name}**: Not installed\n"
    
    # Git status
    report_content += "\n## Git Status\n\n"
    
    if Path('.git').exists():
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            if result.stdout:
                report_content += f"Modified files: {len(result.stdout.strip().split('\\n'))}\n"
            else:
                report_content += "Working directory clean ✅\n"
        
        # Current branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            report_content += f"Current branch: {result.stdout.strip()}\n"
    else:
        report_content += "Not a git repository ❌\n"
    
    # Recommendations
    report_content += "\n## Recommendations\n\n"
    
    recommendations = []
    
    if not Path('.env').exists():
        recommendations.append("- Create `.env` file from `.env.example`")
    
    if not Path('venv').exists():
        recommendations.append("- Create virtual environment: `python -m venv venv`")
    
    if not shutil.which('docker'):
        recommendations.append("- Install Docker for containerized development")
    
    if recommendations:
        report_content += "\n".join(recommendations)
    else:
        report_content += "✅ Environment is properly configured!"
    
    # Save report
    Path(output).write_text(report_content)
    click.echo(f"✅ Report saved to {output}")
    
    # Display summary
    click.echo("\n📋 Summary:")
    click.echo(f"  - System: {platform.system()} with Python {platform.python_version()}")
    click.echo(f"  - Virtual env: {'Yes' if os.environ.get('VIRTUAL_ENV') else 'No'}")
    click.echo(f"  - Git repository: {'Yes' if Path('.git').exists() else 'No'}")
    click.echo(f"  - Docker available: {'Yes' if shutil.which('docker') else 'No'}")


@environment.command()
@click.confirmation_option(prompt='This will remove all generated files. Continue?')
def clean():
    """
    Clean development environment.
    
    Removes all generated files, caches, and temporary data
    but preserves source code and configuration.
    """
    click.echo("🧹 Cleaning development environment...")
    
    # Directories to clean
    clean_dirs = [
        '__pycache__',
        '.pytest_cache',
        '.ruff_cache',
        '.mypy_cache',
        '.tox',
        'htmlcov',
        '.coverage',
        '*.egg-info',
        'build',
        'dist'
    ]
    
    removed_count = 0
    
    for pattern in clean_dirs:
        for path in Path('.').rglob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                removed_count += 1
                click.echo(f"  🗑️  Removed {path}")
            elif path.is_file():
                path.unlink()
                removed_count += 1
    
    # Clean specific file patterns
    file_patterns = ['*.pyc', '*.pyo', '*.pyd', '.coverage.*']
    
    for pattern in file_patterns:
        for path in Path('.').rglob(pattern):
            path.unlink()
            removed_count += 1
    
    click.echo(f"\n✅ Cleaned {removed_count} items")


# Create command aliases
env = environment