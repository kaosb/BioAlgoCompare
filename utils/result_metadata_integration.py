"""
Integration module to ensure all algorithm results include complete metadata.

This module provides utilities to automatically capture and include system
metadata in all algorithm executions.
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from utils.result_schema_v2 import (
    StandardResultV2, SystemInfo, GitInfo, ExecutionInfoV2, 
    DependencyInfo, ResultType, ProblemInfo, AlgorithmInfo,
    SingleRunResult, MultiRunStatistics
)
from utils.result_schema import ResultBuilder
from algorithms.base_v2 import MetaheuristicAlgorithm, Individual


T = TypeVar('T', bound=Individual)


class ResourceMonitor:
    """Monitors system resources during algorithm execution."""
    
    def __init__(self, sample_interval: float = 0.5):
        """
        Initialize resource monitor.
        
        Args:
            sample_interval: Seconds between resource samples
        """
        self.sample_interval = sample_interval
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._process = psutil.Process()
    
    def start(self):
        """Start monitoring resources."""
        self._monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Stop monitoring and return statistics."""
        self._monitoring = False
        if self._thread:
            self._thread.join()
        
        return {
            'cpu_samples': self.cpu_samples.copy(),
            'memory_samples': self.memory_samples.copy(),
            'cpu_avg': np.mean(self.cpu_samples) if self.cpu_samples else 0,
            'cpu_max': max(self.cpu_samples) if self.cpu_samples else 0,
            'memory_avg_mb': np.mean(self.memory_samples) if self.memory_samples else 0,
            'memory_peak_mb': max(self.memory_samples) if self.memory_samples else 0
        }
    
    def _monitor_loop(self):
        """Monitor loop that runs in separate thread."""
        while self._monitoring:
            try:
                # CPU usage
                cpu_percent = self._process.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)
                
                # Memory usage
                memory_mb = self._process.memory_info().rss / (1024 * 1024)
                self.memory_samples.append(memory_mb)
                
                # Wait for next sample
                time.sleep(self.sample_interval)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break


