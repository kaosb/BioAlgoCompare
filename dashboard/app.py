"""
Main dashboard application.
"""

import dash
from dash import Dash, html, dcc
import plotly.graph_objs as go
from flask import Flask
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path

from utils.experiment_tracker import ExperimentTracker
from utils.results_database import ResultsDatabase
from algorithms.base_v2 import MetaheuristicAlgorithm


logger = logging.getLogger(__name__)


class DashboardApp:
    """
    Real-time dashboard application for monitoring algorithm execution.
    """
    
    def __init__(self, 
                 experiment_tracker: Optional[ExperimentTracker] = None,
                 database_path: Optional[str] = None,
                 port: int = 8050,
                 debug: bool = False):
        """
        Initialize dashboard application.
        
        Args:
            experiment_tracker: Experiment tracker instance
            database_path: Path to results database
            port: Port to run dashboard on
            debug: Debug mode
        """
        self.port = port
        self.debug = debug
        
        # Initialize data sources
        self.tracker = experiment_tracker or ExperimentTracker()
        self.db = ResultsDatabase(database_path or "results/dashboard_results.db")
        
        # Running algorithms
        self.active_algorithms: Dict[str, Dict[str, Any]] = {}
        self.algorithm_threads: Dict[str, threading.Thread] = {}
        
        # Create Dash app
        self.server = Flask(__name__)
        self.app = Dash(
            __name__,
            server=self.server,
            suppress_callback_exceptions=True,
            assets_folder=str(Path(__file__).parent / 'assets')
        )
        
        # Configure app
        self.app.title = "BioAlgoCompare Dashboard"
        
        # Data storage
        self.convergence_data: Dict[str, List[Dict]] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        self.comparison_data: List[Dict] = []
        
        # Update interval (ms)
        self.update_interval = 1000
        
    def setup_layout(self):
        """Setup the dashboard layout."""
        from .layouts import get_main_layout
        self.app.layout = get_main_layout(self.update_interval)
        
    def register_callbacks(self):
        """Register all callbacks."""
        from .callbacks import register_callbacks
        register_callbacks(self.app, self)
        
    def run(self, host: str = '127.0.0.1'):
        """
        Run the dashboard.
        
        Args:
            host: Host address
        """
        self.setup_layout()
        self.register_callbacks()
        
        logger.info(f"Starting dashboard on http://{host}:{self.port}")
        self.app.run_server(host=host, port=self.port, debug=self.debug)
        
    def add_algorithm(self, 
                     algorithm: MetaheuristicAlgorithm,
                     run_id: str,
                     metadata: Optional[Dict] = None) -> str:
        """
        Add an algorithm to monitor.
        
        Args:
            algorithm: Algorithm instance
            run_id: Unique run identifier
            metadata: Additional metadata
            
        Returns:
            Run ID
        """
        self.active_algorithms[run_id] = {
            'algorithm': algorithm,
            'start_time': datetime.now(),
            'metadata': metadata or {},
            'status': 'running',
            'convergence': [],
            'metrics': {}
        }
        
        # Initialize data storage
        self.convergence_data[run_id] = []
        self.performance_metrics[run_id] = {
            'best_fitness': [],
            'mean_fitness': [],
            'std_fitness': [],
            'execution_time': []
        }
        
        logger.info(f"Added algorithm {algorithm.__class__.__name__} with run_id {run_id}")
        return run_id
        
    def remove_algorithm(self, run_id: str):
        """Remove an algorithm from monitoring."""
        if run_id in self.active_algorithms:
            self.active_algorithms[run_id]['status'] = 'completed'
            logger.info(f"Removed algorithm with run_id {run_id}")
            
    def update_algorithm_data(self, run_id: str):
        """Update data for a specific algorithm."""
        if run_id not in self.active_algorithms:
            return
            
        algo_info = self.active_algorithms[run_id]
        algorithm = algo_info['algorithm']
        
        # Get current metrics
        current_iter = algorithm.current_iteration
        best_fitness = algorithm.best_solution.fitness() if algorithm.best_solution else float('inf')
        
        # Calculate population statistics
        if hasattr(algorithm, 'population') and algorithm.population:
            fitnesses = [ind.fitness() for ind in algorithm.population]
            mean_fitness = sum(fitnesses) / len(fitnesses)
            std_fitness = (sum((f - mean_fitness) ** 2 for f in fitnesses) / len(fitnesses)) ** 0.5
        else:
            mean_fitness = best_fitness
            std_fitness = 0
            
        # Calculate execution time
        elapsed = (datetime.now() - algo_info['start_time']).total_seconds()
        
        # Update convergence data
        self.convergence_data[run_id].append({
            'iteration': current_iter,
            'best_fitness': best_fitness,
            'mean_fitness': mean_fitness,
            'std_fitness': std_fitness,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update performance metrics
        self.performance_metrics[run_id]['best_fitness'].append(best_fitness)
        self.performance_metrics[run_id]['mean_fitness'].append(mean_fitness)
        self.performance_metrics[run_id]['std_fitness'].append(std_fitness)
        self.performance_metrics[run_id]['execution_time'].append(elapsed)
        
        # Update algorithm info
        algo_info['metrics'] = {
            'current_iteration': current_iter,
            'best_fitness': best_fitness,
            'mean_fitness': mean_fitness,
            'std_fitness': std_fitness,
            'execution_time': elapsed,
            'convergence_rate': self._calculate_convergence_rate(run_id)
        }
        
    def _calculate_convergence_rate(self, run_id: str) -> float:
        """Calculate convergence rate for an algorithm."""
        if run_id not in self.convergence_data:
            return 0.0
            
        data = self.convergence_data[run_id]
        if len(data) < 2:
            return 0.0
            
        # Calculate improvement over last 10 iterations
        window = min(10, len(data) - 1)
        if window < 1:
            return 0.0
            
        initial = data[-window-1]['best_fitness']
        current = data[-1]['best_fitness']
        
        if initial == 0:
            return 0.0
            
        return (initial - current) / initial * 100
        
    def get_active_algorithms(self) -> List[Dict[str, Any]]:
        """Get information about active algorithms."""
        active = []
        for run_id, info in self.active_algorithms.items():
            active.append({
                'run_id': run_id,
                'algorithm': info['algorithm'].__class__.__name__,
                'status': info['status'],
                'start_time': info['start_time'].isoformat(),
                'metrics': info.get('metrics', {})
            })
        return active
        
    def get_convergence_data(self, run_id: str) -> List[Dict]:
        """Get convergence data for a specific run."""
        return self.convergence_data.get(run_id, [])
        
    def get_comparison_data(self) -> List[Dict]:
        """Get comparison data for all algorithms."""
        comparison = []
        
        for run_id, info in self.active_algorithms.items():
            if 'metrics' in info and info['metrics']:
                comparison.append({
                    'run_id': run_id,
                    'algorithm': info['algorithm'].__class__.__name__,
                    'best_fitness': info['metrics']['best_fitness'],
                    'execution_time': info['metrics']['execution_time'],
                    'iterations': info['metrics']['current_iteration'],
                    'convergence_rate': info['metrics']['convergence_rate']
                })
                
        return comparison
        
    def get_performance_history(self, run_id: str) -> Dict[str, List]:
        """Get performance history for a specific run."""
        return self.performance_metrics.get(run_id, {})
        
    def save_snapshot(self, run_id: str, filepath: str):
        """Save a snapshot of current dashboard state."""
        import json
        
        snapshot = {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'algorithm_info': {
                'name': self.active_algorithms[run_id]['algorithm'].__class__.__name__,
                'status': self.active_algorithms[run_id]['status'],
                'metadata': self.active_algorithms[run_id]['metadata']
            },
            'convergence_data': self.convergence_data.get(run_id, []),
            'performance_metrics': self.performance_metrics.get(run_id, {}),
            'final_metrics': self.active_algorithms[run_id].get('metrics', {})
        }
        
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2)
            
        logger.info(f"Saved snapshot to {filepath}")


def create_app(experiment_tracker: Optional[ExperimentTracker] = None,
               database_path: Optional[str] = None,
               port: int = 8050,
               debug: bool = False) -> DashboardApp:
    """
    Create and configure dashboard application.
    
    Args:
        experiment_tracker: Experiment tracker instance
        database_path: Path to results database
        port: Port to run on
        debug: Debug mode
        
    Returns:
        Configured dashboard app
    """
    app = DashboardApp(
        experiment_tracker=experiment_tracker,
        database_path=database_path,
        port=port,
        debug=debug
    )
    
    return app