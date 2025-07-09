"""
Main performance monitoring orchestrator for BioAlgoCompare.

This module provides the central PerformanceMonitor class that coordinates
all monitoring components including metrics collection, dashboards, and exports.
"""

import time
import threading
from typing import Optional, Dict, Any, Union, List
from pathlib import Path
import logging
from contextlib import contextmanager

from .metrics_collector import MetricsCollector
from .terminal_dashboard import TerminalDashboard
from .web_dashboard import WebDashboard
from .metrics_exporter import MetricsExporter

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Central performance monitoring orchestrator.
    
    Coordinates metrics collection, dashboards, and data export for real-time
    algorithm performance monitoring. Provides a unified interface for all
    monitoring capabilities.
    
    Features:
    - Automatic metrics collection
    - Multiple dashboard types (terminal, web)
    - Real-time data export
    - Algorithm integration
    - Resource monitoring
    
    Example:
        >>> from utils.monitoring import PerformanceMonitor
        >>> 
        >>> monitor = PerformanceMonitor(
        ...     dashboard_type='web',
        ...     export_metrics=True
        ... )
        >>> 
        >>> with monitor:
        ...     # Run algorithm with monitoring
        ...     algorithm.run()
    """
    
    def __init__(
        self,
        dashboard_type: str = 'none',
        export_metrics: bool = False,
        export_file: Optional[str] = None,
        web_port: int = 8080,
        collection_interval: float = 1.0,
        enable_system_monitoring: bool = True,
        auto_start: bool = True
    ):
        """
        Initialize performance monitor.
        
        Args:
            dashboard_type: Type of dashboard ('none', 'terminal', 'web', 'both')
            export_metrics: Whether to export metrics to file
            export_file: File path for metrics export (auto-generated if None)
            web_port: Port for web dashboard
            collection_interval: Metrics collection interval in seconds
            enable_system_monitoring: Whether to monitor system resources
            auto_start: Whether to automatically start monitoring
        """
        self.dashboard_type = dashboard_type
        self.export_metrics = export_metrics
        self.export_file = export_file
        self.web_port = web_port
        self.auto_start = auto_start
        
        # Core components
        self.metrics_collector = MetricsCollector(
            collection_interval=collection_interval,
            enable_system_monitoring=enable_system_monitoring
        )
        
        # Dashboard components
        self.terminal_dashboard: Optional[TerminalDashboard] = None
        self.web_dashboard: Optional[WebDashboard] = None
        
        # Export component
        self.metrics_exporter: Optional[MetricsExporter] = None
        if export_metrics:
            self.metrics_exporter = MetricsExporter(
                metrics_collector=self.metrics_collector,
                output_file=export_file
            )
        
        # State
        self._monitoring = False
        self._start_time = time.time()
        
        # Initialize dashboards
        self._initialize_dashboards()
        
        logger.info(f"Performance monitor initialized (dashboard={dashboard_type})")
    
    def _initialize_dashboards(self) -> None:
        """Initialize dashboard components based on configuration."""
        if self.dashboard_type in ['terminal', 'both']:
            self.terminal_dashboard = TerminalDashboard(
                metrics_collector=self.metrics_collector,
                refresh_rate=1.0
            )
        
        if self.dashboard_type in ['web', 'both']:
            self.web_dashboard = WebDashboard(
                metrics_collector=self.metrics_collector,
                port=self.web_port,
                auto_open=True
            )
    
    def start(self) -> None:
        """Start performance monitoring."""
        if self._monitoring:
            return
        
        logger.info("Starting performance monitoring...")
        
        # Start metrics collection
        self.metrics_collector.start_collection()
        
        # Start dashboards
        if self.terminal_dashboard:
            self.terminal_dashboard.start()
        
        if self.web_dashboard:
            self.web_dashboard.start()
        
        # Start metrics export
        if self.metrics_exporter:
            self.metrics_exporter.start()
        
        self._monitoring = True
        self._start_time = time.time()
        
        logger.info("Performance monitoring started")
    
    def stop(self) -> None:
        """Stop performance monitoring."""
        if not self._monitoring:
            return
        
        logger.info("Stopping performance monitoring...")
        
        # Stop dashboards
        if self.terminal_dashboard:
            self.terminal_dashboard.stop()
        
        if self.web_dashboard:
            self.web_dashboard.stop()
        
        # Stop metrics export
        if self.metrics_exporter:
            self.metrics_exporter.stop()
        
        # Stop metrics collection
        self.metrics_collector.stop_collection()
        
        self._monitoring = False
        
        # Final export if requested
        if self.export_metrics:
            self._final_export()
        
        logger.info("Performance monitoring stopped")
    
    def update_algorithm_metrics(self, **kwargs) -> None:
        """
        Update algorithm-specific metrics.
        
        Args:
            **kwargs: Metrics to update (iteration, fitness, population, etc.)
        """
        self.metrics_collector.update_algorithm_metrics(**kwargs)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return self.metrics_collector.get_metrics_summary()
    
    def get_dashboard_url(self) -> Optional[str]:
        """Get web dashboard URL if available."""
        if self.web_dashboard and self.web_dashboard.is_running():
            return self.web_dashboard.get_url()
        return None
    
    def pause(self) -> None:
        """Pause monitoring dashboards."""
        if self.terminal_dashboard:
            self.terminal_dashboard.pause()
        if self.web_dashboard:
            self.web_dashboard._paused = True
        logger.info("Monitoring paused")
    
    def resume(self) -> None:
        """Resume monitoring dashboards."""
        if self.terminal_dashboard:
            self.terminal_dashboard.resume()
        if self.web_dashboard:
            self.web_dashboard._paused = False
        logger.info("Monitoring resumed")
    
    def reset(self) -> None:
        """Reset all metrics and restart monitoring."""
        self.metrics_collector.reset()
        self._start_time = time.time()
        logger.info("Monitoring reset")
    
    def export_current_metrics(self, file_path: Optional[str] = None) -> str:
        """
        Export current metrics to file.
        
        Args:
            file_path: Output file path (auto-generated if None)
        
        Returns:
            Path to exported file
        """
        if not self.metrics_exporter:
            self.metrics_exporter = MetricsExporter(
                metrics_collector=self.metrics_collector,
                output_file=file_path
            )
        
        return self.metrics_exporter.export_current()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        algo_metrics = self.metrics_collector.algorithm_metrics
        sys_metrics = self.metrics_collector.system_metrics
        
        return {
            'monitoring': {
                'active': self._monitoring,
                'uptime': time.time() - self._start_time,
                'dashboard_type': self.dashboard_type,
                'web_url': self.get_dashboard_url()
            },
            'algorithm': {
                'iteration': algo_metrics.iteration,
                'best_fitness': algo_metrics.best_fitness,
                'convergence_rate': algo_metrics.convergence_rate,
                'diversity': algo_metrics.population_diversity,
                'time_per_iteration': algo_metrics.time_per_iteration,
                'estimated_completion': algo_metrics.estimated_completion
            },
            'system': {
                'cpu_percent': sys_metrics.cpu_percent,
                'memory_percent': sys_metrics.memory_percent,
                'memory_used_mb': sys_metrics.memory_used_mb,
                'process_count': sys_metrics.process_count,
                'temperature': sys_metrics.temperature
            },
            'collection': {
                'history_length': len(self.metrics_collector.metrics_history),
                'collection_interval': self.metrics_collector.collection_interval
            }
        }
    
    def _final_export(self) -> None:
        """Perform final metrics export on shutdown."""
        try:
            if self.metrics_exporter:
                export_path = self.metrics_exporter.export_final()
                logger.info(f"Final metrics exported to: {export_path}")
            else:
                # Create temporary exporter for final export
                exporter = MetricsExporter(
                    metrics_collector=self.metrics_collector,
                    output_file=self.export_file
                )
                export_path = exporter.export_final()
                logger.info(f"Final metrics exported to: {export_path}")
        except Exception as e:
            logger.error(f"Failed to export final metrics: {e}")
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def __enter__(self):
        """Context manager entry."""
        if self.auto_start:
            self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Convenience functions for quick monitoring setup

def monitor_algorithm(
    algorithm_runner,
    dashboard_type: str = 'terminal',
    export_file: Optional[str] = None,
    **monitor_kwargs
) -> Dict[str, Any]:
    """
    Monitor algorithm execution with automatic setup.
    
    Args:
        algorithm_runner: Function that runs the algorithm
        dashboard_type: Type of dashboard to show
        export_file: File to export metrics to
        **monitor_kwargs: Additional monitor configuration
    
    Returns:
        Algorithm results and monitoring data
    """
    monitor = PerformanceMonitor(
        dashboard_type=dashboard_type,
        export_metrics=export_file is not None,
        export_file=export_file,
        **monitor_kwargs
    )
    
    with monitor:
        # Run algorithm
        results = algorithm_runner()
        
        # Add monitoring data
        results['monitoring'] = monitor.get_performance_summary()
        
        return results


@contextmanager
def realtime_monitoring(dashboard_type: str = 'web', **kwargs):
    """
    Context manager for easy real-time monitoring setup.
    
    Args:
        dashboard_type: Type of dashboard ('terminal', 'web', 'both')
        **kwargs: Additional monitor configuration
    
    Yields:
        PerformanceMonitor instance
    """
    monitor = PerformanceMonitor(
        dashboard_type=dashboard_type,
        auto_start=True,
        **kwargs
    )
    
    try:
        yield monitor
    finally:
        monitor.stop()


# Integration hook for algorithm classes
class MonitoringMixin:
    """
    Mixin class for algorithm classes to add monitoring capabilities.
    
    Add this to algorithm classes to enable automatic monitoring:
    
    class MyAlgorithm(MetaheuristicAlgorithm, MonitoringMixin):
        def run(self):
            with self.create_monitor() as monitor:
                # Algorithm implementation
                for iteration in range(self.max_iterations):
                    # ... algorithm logic ...
                    
                    # Update monitoring
                    monitor.update_algorithm_metrics(
                        iteration=iteration,
                        current_fitness=current_fitness,
                        best_fitness=self.best_fitness,
                        population=self.population
                    )
    """
    
    def create_monitor(
        self,
        dashboard_type: str = 'none',
        export_metrics: bool = False,
        **kwargs
    ) -> PerformanceMonitor:
        """Create performance monitor for this algorithm."""
        return PerformanceMonitor(
            dashboard_type=dashboard_type,
            export_metrics=export_metrics,
            **kwargs
        )
    
    def enable_monitoring(
        self,
        dashboard_type: str = 'terminal',
        **kwargs
    ) -> None:
        """Enable monitoring for this algorithm instance."""
        self._monitor = self.create_monitor(
            dashboard_type=dashboard_type,
            auto_start=True,
            **kwargs
        )
    
    def disable_monitoring(self) -> None:
        """Disable monitoring for this algorithm instance."""
        if hasattr(self, '_monitor'):
            self._monitor.stop()
            delattr(self, '_monitor')
    
    def update_monitoring(self, **kwargs) -> None:
        """Update monitoring metrics if monitoring is enabled."""
        if hasattr(self, '_monitor'):
            self._monitor.update_algorithm_metrics(**kwargs)