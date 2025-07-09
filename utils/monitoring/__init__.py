"""
Performance monitoring system for BioAlgoCompare.

This package provides real-time monitoring capabilities for algorithm execution,
system resources, and optimization metrics.

Components:
    - PerformanceMonitor: Main monitoring orchestrator
    - MetricsCollector: Collects and aggregates metrics
    - TerminalDashboard: TUI-based real-time dashboard
    - WebDashboard: HTTP-based dashboard with live updates
    - MetricsExporter: Export metrics to various formats
"""

from .performance_monitor import PerformanceMonitor
from .metrics_collector import MetricsCollector, AlgorithmMetrics, SystemMetrics
from .terminal_dashboard import TerminalDashboard
from .web_dashboard import WebDashboard
from .metrics_exporter import MetricsExporter

__all__ = [
    'PerformanceMonitor',
    'MetricsCollector',
    'AlgorithmMetrics',
    'SystemMetrics',
    'TerminalDashboard',
    'WebDashboard',
    'MetricsExporter',
]