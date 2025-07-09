"""
Metrics collection system for real-time algorithm monitoring.

This module provides comprehensive metrics collection including algorithm
performance, system resources, and optimization statistics.
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmMetrics:
    """Algorithm-specific metrics."""
    iteration: int = 0
    current_fitness: float = float('inf')
    best_fitness: float = float('inf')
    population_diversity: float = 0.0
    convergence_rate: float = 0.0
    stagnation_counter: int = 0
    exploration_ratio: float = 0.5
    constraint_violations: int = 0
    improvement_rate: float = 0.0
    elapsed_time: float = 0.0
    time_per_iteration: float = 0.0
    estimated_completion: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'iteration': self.iteration,
            'current_fitness': self.current_fitness,
            'best_fitness': self.best_fitness,
            'population_diversity': self.population_diversity,
            'convergence_rate': self.convergence_rate,
            'stagnation_counter': self.stagnation_counter,
            'exploration_ratio': self.exploration_ratio,
            'constraint_violations': self.constraint_violations,
            'improvement_rate': self.improvement_rate,
            'elapsed_time': self.elapsed_time,
            'time_per_iteration': self.time_per_iteration,
            'estimated_completion': self.estimated_completion
        }


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    disk_io_read: float = 0.0
    disk_io_write: float = 0.0
    network_io_sent: float = 0.0
    network_io_recv: float = 0.0
    temperature: Optional[float] = None
    load_average: List[float] = field(default_factory=list)
    process_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'disk_io_read': self.disk_io_read,
            'disk_io_write': self.disk_io_write,
            'network_io_sent': self.network_io_sent,
            'network_io_recv': self.network_io_recv,
            'temperature': self.temperature,
            'load_average': self.load_average,
            'process_count': self.process_count
        }


class MetricsCollector:
    """
    Collects and manages performance metrics in real-time.
    
    This class handles collection of both algorithm-specific metrics
    (fitness, convergence, etc.) and system metrics (CPU, memory, etc.).
    
    Attributes:
        algorithm_metrics: Current algorithm metrics
        system_metrics: Current system metrics
        metrics_history: Historical metrics data
        callbacks: List of callback functions for metric updates
    """
    
    def __init__(
        self,
        history_size: int = 1000,
        collection_interval: float = 1.0,
        enable_system_monitoring: bool = True
    ):
        """
        Initialize metrics collector.
        
        Args:
            history_size: Maximum number of historical data points to keep
            collection_interval: Interval for automatic collection (seconds)
            enable_system_monitoring: Whether to collect system metrics
        """
        self.history_size = history_size
        self.collection_interval = collection_interval
        self.enable_system_monitoring = enable_system_monitoring
        
        # Current metrics
        self.algorithm_metrics = AlgorithmMetrics()
        self.system_metrics = SystemMetrics()
        
        # Historical data
        self.metrics_history: deque = deque(maxlen=history_size)
        self.fitness_history: deque = deque(maxlen=history_size)
        self.diversity_history: deque = deque(maxlen=history_size)
        self.cpu_history: deque = deque(maxlen=history_size)
        self.memory_history: deque = deque(maxlen=history_size)
        
        # Callbacks
        self.callbacks: List[Callable[[AlgorithmMetrics, SystemMetrics], None]] = []
        
        # Control flags
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        self._start_time = time.time()
        self._last_collection_time = time.time()
        
        # System monitoring setup
        if enable_system_monitoring:
            self._setup_system_monitoring()
        
        logger.info("Metrics collector initialized")
    
    def _setup_system_monitoring(self) -> None:
        """Setup system monitoring components."""
        try:
            # Initialize psutil counters
            psutil.cpu_percent(interval=None)
            psutil.virtual_memory()
            psutil.disk_io_counters()
            psutil.net_io_counters()
        except Exception as e:
            logger.warning(f"Failed to initialize system monitoring: {e}")
            self.enable_system_monitoring = False
    
    def add_callback(self, callback: Callable[[AlgorithmMetrics, SystemMetrics], None]) -> None:
        """Add callback function to be called on metric updates."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[AlgorithmMetrics, SystemMetrics], None]) -> None:
        """Remove callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start_collection(self) -> None:
        """Start automatic metrics collection."""
        if self._collecting:
            return
        
        self._collecting = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True
        )
        self._collection_thread.start()
        logger.info("Started automatic metrics collection")
    
    def stop_collection(self) -> None:
        """Stop automatic metrics collection."""
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)
        logger.info("Stopped automatic metrics collection")
    
    def _collection_loop(self) -> None:
        """Main collection loop running in separate thread."""
        while self._collecting:
            try:
                if self.enable_system_monitoring:
                    self._collect_system_metrics()
                
                # Store snapshot
                self._store_metrics_snapshot()
                
                # Notify callbacks
                self._notify_callbacks()
                
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(self.collection_interval)
    
    def update_algorithm_metrics(
        self,
        iteration: Optional[int] = None,
        current_fitness: Optional[float] = None,
        best_fitness: Optional[float] = None,
        population: Optional[List] = None,
        **kwargs
    ) -> None:
        """
        Update algorithm-specific metrics.
        
        Args:
            iteration: Current iteration number
            current_fitness: Current best fitness value
            best_fitness: Overall best fitness found
            population: Current population (for diversity calculation)
            **kwargs: Additional algorithm-specific metrics
        """
        current_time = time.time()
        elapsed_time = current_time - self._start_time
        
        # Update basic metrics
        if iteration is not None:
            self.algorithm_metrics.iteration = iteration
        if current_fitness is not None:
            self.algorithm_metrics.current_fitness = current_fitness
        if best_fitness is not None:
            # Calculate improvement rate
            if self.algorithm_metrics.best_fitness != float('inf'):
                improvement = abs(best_fitness - self.algorithm_metrics.best_fitness)
                self.algorithm_metrics.improvement_rate = improvement / max(abs(best_fitness), 1e-10)
            self.algorithm_metrics.best_fitness = best_fitness
        
        self.algorithm_metrics.elapsed_time = elapsed_time
        
        # Calculate time per iteration
        if iteration and iteration > 0:
            self.algorithm_metrics.time_per_iteration = elapsed_time / iteration
            
            # Estimate completion time
            if 'max_iterations' in kwargs:
                remaining_iterations = kwargs['max_iterations'] - iteration
                self.algorithm_metrics.estimated_completion = (
                    remaining_iterations * self.algorithm_metrics.time_per_iteration
                )
        
        # Calculate population diversity
        if population:
            self.algorithm_metrics.population_diversity = self._calculate_diversity(population)
        
        # Calculate convergence rate
        self._calculate_convergence_rate()
        
        # Update stagnation counter
        if 'stagnation_counter' in kwargs:
            self.algorithm_metrics.stagnation_counter = kwargs['stagnation_counter']
        
        # Update exploration ratio
        if 'exploration_ratio' in kwargs:
            self.algorithm_metrics.exploration_ratio = kwargs['exploration_ratio']
        
        # Update constraint violations
        if 'constraint_violations' in kwargs:
            self.algorithm_metrics.constraint_violations = kwargs['constraint_violations']
        
        # Store in history
        if current_fitness is not None:
            self.fitness_history.append((current_time, current_fitness))
        if self.algorithm_metrics.population_diversity > 0:
            self.diversity_history.append((current_time, self.algorithm_metrics.population_diversity))
        
        self._last_collection_time = current_time
    
    def _calculate_diversity(self, population: List) -> float:
        """Calculate population diversity."""
        try:
            if len(population) < 2:
                return 0.0
            
            # Get positions/solutions
            positions = []
            for individual in population:
                if hasattr(individual, 'position'):
                    positions.append(individual.position)
                elif hasattr(individual, 'solution'):
                    positions.append(individual.solution)
                else:
                    return 0.0
            
            if not positions:
                return 0.0
            
            positions = np.array(positions)
            
            # Calculate pairwise distances
            mean_position = np.mean(positions, axis=0)
            distances = np.linalg.norm(positions - mean_position, axis=1)
            
            # Normalize by maximum possible distance
            max_distance = np.sqrt(len(mean_position))
            diversity = np.mean(distances) / max_distance if max_distance > 0 else 0.0
            
            return min(diversity, 1.0)
        except Exception as e:
            logger.warning(f"Failed to calculate diversity: {e}")
            return 0.0
    
    def _calculate_convergence_rate(self) -> None:
        """Calculate convergence rate based on recent fitness history."""
        if len(self.fitness_history) < 2:
            self.algorithm_metrics.convergence_rate = 0.0
            return
        
        try:
            # Get recent fitness values
            recent_fitness = list(self.fitness_history)[-10:]  # Last 10 values
            
            if len(recent_fitness) < 2:
                return
            
            # Calculate rate of change
            times = [t for t, _ in recent_fitness]
            fitness_values = [f for _, f in recent_fitness]
            
            # Linear regression slope
            n = len(times)
            mean_time = np.mean(times)
            mean_fitness = np.mean(fitness_values)
            
            numerator = sum((times[i] - mean_time) * (fitness_values[i] - mean_fitness) for i in range(n))
            denominator = sum((times[i] - mean_time) ** 2 for i in range(n))
            
            if denominator > 0:
                slope = numerator / denominator
                self.algorithm_metrics.convergence_rate = abs(slope)
            else:
                self.algorithm_metrics.convergence_rate = 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate convergence rate: {e}")
            self.algorithm_metrics.convergence_rate = 0.0
    
    def _collect_system_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU metrics
            self.system_metrics.cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.system_metrics.memory_percent = memory.percent
            self.system_metrics.memory_used_mb = memory.used / 1024 / 1024
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.system_metrics.disk_io_read = disk_io.read_bytes / 1024 / 1024  # MB
                self.system_metrics.disk_io_write = disk_io.write_bytes / 1024 / 1024  # MB
            
            # Network I/O
            net_io = psutil.net_io_counters()
            if net_io:
                self.system_metrics.network_io_sent = net_io.bytes_sent / 1024 / 1024  # MB
                self.system_metrics.network_io_recv = net_io.bytes_recv / 1024 / 1024  # MB
            
            # Load average (Unix-like systems)
            try:
                load = psutil.getloadavg()
                self.system_metrics.load_average = list(load)
            except (AttributeError, OSError):
                pass
            
            # Process count
            self.system_metrics.process_count = len(psutil.pids())
            
            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get CPU temperature if available
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            if entries:
                                self.system_metrics.temperature = entries[0].current
                                break
            except (AttributeError, OSError):
                pass
            
            # Store in history
            current_time = time.time()
            self.cpu_history.append((current_time, self.system_metrics.cpu_percent))
            self.memory_history.append((current_time, self.system_metrics.memory_percent))
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _store_metrics_snapshot(self) -> None:
        """Store current metrics snapshot in history."""
        snapshot = {
            'timestamp': time.time(),
            'algorithm': self.algorithm_metrics.to_dict(),
            'system': self.system_metrics.to_dict()
        }
        self.metrics_history.append(snapshot)
    
    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks with current metrics."""
        for callback in self.callbacks:
            try:
                callback(self.algorithm_metrics, self.system_metrics)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            'current': {
                'algorithm': self.algorithm_metrics.to_dict(),
                'system': self.system_metrics.to_dict()
            },
            'history_length': len(self.metrics_history),
            'collection_active': self._collecting,
            'start_time': self._start_time,
            'elapsed_time': time.time() - self._start_time
        }
    
    def get_time_series_data(
        self,
        metric_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Tuple[float, float]]:
        """
        Get time series data for a specific metric.
        
        Args:
            metric_name: Name of the metric (e.g., 'fitness', 'cpu', 'memory')
            start_time: Start timestamp (None for all)
            end_time: End timestamp (None for all)
        
        Returns:
            List of (timestamp, value) tuples
        """
        if metric_name == 'fitness':
            data = list(self.fitness_history)
        elif metric_name == 'diversity':
            data = list(self.diversity_history)
        elif metric_name == 'cpu':
            data = list(self.cpu_history)
        elif metric_name == 'memory':
            data = list(self.memory_history)
        else:
            return []
        
        # Filter by time range
        if start_time is not None:
            data = [(t, v) for t, v in data if t >= start_time]
        if end_time is not None:
            data = [(t, v) for t, v in data if t <= end_time]
        
        return data
    
    def export_metrics(self, format: str = 'json') -> Dict[str, Any]:
        """
        Export all collected metrics.
        
        Args:
            format: Export format ('json', 'csv', 'parquet')
        
        Returns:
            Exported metrics data
        """
        export_data = {
            'metadata': {
                'start_time': self._start_time,
                'end_time': time.time(),
                'duration': time.time() - self._start_time,
                'total_samples': len(self.metrics_history),
                'collection_interval': self.collection_interval
            },
            'current_metrics': {
                'algorithm': self.algorithm_metrics.to_dict(),
                'system': self.system_metrics.to_dict()
            },
            'time_series': {
                'fitness': list(self.fitness_history),
                'diversity': list(self.diversity_history),
                'cpu': list(self.cpu_history),
                'memory': list(self.memory_history)
            },
            'full_history': list(self.metrics_history)
        }
        
        return export_data
    
    def reset(self) -> None:
        """Reset all metrics and history."""
        self.algorithm_metrics = AlgorithmMetrics()
        self.system_metrics = SystemMetrics()
        self.metrics_history.clear()
        self.fitness_history.clear()
        self.diversity_history.clear()
        self.cpu_history.clear()
        self.memory_history.clear()
        self._start_time = time.time()
        logger.info("Metrics collector reset")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_collection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_collection()