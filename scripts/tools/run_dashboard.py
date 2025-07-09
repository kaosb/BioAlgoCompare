#!/usr/bin/env python3
"""
Script to run the BioAlgoCompare dashboard.
"""

import click
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard import create_app
from dashboard.monitor import DashboardRunner
from algorithms.factories import AlgorithmFactory
from problems.vrp_v2 import VRPProblemV2
from utils.experiment_tracker import ExperimentTracker


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--port', default=8050, help='Port to run dashboard on')
@click.option('--host', default='127.0.0.1', help='Host address')
@click.option('--debug', is_flag=True, help='Run in debug mode')
@click.option('--demo', is_flag=True, help='Run with demo algorithms')
@click.option('--database', default=None, help='Path to results database')
def main(port, host, debug, demo, database):
    """Run the BioAlgoCompare real-time dashboard."""
    
    click.echo(f"Starting BioAlgoCompare Dashboard on http://{host}:{port}")
    
    # Create experiment tracker
    tracker = ExperimentTracker()
    
    # Create dashboard app
    app = create_app(
        experiment_tracker=tracker,
        database_path=database,
        port=port,
        debug=debug
    )
    
    if demo:
        click.echo("Running in demo mode with sample algorithms...")
        
        # Create dashboard runner
        runner = DashboardRunner(app, auto_start=False)
        
        # Load a sample problem
        problem_path = Path("data/vrp/E-n22-k4.vrp")
        if problem_path.exists():
            problem = VRPProblemV2(str(problem_path))
            
            # Create sample algorithms
            algorithms = {}
            
            # Add a few algorithms for comparison
            algo_names = ['HOA', 'FOA', 'GTO']
            for name in algo_names:
                algo_info = AlgorithmFactory.get_algorithm(name)
                if algo_info:
                    algo = algo_info['class'](
                        problem,
                        population_size=20,
                        max_iterations=100,
                        seed=42
                    )
                    algorithms[name] = algo
                    click.echo(f"  - Added {name} algorithm")
            
            # Start dashboard
            runner.start_dashboard(host=host, port=port)
            
            # Run algorithms
            click.echo("\nStarting algorithm execution...")
            runner.run_comparison(algorithms, blocking=False)
            
            click.echo("\nDashboard is running. Press Ctrl+C to stop.")
            
            try:
                # Keep the main thread alive
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                click.echo("\nStopping dashboard...")
                runner.stop()
        else:
            click.echo("Sample VRP file not found. Running dashboard without demo algorithms.")
            app.run(host=host)
    else:
        # Run dashboard normally
        app.run(host=host)


if __name__ == '__main__':
    main()