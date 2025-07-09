"""
Algorithm monitoring utilities for dashboard integration.
"""

import threading
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import logging

from algorithms.base_v2 import MetaheuristicAlgorithm
from .app import DashboardApp


logger = logging.getLogger(__name__)


class AlgorithmMonitor:
    """
    Monitor for running algorithms with dashboard integration.
    """
    
    def __init__(self, dashboard: DashboardApp):
        """
        Initialize algorithm monitor.
        
        Args:
            dashboard: Dashboard application instance
        """
        self.dashboard = dashboard
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        
    def start_monitoring(self, 
                        algorithm: MetaheuristicAlgorithm,
                        run_id: str,
                        callback: Optional[Callable] = None,
                        update_interval: float = 1.0) -> str:
        """
        Start monitoring an algorithm.
        
        Args:
            algorithm: Algorithm to monitor
            run_id: Unique run identifier
            callback: Optional callback function called each iteration
            update_interval: Update interval in seconds
            
        Returns:
            Run ID
        """
        # Add to dashboard
        self.dashboard.add_algorithm(algorithm, run_id)
        
        # Create stop event
        stop_event = threading.Event()
        self.stop_events[run_id] = stop_event
        
        # Create monitoring thread
        thread = threading.Thread(
            target=self._monitor_algorithm,
            args=(algorithm, run_id, callback, update_interval, stop_event),
            name=f"Monitor-{run_id}"
        )
        
        self.monitoring_threads[run_id] = thread
        thread.start()
        
        logger.info(f"Started monitoring algorithm {algorithm.__class__.__name__} with run_id {run_id}")
        return run_id
        
    def stop_monitoring(self, run_id: str):
        """Stop monitoring an algorithm."""
        if run_id in self.stop_events:
            self.stop_events[run_id].set()
            
            if run_id in self.monitoring_threads:
                thread = self.monitoring_threads[run_id]
                thread.join(timeout=5.0)
                
                if thread.is_alive():
                    logger.warning(f"Monitor thread for {run_id} did not stop gracefully")
                    
                del self.monitoring_threads[run_id]
            
            del self.stop_events[run_id]
            self.dashboard.remove_algorithm(run_id)
            
            logger.info(f"Stopped monitoring run_id {run_id}")
            
    def stop_all(self):
        """Stop all monitoring threads."""
        run_ids = list(self.stop_events.keys())
        for run_id in run_ids:
            self.stop_monitoring(run_id)
            
    def _monitor_algorithm(self, 
                          algorithm: MetaheuristicAlgorithm,
                          run_id: str,
                          callback: Optional[Callable],
                          update_interval: float,
                          stop_event: threading.Event):
        """Monitor algorithm execution."""
        logger.info(f"Monitor thread started for {run_id}")
        
        try:
            while not stop_event.is_set():
                # Check if algorithm is still running
                if (hasattr(algorithm, 'current_iteration') and 
                    hasattr(algorithm, 'max_iterations') and
                    algorithm.current_iteration >= algorithm.max_iterations):
                    logger.info(f"Algorithm {run_id} completed")
                    self.dashboard.active_algorithms[run_id]['status'] = 'completed'
                    break
                
                # Update dashboard data
                self.dashboard.update_algorithm_data(run_id)
                
                # Call user callback if provided
                if callback:
                    try:
                        callback(algorithm, run_id)
                    except Exception as e:
                        logger.error(f"Error in user callback for {run_id}: {e}")
                
                # Wait for next update
                stop_event.wait(update_interval)
                
        except Exception as e:
            logger.error(f"Error in monitor thread for {run_id}: {e}")
            self.dashboard.active_algorithms[run_id]['status'] = 'failed'
            
        finally:
            logger.info(f"Monitor thread stopped for {run_id}")


