"""
Metrics export system for performance monitoring data.

This module provides functionality to export collected metrics in various
formats including JSON, CSV, and real-time streaming.
"""

import json
import csv
import time
import threading
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from datetime import datetime
import logging

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class MetricsExporter:
    """
    Export metrics data in various formats.
    
    Supports real-time streaming and batch export of collected metrics
    in multiple formats for analysis and visualization.
    
    Features:
    - JSON export with full metadata
    - CSV export for spreadsheet analysis
    - Real-time streaming to files
    - Pandas DataFrame export (if available)
    - Automatic file naming and rotation
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        output_file: Optional[str] = None,
        export_format: str = 'json',
        stream_updates: bool = False,
        stream_interval: float = 5.0
    ):
        """
        Initialize metrics exporter.
        
        Args:
            metrics_collector: MetricsCollector instance to export from
            output_file: Base output file path (auto-generated if None)
            export_format: Export format ('json', 'csv', 'both')
            stream_updates: Whether to stream updates in real-time
            stream_interval: Interval for streaming updates (seconds)
        """
        self.metrics_collector = metrics_collector
        self.output_file = output_file
        self.export_format = export_format
        self.stream_updates = stream_updates
        self.stream_interval = stream_interval
        
        # Streaming state
        self._streaming = False
        self._stream_thread: Optional[threading.Thread] = None
        
        # File paths
        self.base_path = self._determine_base_path()
        self.json_path = self.base_path.with_suffix('.json')
        self.csv_path = self.base_path.with_suffix('.csv')
        
        # CSV file handle for streaming
        self._csv_file = None
        self._csv_writer = None
        
        logger.info(f"Metrics exporter initialized (format={export_format}, base={self.base_path})")
    
    def _determine_base_path(self) -> Path:
        """Determine base file path for exports."""
        if self.output_file:
            return Path(self.output_file).with_suffix('')  # Remove extension
        
        # Auto-generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return Path(f"metrics_{timestamp}")
    
    def start(self) -> None:
        """Start real-time metrics streaming."""
        if not self.stream_updates or self._streaming:
            return
        
        self._streaming = True
        
        # Initialize CSV file for streaming
        if self.export_format in ['csv', 'both']:
            self._init_csv_streaming()
        
        # Start streaming thread
        self._stream_thread = threading.Thread(
            target=self._stream_loop,
            daemon=True
        )
        self._stream_thread.start()
        
        logger.info("Started real-time metrics streaming")
    
    def stop(self) -> None:
        """Stop real-time metrics streaming."""
        if not self._streaming:
            return
        
        self._streaming = False
        
        # Wait for stream thread
        if self._stream_thread:
            self._stream_thread.join(timeout=5.0)
        
        # Close CSV file
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None
        
        logger.info("Stopped real-time metrics streaming")
    
    def _init_csv_streaming(self) -> None:
        """Initialize CSV file for streaming."""
        try:
            self._csv_file = open(self.csv_path, 'w', newline='')
            
            # Write header
            fieldnames = [
                'timestamp', 'iteration', 'current_fitness', 'best_fitness',
                'population_diversity', 'convergence_rate', 'stagnation_counter',
                'exploration_ratio', 'constraint_violations', 'improvement_rate',
                'elapsed_time', 'time_per_iteration', 'estimated_completion',
                'cpu_percent', 'memory_percent', 'memory_used_mb',
                'disk_io_read', 'disk_io_write', 'network_io_sent', 'network_io_recv',
                'temperature', 'process_count'
            ]
            
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=fieldnames)
            self._csv_writer.writeheader()
            self._csv_file.flush()
            
            logger.info(f"Initialized CSV streaming to {self.csv_path}")
        except Exception as e:
            logger.error(f"Failed to initialize CSV streaming: {e}")
    
    def _stream_loop(self) -> None:
        """Main streaming loop."""
        while self._streaming:
            try:
                self._stream_current_metrics()
                time.sleep(self.stream_interval)
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                time.sleep(self.stream_interval)
    
    def _stream_current_metrics(self) -> None:
        """Stream current metrics to files."""
        current_time = time.time()
        algo_metrics = self.metrics_collector.algorithm_metrics
        sys_metrics = self.metrics_collector.system_metrics
        
        # Stream to CSV
        if self._csv_writer and self._csv_file:
            row = {
                'timestamp': current_time,
                'iteration': algo_metrics.iteration,
                'current_fitness': algo_metrics.current_fitness if algo_metrics.current_fitness != float('inf') else None,
                'best_fitness': algo_metrics.best_fitness if algo_metrics.best_fitness != float('inf') else None,
                'population_diversity': algo_metrics.population_diversity,
                'convergence_rate': algo_metrics.convergence_rate,
                'stagnation_counter': algo_metrics.stagnation_counter,
                'exploration_ratio': algo_metrics.exploration_ratio,
                'constraint_violations': algo_metrics.constraint_violations,
                'improvement_rate': algo_metrics.improvement_rate,
                'elapsed_time': algo_metrics.elapsed_time,
                'time_per_iteration': algo_metrics.time_per_iteration,
                'estimated_completion': algo_metrics.estimated_completion,
                'cpu_percent': sys_metrics.cpu_percent,
                'memory_percent': sys_metrics.memory_percent,
                'memory_used_mb': sys_metrics.memory_used_mb,
                'disk_io_read': sys_metrics.disk_io_read,
                'disk_io_write': sys_metrics.disk_io_write,
                'network_io_sent': sys_metrics.network_io_sent,
                'network_io_recv': sys_metrics.network_io_recv,
                'temperature': sys_metrics.temperature,
                'process_count': sys_metrics.process_count
            }
            
            self._csv_writer.writerow(row)
            self._csv_file.flush()
    
    def export_current(self) -> str:
        """
        Export current metrics state.
        
        Returns:
            Path to exported file
        """
        data = self.metrics_collector.export_metrics()
        
        if self.export_format in ['json', 'both']:
            self._export_json(data, self.json_path)
        
        if self.export_format in ['csv', 'both']:
            self._export_csv(data, self.csv_path)
        
        return str(self.base_path)
    
    def export_final(self) -> str:
        """
        Export final metrics with summary statistics.
        
        Returns:
            Path to exported file
        """
        data = self.metrics_collector.export_metrics()
        
        # Add summary statistics
        data['summary'] = self._calculate_summary_stats(data)
        
        # Export with final suffix
        if self.export_format in ['json', 'both']:
            final_json_path = self.base_path.with_name(f"{self.base_path.name}_final.json")
            self._export_json(data, final_json_path)
        
        if self.export_format in ['csv', 'both']:
            final_csv_path = self.base_path.with_name(f"{self.base_path.name}_final.csv")
            self._export_csv(data, final_csv_path)
        
        return str(self.base_path)
    
    def _export_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """Export data to JSON format."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported JSON metrics to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
    
    def _export_csv(self, data: Dict[str, Any], file_path: Path) -> None:
        """Export data to CSV format."""
        try:
            # Convert time series data to flat records
            records = []
            
            # Process full history if available
            if 'full_history' in data and data['full_history']:
                for record in data['full_history']:
                    flat_record = {
                        'timestamp': record['timestamp'],
                        **record['algorithm'],
                        **{f"system_{k}": v for k, v in record['system'].items()}
                    }
                    records.append(flat_record)
            else:
                # Fallback to time series data
                fitness_data = data.get('time_series', {}).get('fitness', [])
                cpu_data = data.get('time_series', {}).get('cpu', [])
                memory_data = data.get('time_series', {}).get('memory', [])
                
                # Combine time series
                for i, (timestamp, fitness) in enumerate(fitness_data):
                    record = {
                        'timestamp': timestamp,
                        'fitness': fitness,
                        'cpu_percent': cpu_data[i][1] if i < len(cpu_data) else None,
                        'memory_percent': memory_data[i][1] if i < len(memory_data) else None
                    }
                    records.append(record)
            
            if records:
                # Write CSV
                with open(file_path, 'w', newline='') as f:
                    if records:
                        writer = csv.DictWriter(f, fieldnames=records[0].keys())
                        writer.writeheader()
                        writer.writerows(records)
                
                logger.info(f"Exported CSV metrics to {file_path} ({len(records)} records)")
            else:
                logger.warning("No data to export to CSV")
                
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
    
    def _calculate_summary_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics from metrics data."""
        summary = {
            'total_duration': data['metadata']['duration'],
            'total_samples': data['metadata']['total_samples'],
            'collection_rate': data['metadata']['total_samples'] / max(data['metadata']['duration'], 1)
        }
        
        # Algorithm summary
        algo_current = data['current_metrics']['algorithm']
        summary['algorithm'] = {
            'final_iteration': algo_current['iteration'],
            'final_best_fitness': algo_current['best_fitness'],
            'final_diversity': algo_current['population_diversity'],
            'average_time_per_iteration': algo_current['time_per_iteration'],
            'total_stagnation': algo_current['stagnation_counter']
        }
        
        # System summary
        sys_current = data['current_metrics']['system']
        summary['system'] = {
            'peak_cpu': sys_current['cpu_percent'],
            'peak_memory': sys_current['memory_percent'],
            'final_memory_mb': sys_current['memory_used_mb'],
            'final_process_count': sys_current['process_count']
        }
        
        # Calculate statistics from time series
        if data['time_series']:
            fitness_data = data['time_series'].get('fitness', [])
            if fitness_data:
                fitness_values = [f for _, f in fitness_data]
                summary['algorithm'].update({
                    'min_fitness': min(fitness_values),
                    'max_fitness': max(fitness_values),
                    'fitness_improvement': fitness_values[0] - fitness_values[-1] if len(fitness_values) > 1 else 0
                })
            
            cpu_data = data['time_series'].get('cpu', [])
            if cpu_data:
                cpu_values = [c for _, c in cpu_data]
                summary['system'].update({
                    'avg_cpu': sum(cpu_values) / len(cpu_values),
                    'max_cpu': max(cpu_values),
                    'min_cpu': min(cpu_values)
                })
            
            memory_data = data['time_series'].get('memory', [])
            if memory_data:
                memory_values = [m for _, m in memory_data]
                summary['system'].update({
                    'avg_memory': sum(memory_values) / len(memory_values),
                    'max_memory': max(memory_values),
                    'min_memory': min(memory_values)
                })
        
        return summary
    
    def export_to_dataframe(self) -> Optional['pd.DataFrame']:
        """
        Export metrics to pandas DataFrame.
        
        Returns:
            DataFrame with metrics data (None if pandas not available)
        """
        if not PANDAS_AVAILABLE:
            logger.warning("Pandas not available for DataFrame export")
            return None
        
        try:
            data = self.metrics_collector.export_metrics()
            
            # Convert full history to DataFrame
            if 'full_history' in data and data['full_history']:
                records = []
                for record in data['full_history']:
                    flat_record = {
                        'timestamp': pd.to_datetime(record['timestamp'], unit='s'),
                        **record['algorithm'],
                        **{f"system_{k}": v for k, v in record['system'].items()}
                    }
                    records.append(flat_record)
                
                df = pd.DataFrame(records)
                df.set_index('timestamp', inplace=True)
                
                logger.info(f"Created DataFrame with {len(df)} records")
                return df
            else:
                logger.warning("No full history data available for DataFrame")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create DataFrame: {e}")
            return None
    
    def export_time_series(self, metric_name: str, format: str = 'json') -> str:
        """
        Export specific time series data.
        
        Args:
            metric_name: Name of metric to export ('fitness', 'cpu', 'memory', etc.)
            format: Export format ('json', 'csv')
        
        Returns:
            Path to exported file
        """
        data = self.metrics_collector.get_time_series_data(metric_name)
        
        output_path = self.base_path.with_name(f"{self.base_path.name}_{metric_name}")
        
        if format == 'json':
            output_path = output_path.with_suffix('.json')
            export_data = {
                'metric': metric_name,
                'data': data,
                'length': len(data),
                'export_time': time.time()
            }
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif format == 'csv':
            output_path = output_path.with_suffix('.csv')
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'value'])
                writer.writerows(data)
        
        logger.info(f"Exported {metric_name} time series to {output_path}")
        return str(output_path)
    
    def get_export_summary(self) -> Dict[str, Any]:
        """Get summary of export configuration and status."""
        return {
            'base_path': str(self.base_path),
            'export_format': self.export_format,
            'streaming': self._streaming,
            'stream_interval': self.stream_interval,
            'files': {
                'json': str(self.json_path) if self.export_format in ['json', 'both'] else None,
                'csv': str(self.csv_path) if self.export_format in ['csv', 'both'] else None
            },
            'metrics_available': len(self.metrics_collector.metrics_history) > 0
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()