"""
Terminal-based real-time dashboard for algorithm monitoring.

This module provides a text-based user interface (TUI) for displaying
real-time algorithm performance and system metrics in the terminal.
"""

import time
import threading
from typing import Optional, Dict, Any, List, Tuple
import logging
from datetime import datetime, timedelta

# Try to import rich for better terminal display
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.rule import Rule
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .metrics_collector import MetricsCollector, AlgorithmMetrics, SystemMetrics

logger = logging.getLogger(__name__)


class TerminalDashboard:
    """
    Terminal-based real-time dashboard for monitoring algorithm performance.
    
    Provides a comprehensive view of algorithm metrics, system resources,
    and progress tracking in a terminal interface.
    
    Features:
    - Real-time algorithm metrics display
    - System resource monitoring
    - Fitness progression graphs
    - Estimated time to completion
    - Interactive controls (pause/resume)
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        refresh_rate: float = 1.0,
        use_rich: bool = True
    ):
        """
        Initialize terminal dashboard.
        
        Args:
            metrics_collector: MetricsCollector instance to monitor
            refresh_rate: Display refresh rate in seconds
            use_rich: Whether to use rich library for enhanced display
        """
        self.metrics_collector = metrics_collector
        self.refresh_rate = refresh_rate
        self.use_rich = use_rich and RICH_AVAILABLE
        
        # Display state
        self._running = False
        self._paused = False
        self._display_thread: Optional[threading.Thread] = None
        
        # Rich components
        if self.use_rich:
            self.console = Console()
            self.layout = Layout()
            self._setup_rich_layout()
        
        # Simple terminal fallback
        self._last_display_time = 0
        self._start_time = time.time()
        
        # Register as callback
        self.metrics_collector.add_callback(self._on_metrics_update)
        
        logger.info(f"Terminal dashboard initialized (rich={self.use_rich})")
    
    def _setup_rich_layout(self) -> None:
        """Setup Rich library layout structure."""
        if not self.use_rich:
            return
        
        # Create main layout
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Split main area
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Split left panel
        self.layout["left"].split_column(
            Layout(name="algorithm", ratio=2),
            Layout(name="progress", ratio=1)
        )
        
        # Split right panel
        self.layout["right"].split_column(
            Layout(name="system", ratio=1),
            Layout(name="charts", ratio=2)
        )
    
    def start(self) -> None:
        """Start the dashboard display."""
        if self._running:
            return
        
        self._running = True
        self._start_time = time.time()
        
        if self.use_rich:
            self._start_rich_display()
        else:
            self._start_simple_display()
        
        logger.info("Terminal dashboard started")
    
    def stop(self) -> None:
        """Stop the dashboard display."""
        self._running = False
        
        if self._display_thread:
            self._display_thread.join(timeout=2.0)
        
        if self.use_rich:
            self.console.print("\n[bold green]Dashboard stopped[/bold green]")
        else:
            print("\nDashboard stopped")
        
        logger.info("Terminal dashboard stopped")
    
    def pause(self) -> None:
        """Pause the dashboard updates."""
        self._paused = True
    
    def resume(self) -> None:
        """Resume the dashboard updates."""
        self._paused = False
    
    def _start_rich_display(self) -> None:
        """Start Rich-based display."""
        def display_loop():
            with Live(self.layout, console=self.console, refresh_per_second=1/self.refresh_rate):
                while self._running:
                    if not self._paused:
                        self._update_rich_display()
                    time.sleep(self.refresh_rate)
        
        self._display_thread = threading.Thread(target=display_loop, daemon=True)
        self._display_thread.start()
    
    def _start_simple_display(self) -> None:
        """Start simple text-based display."""
        def display_loop():
            while self._running:
                if not self._paused:
                    self._update_simple_display()
                time.sleep(self.refresh_rate)
        
        self._display_thread = threading.Thread(target=display_loop, daemon=True)
        self._display_thread.start()
    
    def _update_rich_display(self) -> None:
        """Update Rich-based display components."""
        try:
            algo_metrics = self.metrics_collector.algorithm_metrics
            sys_metrics = self.metrics_collector.system_metrics
            
            # Update header
            self._update_header()
            
            # Update algorithm panel
            self._update_algorithm_panel(algo_metrics)
            
            # Update progress panel
            self._update_progress_panel(algo_metrics)
            
            # Update system panel
            self._update_system_panel(sys_metrics)
            
            # Update charts panel
            self._update_charts_panel()
            
            # Update footer
            self._update_footer()
            
        except Exception as e:
            logger.error(f"Error updating rich display: {e}")
    
    def _update_header(self) -> None:
        """Update header panel."""
        current_time = datetime.now().strftime("%H:%M:%S")
        uptime = timedelta(seconds=int(time.time() - self._start_time))
        
        title = Text("BioAlgoCompare Real-Time Monitor", style="bold cyan")
        subtitle = Text(f"Time: {current_time} | Uptime: {uptime}", style="dim")
        
        header_content = Align.center(
            Columns([title, subtitle], equal=True)
        )
        
        self.layout["header"].update(
            Panel(header_content, style="blue", padding=(0, 1))
        )
    
    def _update_algorithm_panel(self, metrics: AlgorithmMetrics) -> None:
        """Update algorithm metrics panel."""
        table = Table(title="Algorithm Metrics", show_header=False, box=None)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        # Format values
        fitness_str = f"{metrics.best_fitness:.6f}" if metrics.best_fitness != float('inf') else "N/A"
        current_fitness_str = f"{metrics.current_fitness:.6f}" if metrics.current_fitness != float('inf') else "N/A"
        diversity_str = f"{metrics.population_diversity:.4f}"
        convergence_str = f"{metrics.convergence_rate:.6f}"
        improvement_str = f"{metrics.improvement_rate:.4f}%"
        
        # Add rows
        table.add_row("Iteration", str(metrics.iteration))
        table.add_row("Best Fitness", fitness_str)
        table.add_row("Current Fitness", current_fitness_str)
        table.add_row("Diversity", diversity_str)
        table.add_row("Convergence Rate", convergence_str)
        table.add_row("Improvement", improvement_str)
        table.add_row("Stagnation", str(metrics.stagnation_counter))
        table.add_row("Exploration", f"{metrics.exploration_ratio:.2f}")
        
        self.layout["algorithm"].update(Panel(table, style="green"))
    
    def _update_progress_panel(self, metrics: AlgorithmMetrics) -> None:
        """Update progress panel."""
        table = Table(title="Progress", show_header=False, box=None)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        # Time formatting
        elapsed_str = str(timedelta(seconds=int(metrics.elapsed_time)))
        time_per_iter = f"{metrics.time_per_iteration:.3f}s" if metrics.time_per_iteration > 0 else "N/A"
        eta_str = str(timedelta(seconds=int(metrics.estimated_completion))) if metrics.estimated_completion > 0 else "N/A"
        
        table.add_row("Elapsed Time", elapsed_str)
        table.add_row("Time/Iteration", time_per_iter)
        table.add_row("ETA", eta_str)
        table.add_row("Violations", str(metrics.constraint_violations))
        
        self.layout["progress"].update(Panel(table, style="yellow"))
    
    def _update_system_panel(self, metrics: SystemMetrics) -> None:
        """Update system metrics panel."""
        table = Table(title="System Resources", show_header=False, box=None)
        table.add_column("Resource", style="cyan", width=15)
        table.add_column("Value", style="white")
        
        # CPU with color coding
        cpu_color = "red" if metrics.cpu_percent > 80 else "yellow" if metrics.cpu_percent > 60 else "green"
        cpu_text = Text(f"{metrics.cpu_percent:.1f}%", style=cpu_color)
        
        # Memory with color coding
        mem_color = "red" if metrics.memory_percent > 80 else "yellow" if metrics.memory_percent > 60 else "green"
        mem_text = Text(f"{metrics.memory_percent:.1f}%", style=mem_color)
        mem_mb_text = Text(f"({metrics.memory_used_mb:.0f} MB)", style="dim")
        
        table.add_row("CPU", cpu_text)
        table.add_row("Memory", Columns([mem_text, mem_mb_text]))
        table.add_row("Processes", str(metrics.process_count))
        
        if metrics.temperature is not None:
            temp_color = "red" if metrics.temperature > 70 else "yellow" if metrics.temperature > 60 else "green"
            temp_text = Text(f"{metrics.temperature:.1f}°C", style=temp_color)
            table.add_row("CPU Temp", temp_text)
        
        if metrics.load_average:
            load_str = " | ".join(f"{load:.2f}" for load in metrics.load_average[:3])
            table.add_row("Load Avg", load_str)
        
        self.layout["system"].update(Panel(table, style="magenta"))
    
    def _update_charts_panel(self) -> None:
        """Update charts panel with ASCII graphs."""
        try:
            # Get recent fitness history
            fitness_data = self.metrics_collector.get_time_series_data('fitness')
            cpu_data = self.metrics_collector.get_time_series_data('cpu')
            
            charts_content = []
            
            # Fitness chart
            if fitness_data:
                fitness_chart = self._create_ascii_chart(
                    fitness_data[-20:],  # Last 20 points
                    title="Fitness Trend",
                    width=40,
                    height=8
                )
                charts_content.append(fitness_chart)
            
            # CPU chart
            if cpu_data:
                cpu_chart = self._create_ascii_chart(
                    cpu_data[-20:],  # Last 20 points
                    title="CPU Usage %",
                    width=40,
                    height=6
                )
                charts_content.append(cpu_chart)
            
            if charts_content:
                content = "\n".join(charts_content)
            else:
                content = "No data available yet..."
            
            self.layout["charts"].update(Panel(content, title="Charts", style="blue"))
            
        except Exception as e:
            logger.error(f"Error updating charts: {e}")
            self.layout["charts"].update(Panel("Chart update error", style="red"))
    
    def _create_ascii_chart(
        self,
        data: List[Tuple[float, float]],
        title: str,
        width: int = 40,
        height: int = 8
    ) -> str:
        """Create ASCII chart from time series data."""
        if not data or len(data) < 2:
            return f"{title}: No data"
        
        values = [v for _, v in data]
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            # All values are the same
            chart_lines = [f"{title}: {min_val:.3f} (constant)"]
            return "\n".join(chart_lines)
        
        # Normalize values to chart height
        normalized = []
        for val in values:
            norm = int((val - min_val) / (max_val - min_val) * (height - 1))
            normalized.append(norm)
        
        # Create chart
        chart_lines = [f"{title}: {min_val:.3f} -> {max_val:.3f}"]
        
        for row in range(height - 1, -1, -1):
            line = ""
            for col in range(min(len(normalized), width)):
                if normalized[col] >= row:
                    line += "█"
                else:
                    line += " "
            
            # Add value label
            if row == height - 1:
                line += f" {max_val:.3f}"
            elif row == 0:
                line += f" {min_val:.3f}"
            
            chart_lines.append(line)
        
        return "\n".join(chart_lines)
    
    def _update_footer(self) -> None:
        """Update footer panel."""
        controls = [
            "[bold]Controls:[/bold]",
            "[cyan]Space[/cyan]: Pause/Resume",
            "[cyan]Q[/cyan]: Quit",
            "[cyan]R[/cyan]: Reset"
        ]
        
        status = "[green]Running[/green]" if not self._paused else "[yellow]Paused[/yellow]"
        
        footer_content = Columns([
            Text(" | ".join(controls)),
            Text(f"Status: {status}")
        ])
        
        self.layout["footer"].update(
            Panel(Align.center(footer_content), style="blue", padding=(0, 1))
        )
    
    def _update_simple_display(self) -> None:
        """Update simple text-based display."""
        current_time = time.time()
        if current_time - self._last_display_time < self.refresh_rate:
            return
        
        algo_metrics = self.metrics_collector.algorithm_metrics
        sys_metrics = self.metrics_collector.system_metrics
        
        # Clear screen (simple method)
        print("\033[2J\033[H", end="")
        
        # Header
        print("=" * 80)
        print("BioAlgoCompare Real-Time Monitor".center(80))
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}".center(80))
        print("=" * 80)
        
        # Algorithm metrics
        print("\nAlgorithm Metrics:")
        print(f"  Iteration: {algo_metrics.iteration}")
        print(f"  Best Fitness: {algo_metrics.best_fitness:.6f}" if algo_metrics.best_fitness != float('inf') else "  Best Fitness: N/A")
        print(f"  Current Fitness: {algo_metrics.current_fitness:.6f}" if algo_metrics.current_fitness != float('inf') else "  Current Fitness: N/A")
        print(f"  Diversity: {algo_metrics.population_diversity:.4f}")
        print(f"  Convergence Rate: {algo_metrics.convergence_rate:.6f}")
        print(f"  Stagnation: {algo_metrics.stagnation_counter}")
        
        # Progress
        elapsed_str = str(timedelta(seconds=int(algo_metrics.elapsed_time)))
        print(f"\nProgress:")
        print(f"  Elapsed Time: {elapsed_str}")
        print(f"  Time/Iteration: {algo_metrics.time_per_iteration:.3f}s" if algo_metrics.time_per_iteration > 0 else "  Time/Iteration: N/A")
        
        # System metrics
        print(f"\nSystem Resources:")
        print(f"  CPU: {sys_metrics.cpu_percent:.1f}%")
        print(f"  Memory: {sys_metrics.memory_percent:.1f}% ({sys_metrics.memory_used_mb:.0f} MB)")
        print(f"  Processes: {sys_metrics.process_count}")
        
        if sys_metrics.temperature is not None:
            print(f"  CPU Temperature: {sys_metrics.temperature:.1f}°C")
        
        print("\n" + "-" * 80)
        print("Press Ctrl+C to stop monitoring")
        
        self._last_display_time = current_time
    
    def _on_metrics_update(self, algo_metrics: AlgorithmMetrics, sys_metrics: SystemMetrics) -> None:
        """Callback for metrics updates."""
        # In this implementation, updates are handled by the display loop
        # This could be used for additional processing or notifications
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()