class DashboardRunner:
    """
    Runner that integrates algorithm execution with dashboard.
    """
    
    def __init__(self, dashboard: Optional[DashboardApp] = None,
                 auto_start: bool = True):
        """
        Initialize dashboard runner.
        
        Args:
            dashboard: Dashboard instance (creates new if None)
            auto_start: Automatically start dashboard server
        """
        self.dashboard = dashboard or DashboardApp()
        self.monitor = AlgorithmMonitor(self.dashboard)
        self.auto_start = auto_start
        self._dashboard_thread = None
        
        if auto_start:
            self.start_dashboard()
            
    def start_dashboard(self, host: str = '127.0.0.1', port: int = 8050):
        """Start dashboard server in background."""
        if self._dashboard_thread and self._dashboard_thread.is_alive():
            logger.warning("Dashboard already running")
            return
            
        self._dashboard_thread = threading.Thread(
            target=self.dashboard.run,
            args=(host,),
            kwargs={'port': port},
            daemon=True
        )
        self._dashboard_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        logger.info(f"Dashboard started at http://{host}:{port}")
        
    def run_algorithm(self, 
                     algorithm: MetaheuristicAlgorithm,
                     run_id: Optional[str] = None,
                     monitor: bool = True,
                     blocking: bool = True) -> Dict[str, Any]:
        """
        Run algorithm with optional monitoring.
        
        Args:
            algorithm: Algorithm to run
            run_id: Run identifier (auto-generated if None)
            monitor: Whether to monitor in dashboard
            blocking: Whether to block until completion
            
        Returns:
            Results dictionary
        """
        # Generate run ID if not provided
        if run_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id = f"{algorithm.__class__.__name__}_{timestamp}"
            
        # Start monitoring if requested
        if monitor:
            self.monitor.start_monitoring(algorithm, run_id)
            
        # Run algorithm
        if blocking:
            # Run in current thread
            algorithm.run()
            
            # Stop monitoring
            if monitor:
                self.monitor.stop_monitoring(run_id)
                
            # Return results
            return {
                'run_id': run_id,
                'algorithm': algorithm.__class__.__name__,
                'best_fitness': algorithm.best_solution.fitness(),
                'iterations': algorithm.current_iteration,
                'execution_time': getattr(algorithm, 'execution_time', None)
            }
        else:
            # Run in separate thread
            thread = threading.Thread(
                target=algorithm.run,
                name=f"Algorithm-{run_id}"
            )
            thread.start()
            
            return {
                'run_id': run_id,
                'status': 'started',
                'thread': thread
            }
            
    def run_comparison(self, 
                      algorithms: Dict[str, MetaheuristicAlgorithm],
                      blocking: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Run multiple algorithms for comparison.
        
        Args:
            algorithms: Dictionary of {name: algorithm}
            blocking: Whether to wait for all to complete
            
        Returns:
            Results for each algorithm
        """
        results = {}
        threads = []
        
        for name, algorithm in algorithms.items():
            result = self.run_algorithm(
                algorithm,
                run_id=name,
                monitor=True,
                blocking=False
            )
            results[name] = result
            threads.append(result['thread'])
            
            # Stagger starts slightly
            time.sleep(0.5)
            
        if blocking:
            # Wait for all to complete
            for thread in threads:
                thread.join()
                
            # Update results with final values
            for name, algorithm in algorithms.items():
                results[name].update({
                    'best_fitness': algorithm.best_solution.fitness(),
                    'iterations': algorithm.current_iteration,
                    'status': 'completed'
                })
                
        return results
        
    def stop(self):
        """Stop all monitoring and cleanup."""
        self.monitor.stop_all()
        logger.info("Dashboard runner stopped")


def create_monitored_algorithm(algorithm_class: type,
                              problem,
                              dashboard: Optional[DashboardApp] = None,
                              **kwargs) -> MetaheuristicAlgorithm:
    """
    Create an algorithm instance with automatic monitoring.
    
    Args:
        algorithm_class: Algorithm class
        problem: Problem instance
        dashboard: Dashboard instance
        **kwargs: Algorithm parameters
        
    Returns:
        Algorithm instance with monitoring setup
    """
    # Create algorithm
    algorithm = algorithm_class(problem, **kwargs)
    
    # Create wrapper that starts monitoring on run
    original_run = algorithm.run
    
    def monitored_run():
        runner = DashboardRunner(dashboard)
        runner.run_algorithm(algorithm, monitor=True, blocking=True)
        
    algorithm.run = monitored_run
    
    return algorithm