class MetadataEnhancedAlgorithm(Generic[T], MetaheuristicAlgorithm[T]):
    """
    Enhanced algorithm base class that automatically captures metadata.
    
    This class wraps algorithm execution to ensure complete metadata
    is captured for every run.
    """
    
    def __init__(
        self,
        problem: Any,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None,
        capture_metadata: bool = True,
        monitor_resources: bool = True
    ):
        """
        Initialize with metadata capture capabilities.
        
        Args:
            problem: Optimization problem
            population_size: Population size
            max_iterations: Maximum iterations
            seed: Random seed
            capture_metadata: Whether to capture system metadata
            monitor_resources: Whether to monitor resource usage
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        self.capture_metadata = capture_metadata
        self.monitor_resources = monitor_resources
        self._resource_monitor = ResourceMonitor() if monitor_resources else None
        self._metadata_captured = False
        
        # Storage for metadata
        self.system_info: Optional[SystemInfo] = None
        self.git_info: Optional[GitInfo] = None
        self.execution_info: Optional[ExecutionInfoV2] = None
        self.dependencies: Optional[List[DependencyInfo]] = None
    
    def execute(self) -> T:
        """Execute algorithm with metadata capture."""
        # Capture metadata before execution
        if self.capture_metadata and not self._metadata_captured:
            self._capture_metadata()
        
        # Start resource monitoring
        if self._resource_monitor:
            self._resource_monitor.start()
        
        # Start execution tracking
        if self.execution_info:
            self.execution_info.start_time = datetime.now()
        
        try:
            # Run the algorithm
            result = super().execute()
            
        finally:
            # Stop resource monitoring
            if self._resource_monitor:
                stats = self._resource_monitor.stop()
                if self.execution_info:
                    self.execution_info.finalize(
                        cpu_samples=stats['cpu_samples'],
                        memory_samples=stats['memory_samples']
                    )
            
            # Finalize execution info
            if self.execution_info:
                self.execution_info.end_time = datetime.now()
                self.execution_info.duration_seconds = (
                    self.execution_info.end_time - self.execution_info.start_time
                ).total_seconds()
        
        return result
    
    def _capture_metadata(self):
        """Capture all system metadata."""
        self.system_info = SystemInfo.capture()
        self.git_info = GitInfo.capture()
        self.execution_info = ExecutionInfoV2.start_tracking(
            seed=self.seed or 0,
            parallel=False
        )
        self.dependencies = DependencyInfo.capture_all()
        self._metadata_captured = True
    
    def get_complete_result(self) -> StandardResultV2:
        """
        Get complete result with all metadata.
        
        Returns:
            StandardResultV2 with full metadata
        """
        # Create problem info
        problem_info = ProblemInfo(
            name=getattr(self.problem, 'name', 'unknown'),
            type=self.problem.__class__.__name__,
            dimension=getattr(self.problem, 'dimension', 0),
            optimal_value=getattr(self.problem, 'optimal_value', None),
            instance_file=getattr(self.problem, 'instance_path', None)
        )
        
        # Create algorithm info
        algorithm_info = AlgorithmInfo(
            name=self.__class__.__name__,
            version='v2',
            population_size=self.population_size,
            max_iterations=self.max_iterations,
            parameters={
                'population_size': self.population_size,
                'max_iterations': self.max_iterations
            },
            seed=self.seed
        )
        
        # Create single run result
        best_solution_value = None
        if self.best_solution:
            if hasattr(self.best_solution.position, 'tolist'):
                best_solution_value = self.best_solution.position.tolist()
            else:
                best_solution_value = self.best_solution.position
        
        run_result = SingleRunResult(
            run_id=0,
            seed=self.seed or 0,
            best_fitness=self.best_solution.fitness() if self.best_solution else float('inf'),
            best_solution=best_solution_value,
            convergence_curve=self.convergence_curve.copy(),
            execution_time=self.get_execution_time(),
            iterations_completed=self.iteration,
            evaluations=self.iteration * self.population_size
        )
        
        # Calculate statistics for single run
        stats = MultiRunStatistics(
            n_runs=1,
            best_fitness=run_result.best_fitness,
            worst_fitness=run_result.best_fitness,
            mean_fitness=run_result.best_fitness,
            std_fitness=0.0,
            median_fitness=run_result.best_fitness,
            q1_fitness=run_result.best_fitness,
            q3_fitness=run_result.best_fitness,
            iqr_fitness=0.0,
            cv_fitness=0.0,
            confidence_interval_95=(run_result.best_fitness, run_result.best_fitness),
            success_rate=1.0 if run_result.best_fitness < float('inf') else 0.0,
            mean_convergence_rate=run_result.get_convergence_rate() if hasattr(run_result, 'get_convergence_rate') else 0.0,
            mean_execution_time=run_result.execution_time,
            total_execution_time=run_result.execution_time
        )
        
        # Create complete result
        result = StandardResultV2(
            result_type=ResultType.SINGLE_RUN,
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[run_result],
            statistics=stats,
            system_info=self.system_info,
            git_info=self.git_info,
            execution_info=self.execution_info,
            dependencies=self.dependencies
        )
        
        # Calculate checksum
        result.checksum = result.calculate_checksum()
        
        return result


def wrap_algorithm_with_metadata(
    algorithm_class: type,
    capture_metadata: bool = True,
    monitor_resources: bool = True
) -> type:
    """
    Create a wrapped version of an algorithm that captures metadata.
    
    Args:
        algorithm_class: Original algorithm class
        capture_metadata: Whether to capture metadata
        monitor_resources: Whether to monitor resources
        
    Returns:
        Wrapped algorithm class
    """
    class_name = f"Metadata{algorithm_class.__name__}"
    
    class WrappedAlgorithm(MetadataEnhancedAlgorithm):
        """Wrapped algorithm with metadata capture."""
        
        def __init__(self, *args, **kwargs):
            # Extract metadata options
            capture_meta = kwargs.pop('capture_metadata', capture_metadata)
            monitor_res = kwargs.pop('monitor_resources', monitor_resources)
            
            # Initialize parent
            super().__init__(
                *args,
                capture_metadata=capture_meta,
                monitor_resources=monitor_res,
                **kwargs
            )
            
            # Create instance of original algorithm
            self._original = algorithm_class(*args, **kwargs)
        
        def _create_individual(self):
            return self._original._create_individual()
        
        def _create_move_context(self):
            return self._original._create_move_context()
        
        def initialize_population(self):
            # Use original initialization
            self._original.initialize_population()
            self.population = self._original.population
            self.best_solution = self._original.best_solution
            self.convergence_curve = self._original.convergence_curve
        
        def update_population(self):
            # Use original update
            self._original.update_population()
            self.population = self._original.population
            self.best_solution = self._original.best_solution
            self.convergence_curve = self._original.convergence_curve
            self.iteration = self._original.iteration
    
    # Set class name and return
    WrappedAlgorithm.__name__ = class_name
    WrappedAlgorithm.__qualname__ = class_name
    
    return WrappedAlgorithm


def ensure_metadata_in_result(result: Dict[str, Any]) -> StandardResultV2:
    """
    Ensure a result dictionary contains complete metadata.
    
    If metadata is missing, it will be captured at the time of calling.
    
    Args:
        result: Result dictionary
        
    Returns:
        StandardResultV2 with complete metadata
    """
    # Check if already a StandardResultV2
    if isinstance(result, StandardResultV2):
        return result
    
    # Create problem info
    problem_info = ProblemInfo(
        name=result.get('instance_name', 'unknown'),
        type=result.get('problem_type', 'VRP'),
        dimension=result.get('dimension', 0),
        optimal_value=result.get('optimal_value')
    )
    
    # Create algorithm info
    algorithm_info = AlgorithmInfo(
        name=result.get('algorithm_name', 'Unknown'),
        version='v2',
        population_size=result.get('population_size', 30),
        max_iterations=result.get('max_iterations', 100),
        parameters=result.get('parameters', {}),
        seed=result.get('seed')
    )
    
    # Create runs
    runs = []
    if 'runs' in result:
        for i, run in enumerate(result['runs']):
            runs.append(SingleRunResult(
                run_id=i,
                seed=run.get('seed', result.get('seed', 0)),
                best_fitness=run.get('fitness', float('inf')),
                best_solution=run.get('solution'),
                convergence_curve=run.get('convergence_curve', []),
                execution_time=run.get('execution_time', 0),
                iterations_completed=run.get('iterations', 100),
                evaluations=run.get('evaluations', 0)
            ))
    else:
        # Single run
        runs.append(SingleRunResult(
            run_id=0,
            seed=result.get('seed', 0),
            best_fitness=result.get('fitness', float('inf')),
            best_solution=result.get('solution'),
            convergence_curve=result.get('convergence_curve', []),
            execution_time=result.get('execution_time', 0),
            iterations_completed=result.get('iterations', 100),
            evaluations=result.get('evaluations', 0)
        ))
    
    # Calculate statistics
    statistics = MultiRunStatistics.from_runs(runs)
    
    # Determine result type
    result_type = ResultType.SINGLE_RUN if len(runs) == 1 else ResultType.MULTI_RUN
    
    # Create execution info
    execution_info = ExecutionInfoV2.start_tracking(
        seed=result.get('seed', 0),
        parallel=result.get('parallel', False)
    )
    execution_info.finalize()
    
    # Create enhanced result with metadata
    enhanced_result = StandardResultV2(
        result_type=result_type,
        problem_info=problem_info,
        algorithm_info=algorithm_info,
        runs=runs,
        statistics=statistics,
        system_info=SystemInfo.capture(),
        git_info=GitInfo.capture(),
        execution_info=execution_info,
        dependencies=DependencyInfo.capture_all()
    )
    
    # Calculate checksum
    enhanced_result.checksum = enhanced_result.calculate_checksum()
    
    return enhanced_result