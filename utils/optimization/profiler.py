"""
Performance profiling integration for algorithm optimization.

This module provides comprehensive profiling tools to identify performance
bottlenecks and optimize algorithm execution.
"""

import time
import cProfile
import pstats
import io
import functools
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
import tracemalloc
import sys

try:
    import line_profiler
    LINE_PROFILER_AVAILABLE = True
except ImportError:
    LINE_PROFILER_AVAILABLE = False

try:
    import memory_profiler
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Container for profiling results."""
    function_name: str
    total_time: float
    calls: int
    time_per_call: float
    cumulative_time: float
    memory_peak_mb: Optional[float] = None
    memory_allocated_mb: Optional[float] = None
    line_stats: Optional[Dict[int, Dict[str, float]]] = None
    call_stack: Optional[List[Tuple[str, float]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'function_name': self.function_name,
            'total_time': self.total_time,
            'calls': self.calls,
            'time_per_call': self.time_per_call,
            'cumulative_time': self.cumulative_time,
            'memory_peak_mb': self.memory_peak_mb,
            'memory_allocated_mb': self.memory_allocated_mb,
            'line_stats': self.line_stats,
            'call_stack': self.call_stack
        }


@dataclass
class ProfileReport:
    """Comprehensive profiling report."""
    start_time: float
    end_time: float
    duration: float
    results: List[ProfileResult]
    hotspots: List[Tuple[str, float]]  # Function name, percentage of time
    memory_summary: Optional[Dict[str, float]] = None
    recommendations: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            f"Profile Report",
            f"=" * 50,
            f"Duration: {self.duration:.3f}s",
            f"Functions profiled: {len(self.results)}",
            "",
            "Top 5 Hotspots:",
        ]
        
        for func, percentage in self.hotspots[:5]:
            lines.append(f"  {func}: {percentage:.1f}%")
        
        if self.memory_summary:
            lines.extend([
                "",
                "Memory Summary:",
                f"  Peak: {self.memory_summary['peak_mb']:.1f}MB",
                f"  Allocated: {self.memory_summary['allocated_mb']:.1f}MB"
            ])
        
        if self.recommendations:
            lines.extend([
                "",
                "Recommendations:",
            ])
            for rec in self.recommendations:
                lines.append(f"  - {rec}")
        
        return "\n".join(lines)


class PerformanceProfiler:
    """
    Comprehensive performance profiler for algorithm optimization.
    
    Features:
    - CPU time profiling
    - Memory profiling
    - Line-by-line profiling
    - Hot spot detection
    - Automatic bottleneck identification
    - Performance recommendations
    
    Example:
        >>> profiler = PerformanceProfiler()
        >>> with profiler.profile("algorithm_run"):
        ...     result = algorithm.run()
        >>> report = profiler.generate_report()
        >>> print(report.get_summary())
    """
    
    def __init__(
        self,
        enable_memory: bool = True,
        enable_line_profiler: bool = False,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize performance profiler.
        
        Args:
            enable_memory: Enable memory profiling
            enable_line_profiler: Enable line-by-line profiling
            output_dir: Directory for profiling outputs
        """
        self.enable_memory = enable_memory and MEMORY_PROFILER_AVAILABLE
        self.enable_line_profiler = enable_line_profiler and LINE_PROFILER_AVAILABLE
        self.output_dir = output_dir
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Profiling data
        self._profiles: Dict[str, Any] = {}
        self._timings: Dict[str, List[float]] = defaultdict(list)
        self._memory_snapshots: Dict[str, Any] = {}
        self._current_profile = None
        
        # Memory tracking
        if self.enable_memory:
            tracemalloc.start()
        
        logger.info(f"Initialized PerformanceProfiler (memory={self.enable_memory}, "
                   f"line_profiler={self.enable_line_profiler})")
    
    @contextmanager
    def profile(self, name: str = "main"):
        """
        Profile a code section.
        
        Args:
            name: Name for this profile section
            
        Example:
            >>> with profiler.profile("optimization_loop"):
            ...     for i in range(100):
            ...         optimize_step()
        """
        # Start CPU profiling
        cpu_profiler = cProfile.Profile()
        cpu_profiler.enable()
        
        # Memory snapshot before
        if self.enable_memory:
            snapshot_before = tracemalloc.take_snapshot()
        
        start_time = time.time()
        self._current_profile = name
        
        try:
            yield self
        finally:
            # Stop CPU profiling
            cpu_profiler.disable()
            end_time = time.time()
            
            # Memory snapshot after
            if self.enable_memory:
                snapshot_after = tracemalloc.take_snapshot()
                self._memory_snapshots[name] = {
                    'before': snapshot_before,
                    'after': snapshot_after
                }
            
            # Store profile data
            self._profiles[name] = {
                'cpu_profile': cpu_profiler,
                'duration': end_time - start_time,
                'start_time': start_time,
                'end_time': end_time
            }
            
            self._current_profile = None
    
    def time_function(self, name: Optional[str] = None):
        """
        Decorator for timing function execution.
        
        Args:
            name: Custom name for the timing
            
        Example:
            >>> @profiler.time_function()
            ... def expensive_operation(x):
            ...     return x ** 2
        """
        def decorator(func):
            timing_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    self._timings[timing_name].append(duration)
            
            return wrapper
        return decorator
    
    def analyze_profile(self, name: str) -> List[ProfileResult]:
        """Analyze a specific profile."""
        if name not in self._profiles:
            return []
        
        profile_data = self._profiles[name]
        cpu_profile = profile_data['cpu_profile']
        
        # Analyze CPU profile
        stats = pstats.Stats(cpu_profile)
        stats.sort_stats('cumulative')
        
        results = []
        
        # Extract function statistics
        for func_info, (cc, nc, tt, ct, callers) in stats.stats.items():
            filename, line_num, func_name = func_info
            
            # Skip built-in functions unless significant
            if filename.startswith('<') and tt < 0.01:
                continue
            
            result = ProfileResult(
                function_name=f"{filename}:{line_num}({func_name})",
                total_time=tt,
                calls=nc,
                time_per_call=tt / nc if nc > 0 else 0,
                cumulative_time=ct
            )
            
            results.append(result)
        
        # Add memory information if available
        if self.enable_memory and name in self._memory_snapshots:
            memory_stats = self._analyze_memory(name)
            for result in results:
                result.memory_peak_mb = memory_stats.get('peak_mb')
                result.memory_allocated_mb = memory_stats.get('allocated_mb')
        
        return results
    
    def _analyze_memory(self, name: str) -> Dict[str, float]:
        """Analyze memory usage for a profile."""
        if name not in self._memory_snapshots:
            return {}
        
        snapshots = self._memory_snapshots[name]
        snapshot_before = snapshots['before']
        snapshot_after = snapshots['after']
        
        # Calculate differences
        top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        
        total_allocated = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        peak_memory = snapshot_after.traceback._total_nframe
        
        return {
            'allocated_mb': total_allocated / (1024 * 1024),
            'peak_mb': peak_memory / (1024 * 1024)
        }
    
    def generate_report(self) -> ProfileReport:
        """Generate comprehensive profiling report."""
        all_results = []
        total_duration = 0
        
        # Analyze all profiles
        for name, profile_data in self._profiles.items():
            results = self.analyze_profile(name)
            all_results.extend(results)
            total_duration += profile_data['duration']
        
        # Calculate hotspots
        total_time = sum(r.cumulative_time for r in all_results)
        hotspots = []
        
        if total_time > 0:
            for result in sorted(all_results, key=lambda r: r.cumulative_time, reverse=True):
                percentage = (result.cumulative_time / total_time) * 100
                hotspots.append((result.function_name, percentage))
        
        # Memory summary
        memory_summary = None
        if self.enable_memory:
            peak_mb = max((r.memory_peak_mb or 0) for r in all_results) if all_results else 0
            allocated_mb = sum((r.memory_allocated_mb or 0) for r in all_results)
            memory_summary = {
                'peak_mb': peak_mb,
                'allocated_mb': allocated_mb
            }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_results, hotspots)
        
        # Get timing statistics
        start_time = min(p['start_time'] for p in self._profiles.values()) if self._profiles else 0
        end_time = max(p['end_time'] for p in self._profiles.values()) if self._profiles else 0
        
        return ProfileReport(
            start_time=start_time,
            end_time=end_time,
            duration=total_duration,
            results=all_results,
            hotspots=hotspots,
            memory_summary=memory_summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        results: List[ProfileResult],
        hotspots: List[Tuple[str, float]]
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Check for functions taking >20% of time
        for func, percentage in hotspots:
            if percentage > 20:
                recommendations.append(
                    f"Function '{func}' takes {percentage:.1f}% of execution time. "
                    "Consider optimization or caching."
                )
        
        # Check for functions called many times
        for result in results:
            if result.calls > 10000 and result.time_per_call > 0.00001:
                recommendations.append(
                    f"Function '{result.function_name}' called {result.calls} times. "
                    "Consider vectorization or batching."
                )
        
        # Memory recommendations
        if self.enable_memory:
            peak_mb = max((r.memory_peak_mb or 0) for r in results) if results else 0
            if peak_mb > 1000:  # 1GB
                recommendations.append(
                    f"High memory usage detected ({peak_mb:.1f}MB). "
                    "Consider streaming processing or memory optimization."
                )
        
        # Timing variations
        for name, timings in self._timings.items():
            if len(timings) > 10:
                std_dev = np.std(timings)
                mean_time = np.mean(timings)
                cv = std_dev / mean_time if mean_time > 0 else 0
                
                if cv > 0.5:  # High variation
                    recommendations.append(
                        f"High timing variation in '{name}' (CV={cv:.2f}). "
                        "Consider investigating system load or algorithm stability."
                    )
        
        return recommendations
    
    def save_report(self, report: ProfileReport, filename: Optional[str] = None):
        """Save profiling report to file."""
        if not self.output_dir:
            logger.warning("No output directory specified")
            return
        
        filename = filename or f"profile_report_{int(time.time())}.txt"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write(report.get_summary())
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("Detailed Results:\n\n")
            
            # Write detailed results
            for result in sorted(report.results, key=lambda r: r.cumulative_time, reverse=True):
                f.write(f"Function: {result.function_name}\n")
                f.write(f"  Total time: {result.total_time:.6f}s\n")
                f.write(f"  Calls: {result.calls}\n")
                f.write(f"  Time per call: {result.time_per_call:.6f}s\n")
                f.write(f"  Cumulative time: {result.cumulative_time:.6f}s\n")
                if result.memory_peak_mb:
                    f.write(f"  Memory peak: {result.memory_peak_mb:.1f}MB\n")
                f.write("\n")
        
        logger.info(f"Saved profiling report to {output_path}")
    
    def get_timing_stats(self, name: str) -> Dict[str, float]:
        """Get timing statistics for a specific function."""
        if name not in self._timings:
            return {}
        
        timings = self._timings[name]
        if not timings:
            return {}
        
        return {
            'count': len(timings),
            'total': sum(timings),
            'mean': np.mean(timings),
            'std': np.std(timings),
            'min': min(timings),
            'max': max(timings),
            'median': np.median(timings)
        }
    
    def clear(self):
        """Clear all profiling data."""
        self._profiles.clear()
        self._timings.clear()
        self._memory_snapshots.clear()
        
        if self.enable_memory and tracemalloc.is_tracing():
            tracemalloc.clear_traces()


# Decorator for quick profiling

def profile_function(
    output_file: Optional[str] = None,
    enable_memory: bool = True
):
    """
    Decorator for profiling function execution.
    
    Args:
        output_file: Optional file to save profile results
        enable_memory: Enable memory profiling
        
    Example:
        >>> @profile_function(output_file="profile.txt")
        ... def optimize_algorithm(data):
        ...     # Algorithm implementation
        ...     pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = PerformanceProfiler(enable_memory=enable_memory)
            
            with profiler.profile(func.__name__):
                result = func(*args, **kwargs)
            
            # Generate and display report
            report = profiler.generate_report()
            print(report.get_summary())
            
            # Save if requested
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                profiler.save_report(report, output_path.name)
            
            return result
        
        return wrapper
    
    return decorator


# Specialized profilers for algorithms

class AlgorithmProfiler(PerformanceProfiler):
    """
    Specialized profiler for algorithm-specific metrics.
    
    Tracks algorithm-specific performance indicators like:
    - Iteration times
    - Population evaluations
    - Convergence rate
    - Memory usage per generation
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Algorithm-specific metrics
        self.iteration_times: List[float] = []
        self.fitness_evaluations: List[int] = []
        self.population_diversity: List[float] = []
        self.best_fitness_history: List[float] = []
    
    def record_iteration(
        self,
        iteration: int,
        duration: float,
        evaluations: int,
        best_fitness: float,
        diversity: Optional[float] = None
    ):
        """Record metrics for an algorithm iteration."""
        self.iteration_times.append(duration)
        self.fitness_evaluations.append(evaluations)
        self.best_fitness_history.append(best_fitness)
        
        if diversity is not None:
            self.population_diversity.append(diversity)
    
    def get_algorithm_summary(self) -> Dict[str, Any]:
        """Get algorithm-specific performance summary."""
        if not self.iteration_times:
            return {}
        
        total_evaluations = sum(self.fitness_evaluations)
        
        return {
            'iterations': len(self.iteration_times),
            'total_time': sum(self.iteration_times),
            'avg_iteration_time': np.mean(self.iteration_times),
            'total_evaluations': total_evaluations,
            'evaluations_per_second': total_evaluations / sum(self.iteration_times),
            'convergence_rate': self._calculate_convergence_rate(),
            'memory_efficiency': self._calculate_memory_efficiency()
        }
    
    def _calculate_convergence_rate(self) -> float:
        """Calculate convergence rate."""
        if len(self.best_fitness_history) < 2:
            return 0.0
        
        # Calculate improvement rate
        improvements = []
        for i in range(1, len(self.best_fitness_history)):
            prev = self.best_fitness_history[i-1]
            curr = self.best_fitness_history[i]
            if prev != 0:
                improvement = abs((curr - prev) / prev)
                improvements.append(improvement)
        
        return np.mean(improvements) if improvements else 0.0
    
    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory efficiency metric."""
        if not self.enable_memory:
            return 0.0
        
        # Memory per evaluation
        report = self.generate_report()
        if report.memory_summary and self.fitness_evaluations:
            total_memory = report.memory_summary['allocated_mb']
            total_evaluations = sum(self.fitness_evaluations)
            return total_evaluations / total_memory if total_memory > 0 else 0.0
        
        return 0.0